from __future__ import annotations

import re
from dataclasses import dataclass

from nemoclaw.action_rail import authorize_action

from tools import delete_all_data, read_customer_db


ACTION_RE = re.compile(r"^ACTION:\s*(?P<action>[a-zA-Z0-9_]+)\s*$", re.MULTILINE)
INPUT_RE = re.compile(r"^ACTION_INPUT:\s*(?P<input>.*)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class DispatchResult:
    action: str
    action_input: str
    observation: str


def parse_action(model_text: str) -> tuple[str, str]:
    action_match = ACTION_RE.search(model_text)
    input_match = INPUT_RE.search(model_text)
    if not action_match:
        return "none", ""
    return action_match.group("action"), input_match.group("input").strip() if input_match else ""


def dispatch(model_text: str, *, defended: bool = False) -> DispatchResult:
    action, action_input = parse_action(model_text)
    if defended:
        allowed, reason = authorize_action(action, role="support_agent")
        if not allowed:
            return DispatchResult(action, action_input, f"rejected: {reason}")

    if action == "delete_all_data":
        return DispatchResult(action, action_input, delete_all_data(action_input or "customer_db.json"))
    if action == "read_customer_db":
        return DispatchResult(action, action_input, read_customer_db())
    return DispatchResult(action, action_input, "no action")
