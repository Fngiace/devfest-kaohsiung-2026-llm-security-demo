import json
import pytest
from nemoclaw import policy


@pytest.fixture
def isolated_audit(tmp_path, monkeypatch):
    target = tmp_path / "actions.jsonl"
    monkeypatch.setattr(policy, "AUDIT_PATH", target)
    return target


def test_all_decisions_recorded(isolated_audit):
    for action, expected in [("read_customer_db", True), ("delete_all_data", False), ("issue_refund", False), ("unknown", False)]:
        allowed, _ = policy.authorize(action, "support_agent", parameters={"input": "customer_db.json"})
        assert allowed == expected
    rows = [json.loads(x) for x in isolated_audit.read_text().splitlines()]
    assert [r["decision"] for r in rows] == ["allow", "deny", "confirm", "deny"]
    assert all(r["parameters"] == {"input": "customer_db.json"} and r["rule"] and r["timestamp"] for r in rows)


def test_missing_and_invalid_policy_fail_closed(tmp_path, monkeypatch, isolated_audit):
    target = tmp_path / "policy.yaml"
    monkeypatch.setattr(policy, "POLICY_PATH", target)
    assert not policy.authorize("read_customer_db", "support_agent")[0]
    target.write_text('{"default":"allow","roles":{}}')
    assert not policy.authorize("read_customer_db", "support_agent")[0]


def test_admin_confirmation_and_unknown_role(isolated_audit):
    assert not policy.authorize("delete_all_data", "maintenance_admin")[0]
    assert not policy.authorize("delete_all_data", "maintenance_admin", "wrong")[0]
    assert policy.authorize("delete_all_data", "maintenance_admin", "ALLOW-DEMO-DELETE")[0]
    assert not policy.authorize("read_customer_db", "unrecognized_role")[0]


def test_audit_failure_blocks_allow(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "AUDIT_PATH", tmp_path)
    with pytest.raises(OSError):
        policy.authorize("read_customer_db", "support_agent")
