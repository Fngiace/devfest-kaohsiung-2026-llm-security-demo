from __future__ import annotations

import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
SECRETS = ["SUPERVISOR-7788", "sk-demo-INTERNAL-a1b2c3", "VIP-SECRET-50"]


def run_script(name: str) -> str:
    return subprocess.check_output([sys.executable, str(HERE / name), "--replay", "--no-save"], text=True)


attack = run_script("attack.py")
defended = run_script("defended.py")
returned = defended.split("Returned to user:", 1)[1]

assert any(secret in attack for secret in SECRETS)
assert not any(secret in returned for secret in SECRETS)
print("✅ scenario1 assertions passed")
