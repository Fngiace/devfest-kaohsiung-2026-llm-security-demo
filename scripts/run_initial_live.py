"""Run sequential GPU stages after a successful model pull; retain every failure."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(ROOT / "venv/bin/python")


def run(stage, command, output):
    path = ROOT / output
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError(f"refusing to overwrite evidence: {path}")
    print(f"START {stage}: {' '.join(command)}", flush=True)
    started = datetime.now().astimezone().isoformat()
    before = time.perf_counter()
    with path.open("w") as handle:
        result = subprocess.run(command, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT)
    row = {"stage": stage, "started_at": started, "wall_seconds": time.perf_counter() - before,
           "returncode": result.returncode, "command": command, "output": output}
    with (ROOT / "evidence/live-stage-status.jsonl").open("a") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"END {stage}: exit={result.returncode}; seconds={row['wall_seconds']:.2f}", flush=True)
    return result.returncode


def checkpoint(stage, summary, *paths):
    subprocess.run(["git", "add", "--", *paths], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", f"devfest-kh: {stage} {summary}"], cwd=ROOT, check=True)


def main():
    run("M0 version", ["ollama", "--version"], "evidence/m0/ollama-version.txt")
    run("M0 list", ["ollama", "list"], "evidence/m0/ollama-list.txt")
    run("M0 show", ["ollama", "show", "gemma4:e4b"], "evidence/m0/ollama-show.txt")
    if run("M0 capture", [PYTHON, "scripts/check_env.py", "--capture"], "evidence/m0/capture.txt"):
        raise RuntimeError("Cannot record environment; inspect evidence/m0/capture.txt")
    (ROOT / "evidence/m0/env-lock.json").write_bytes((ROOT / "env-lock.json").read_bytes())
    run("M0 check", [PYTHON, "scripts/check_env.py"], "evidence/m0/check.txt")
    checkpoint("M0", "lock verified local model and runtime", "env-lock.json", "evidence/m0", "evidence/live-stage-status.jsonl")
    run("M1", [PYTHON, "scripts/run_matrix.py", "--phase", "m1", "--repeats", "3"], "evidence/m1-console.txt")
    checkpoint("M1", "record all 24 live baseline trials including failures", "evidence/m1", "evidence/m1-console.txt", "evidence/live-stage-status.jsonl")
    run("M2", [PYTHON, "scripts/build_timing.py"], "evidence/m2/timing-console.txt")
    checkpoint("M2", "publish measured medians and live recommendations", "timing-m2.md", "evidence/m2", "evidence/live-stage-status.jsonl")
    run("M3", [PYTHON, "-u", "tech-demo/a_raw_api/probe_raw.py"], "evidence/m3/probe.txt")
    checkpoint("M3", "record three raw API thinking configurations", "tech-demo/a_raw_api/out", "evidence/m3", "evidence/live-stage-status.jsonl")
    run("M4 scan", [PYTHON, "-u", "tech-demo/b_fail_open/scan_budget.py"], "evidence/m4/scan.txt")
    run("M4 compare", [PYTHON, "-u", "tech-demo/b_fail_open/run_compare.py", "--repeat", "5"], "evidence/m4/compare.txt")
    checkpoint("M4", "record truncation scan and five actual comparisons", "tech-demo/b_fail_open/config.json", "tech-demo/b_fail_open/out", "evidence/m4", "evidence/live-stage-status.jsonl")


if __name__ == "__main__":
    main()
