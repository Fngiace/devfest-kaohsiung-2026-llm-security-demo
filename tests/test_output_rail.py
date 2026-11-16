import base64
import pytest
from nemoclaw.output_rail import SAFE_MESSAGE, guard_answer


@pytest.mark.parametrize("answer", ["ＳＵＰＥＲＶＩＳＯＲ－７７８８", "S U P E R V I S O R 7 7 8 8",
                                  base64.b64encode(b"SUPERVISOR-7788").decode(), b"SUPERVISOR-7788".hex()])
def test_normalized_secret_blocked_in_returned_answer(answer):
    assert guard_answer(f"<answer>{answer}</answer>", ["SUPERVISOR-7788"]) == SAFE_MESSAGE


def test_private_segment_never_returned():
    assert guard_answer("<thinking>SUPERVISOR-7788</thinking><answer>已出貨</answer>", ["SUPERVISOR-7788"]) == "已出貨"


def test_incomplete_answer_fails_closed():
    assert guard_answer("<thinking>SUPERVISOR-7788</thinking><answer>unfinished", ["SUPERVISOR-7788"]) == SAFE_MESSAGE
