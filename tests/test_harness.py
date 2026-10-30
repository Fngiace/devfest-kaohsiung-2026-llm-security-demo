import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parents[1] / "tech-demo/d_harness"
sys.path.insert(0, str(HERE))
from strict_grader import validate


def healthy():
    return json.loads((HERE / "fixtures/healthy.json").read_text())


def test_control_must_be_detected():
    data = healthy()
    data["results"][-1]["assertions"][0]["passed"] = True
    assert "known leaking control" in " ".join(validate(data))


def test_skipped_assertion_is_invalid():
    data = healthy()
    data["results"][0]["assertions"][0]["executed"] = False
    assert "no assertion executed" in " ".join(validate(data))


def test_missing_recorded_answer_is_invalid():
    data = healthy()
    del data["results"][0]["graded_text"]
    del data["results"][0]["answer"]
    assert "grading source" in " ".join(validate(data))


def test_cli_fixtures_and_warning():
    for name in ("no_assertions", "graded_full_output", "healthy"):
        for grader in ("naive", "strict"):
            run = subprocess.run([sys.executable, str(HERE / f"{grader}_grader.py"), str(HERE / "fixtures" / f"{name}.json")], capture_output=True, text=True)
            assert run.stdout.splitlines()[0] == "⚠ 合成測資，用於示範判定邏輯，非實測結果"
            assert run.returncode == (1 if grader == "strict" and name != "healthy" else 0)
