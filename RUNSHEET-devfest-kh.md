# DevFest 高雄現場操作表：本次候選機

開講前 10 分鐘：

1. 接電源、關閉大型程式，確認指定模型已下載。
2. `venv/bin/python scripts/check_env.py`；非零先排除差異。
3. `venv/bin/python scripts/warmup.py`。
4. 深色終端、至少 20pt；開啟勿擾、關閉通知。
5. `cat fallback-logs/devfest-kh/c-pytest.txt` 確認離線備援可讀。

以下皆在專案根目錄執行。備援是本機實測文字，未通過紀錄有明確標示。

| 段落 | 精確指令 | 秒數中位數 | 初始成功 | 建議 | 失敗切換 | 台上口徑 |
|---|---|---:|---:|---|---|---|
| s1-attack | `venv/bin/python scenario1-systemprompt/attack.py --live --no-save` | 13.22 | 3/3 | LIVE | `cat fallback-logs/devfest-kh/s1-attack.txt` | 每個生成欄位都要確認去向。 |
| s1-defended | `venv/bin/python scenario1-systemprompt/defended.py --no-save` | 11.91 | 3/3 | LIVE | `cat fallback-logs/devfest-kh/s1-defended.txt` | 每個生成欄位都要確認去向。 |
| s1-attack-zh | `venv/bin/python scenario1-systemprompt/attack_zh.py --live --no-save` | 11.17 | 3/3 | LIVE | `cat fallback-logs/devfest-kh/s1-attack-zh.txt` | 每個生成欄位都要確認去向。 |
| s1-defended-zh | `venv/bin/python scenario1-systemprompt/defended_zh.py --live --no-save` | 18.83 | 3/3 | LIVE | `cat fallback-logs/devfest-kh/s1-defended-zh.txt` | 每個生成欄位都要確認去向。 |
| s2-attack | `venv/bin/python scenario2-rag/attack.py --no-save` | 13.38 | 3/3 | 預錄 | `cat fallback-logs/devfest-kh/s2-attack.txt` | 檢索資料不是指令來源。 |
| s2-defended | `venv/bin/python scenario2-rag/defended.py --no-save` | 9.32 | 3/3 | LIVE | `cat fallback-logs/devfest-kh/s2-defended.txt` | 檢索資料不是指令來源。 |
| s3-attack | `venv/bin/python scenario3-agent-privilege/attack.py --live --no-save` | 2.67 | 3/3 | LIVE | `cat fallback-logs/devfest-kh/s3-attack.txt` | 工具權限由程式端政策決定。 |
| s3-defended | `venv/bin/python scenario3-agent-privilege/defended.py --no-save` | 2.91 | 3/3 | LIVE | `cat fallback-logs/devfest-kh/s3-defended.txt` | 工具權限由程式端政策決定。 |

建議同時採納兩輪穩定度；RAG 攻擊若回歸有失敗，即使初始 M2 表為 LIVE 仍切備援。
預期畫面：S1 攻擊檢查 canary，defended 的 Returned to user 不含機密；S2 攻擊檢查 ORCHID-ESCALATE-9；S3 defended 顯示 rejected 且 customer_db.json exists: True。

| 技術段落 | 指令 | 預期畫面／實測秒數 | 失敗切換 | 台上口徑 |
|---|---|---|---|---|
| A | `venv/bin/python scripts/demo.py --scene raw-api --mode live` | 三設定原始 JSON；API 合計 35.45s | `cat fallback-logs/devfest-kh/a-raw-json.txt` | 先看真實欄位再決定哪些資料能離開後端。 |
| A curl | `sh tech-demo/a_raw_api/curl.sh false evidence/run-20261103/m3/out` | 同一份已保存 request | `cat evidence/run-20261103/m3/out/false.json` | 直接 HTTP 驗證 runtime。 |
| B 備援 | `cat fallback-logs/devfest-kh/b-compare.txt` | 未找到連續 5/5 的 N；只重播有來源的真實結果 | 同左 | 這是本機實測回應，未達穩定 LIVE 門檻。 |
| B diff | `cat tech-demo/b_fail_open/diff.patch` | naive 與 fixed 的實際差異 | 同左 | 缺少閉合標籤時 fail closed。 |
| C | `venv/bin/python -m pytest -v` | 全綠；整個程序 0.959s | `cat fallback-logs/devfest-kh/c-pytest.txt` | 掃描涵蓋常見包裝，語意改寫仍有限制。 |
| D | `sh tech-demo/d_harness/run_d.sh` | 首行合成警語，strict 兩壞一好；0.205s | `cat fallback-logs/devfest-kh/d-harness.txt` | 先驗證斷言真的執行。 |
| 稽核 | `venv/bin/python scripts/audit_tail.py` | 最近三筆決策與規則 | `tail -n 3 fallback-logs/devfest-kh/s3-audit.jsonl` | 每次工具呼叫都留下決策。 |

有 jq：`tail -n 3 audit/actions.jsonl | jq .`；單筆替代：`tail -n 1 audit/actions.jsonl | venv/bin/python -m json.tool`。

40 分鐘建議節奏：0–5 分鐘介紹；5–14 分鐘 S1 與 A；14–22 分鐘 B 與 C；22–28 分鐘 D；28–35 分鐘 S2、S3 與稽核；35–40 分鐘限制與問答。

單次速度不代表穩定：參考 timing-m2.md 的三次成功率與最慢值。未重現的段落不能說成功；M6 live 第一行有合成警語，備援檔第一行依 SDD 是時間/digest。

## 已驗證的演示入口

互動選段：`venv/bin/python scripts/demo.py`。完整彩排：`venv/bin/python scripts/demo.py --rehearse`。

本次完整彩排 80.72 秒：9 段 LIVE 通過、2 段備援。RAG 攻擊與 fail-open 的 auto 模式預設 replay；其他已驗證段落預設 LIVE。LIVE 若未通過會顯示備援並以 2 結束，不算本次成功。

完全不呼叫模型：`venv/bin/python scripts/demo.py --rehearse --mode replay`（11 段已實跑驗證）。
