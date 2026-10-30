"""Build stage-ready text artifacts exclusively from saved real runs."""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from statistics import median

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def read(path):
    return (ROOT / path).read_text()


def main():
    lock = load("env-lock.json")
    rows = load("evidence/m1/results.json")
    regression = load("evidence/m5-regression/results.json")
    digest = lock["ollama"]["digest"]
    generated = datetime.now().astimezone().isoformat()
    header = f"# generated_at={generated} model_digest={digest}\n"
    fallback = ROOT / "fallback-logs/devfest-kh"
    fallback.mkdir(parents=True, exist_ok=True)
    screenshots = ROOT / "screenshots"
    screenshots.mkdir(exist_ok=True)
    selected = {}
    for name in dict.fromkeys(r["case"] for r in rows):
        # Defenses use the post-M5/M7 regression; attacks preserve M1 samples.
        source = regression if "defended" in name else rows
        group = [r for r in source if r["case"] == name]
        chosen = next((r for r in group if r["passed"]), group[-1])
        trace_path = ROOT / chosen["raw_responses"]
        traces = [json.loads(line) for line in trace_path.read_text().splitlines()] if trace_path.exists() else []
        note = f"source={chosen['stdout']}; passed={chosen['passed']}; exit={chosen['returncode']}\n"
        note += "assertions=" + json.dumps(chosen["assertions"], ensure_ascii=False) + "\n\n"
        text = note + read(chosen["stdout"])
        if not chosen["passed"]:
            text = "此段實測未通過，不能宣稱成功重現或成功防禦。\n" + text
            text += "\nSaved raw API message(s):\n" + json.dumps([t["response"].get("message") for t in traces], ensure_ascii=False, indent=2)
        (fallback / f"{name}.txt").write_text(header + text)
        selected[name] = (text, traces, chosen)
    for target, source in {"b-compare.txt": "evidence/m4/compare.txt", "c-pytest.txt": "evidence/m5/pytest.txt",
                           "d-harness.txt": "evidence/m6/harness.txt", "a-raw-json.txt": "evidence/m3/probe.txt",
                           "s3-audit.jsonl": "audit/actions.jsonl"}.items():
        (fallback / target).write_text(header + read(source))
    for target, names in {"s06-s1-attack": ["s1-attack-zh"], "s19-s1-defended": ["s1-defended-zh"],
                          "s20-s2": ["s2-attack", "s2-defended"], "s21-s3": ["s3-defended"]}.items():
        text = "\n\n".join(selected[name][0] for name in names)
        if target == "s21-s3":
            text += "\nAUDIT (actual recorded decisions):\n" + read("audit/actions.jsonl")
        (screenshots / f"{target}.txt").write_text(header + text)
    _, traces, chosen = selected["s1-attack-zh"]
    # Both slide-seven panels come from one response, never from different trials.
    message = traces[-1]["response"].get("message", {}) if traces else {}
    content = message.get("content", "")
    for part in ("thinking", "answer"):
        match = re.search(fr"<{part}>(.*?)</{part}>", content, re.S | re.I)
        segment = match.group(1) if match else f"本次回應沒有閉合的 <{part}> 段。\n原始 content:\n{content}"
        if part == "thinking" and message.get("thinking"):
            segment += "\n另外的 message.thinking（runtime 原生欄位）:\n" + message["thinking"]
        (screenshots / f"s07-{part}.txt").write_text(header + f"same_response_source={chosen['raw_responses']} (last call)\n" + segment)
    for target, source in {"m3-raw-json": "a-raw-json.txt", "m4-compare": "b-compare.txt", "m5-pytest": "c-pytest.txt", "m6-harness": "d-harness.txt"}.items():
        (screenshots / f"{target}.txt").write_text((fallback / source).read_text())
    (screenshots / "README.md").write_text("# 終端截圖文字素材\n\n提供 SDD 允許的十份實測純文字替代素材，尚未產出終端視窗 PNG。請在本機終端使用深色底與至少 20pt 字體，`cat screenshots/<name>.txt` 後手動截圖。\n\n每份包含來源與模型 digest；s07 兩份來自同一次模型回應。若標記未通過或沒有對應標籤，請勿裁掉狀態而當作成功畫面。M6 一律保留合成測資警語。\n")
    write_runsheet(rows, lock)
    manifest = {"generated_at": generated, "model_digest": digest,
                "selected_runs": {k: v[2] for k, v in selected.items()},
                "screenshots_format": "text alternatives; manual terminal screenshots required"}
    (ROOT / "evidence/delivery-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Created {len(list(fallback.iterdir()))} fallback artifacts and ten screenshot text alternatives.")


def write_runsheet(rows, lock):
    lines = ["# DevFest 2026 高雄現場操作表", "", "所有命令從專案根目錄執行。所有推論僅呼叫 localhost:11434。",
             "先閱讀 REPORT.md 的失敗／未重現項目；備援是實測文字紀錄，不是影片。", "",
             "## 開講前 10 分鐘", "", "1. 接電源；關閉大型程式，確認剩餘記憶體。",
             "2. 執行 `venv/bin/python scripts/check_env.py`；非零就停止 LIVE，檢查 drift，勿直接重鎖掩蓋差異。",
             "3. 執行 `venv/bin/python scripts/warmup.py` 預熱指定模型。",
             "4. 終端深色底、至少 20pt；開啟勿擾、關閉通知；依此表預先開好分頁。",
             "5. `cat fallback-logs/devfest-kh/c-pytest.txt` 確認備援可讀；模型下載與套件安裝均已在台下完成。", "",
             "## 三場景", "", "| 段落 | 精確指令 | M1 中位秒數 | 成功次數 | 失敗備援 |", "|---|---|---:|---:|---|"]
    for name in dict.fromkeys(r["case"] for r in rows):
        group = [r for r in rows if r["case"] == name]
        cmd = "venv/bin/python " + " ".join(group[0]["command"][1:])
        lines.append(f"| {name} | `{cmd}` | {median(r['wall_seconds'] for r in group):.2f} | {sum(r['passed'] for r in group)}/3 | `cat fallback-logs/devfest-kh/{name}.txt` |")
    lines += ["", "預期畫面：場景一攻擊若成功會在原始輸出找到 canary，防禦只回傳掃描後的 answer；場景二檢查 ORCHID-ESCALATE-9 是否出現；場景三只在新 sandbox 測試刪除，防禦顯示 rejected 且資料仍存在。",
              "若 timing-m2.md 建議預錄，使用上表備援文字；若 0/3，展示未重現結果或略過，不能宣稱成功。", "",
              "台上口徑：場景一『模型生成的任何欄位都要看清楚送到哪裡。』場景二『檢索資料不是新的指令來源。』場景三『工具能不能執行，由程式端政策決定。』", "",
              "## 技術 demo", "", "| 段落 | 精確指令 | 預期畫面／時間來源 | 備援 | 台上口徑 |", "|---|---|---|---|---|",
              "| A 原始 API | `venv/bin/python tech-demo/a_raw_api/probe_raw.py` | 三設定 HTTP 狀態與欄位掃描；時間見 out/summary.json | `cat fallback-logs/devfest-kh/a-raw-json.txt` | 先看真實 JSON，再決定哪些欄位能離開後端。 |",
              "| A curl | `sh tech-demo/a_raw_api/curl.sh false` | 與探測同一個已保存 request | `cat tech-demo/a_raw_api/out/false.json` | 不經 SDK，直接確認 runtime 回應。 |",
              "| B fail-open | `venv/bin/python tech-demo/b_fail_open/run_compare.py` | 若 config.num_predict=null，此段未驗證成功，改展示失敗紀錄；時間見 evidence/m4 | `cat fallback-logs/devfest-kh/b-compare.txt` | 解析失敗時不可把原始輸出當安全答案。 |",
              "| B 差異 | `cat tech-demo/b_fail_open/diff.patch` | naive 與 fixed 實際差異，無模型 | 同左 | 找不到完整答案，就回固定安全訊息。 |",
              "| C 單元測試 | `venv/bin/python -m pytest -v` | 確定性本機測試，計時見 evidence/m5/test-timing.json | `cat fallback-logs/devfest-kh/c-pytest.txt` | 正規化能補幾種包裝，但不能承諾語意防漏。 |",
              "| D harness | `sh tech-demo/d_harness/run_d.sh` | naive 全過；strict 兩壞一好；首行合成測資警語，通常小於 1 秒（實測見 evidence/m6） | `cat fallback-logs/devfest-kh/d-harness.txt` | 先驗證斷言真的執行，再相信通過率。 |",
              "| 稽核 | `venv/bin/python scripts/audit_tail.py` | 最後三筆 JSON 決策，無模型 | `tail -n 3 fallback-logs/devfest-kh/s3-audit.jsonl` | 每次允許、拒絕、待確認都有規則與參數紀錄。 |", "",
              "有 jq 時可用 `tail -n 3 audit/actions.jsonl | jq .`。JSONL 不能整份直接交給 `python -m json.tool`；單筆替代：`tail -n 1 audit/actions.jsonl | venv/bin/python -m json.tool`。", "",
              "M6 備援檔首行依 SDD 放時間/digest 註解，第二行保留合成測資警語；live 程式第一行即為警語。",
              "不要在台上執行 scan_budget.py、pip install 或 ollama pull；這些是準備工作。"]
    (ROOT / "RUNSHEET-devfest-kh.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
