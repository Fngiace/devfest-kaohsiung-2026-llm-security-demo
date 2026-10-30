# DevFest 高雄 2026 執行報告

本報告隨實測更新。尚未執行的項目不視為通過。

## 環境摘要

- 本機：Apple M2，16 GiB，macOS 27.0.1（26A434）。
- Ollama server：0.40.6；指定模型 `gemma4:e4b` 正在下載。
- Python：3.14.6，`venv/`；基線 `requirements.txt` 原版本安裝成功。
- GitHub：`Fngiace/devfest-kaohsiung-2026-llm-security-demo`，分支 `devfest-kh-2026`。
- COSCUP 基線：`d713626`（包含指定的 `d6149b9`），保留完整上游歷史後匯入新專案。

## 各階段結果

| 階段 | 狀態 | 證據 |
|---|---|---|
| M0 | 進行中，等待模型下載完成後鎖定 | `scripts/check_env.py`、`evidence/setup/` |
| M1 | 待模型下載，已準備實跑驗證器 | `scripts/run_matrix.py` |
| M2 | 待 M1 量測 | — |
| M3 | 程式已準備，尚未實測 | `tech-demo/a_raw_api/` |
| M4 | 程式已準備，尚未實測 | `tech-demo/b_fail_open/` |
| M5 | 掃描器測試已過；尚未整合、模型回歸未執行 | `nemoclaw/secret_scan.py` |
| M6 | 完成 | `evidence/m6/harness.txt`、`evidence/m6/pytest.txt` |
| M7 | 政策模組與測試已準備，尚未整合 | `nemoclaw/policy.py`、`tests/test_policy.py` |
| M8 | 待實測 | — |

## M2 時間表

待實測，不填入估計數字冒充量測。

## M3 原始回應結論

待本機模型實測。

## M4 截斷預算

待實測。候選 N 為 64、96、128、160、200、256；「最小」定義為此候選集合內最小合格值。

## 偏離 SDD 的地方與原因

- 這是使用者指定的新 repository；先同步 SDD，再合併 COSCUP `main` 的完整歷史到工作分支。沒有修改上游 `main`，也沒有建立本機或新遠端 `main`。
- 模型下載期間先完成獨立的 M6，階段提交順序不代表全部按編號完成。
- 英文場景一 defended 不支援 `--live`，依文件例外使用 `--no-save`。
- 上游 `assert_check.py` 使用 `--replay` 合成回應，不當作 M1 實測證據；新增實跑驗證器檢查真實 API 回應。
- 新增獨立 `requirements-dev.txt` 鎖定 pytest 及其相依套件，既有 requirements 不變。
- `policy.yaml` 採 YAML 1.2 相容的 JSON 語法，使用標準函式庫讀取，避免為政策解析升級既有套件。
- `env-lock.json` 的 `repo.commit` 定義為最後修改執行程式路徑的 commit，另比對來源雜湊；排除純報告提交，避免 commit 與鎖檔互相參照而無法驗證。
- 推論僅限 localhost。下載模型、安裝套件、取得基線與 GitHub 同步是文件明許的建置網路操作。

## 待 Fngi 決定

- 待 M2、M3、M4 實測後決定 LIVE／備援段落。

## 已知限制

- 正規化機密掃描是示範，無法阻止翻譯、語意改寫、分段或多層編碼；單層解碼 token 上限 16,384 字元。
- `success: true` 在 M6 合成資料代表評測請求完成，不代表機密斷言通過；healthy 的洩漏對照組必須有失敗的 no_secret 斷言。
- 所有機密值均為既有 demo canary，未使用真實客戶資料。
