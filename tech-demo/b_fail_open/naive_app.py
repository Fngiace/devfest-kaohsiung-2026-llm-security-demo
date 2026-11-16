import re


def render(raw_output: str, canaries: list[str]) -> str:
    match = re.search(r"<answer>(.*?)</answer>", raw_output, flags=re.S | re.I)
    if not match:
        return raw_output  # Deliberately vulnerable: fail open.
    return match.group(1).strip()
