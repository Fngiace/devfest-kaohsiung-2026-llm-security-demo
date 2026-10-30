import importlib.util
import json
from pathlib import Path
import sys
from nemoclaw import policy

HERE = Path(__file__).resolve().parents[1] / "scenario3-agent-privilege"
sys.path.insert(0, str(HERE))
from agent import dispatch
from tools import CUSTOMER_DB, reset_sandbox


def test_actual_dispatch_denies_before_delete_and_audits(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "AUDIT_PATH", tmp_path / "actions.jsonl")
    reset_sandbox()
    result = dispatch("ACTION: delete_all_data\nACTION_INPUT: customer_db.json", defended=True)
    assert "rejected:" in result.observation
    assert CUSTOMER_DB.exists()
    row = json.loads(policy.AUDIT_PATH.read_text())
    assert row["decision"] == "deny" and row["parameters"] == {"input": "customer_db.json"}
    assert "deny_patterns:delete_*" in row["rule"]


def test_unguarded_demo_is_logged_as_bypass(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "AUDIT_PATH", tmp_path / "actions.jsonl")
    reset_sandbox()
    result = dispatch("ACTION: delete_all_data\nACTION_INPUT: customer_db.json", defended=False)
    assert result.observation == "deleted customer_db.json"
    assert not CUSTOMER_DB.exists()
    row = json.loads(policy.AUDIT_PATH.read_text())
    assert row["decision"] == "allow" and row["rule"] == "demo.unguarded_dispatch"
