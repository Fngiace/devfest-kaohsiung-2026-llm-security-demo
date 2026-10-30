from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FALLBACK_DIR = ROOT / "fallback-logs"


def save_fallback_log(name: str, text: str) -> None:
    FALLBACK_DIR.mkdir(exist_ok=True)
    (FALLBACK_DIR / name).write_text(text, encoding="utf-8")


def print_and_save(name: str, text: str) -> None:
    print(text)
    save_fallback_log(name, text)
