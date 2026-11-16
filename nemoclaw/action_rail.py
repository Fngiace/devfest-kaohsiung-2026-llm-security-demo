from __future__ import annotations


from nemoclaw.policy import authorize


def authorize_action(action: str, role: str, confirmation_token: str | None = None,
                     *, parameters: dict | None = None) -> tuple[bool, str]:
    return authorize(action, role, confirmation_token, parameters=parameters)
