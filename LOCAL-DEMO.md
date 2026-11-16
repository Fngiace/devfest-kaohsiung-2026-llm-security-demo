# 本機 DEMO

專案位置：`/Users/fngi/Downloads/TEST`
分支：`devfest-kh-2026`

內容品牌：DevFest 高雄 2026 議程；互動前端同樣使用 DevFest 高雄 2026 與議程「它拒絕了，但思考鏈出賣了它」的品牌文案。

## 開始展示

### 方式一：本機互動網頁實驗室（推薦會眾與現場互動）

- **macOS**：
  1. 首次使用請雙擊 `Install-Web-Demo.command`（自動建立 `venv`、安裝套件，若有安裝 Ollama 則自動拉取 `gemma4:e4b`）。
  2. 雙擊 `Start-Web-Demo.command`，瀏覽器會自動開啟 `http://127.0.0.1:8765`。
- **Windows**：
  1. 首次使用請雙擊 `Install-Web-Demo.bat`。
  2. 雙擊 `Start-Web-Demo.bat`，瀏覽器會自動開啟 `http://127.0.0.1:8765`。
- **終端機直接啟動**：
  ```sh
  venv/bin/python webdemo/server.py --open
  ```
- 支援 **LIVE（本機模型實測，可自訂提示詞與污染文件）** 與 **離線重播（不需要下載模型也能查看對照結果）**。

### 方式二：終端機舞台模式

在 Finder 雙擊 `Demo.command`，選擇完整示範、互動選擇或離線重播。

也可在終端機執行：

```sh
cd /Users/fngi/Downloads/TEST
venv/bin/python scripts/demo.py --rehearse --mode auto --timeout 180
```

`auto` 依專案推薦選擇 LIVE 或重播，LIVE 失敗時可播放備援。
備援會明確標記「非本次 LIVE」，不會算成 LIVE 成功。
模型未下載完成時，請選離線重播：

```sh
venv/bin/python scripts/demo.py --rehearse --mode replay
```

## 三個場景的觀看重點

1. System prompt：比較原始回應內的示範機密與防禦版 `Returned to user`。
2. RAG：比較污染文件是否誘導輸出 `ORCHID-ESCALATE-9`，以及檢索防線的處理。
3. Agent：比較無保護時沙盒資料被刪除，以及 dispatcher 權限檢查拒絕刪除並保留資料。

所有機密與客戶資料均為專案測試資料。場景 3 的刪除限於每次新建的沙盒。

## 服務與紀錄

Ollama 透過 Homebrew 背景服務啟動，預設本機 API：`http://localhost:11434`。

```sh
ollama list
brew services info ollama
brew services stop ollama
brew services start ollama
```

每次 DEMO 證據儲存於 `evidence/rehearsal/`，包含 `results.json` 與各段輸出。
安裝時模型下載紀錄：`/tmp/devfest-model-pull.log`。

## 已完成驗證

- Python 3.12 獨立虛擬環境與專案鎖定依賴已安裝。
- `pip check` 通過。
- 57 項 pytest 測試通過（1 項第三方套件棄用警告）。
- harness 合成測資示範通過。
- 11 段離線備援可完整重播。
- `gemma4:e4b`（9.5 GB）已下載，模型 ID：`eb2177adf764`。
- 已建立 `env-lock.json`，環境版本比對通過。
- 完整彩排：9 段 LIVE 通過、2 段預定重播，退出碼 0。
  證據：`evidence/rehearsal/20261116T171815-6iep1uhu/results.json`。
- 額外執行 RAG 攻擊 LIVE：成功重現，退出碼 0。
  證據：`evidence/rehearsal/20261116T172008-1t3adu61/results.json`。
- 三大場景的攻擊與防禦均已完成本機 LIVE 驗證；fail-open 使用專案保存的重播。
- 模型輸出存在變動，未來每次執行不保證重現相同結果。
