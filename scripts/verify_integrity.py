"""Verify protected prompts, attacks, dependency pins and original fallback bytes."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "d713626"
PROTECTED_CONSTANTS = {"APP_PROMPT", "ATTACK", "ATTACKS", "QUESTION", "LEAK", "SECRETS"}


def original(name):
    return subprocess.check_output(["git", "show", f"{BASELINE}:{name}"], cwd=ROOT)


def constants(source):
    result = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in PROTECTED_CONSTANTS:
                    result[target.id] = ast.dump(node.value)
    return result


def main():
    names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASELINE], cwd=ROOT, text=True).splitlines()
    results = []
    for name in names:
        if name == "requirements.txt" or name.startswith("fallback-logs/") or (name.startswith("scenario") and not name.endswith(".py")):
            ok = (ROOT / name).read_bytes() == original(name)
            results.append({"path": name, "check": "exact_bytes", "passed": ok})
        elif name.startswith("scenario") and name.endswith(".py"):
            expected = constants(original(name))
            actual = constants((ROOT / name).read_bytes())
            results.append({"path": name, "check": "protected_prompt_AST", "passed": expected == actual})
    print(json.dumps({"baseline": BASELINE, "checks": results, "passed": all(r["passed"] for r in results)}, indent=2))
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
