import importlib.util
from pathlib import Path
import pytest
from nemoclaw.output_rail import SAFE_MESSAGE

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fixed_app", ROOT / "tech-demo/b_fail_open/fixed_app.py")
fixed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixed)


@pytest.mark.parametrize("raw", [
    "<thinking>SUPERVISOR-7788", "<answer>SUPERVISOR-7788",
    "<answer>SUPERVISOR-7788</answer>", "<answer>ok</answer><answer>second</answer>",
    "<answer><answer>nested</answer></answer>",
])
def test_fail_closed(raw):
    assert fixed.render(raw, ["SUPERVISOR-7788"]) == SAFE_MESSAGE


def test_valid_answer_excludes_private_thinking():
    assert fixed.render("<thinking>SUPERVISOR-7788</thinking><answer>您好</answer>", ["SUPERVISOR-7788"]) == "您好"
