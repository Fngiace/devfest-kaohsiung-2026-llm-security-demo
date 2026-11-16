import re
from nemoclaw.output_rail import SAFE_MESSAGE, guard_answer


def render(raw_output: str, canaries: list[str]) -> str:
    matches = list(re.finditer(r"<answer>([^<>]*)</answer>", raw_output, flags=re.S | re.I))
    if len(matches) != 1 or len(re.findall(r"</?answer\b", raw_output, re.I)) != 2:
        return SAFE_MESSAGE
    return guard_answer(matches[0].group(0), canaries)
