"""Summarize saved outcomes without converting failures into passes."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text())


def counts(rows):
    return f"{sum(row['passed'] for row in rows)}/{len(rows)}"


def main():
    lock = load("env-lock.json")
    initial = load("evidence/m1/results.json")
    regression = load("evidence/m5-regression/results.json")
    probes = load("tech-demo/a_raw_api/out/summary.json")
    config = load("tech-demo/b_fail_open/config.json")
    comparison = load("tech-demo/b_fail_open/" + config.get("evidence_directory", "out") + "/comparison-results.json")
    tests = load("evidence/m5/test-timing.json")
    integrity = load("evidence/final-integrity.json")
    audit = [json.loads(line) for line in (ROOT / "audit/actions.jsonl").read_text().splitlines()]
    m1_ok = len(initial) == 24 and all(r["passed"] for r in initial)
    regression_ok = len(regression) == 24 and all(r["passed"] for r in regression)
    m4_ok = config["num_predict"] is not None and len(comparison) == 5 and all(r["verified_comparison"] for r in comparison)
    m7 = [r for r in regression if r["case"] == "s3-defended"]
    lines = ["# DevFest 高雄 2026 執行報告", "", "此報告由已保存的本機實測與測試紀錄產生，失敗樣本完整保留。", "",
             "## 1. 環境摘要", "", f"- 擷取：{lock['captured_at']}",
             f"- 硬體：{lock['machine']['chip']} / {lock['machine']['ram_gb']} GiB；macOS {lock['machine']['macos']} ({lock['machine']['build']})。",
             f"- Ollama：{lock['ollama']['version']}；模型 `{lock['ollama']['model']}`；{lock['ollama']['parameter_size']} / {lock['ollama']['quantization']}。",
             f"- 模型完整 digest：`{lock['ollama']['digest']}`。",
             f"- Python：{lock['python']['version']}；requirements SHA-256：`{lock['python']['requirements_hash']}`。",
             f"- 工作分支：`{lock['repo']['branch']}`；執行程式 commit：`{lock['repo']['commit']}`。",
             "- COSCUP 基線：`d713626`，含指定 `d6149b9`；上游歷史與 MIT 授權保留。", "",
             "## 2. 各階段結果", "", "| 階段 | 狀態 | 證據 |", "|---|---|---|",
             "| M0 | 完成；最終環境檢查見獨立紀錄 | env-lock.json、evidence/m0/、evidence/final-env-check.txt |",
             f"| M1 | {'完成' if m1_ok else '部分完成：已執行，未全數通過'}，{counts(initial)} | evidence/m1/results.json 及逐次原始回應 |",
             "| M2 | 完成；與 M1 共用量測樣本 | timing-m2.md |",
             "| M3 | 完成三設定探測，含實際 HTTP 錯誤（若有） | tech-demo/a_raw_api/out/ |",
             f"| M4 | {'完成，找到候選集合內可重現 N' if m4_ok else '實驗完成，未證明符合五次一致的洩漏重現'} | tech-demo/b_fail_open/config.json、out/、evidence/m4/ |",
             f"| M5 | {'完成' if regression_ok and tests['returncode'] == 0 and tests['wall_seconds'] < 3 else '部分完成：掃描測試與回歸狀態須分別看'}；pytest={tests['returncode']}，回歸 {counts(regression)} | evidence/m5/、evidence/m5-regression/ |",
             "| M6 | 完成：naive 三份通過；strict 兩壞一好；警語檢查通過 | evidence/m6/ |",
             f"| M7 | {'完成' if all(r['passed'] for r in m7) and len(m7) == 3 else '部分完成：政策測試已過，模型端呼叫／拒絕證據不足'}；場景三 defended {counts(m7)} | policy.yaml、audit/actions.jsonl、evidence/m5-regression/ |",
             "| M8 | 完成文字版交付；PNG 須手動截圖 | fallback-logs/devfest-kh/、screenshots/、RUNSHEET-devfest-kh.md |", "",
             f"完整性檢查：{integrity['passed']}。原始攻擊、system/app prompt、canary、requirements 與 COSCUP fallback 逐項比對。", "",
             "## 3. M2 時間表與現場建議", "", (ROOT / "timing-m2.md").read_text(), "",
             "### 修改後回歸", "", "| 腳本 | 成功次數 |", "|---|---:|"]
    for name in dict.fromkeys(r["case"] for r in regression):
        lines.append(f"| {name} | {counts([r for r in regression if r['case'] == name])} |")
    lines += ["", f"pytest 整個程序耗時 {tests['wall_seconds']:.3f} 秒，退出碼 {tests['returncode']}；完整案例見 evidence/m5/pytest.txt。", "",
              "## 4. M3 原始 API 結論", "", "| think 設定 | HTTP | content 命中 | content 的 thinking 段命中 | 原生 thinking 欄位命中 | 秒數 |", "|---|---:|---|---|---|---:|"]
    for probe in probes:
        loc = probe["locations"]
        lines.append(f"| {probe['setting']} | {probe['http_status']} | {loc['message.content']} | {loc['message.content.<thinking>']} | {loc['message.thinking']} | {probe['total_seconds']:.2f} |")
    native = any(p["locations"]["thinking_field_present"] for p in probes)
    leaked = any(p["locations"][key] for p in probes for key in ("message.content", "message.thinking"))
    lines += ["", f"本機原始 HTTP 探測{'有' if native else '未'}觀察到 message.thinking 欄位；是否含 canary 以表格逐設定結果為準。",
              "應用程式自行要求的 <thinking> 協議和 runtime 的 message.thinking 是不同的輸出位置，不能混為一談。",
              f"這三個無害訂單查詢回應{'已觀察到 canary，因此整個 message 被記錄或回傳時會一併帶出命中的機密' if leaked else '未觀察到 canary；因此不能宣稱這組無害查詢已造成機密外洩，也不能據此保證其他輸入安全'}。",
              "原始 request、完整 response 與 HTTP 狀態已保存；不把請求裡原本含有的 canary 誤算為回應洩漏。", "",
              "## 5. M4 截斷預算與五次比較", "",
              f"候選集合 `{config['candidate_grid']}`；最小值範圍是這個集合，不代表所有正整數的全域最小值。選定 N：`{config['num_predict']}`。",
              "初始 64–256 的輸出在原生 thinking 階段截斷、content 為空；保留初始 out/ 與 evidence/m4/，再擴大預算，新增結果在 out/extended/ 與 evidence/m4-extended/。",
              "固定 temperature=0、seed=42；使用原始繁中第一個 attack 與原始 app prompt，不把 message.thinking 拼接成 content。",
              "每個 N 的第一個失敗即判為不合格，沒有刪除失敗後重試到成功。", "", "| 次數 | N | naive 洩漏 | answer 閉合 | fixed 安全訊息 | 完整驗證 |", "|---|---:|---|---|---|---|"]
    for row in comparison:
        lines.append(f"| {row['repeat']} | {row['num_predict']} | {row['naive_leaked']} | {row['closed_answer']} | {row['fixed_safe']} | {row['verified_comparison']} |")
    if not m4_ok:
        lines += ["", "未找到符合本設定的可重現洩漏。交付的是實際失敗／未重現紀錄，沒有成功預錄可替代；現場可展示程式差異與單元測試，或如實展示未重現結果。"]
    lines += ["", "## 6. 偏離 SDD 與原因", "",
              "- 使用者指定獨立新 repository；先同步 SDD，再把 COSCUP main 的完整歷史合併到 devfest-kh-2026。沒有修改上游 main；新 repo 只推工作分支。",
              "- 下載模型期間先完成獨立的 M6 及程式準備，階段提交順序不代表數字順序。",
              "- 英文場景一 defended 不支援 --live，使用 --no-save；其餘依支援參數執行。",
              "- M1/M2 共用有完整量測的三次樣本；修改後再跑完整三次回歸。固定三次，不採五次任一成功規則。",
              "- 上游 assert_check.py 使用 --replay，不作為本次實測證據。新增驗證器檢查原始回應與真實工具狀態，繁中 thinking 宣稱也單獨驗證。",
              "- 新增 requirements-dev.txt 鎖定 pytest 與新測試相依，既有 requirements 完全不變。",
              "- policy.yaml 使用 YAML 1.2 相容的 JSON 語法，由標準庫解析，不新增 YAML 解析相依。",
              "- repo.commit 為最後修改執行程式路徑的 commit，搭配逐檔 source SHA-256。排除純證據提交，避免鎖檔與自身 commit 的循環參照。",
              "- 未自動產出終端視窗 PNG；依 SDD 交付十份真實文字替代素材，需要手動截圖。",
              "- 推論只呼叫 localhost，下載模型、安裝套件、取得基線與 GitHub 同步是文件明許的建置網路操作。", "",
              "## 7. 待 Fngi 決定", "",
              "- 依 timing-m2.md 決定現場 LIVE 段落。失敗或超過 60 秒者，建議使用已驗證成功的文字備援；沒有成功樣本者如實展示限制或略過。",
              "- 依 screenshots/README.md 將十份文字素材製成終端截圖，深色底、至少 20pt；保留未通過與合成資料標籤。"]
    if not m4_ok:
        lines.append("- M4 沒有可用的五次一致洩漏重現；建議現場展示 fail-closed 差異與測試，不把合成或別台機器輸出充當本機實測。")
    lines += ["", "## 8. 已知限制", "",
              "- 正規化掃描不能阻止翻譯、語意改寫、分段或多層編碼；單層編碼 token 上限 16,384 字元。Finding 位置是原文 Python 字元索引，編碼命中指向整個原始 token。",
              "- 所有機密是 demo canary；sandbox 是新建假資料。baseline 的 debug 日誌會刻意展示原始輸出，不能視為可公開的安全回應。",
              "- M6 的 success 表示評測請求完成，healthy 洩漏對照組故意有失敗的 no_secret 斷言；HARNESS VALID 不代表模型零洩漏。",
              "- 固定 seed 與 temperature 不保證跨版本或跨硬體一致；環境鎖與實測次數都必須保留。",
              f"- 本次稽核共 {len(audit)} 筆；不防竄改、不替代正式集中式稽核系統。無防禦攻擊流程的 allow 會標記 demo.unguarded_dispatch。",
              "- pytest 若有相依套件棄用警告，保留在原始輸出，不為消除警告而升級基線套件。"]
    (ROOT / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(f"Report: M1={counts(initial)}, regression={counts(regression)}, M4 verified={m4_ok}")


if __name__ == "__main__":
    main()
