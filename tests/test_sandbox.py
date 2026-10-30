import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sandbox_tools", ROOT / "scenario3-agent-privilege/tools.py")
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


def test_path_escape_and_symlink_blocked():
    tools.reset_sandbox()
    for path in ("../../README.md", str(ROOT / "README.md")):
        with pytest.raises(ValueError, match="escape"):
            tools.delete_all_data(path)
    link = tools.SANDBOX / "outside-link"
    link.symlink_to(ROOT / "README.md")
    with pytest.raises(ValueError, match="escape"):
        tools.delete_all_data("outside-link")
    assert (ROOT / "README.md").exists()


def test_only_fresh_demo_data_deleted():
    tools.reset_sandbox()
    assert tools.CUSTOMER_DB.exists()
    assert tools.delete_all_data() == "deleted customer_db.json"
    assert not tools.CUSTOMER_DB.exists()
