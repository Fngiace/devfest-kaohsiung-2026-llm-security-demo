"""JSONL-aware alternative to tail -n 3 audit/actions.jsonl | jq ."""
import json
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "audit/actions.jsonl"
for line in path.read_text().splitlines()[-3:]:
    print(json.dumps(json.loads(line), ensure_ascii=False, indent=2))
