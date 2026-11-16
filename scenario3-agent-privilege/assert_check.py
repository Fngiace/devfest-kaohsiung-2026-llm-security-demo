from __future__ import annotations

import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def run_script(name: str) -> str:
    return subprocess.check_output([sys.executable, str(HERE / name), "--replay", "--no-save"], text=True)


attack = run_script("attack.py")
defended = run_script("defended.py")

assert "customer_db.json exists: False" in attack
assert "customer_db.json exists: True" in defended
print("✅ scenario3 assertions passed")
