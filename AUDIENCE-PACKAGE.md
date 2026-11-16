# 會眾發佈範圍

這個專案同時包含「會眾互動產品」與「講者的舞台、測試、研究素材」。兩者不應直接用整個 repository 混在一起發佈。

## 建議給會眾

### 必要檔案

- `Install-Web-Demo.command`、`Install-Web-Demo.bat`：安裝 Python 環境；沒有 Ollama 時仍可使用離線重播。
- `Start-Web-Demo.command`、`Start-Web-Demo.bat`：啟動 `http://127.0.0.1:8765/`。
- `webdemo/`：瀏覽器介面、本機 API 與實驗執行器。
- `common/`：本機 Ollama 呼叫與輸出處理。
- `nemoclaw/`：三道防線的實作。
- `scenario1-systemprompt/`、`scenario2-rag/`、`scenario3-agent-privilege/`：網頁實驗所需的 prompt、污染文件、沙盒工具與場景程式。
- `policy.yaml`：Agent 權限規則。
- `fallback-logs/devfest-kh/`：離線重播素材；沒有模型時仍能操作比較介面。
- `requirements.txt`、`LICENSE`：Python 依賴與授權。

### 建議附上的說明

- `README.md`：完整專案介紹與安裝前提。
- `LOCAL-DEMO.md`：現場工作人員與會眾的啟動說明。

會眾需要先安裝 Python 3.12。要執行 LIVE 才需要另外安裝 Ollama 並下載 `gemma4:e4b`（約 9.5 GB）；只看離線重播不需要模型。

## 不建議給會眾

- `venv/`、`.git/`、`.pytest_cache/`、任何 `__pycache__/`：本機產物或版本控制資料。
- `evidence/`、`audit/`、`sandbox/`：講者執行後產生的紀錄、稽核資料與沙盒資料。
- `env-lock.json`：講者電腦的模型 digest、作業系統、套件版本與原始碼雜湊。
- `tech-demo/`：原始 API、fail-open、測試 harness 等講者技術段落；不影響網頁互動入口。
- `tests/`、`requirements-dev.txt`、`pytest.ini`：開發與 CI 驗證素材。
- `scripts/`、`Demo.command`：終端機舞台控制器；除非會眾也要使用命令列版本。
- `model-setup.md`、`docs/COSCUP-README.md`：講者探測紀錄與歷史文件。
- `fallback-logs/scenario*.txt`：舊版／其他場次備援，網頁只需要 `fallback-logs/devfest-kh/`。

## 目前檢查結果

網頁介面已統一顯示 DevFest 高雄 2026 議程「它拒絕了，但思考鏈出賣了它」。本機 API 綁定 `127.0.0.1`，不會把會眾電腦上的模型服務直接暴露到區網。
