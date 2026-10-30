import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.local_api import make_payload, request

status, response = request("/api/chat", make_payload("You are a helpful assistant.", "Say hello.", 32))
print(f"HTTP {status}; model={response.get('model')}; eval_count={response.get('eval_count')}")
raise SystemExit(0 if status == 200 else 1)
