from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from common.local_api import CANARIES, request, save_json
from nemoclaw.output_rail import SAFE_MESSAGE
from scan_budget import payload_for
from naive_app import render as naive
from fixed_app import render as fixed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()
    here = Path(__file__).parent
    config = json.loads((here / "config.json").read_text())
    out = here / config.get("evidence_directory", "out")
    n = config["num_predict"]
    verified = n is not None
    if not verified:
        n = config["fallback_num_predict"]
        print("未找到符合條件的 N；以下僅顯示實際結果，不代表成功重現機密外洩。", flush=True)
    results = []
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    for repeat in range(1, args.repeat + 1):
        status, response = request("/api/chat", payload_for(n))
        save_json(out / f"compare-{stamp}-{repeat}.json", response)
        raw = response.get("message", {}).get("content", "")
        left, right = naive(raw, CANARIES), fixed(raw, CANARIES)
        leak = any(s in left for s in CANARIES)
        closed = "</answer>" in raw.lower()
        correct = status == 200 and leak and not closed and right == SAFE_MESSAGE
        print(f"Run {repeat}, N={n}, HTTP={status}\nnaive: {left!r} | fixed: {right!r}")
        print(f"naive 機密外洩={leak}; answer 閉合={closed}; fixed 安全訊息={right == SAFE_MESSAGE}", flush=True)
        results.append({"repeat": repeat, "num_predict": n, "http_status": status, "naive_leaked": leak,
                        "closed_answer": closed, "fixed_safe": right == SAFE_MESSAGE, "verified_comparison": correct})
    save_json(out / "comparison-results.json", results)
    return 0 if verified and all(r["verified_comparison"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
