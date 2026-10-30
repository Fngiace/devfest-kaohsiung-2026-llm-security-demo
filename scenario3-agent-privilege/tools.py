from __future__ import annotations

import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_ROOT = ROOT / "sandbox"
if SANDBOX_ROOT.is_symlink():
    raise ValueError("sandbox root symlink blocked")
SANDBOX_ROOT.mkdir(exist_ok=True)
SANDBOX = Path(tempfile.mkdtemp(prefix="run-", dir=SANDBOX_ROOT))
CUSTOMER_DB = SANDBOX / "customer_db.json"


def reset_sandbox() -> None:
    if SANDBOX.is_symlink() or SANDBOX.resolve().parent != SANDBOX_ROOT.resolve():
        raise ValueError("sandbox path escape blocked")
    if CUSTOMER_DB.is_symlink():
        raise ValueError("customer DB symlink blocked")
    CUSTOMER_DB.write_text(
        json.dumps(
            [
                {"id": "cust_001", "name": "Demo Alice", "tier": "VIP"},
                {"id": "cust_002", "name": "Demo Bob", "tier": "Standard"},
            ],
            indent=2,
        ),
        encoding="utf-8",
    )


def _inside_sandbox(path: Path) -> bool:
    resolved = path.resolve()
    sandbox = SANDBOX.resolve()
    return resolved == sandbox or sandbox in resolved.parents


def delete_all_data(target: str = "customer_db.json") -> str:
    target_path = SANDBOX / target
    if not _inside_sandbox(target_path):
        raise ValueError("path escape blocked")
    if target_path.exists():
        target_path.unlink()
        return f"deleted {target_path.name}"
    return f"{target_path.name} did not exist"


def read_customer_db() -> str:
    if not CUSTOMER_DB.exists():
        return "customer_db.json missing"
    return CUSTOMER_DB.read_text(encoding="utf-8")
