import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_env", ROOT / "scripts/check_env.py")
check_env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_env)


def test_nested_drift_is_reported():
    expected = {"ollama": {"digest": "locked"}, "python": {"version": "3.14.6"}}
    actual = {"ollama": {"digest": "changed"}, "python": {"version": "3.14.6"}}
    diffs = check_env.differences(expected, actual)
    assert len(diffs) == 1 and diffs[0].startswith("ollama.digest:")


def test_added_or_missing_fields_are_drift():
    assert check_env.differences({"a": 1}, {"a": 1, "b": 2})
    assert check_env.differences({"a": 1, "b": 2}, {"a": 1})
    assert not check_env.differences({"a": 1}, {"a": 1})
