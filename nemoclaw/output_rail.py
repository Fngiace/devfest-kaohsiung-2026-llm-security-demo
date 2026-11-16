from __future__ import annotations

import re
from nemoclaw.secret_scan import find_secrets


SAFE_MESSAGE = "抱歉，我無法處理這個請求。"


def guard_answer(raw_output: str, blocked_terms: list[str]) -> str:
    match = re.search(r"<answer>(.*?)</answer>", raw_output, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return SAFE_MESSAGE

    answer = match.group(1).strip()
    if find_secrets(answer, blocked_terms):
        return SAFE_MESSAGE
    return answer
