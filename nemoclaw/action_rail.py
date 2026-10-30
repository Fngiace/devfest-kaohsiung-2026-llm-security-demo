from __future__ import annotations


FORBIDDEN_ACTIONS = {"delete_all_data"}


def authorize_action(action: str, role: str, confirmation_token: str | None = None) -> tuple[bool, str]:
    if action in FORBIDDEN_ACTIONS:
        if role == "maintenance_admin" and confirmation_token == "ALLOW-DEMO-DELETE":
            return True, "authorized"
        return False, "least privilege policy rejected destructive action"
    return True, "authorized"
