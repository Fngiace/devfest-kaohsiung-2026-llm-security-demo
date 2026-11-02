import json
import argparse
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]


def build(source: Path | None = None) -> str:
    source = source or ROOT / "evidence/m1/results.json"
    rows = json.loads(source.read_text())
    lines = ["# M2 實測時間表", "", "M1 與 M2 共用同一批已加上量測的三次實跑，無 replay、無 LLM 裁判。",
             "總時間含 CLI 啟動與多次攻擊嘗試；token/s = 此次所有模型呼叫的 eval_count 總和 / eval_duration 總和。",
             "模型首次載入時間包含在實測內；未扣除。最慢值提示尾端延遲，建議欄仍依 SDD 的中位數規則。", "", "| 腳本 | 成功 | 總秒數中位數 | 最慢秒數 | 生成 token 中位數 | token/s 中位數 | 建議現場跑法 |",
             "|---|---:|---:|---:|---:|---:|---|"]
    for name in dict.fromkeys(r["case"] for r in rows):
        group = [r for r in rows if r["case"] == name]
        seconds = median(r["wall_seconds"] for r in group)
        successes = sum(r["passed"] for r in group)
        complete = len(group) == 3 and successes == 3
        advice = ("LIVE" if seconds <= 30 else "LIVE，備妥預錄") if complete and seconds <= 60 else "預錄；先確認有成功實測"
        if successes == 0:
            advice = "未重現／未通過：展示失敗紀錄或略過，無成功預錄可用"
        tokens = [r["generated_tokens"] for r in group if r["generated_tokens"] is not None]
        rates = [r["tokens_per_second"] for r in group if r["tokens_per_second"] is not None]
        tok = f"{median(tokens):.0f}" if tokens else "unavailable"
        rate = f"{median(rates):.2f}" if rates else "unavailable"
        lines.append(f"| {name} | {successes}/{len(group)} | {seconds:.2f} | {max(r['wall_seconds'] for r in group):.2f} | {tok} | {rate} | {advice} |")
    lines += ["", f"逐次命令、exit code、確定性斷言、時間與原始回應見 `{source.relative_to(ROOT)}`。",
              "固定三次，不採『最多五次任一次成功即過』，不刪除失敗樣本。"]
    text = "\n".join(lines) + "\n"
    (ROOT / "timing-m2.md").write_text(text)
    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    print(build(args.source.resolve() if args.source else None))
