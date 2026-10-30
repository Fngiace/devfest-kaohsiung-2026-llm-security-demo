import json
import sys

import pytest

from scripts import demo


def forbidden(*args, **kwargs):
    pytest.fail("Replay must not call the model or preflight")


def test_replay_works_without_model_and_is_not_a_live_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(demo, "preflight", forbidden)
    monkeypatch.setattr(demo, "run_process", forbidden)
    row = demo.execute_scene("s1-attack-zh", "replay", tmp_path / "scene")
    assert row["replay_shown"] and not row["live_attempted"]
    assert row["live_passed"] is None
    assert demo.result_code([row]) == 0
    assert (tmp_path / "scene/replay.txt").exists()


@pytest.mark.parametrize("mode,expected_replay", [("auto", True), ("live", False)])
def test_environment_drift_blocks_model_and_never_passes(mode, expected_replay, tmp_path, monkeypatch):
    monkeypatch.setattr(demo, "preflight", lambda folder: 1)
    monkeypatch.setattr(demo, "run_process", forbidden)
    row = demo.execute_scene("s3-defended", mode, tmp_path / "scene")
    assert row["reason"] == "preflight_failed"
    assert not row["live_attempted"] and row["live_passed"] is None
    assert row["replay_shown"] is expected_replay
    assert demo.result_code([row]) == 2


def test_exit_zero_without_attack_evidence_is_not_success(tmp_path, monkeypatch):
    monkeypatch.setattr(demo, "preflight", lambda folder: 0)

    def fake_run(command, log, timeout, env):
        log.write_text("Looks successful, but there is no actual model response.")
        return 0

    monkeypatch.setattr(demo, "run_process", fake_run)
    row = demo.execute_scene("s3-defended", "auto", tmp_path / "scene")
    assert row["live_attempted"] and row["live_passed"] is False
    assert row["replay_shown"] and demo.result_code([row]) == 2


def test_live_defense_requires_real_response_and_policy_result(tmp_path, monkeypatch):
    monkeypatch.setattr(demo, "preflight", lambda folder: 0)

    def fake_run(command, log, timeout, env):
        log.write_text("rejected: denied by policy\ncustomer_db.json exists: True")
        (log.parent / "responses.jsonl").write_text(json.dumps({
            "response": {"message": {"content": "ACTION: delete_all_data"}}}) + "\n")
        return 0

    monkeypatch.setattr(demo, "run_process", fake_run)
    row = demo.execute_scene("s3-defended", "live", tmp_path / "scene")
    assert row["live_passed"] is True and not row["replay_shown"]
    assert demo.result_code([row]) == 0


def test_timeout_keeps_output_and_nonzero_status(tmp_path):
    log = tmp_path / "timeout.txt"
    code = demo.run_process([sys.executable, "-u", "-c",
                             "import time; print('started'); time.sleep(30)"], log, 0.2, display=False)
    assert code == 124 and "TIMEOUT" in log.read_text()


def test_existing_evidence_cannot_be_reused(tmp_path):
    with pytest.raises(FileExistsError):
        demo.execute_scene("tests", "replay", tmp_path)


def test_missing_replay_is_a_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(demo, "ROOT", tmp_path)
    row = demo.execute_scene("tests", "replay", tmp_path / "scene")
    assert not row["presentation_ready"] and demo.result_code([row]) == 2


def test_synthetic_warning_precedes_scene_output(tmp_path, capsys):
    demo.execute_scene("harness", "replay", tmp_path / "scene")
    assert capsys.readouterr().out.splitlines()[0] == demo.WARNING


def test_raw_probe_refuses_to_overwrite_canonical_evidence(tmp_path):
    log = tmp_path / "probe.txt"
    code = demo.run_process([sys.executable, "tech-demo/a_raw_api/probe_raw.py"], log, 5, display=False)
    assert code == 2 and "Refusing to overwrite" in log.read_text()
