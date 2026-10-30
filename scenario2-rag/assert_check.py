from __future__ import annotations

import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
LEAK = "ORCHID-ESCALATE-9"


def run_script(name: str) -> str:
    return subprocess.check_output([sys.executable, str(HERE / name), "--replay", "--no-save"], text=True)


attack = run_script("attack.py")
defended = run_script("defended.py")

assert LEAK in attack
assert LEAK not in defended
print("✅ scenario2 assertions passed")
