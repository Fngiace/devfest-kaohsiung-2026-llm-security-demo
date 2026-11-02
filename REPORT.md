# DevFest 高雄 2026：候選上台機重新實測

本次開始：2026-11-03T01:08:16.994011+08:00。本次證據：`evidence/run-20261103/`。舊 M2 報告與環境鎖保留在 `evidence/run-20261103/previous/`。
所有成功與失敗均保留，先前機器的輸出不計入本次成功率。

## 1. 環境摘要

- 實際硬體：Apple M1 Pro／32.0 GiB；macOS 27.0.1。
- Ollama 0.40.9；固定模型 `gemma4:e4b`；8.1B／nvfp4。
- digest：`eb2177adf7646d15faead94fdad6d3e170dc8015653418a3b7d5d52a6380be5b`。
- Python 3.12.15；requirements SHA-256 `e5112a16798feb11436f224597bf85052a838b3ccf5e26f624ed180be1699dc2`。
- 工作分支 devfest-kh-2026；從指定遠端既有分支續作，保留原有 COSCUP 歷史；main 沒有修改。

## 2. 各階段結果

| 階段 | 狀態 | 證據目錄 |
|---|---|---|
| M0 | 完成 | evidence/run-20261103/m0/ |
| M1 | 待執行 | evidence/run-20261103/m1/ |
| M2 | 待執行 | evidence/run-20261103/m2/ |
| M3 | 待執行 | evidence/run-20261103/m3/ |
| M4 | 待執行 | evidence/run-20261103/m4/ |
| M5 | 待執行 | evidence/run-20261103/m5/ |
| M6 | 待執行 | evidence/run-20261103/m6/ |
| M7 | 待執行 | evidence/run-20261103/m7/ |
| M8 | 待執行 | evidence/run-20261103/m8/ |

## 3. M2 時間與現場建議


## 4. M3 原始 API 結論

| think | HTTP | content 機密 | content thinking 段機密 | 原生 thinking 機密 | 秒數 |
|---|---:|---|---|---|---:|

## 5. M4 截斷掃描與五次結果

選定 N：`None`；候選集合：`[]`。最小值限於宣告的遞增候選集合。
temperature=0、seed=42；沿用原攻擊與原 prompt；不把原生 message.thinking 拼接成 naive 顯示的 content。
每個候選第一次不合格即淘汰；選中的候選必須連續五次合格，再獨立比較五次。

| 次數 | N | naive 洩漏 | answer 閉合 | fixed 安全 | 完整驗證 |
|---|---:|---|---|---|---|

## 6. 偏離 SDD 與原因

- 使用者同意以這台候選上台機試跑；實際是 M1 Pro／32GB，不能把這次量測標成 M2。
- 遠端既有 devfest-kh-2026 已含全部實作；本次沿用該分支與保護機制，做兩輪獨立完整回歸，沒有假裝重新寫出已存在的修補。
- 英文 S1 defended 不支援 --live，照實使用 --no-save。
- M1/M2 共用同批三次有完整 token 計時的實跑；固定三次，不挑成功樣本替代失敗。
- 模型下載、Git clone 與 pip install 是文件允許的準備連網；模型推論只走 localhost:11434，評分為確定性判定。
- Terminal 的 Computer Use 存取被工具拒絕；依 SDD 產出十份真實文字素材，需要手動截圖。
- 原有 requirements.txt 與 requirements-dev.txt 版本完全保留；Python 和 Ollama 使用本機版本並鎖定。
- env-lock 的 commit 是最後影響 runtime 原始碼的提交，搭配逐檔 hash；M4 config 更新後重新鎖定，避免鎖檔自我參照。

## 7. 待 Fngi 決定

- 依本次成功率、中位數與最慢值決定這台是否上台；不穩定或超時段落建議使用有來源的實測文字備援。
- 截圖素材使用深色終端、至少 20pt 手動截圖；保留警語與未通過標籤。

## 8. 已知限制

- 正規化掃描無法阻止翻譯、語意改寫、跨段或多層編碼；Finding 是原文 Python 字元位置，編碼命中指向整個 token。
- 所有機密是展示 canary；刪除只在每次新建的 sandbox/run-* 內進行，路徑逃逸測試另外驗證。
- 固定 temperature/seed 無法保證跨 runtime、模型 digest 或硬體一致；保留失敗而不改 prompt。
- M6 success 表示請求完成，healthy 的已知洩漏對照組應被斷言抓到；HARNESS VALID 不代表模型零洩漏。
- audit 是示範 JSONL，未提供防竄改保證；confirm 不是人類已批准。
- pytest 的相依棄用警告保留，不為消除警告升級套件。
