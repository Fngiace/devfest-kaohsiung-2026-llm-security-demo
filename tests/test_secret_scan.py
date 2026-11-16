import base64
import pytest
from nemoclaw.secret_scan import find_secrets

SECRET = "SUPERVISOR-7788"
CANARIES = [SECRET, "VIP-SECRET-50"]


@pytest.mark.parametrize("text,step", [
    (SECRET, "exact"),
    ("ＳＵＰＥＲＶＩＳＯＲ－７７８８", "NFKC"),
    ("S U P E R V I S O R 7 7 8 8", "remove_separators"),
    ("\u200b".join(SECRET), "remove_zero_width"),
    (SECRET.lower(), "casefold"),
    (base64.b64encode(SECRET.encode()).decode(), "base64"),
    ("VIP-SECRET-50".encode().hex(), "hex"),
    (base64.b64encode("s u p e r v i s o r 7 7 8 8".encode()).decode(), "base64"),
])
def test_forms_and_original_offsets(text, step):
    prefix = "訂單："
    findings = find_secrets(prefix + text + "！", CANARIES)
    assert findings
    assert any(step in f.transformations for f in findings)
    assert all((f.start, f.end) == (len(prefix), len(prefix) + len(text)) for f in findings)


@pytest.mark.parametrize("text", ["您好，您的訂單已出貨。", "SUPERVISOR", "abc123", "", "YWJjZGVmZ2hpamts"])
def test_no_false_positive(text):
    assert find_secrets(text, CANARIES) == []


def test_multiple_occurrences():
    text = SECRET + " / " + SECRET
    findings = find_secrets(text, [SECRET])
    assert [(f.start, f.end) for f in findings] == [(0, len(SECRET)), (len(SECRET) + 3, len(text))]


def test_empty_canary_ignored():
    assert find_secrets("hello", [""]) == []


def test_normalized_encoded_token_original_offsets():
    token = base64.b64encode(SECRET.encode()).decode()
    token = "\u200b".join(chr(ord(c) + 0xFEE0) for c in token)
    findings = find_secrets("！" + token + "！", [SECRET])
    assert len(findings) == 1
    assert "base64" in findings[0].transformations
    assert (findings[0].start, findings[0].end) == (1, 1 + len(token))
