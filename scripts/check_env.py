"""Capture/compare runtime identity. repo.commit is the latest runtime-code commit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common.local_api import MODEL, request, save_json

SOURCE_PATHS = ["common", "nemoclaw", "scripts", "tech-demo", "tests", "scenario1-systemprompt",
                "scenario2-rag", "scenario3-agent-privilege", "requirements.txt", "requirements-dev.txt", "policy.yaml", "pytest.ini",
                ":(exclude)tech-demo/**/out/**", ":(exclude)**/__pycache__/**", ":(exclude)**/sandbox/**"]


def command(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def source_manifest() -> dict:
    names = command("git", "ls-files", "--cached", "--others", "--exclude-standard", "--", *SOURCE_PATHS).splitlines()
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names
            if "out" not in Path(name).parts
            and Path(name).suffix in {".py", ".sh", ".txt", ".yaml", ".json", ".ini"}}


def snapshot() -> dict:
    listing = command("ollama", "list")
    row = next(line.split() for line in listing.splitlines()[1:] if line.split()[0] == MODEL)
    show_text = command("ollama", "show", MODEL)
    status, show = request("/api/show", {"model": MODEL})
    if status != 200:
        raise RuntimeError(show)
    _, tags = request("/api/tags")
    tag = next(item for item in tags["models"] if item["name"] == MODEL)
    _, runtime = request("/api/version")
    packages = {d.metadata["Name"].lower(): d.version for d in importlib.metadata.distributions()}
    return {
        "machine": {"chip": command("sysctl", "-n", "machdep.cpu.brand_string"),
                    "ram_gb": int(command("sysctl", "-n", "hw.memsize")) / 1024**3,
                    "macos": command("sw_vers", "-productVersion"), "build": command("sw_vers", "-buildVersion")},
        "ollama": {"version": runtime["version"], "model": MODEL, "digest": tag["digest"],
                   "list_id": row[1], "quantization": show["details"]["quantization_level"],
                   "parameter_size": show["details"]["parameter_size"]},
        "python": {"version": platform.python_version(),
                   "requirements_hash": hashlib.sha256((ROOT / "requirements.txt").read_bytes()).hexdigest(),
                   "packages": dict(sorted(packages.items()))},
        "repo": {"branch": command("git", "branch", "--show-current"),
                 "commit": command("git", "log", "-1", "--format=%H", "--", *SOURCE_PATHS),
                 "commit_semantics": "latest commit affecting runtime source paths; evidence-only commits excluded",
                 "source_sha256": source_manifest()},
    }


def differences(expected: object, current: object, prefix: str = "") -> list[str]:
    if isinstance(expected, dict) and isinstance(current, dict):
        return [item for key in sorted(expected.keys() | current.keys())
                for item in differences(expected.get(key), current.get(key), f"{prefix}.{key}".strip("."))]
    return [] if expected == current else [f"{prefix}: locked={expected!r}; current={current!r}"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    try:
        current = snapshot()
        path = ROOT / "env-lock.json"
        if args.capture:
            save_json(path, {"captured_at": datetime.now().astimezone().isoformat(), **current})
            print("Captured env-lock.json (runtime-code commit, package versions, source hashes)")
            return 0
        expected = json.loads(path.read_text())
        expected.pop("captured_at")
        diffs = differences(expected, current)
        for diff in diffs:
            print(f"\033[31mMISMATCH {diff}\033[0m")
        if diffs:
            return 1
        print("\033[32mPASS: environment matches env-lock.json\033[0m")
        return 0
    except Exception as exc:
        print(f"\033[31mENV CHECK FAILED: {exc}\033[0m")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
