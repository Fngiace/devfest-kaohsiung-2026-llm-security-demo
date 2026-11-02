"""Terminal stage runner. Saved evidence is never counted as a successful live run."""
from __future__ import annotations

import argparse
import codecs
from datetime import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common.local_api import save_json
from scripts.run_matrix import CASES, validate

PYTHON = str(ROOT / "venv/bin/python")
WARNING = "⚠ 合成測資，用於示範判定邏輯，非實測結果"
SCENES = {
    name: {"command": [script, *(["--live"] if live else []), "--no-save"],
           "fallback": f"{name}.txt", "model": True, "timeout": 60,
           # Current laptop: S1 passes both rounds; S2 attack is 5/6 overall.
           "recommended": "replay" if name == "s2-attack" else "live"}
    for name, script, live in CASES
}
SCENES.update({
    "raw-api": {"command": ["tech-demo/a_raw_api/probe_raw.py"], "fallback": "a-raw-json.txt",
                "model": True, "timeout": 90, "recommended": "live"},
    "fail-open": {"command": ["tech-demo/b_fail_open/run_compare.py"], "fallback": "b-compare.txt",
                  "model": True, "timeout": 60, "recommended": "replay"},
    "tests": {"command": ["-m", "pytest", "-v"], "fallback": "c-pytest.txt",
              "model": False, "timeout": 30, "recommended": "live"},
    "harness": {"command": ["tech-demo/d_harness/run_d.py"], "fallback": "d-harness.txt",
                "model": False, "timeout": 15, "recommended": "live"},
    "audit": {"command": ["scripts/audit_tail.py"], "fallback": "s3-audit.jsonl",
              "model": False, "timeout": 15, "recommended": "live"},
})
REHEARSAL = ["s1-attack-zh", "s1-defended-zh", "raw-api", "fail-open", "tests", "harness",
             "s2-attack", "s2-defended", "s3-attack", "s3-defended", "audit"]


def run_process(command: list[str], log: Path, timeout: float, env: dict | None = None,
                display: bool = True) -> int:
    """Stream file-backed output; kill the whole CLI process group on timeout/cancel."""
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    with log.open("wb") as output, log.open("rb") as reader:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        started = time.monotonic()
        try:
            while process.poll() is None:
                chunk = reader.read()
                if display and chunk:
                    print(decoder.decode(chunk), end="", flush=True)
                if time.monotonic() - started >= timeout:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    output.write(f"\nTIMEOUT: {timeout:g} seconds\n".encode())
                    output.flush()
                    returncode = 124
                    break
                time.sleep(0.05)
            else:
                returncode = process.returncode
        except BaseException:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise
        if display:
            print(decoder.decode(reader.read(), final=True), end="", flush=True)
    return returncode


def preflight(folder: Path) -> int:
    return run_process([PYTHON, "scripts/check_env.py"], folder / "preflight.txt", 30, display=False)


def replay(name: str, folder: Path) -> bool:
    source = ROOT / "fallback-logs/devfest-kh" / SCENES[name]["fallback"]
    print(f"[備援：已保存紀錄；非本次 LIVE] {source.relative_to(ROOT)}", flush=True)
    try:
        content = source.read_text()
        (folder / "replay.txt").write_text(content)
        print(content, flush=True)
        return bool(content.strip())
    except OSError as exc:
        print(f"備援讀取失敗：{exc}", flush=True)
        return False


def live_assertions(name: str, folder: Path) -> dict:
    if name.startswith("s") and name in {case[0] for case in CASES}:
        trace = folder / "responses.jsonl"
        traces = [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
        return validate(name, (folder / "live.txt").read_text(), traces)
    if name == "raw-api":
        rows = json.loads((folder / "artifacts/summary.json").read_text())
        by_setting = {row["setting"]: row for row in rows}
        return {
            "three_settings": set(by_setting) == {"omitted", "true", "false"},
            "http_ok": len(rows) == 3 and all(row["http_status"] == 200 for row in rows),
            "native_thinking_leak_observed": any(
                row["locations"]["message.thinking"] for row in rows if row["setting"] in {"omitted", "true"}),
            "think_false_no_native_field": "false" in by_setting and not by_setting["false"]["locations"]["thinking_field_present"],
        }
    if name == "fail-open":
        rows = json.loads((folder / "artifacts/comparison-results.json").read_text())
        return {"verified_comparison": bool(rows) and all(row["verified_comparison"] for row in rows)}
    # pytest and harness have their own assertion-driven exit codes; audit only displays records.
    return {"output_present": bool((folder / "live.txt").read_text().strip())}


def execute_scene(name: str, mode: str, folder: Path, timeout: float | None = None) -> dict:
    folder.mkdir(parents=True, exist_ok=False)
    scene = SCENES[name]
    selected = scene["recommended"] if mode == "auto" else mode
    row = {"scene": name, "requested_mode": mode, "selected_mode": selected,
           "started_at": datetime.now().astimezone().isoformat(), "live_attempted": False,
           "live_passed": None, "replay_shown": False, "presentation_ready": False,
           "reason": None, "returncode": None, "assertions": {}}
    started = time.perf_counter()
    if name == "harness":
        print(WARNING, flush=True)
    print(f"\n=== {name} | {selected.upper()} ===", flush=True)
    try:
        if selected == "replay":
            row["reason"] = "planned_replay"
            row["replay_shown"] = replay(name, folder)
            row["presentation_ready"] = row["replay_shown"]
        else:
            # Local deterministic tests and fixtures do not require a running model.
            check = preflight(folder) if scene["model"] else 0
            if check != 0:
                row["reason"] = "preflight_failed"
                print("LIVE 已停止：環境檢查未通過；詳見 preflight.txt。", flush=True)
            else:
                row["live_attempted"] = True
                command = [PYTHON, *scene["command"]]
                if name in {"raw-api", "fail-open"}:
                    command += ["--out-dir", str(folder / "artifacts")]
                row["command"] = command
                env = {**os.environ, "PYTHONUNBUFFERED": "1", "DEVFEST_TRACE": str(folder / "responses.jsonl")}
                row["returncode"] = run_process(command, folder / "live.txt", timeout or scene["timeout"], env)
                try:
                    row["assertions"] = live_assertions(name, folder)
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    row["assertions"] = {"evidence_readable": False}
                    row["validation_error"] = str(exc)
                row["live_passed"] = row["returncode"] == 0 and all(row["assertions"].values())
                row["presentation_ready"] = row["live_passed"]
                row["reason"] = "live_passed" if row["live_passed"] else "live_failed_or_not_reproduced"
                print(f"[LIVE {'PASS' if row['live_passed'] else '未通過／未重現'}] {name}", flush=True)
            if mode == "auto" and not row["presentation_ready"]:
                row["replay_shown"] = replay(name, folder)
                row["presentation_ready"] = row["replay_shown"]
    except KeyboardInterrupt:
        row["reason"] = "cancelled"
        raise
    except OSError as exc:
        row["reason"] = "execution_error"
        row["error"] = str(exc)
        print(f"執行失敗：{exc}", flush=True)
        if mode == "auto":
            row["replay_shown"] = replay(name, folder)
            row["presentation_ready"] = row["replay_shown"]
    finally:
        row["wall_seconds"] = time.perf_counter() - started
        save_json(folder / "result.json", row)
    return row


def result_code(rows: list[dict]) -> int:
    return 0 if rows and all(row["presentation_ready"] and
                            row["reason"] in {"planned_replay", "live_passed"} for row in rows) else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="DevFest 終端演示：LIVE／實測備援；每次產生獨立證據。")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--list", action="store_true")
    selection.add_argument("--scene", choices=SCENES)
    selection.add_argument("--rehearse", action="store_true", help="依推薦順序跑完整技術彩排")
    parser.add_argument("--mode", choices=["auto", "live", "replay"], default="auto")
    parser.add_argument("--timeout", type=float, help="每個 LIVE 段落的秒數上限（不含環境檢查）")
    args = parser.parse_args()
    if args.timeout is not None and (not 0 < args.timeout <= 900):
        parser.error("--timeout must be between 0 and 900 seconds")
    if args.list:
        for name, scene in SCENES.items():
            print(f"{name:20} auto={scene['recommended']:6} timeout={scene['timeout']}s")
        return 0
    if not args.scene and not args.rehearse:
        if not sys.stdin.isatty():
            parser.error("非互動終端請指定 --scene 或 --rehearse；--list 可列出段落")
        names = list(SCENES)
        for index, name in enumerate(names, 1):
            print(f"{index:2}. {name} ({SCENES[name]['recommended']})")
        choice = input("輸入段落編號，或 a 執行完整彩排，q 離開：").strip()
        if choice.lower() == "q":
            return 0
        if choice.lower() == "a":
            args.rehearse = True
        elif choice.isdigit() and 1 <= int(choice) <= len(names):
            args.scene = names[int(choice) - 1]
        else:
            parser.error("無效的段落編號")
    parent = ROOT / "evidence/rehearsal"
    parent.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix=datetime.now().strftime("%Y%m%dT%H%M%S-"), dir=parent))
    names = REHEARSAL if args.rehearse else [args.scene]
    rows = []
    if "harness" in names:
        print(WARNING, flush=True)
    print(f"本次證據：{folder}", flush=True)
    try:
        for name in names:
            rows.append(execute_scene(name, args.mode, folder / name, args.timeout))
            save_json(folder / "results.json", rows)
    except KeyboardInterrupt:
        print("\n彩排已取消；子程序已停止，保留已產生證據。", flush=True)
        return 130
    print(f"\n完成：LIVE 通過 {sum(r['live_passed'] is True for r in rows)}；"
          f"備援 {sum(r['replay_shown'] for r in rows)}；退出碼 {result_code(rows)}", flush=True)
    print(f"結果：{folder / 'results.json'}", flush=True)
    return result_code(rows)


if __name__ == "__main__":
    raise SystemExit(main())
