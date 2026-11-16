import json
import sys

WARNING = "⚠ 合成測資，用於示範判定邏輯，非實測結果"


def main() -> int:
    print(WARNING, flush=True)
    rows = json.load(open(sys.argv[1], encoding="utf-8"))["results"]
    passed = sum(row.get("success") is True for row in rows)
    print(f"PASS {passed}/{len(rows)} (naive: success field only)")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
