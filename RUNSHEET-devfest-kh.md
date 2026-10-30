# DevFest 2026 高雄現場操作表

所有命令從專案根目錄執行。所有推論僅呼叫 localhost:11434。
先閱讀 REPORT.md 的失敗／未重現項目；備援是實測文字紀錄，不是影片。

## 開講前 10 分鐘

1. 接電源；關閉大型程式，確認剩餘記憶體。
2. 執行 `venv/bin/python scripts/check_env.py`；非零就停止 LIVE，檢查 drift，勿直接重鎖掩蓋差異。
3. 執行 `venv/bin/python scripts/warmup.py` 預熱指定模型。
4. 終端深色底、至少 20pt；開啟勿擾、關閉通知；依此表預先開好分頁。
5. `cat fallback-logs/devfest-kh/c-pytest.txt` 確認備援可讀；模型下載與套件安裝均已在台下完成。

## 三場景

建議以 `venv/bin/python scripts/demo.py` 選擇段落；`--rehearse` 會無停頓依序跑 11 段技術彩排。正式講解請逐段執行，讓觀眾有時間閱讀。

| 模式 | 行為 |
|---|---|
| `--mode auto`（預設） | S1 攻擊與 S2 攻擊使用歷史實測備援；其餘 LIVE。LIVE 失敗時明示並切換備援。 |
| `--mode live` | 強制嘗試 LIVE；環境不符就停止模型呼叫，不顯示替代成功。 |
| `--mode replay` | 只讀已保存紀錄，模型離線也能展示。 |

例：`venv/bin/python scripts/demo.py --scene fail-open --mode live`。`--list` 列出全部 13 段；`--timeout 45` 可覆寫單段時限。預設模型段落 60 秒，原始 API 三設定合計 90 秒。逾時會終止該次 CLI 子程序群組、保留部分輸出；Ollama 服務維持運行，伺服器端請求可能需要時間才停止。Ctrl+C 取消整次彩排，不自動繼續下一段。

每次彩排產生新的 `evidence/rehearsal/<時間-唯一值>/`，包含 `results.json`、逐段 `result.json`、原始模型回應、輸出與環境檢查。`live_passed=null` 表示未進行 LIVE，不能算成功；`false` 表示未通過。退出碼 `0` 表示推薦展示完成（可能包含預定備援），`2` 表示 LIVE 失敗／環境不符／備援缺失，`130` 表示取消。成功顯示備援也不會消除本次 LIVE 失敗。

### 40 分鐘講解節奏

| 時間 | 段落／操作 | 觀眾應看到的重點 |
|---|---|---|
| 00–04 分 | 開場與資料流 | canary 是假機密；原始輸出、使用者答案、工具執行是不同邊界。 |
| 04–10 分 | `s1-attack-zh` → `s1-defended-zh` | 備援攻擊與 LIVE 防禦分別標示；答案通過輸出檢查後才回傳。 |
| 10–16 分 | `raw-api` → `fail-open` | 分清 native thinking 與文字標籤；N=320 截斷時 naive 與 fixed 的差異。 |
| 16–21 分 | `tests` → `harness` | 先看實際斷言；harness 段首標明合成測資。 |
| 21–27 分 | `s2-attack` → `s2-defended` | RAG 攻擊歷史僅 2/3，不宣稱穩定；展示不可信文件的處理。 |
| 27–33 分 | `s3-attack` → `s3-defended` → `audit` | 新 sandbox 假資料、policy 拒絕與可追溯決策。 |
| 33–36 分 | 重點回顧 | 輸出檢查、工具授權、評估斷言各自負責什麼。 |
| 36–40 分 | 問答／緩衝 | 不在現場重新掃描 token 預算或安裝依賴。 |

以下保留底層命令供排查使用；台上優先使用入口，以免原始 CLI 無時限地等待。

| 段落 | 精確指令 | M1 中位秒數 | 成功次數 | 失敗備援 |
|---|---|---:|---:|---|
| s1-attack | `venv/bin/python scenario1-systemprompt/attack.py --live --no-save` | 18.69 | 3/3 | `cat fallback-logs/devfest-kh/s1-attack.txt` |
| s1-defended | `venv/bin/python scenario1-systemprompt/defended.py --no-save` | 16.00 | 3/3 | `cat fallback-logs/devfest-kh/s1-defended.txt` |
| s1-attack-zh | `venv/bin/python scenario1-systemprompt/attack_zh.py --live --no-save` | 26.40 | 3/3 | `cat fallback-logs/devfest-kh/s1-attack-zh.txt` |
| s1-defended-zh | `venv/bin/python scenario1-systemprompt/defended_zh.py --live --no-save` | 38.62 | 3/3 | `cat fallback-logs/devfest-kh/s1-defended-zh.txt` |
| s2-attack | `venv/bin/python scenario2-rag/attack.py --no-save` | 33.25 | 2/3 | `cat fallback-logs/devfest-kh/s2-attack.txt` |
| s2-defended | `venv/bin/python scenario2-rag/defended.py --no-save` | 14.73 | 3/3 | `cat fallback-logs/devfest-kh/s2-defended.txt` |
| s3-attack | `venv/bin/python scenario3-agent-privilege/attack.py --live --no-save` | 5.00 | 3/3 | `cat fallback-logs/devfest-kh/s3-attack.txt` |
| s3-defended | `venv/bin/python scenario3-agent-privilege/defended.py --no-save` | 4.06 | 3/3 | `cat fallback-logs/devfest-kh/s3-defended.txt` |

預期畫面：場景一攻擊若成功會在原始輸出找到 canary，防禦只回傳掃描後的 answer；場景二檢查 ORCHID-ESCALATE-9 是否出現；場景三只在新 sandbox 測試刪除，防禦顯示 rejected 且資料仍存在。
若 timing-m2.md 建議預錄，使用上表備援文字；若 0/3，展示未重現結果或略過，不能宣稱成功。

台上口徑：場景一『模型生成的任何欄位都要看清楚送到哪裡。』場景二『檢索資料不是新的指令來源。』場景三『工具能不能執行，由程式端政策決定。』

## 技術 demo

| 段落 | 精確指令 | 預期畫面／時間來源 | 備援 | 台上口徑 |
|---|---|---|---|---|
| A 原始 API | `venv/bin/python scripts/demo.py --scene raw-api --mode live` | 三設定 HTTP 狀態與欄位掃描；API 時間合計 59.17 秒 | `cat fallback-logs/devfest-kh/a-raw-json.txt` | 先看真實 JSON，再決定哪些欄位能離開後端。 |
| A curl | `sh tech-demo/a_raw_api/curl.sh false` | 與探測同一個已保存 request | `cat tech-demo/a_raw_api/out/false.json` | 不經 SDK，直接確認 runtime 回應。 |
| B fail-open | `venv/bin/python tech-demo/b_fail_open/run_compare.py` | N=320；API 中位 11.58 秒；若 N=null，未驗證成功，改展示失敗紀錄 | `cat fallback-logs/devfest-kh/b-compare.txt` | 解析失敗時不可把原始輸出當安全答案。 |
| B 差異 | `cat tech-demo/b_fail_open/diff.patch` | naive 與 fixed 實際差異，無模型 | 同左 | 找不到完整答案，就回固定安全訊息。 |
| C 單元測試 | `venv/bin/python -m pytest -v` | 確定性本機測試，計時見 evidence/m5/test-timing.json | `cat fallback-logs/devfest-kh/c-pytest.txt` | 正規化能補幾種包裝，但不能承諾語意防漏。 |
| D harness | `sh tech-demo/d_harness/run_d.sh` | naive 全過；strict 兩壞一好；首行合成測資警語，實測 0.176 秒 | `cat fallback-logs/devfest-kh/d-harness.txt` | 先驗證斷言真的執行，再相信通過率。 |
| 稽核 | `venv/bin/python scripts/audit_tail.py` | 最後三筆 JSON 決策，無模型 | `tail -n 3 fallback-logs/devfest-kh/s3-audit.jsonl` | 每次允許、拒絕、待確認都有規則與參數紀錄。 |

有 jq 時可用 `tail -n 3 audit/actions.jsonl | jq .`。JSONL 不能整份直接交給 `python -m json.tool`；單筆替代：`tail -n 1 audit/actions.jsonl | venv/bin/python -m json.tool`。

M6 備援檔首行依 SDD 放時間/digest 註解，第二行保留合成測資警語；live 程式第一行即為警語。
不要在台上執行 scan_budget.py、pip install 或 ollama pull；這些是準備工作。
