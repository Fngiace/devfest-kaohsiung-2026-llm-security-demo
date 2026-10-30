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
| A 原始 API | `venv/bin/python tech-demo/a_raw_api/probe_raw.py` | 三設定 HTTP 狀態與欄位掃描；API 時間合計 59.17 秒 | `cat fallback-logs/devfest-kh/a-raw-json.txt` | 先看真實 JSON，再決定哪些欄位能離開後端。 |
| A curl | `sh tech-demo/a_raw_api/curl.sh false` | 與探測同一個已保存 request | `cat tech-demo/a_raw_api/out/false.json` | 不經 SDK，直接確認 runtime 回應。 |
| B fail-open | `venv/bin/python tech-demo/b_fail_open/run_compare.py` | N=320；API 中位 11.58 秒；若 N=null，未驗證成功，改展示失敗紀錄 | `cat fallback-logs/devfest-kh/b-compare.txt` | 解析失敗時不可把原始輸出當安全答案。 |
| B 差異 | `cat tech-demo/b_fail_open/diff.patch` | naive 與 fixed 實際差異，無模型 | 同左 | 找不到完整答案，就回固定安全訊息。 |
| C 單元測試 | `venv/bin/python -m pytest -v` | 確定性本機測試，計時見 evidence/m5/test-timing.json | `cat fallback-logs/devfest-kh/c-pytest.txt` | 正規化能補幾種包裝，但不能承諾語意防漏。 |
| D harness | `sh tech-demo/d_harness/run_d.sh` | naive 全過；strict 兩壞一好；首行合成測資警語，實測 0.176 秒 | `cat fallback-logs/devfest-kh/d-harness.txt` | 先驗證斷言真的執行，再相信通過率。 |
| 稽核 | `venv/bin/python scripts/audit_tail.py` | 最後三筆 JSON 決策，無模型 | `tail -n 3 fallback-logs/devfest-kh/s3-audit.jsonl` | 每次允許、拒絕、待確認都有規則與參數紀錄。 |

有 jq 時可用 `tail -n 3 audit/actions.jsonl | jq .`。JSONL 不能整份直接交給 `python -m json.tool`；單筆替代：`tail -n 1 audit/actions.jsonl | venv/bin/python -m json.tool`。

M6 備援檔首行依 SDD 放時間/digest 註解，第二行保留合成測資警語；live 程式第一行即為警語。
不要在台上執行 scan_budget.py、pip install 或 ollama pull；這些是準備工作。
