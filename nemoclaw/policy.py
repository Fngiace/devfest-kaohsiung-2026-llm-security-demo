"""Fail-closed execution policy. policy.yaml uses the JSON subset of YAML 1.2."""
from __future__ import annotations

from datetime import datetime
import fnmatch
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy.yaml"
AUDIT_PATH = ROOT / "audit/actions.jsonl"


def load_policy() -> dict:
    policy = json.loads(POLICY_PATH.read_text())
    if policy.get("default") != "deny" or not isinstance(policy.get("roles"), dict):
        raise ValueError("policy must declare default deny and roles")
    for role, rules in policy["roles"].items():
        if not isinstance(rules, dict):
            raise ValueError("role rules must be objects")
        for key in ("allow", "deny_patterns", "require_human_confirm"):
            value = rules.get(key, [])
            if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
                raise ValueError(f"invalid {role}.{key}")
    return policy


def record_action(role: str, tool: str, parameters: dict, decision: str, rule: str) -> None:
    row = {"timestamp": datetime.now().astimezone().isoformat(), "role": role, "tool": tool,
           "parameters": parameters, "decision": decision, "rule": rule}
    if AUDIT_PATH.parent.is_symlink():
        raise ValueError("audit directory symlink blocked")
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    encoded = (json.dumps(row, ensure_ascii=False) + "\n").encode()
    fd = os.open(AUDIT_PATH, flags, 0o600)
    try:
        if os.write(fd, encoded) != len(encoded):
            raise OSError("incomplete audit write; action blocked")
    finally:
        os.close(fd)


def decide(action: str, role: str, confirmation_token: str | None = None) -> tuple[str, str]:
    try:
        policy = load_policy()
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        return "deny", f"invalid_policy:{type(exc).__name__}"
    rules = policy["roles"].get(role)
    if rules is None:
        return "deny", "default:unknown_role"
    for pattern in rules.get("deny_patterns", []):
        if fnmatch.fnmatchcase(action, pattern):
            return "deny", f"roles.{role}.deny_patterns:{pattern}"
    if action in rules.get("require_human_confirm", []):
        expected = rules.get("confirmation_token")
        if isinstance(expected, str) and expected and confirmation_token == expected:
            return "allow", f"roles.{role}.require_human_confirm:confirmed"
        return "confirm", f"roles.{role}.require_human_confirm:{action}"
    if action in rules.get("allow", []):
        return "allow", f"roles.{role}.allow:{action}"
    return "deny", "default:deny"


def authorize(action: str, role: str, confirmation_token: str | None = None,
              *, parameters: dict | None = None) -> tuple[bool, str]:
    decision, rule = decide(action, role, confirmation_token)
    # Audit failure propagates before any action can execute.
    record_action(role, action, parameters or {}, decision, rule)
    return decision == "allow", f"{decision}: {rule}"
