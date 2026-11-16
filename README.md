# DevFest 2026 高雄｜LLM 安全實戰示範

議程：**它拒絕了，但思考鏈出賣了它**（2026-11-14，DevFest 高雄，40 分鐘）。

這個 repo 是現場 demo 的完整程式碼：在本機 Ollama 的 `gemma4:e4b` 上重現三個 LLM 應用安全問題，並示範對應的防禦。全程只呼叫本機模型（`http://localhost:11434`），不使用雲端 API，也不用 LLM 當裁判，判定一律是確定性的字串比對。

議程、技術內容與會眾操作的互動前端統一使用 **DevFest 高雄 2026** 與議程 **「它拒絕了，但思考鏈出賣了它」** 的品牌文案。

> 所有「機密」都是示範用的假字串（canary），客戶資料是每次執行新建的沙盒假資料。

## 三個場景

| 場景 | 問題 | 防禦 | 腳本 |
|---|---|---|---|
| 1. System prompt 外洩 | 模型嘴上拒絕，機密卻寫在 `<thinking>` 裡，整包回傳就外洩 | `output_rail`：只回傳 `<answer>`、沒有合法標籤就 fail closed、輸出端掃描 canary | `scenario1-systemprompt/` |
| 2. RAG 間接注入 | 知識庫裡被污染的文件夾帶指令，模型照做 | `retrieval_rail`：取回內容先掃描注入特徵，並明確區隔資料與指令 | `scenario2-rag/` |
| 3. Agent 權限過大 | Agent 被誘導呼叫 `delete_all_data` | `action_rail`：權限檢查放在 dispatcher（程式層），規則在 `policy.yaml`，每次呼叫寫一行 JSONL 稽核 | `scenario3-agent-privilege/` |

場景 1 另有繁體中文版（`*_zh.py`）。防禦邏輯在 [`nemoclaw/`](nemoclaw/)。

## 四個技術示範（`tech-demo/`）

- **A　原始 API 回應**：同一次回應裡，`message.thinking` 與 `message.content` 是兩個欄位；比較 `think` 參數省略／true／false 的差異。
- **B　Fail-open 重現**：回答被截斷、缺少閉合標籤時，naive 實作會把原始輸出整包回傳；fixed 版本改為 fail closed。差異見 [`diff.patch`](tech-demo/b_fail_open/diff.patch)。
- **C　單元測試**：`pytest -v`，包含正規化掃描（NFKC、零寬字元、分隔符、大小寫、base64／hex）。
- **D　測試工具自我檢查**：`naive` 判定器只看 success 欄位，`strict` 會檢查斷言有沒有真的執行、判定的是不是 `answer`、對照組有沒有被抓到。測資為合成資料，執行時第一行會印出警語。

## 快速開始（會眾本機體驗）

### 一鍵啟動本機網頁實驗室（macOS / Windows）

不需手動敲指令，裝完即可在自己的瀏覽器親手修改 Prompt 與污染文件，並同時比較「無防禦 vs. 有防禦」：

1. 先安裝 [Python 3.12](https://www.python.org) 與 [Ollama](https://ollama.com)（若只想看已保存的「離線重播」，可略過 Ollama）。
2. **macOS**：雙擊 `Install-Web-Demo.command` 完成安裝，之後雙擊 `Start-Web-Demo.command`。
3. **Windows**：雙擊 `Install-Web-Demo.bat` 完成安裝，之後雙擊 `Start-Web-Demo.bat`。
4. 瀏覽器會自動開啟 `http://127.0.0.1:8765`（僅綁定本機 Loopback，不對外開放）。

### 終端機手動安裝與執行

需要 Python 3.12 與 [Ollama](https://ollama.com)。

```sh
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
ollama pull gemma4:e4b
ollama serve   # 或開啟 Ollama App
```

啟動網頁實驗室：

```sh
venv/bin/python webdemo/server.py --open
```

跑測試（不需要模型）：

```sh
venv/bin/python -m pytest -v
```

跑 demo：

```sh
venv/bin/python scripts/demo.py --list                       # 列出所有段落
venv/bin/python scripts/demo.py --scene s1-attack-zh --mode live
venv/bin/python scripts/demo.py --scene s3-defended --mode live
venv/bin/python scripts/demo.py --scene harness              # 不需要模型
```

段落名稱：`s1-attack`、`s1-defended`、`s1-attack-zh`、`s1-defended-zh`、`s2-attack`、`s2-defended`、`s3-attack`、`s3-defended`、`raw-api`、`fail-open`、`tests`、`harness`、`audit`。

`--mode` 有三種：`auto`（預設，LIVE 沒重現就改播備援）、`live`（不自動切換）、`replay`（不呼叫模型，播放 [`fallback-logs/devfest-kh/`](fallback-logs/devfest-kh/) 的已保存輸出）。LIVE 沒有通過時會以退出碼 `2` 結束，不會把備援算成成功。每次執行的紀錄會存到 `evidence/rehearsal/`（已被 `.gitignore` 排除）。

也可以直接執行單一腳本，例如：

```sh
venv/bin/python scenario1-systemprompt/attack_zh.py --live --no-save
```

### 選用：鎖定環境

`scripts/check_env.py --capture` 會在你的機器上記錄模型 digest、套件版本與來源雜湊到 `env-lock.json`；之後 `demo.py` 的 LIVE 模式會先比對，環境一變就停止。沒有 `env-lock.json` 時會略過這個檢查。

## 重現時請注意

- 模型輸出不是確定性的：同一支攻擊腳本不保證每次都洩漏，防禦腳本也不保證每次格式都合規。講者的測試中，RAG 攻擊在 6 次裡重現 5 次；fail-open 的截斷點沒有找到連續穩定重現的長度，所以現場用保存的真實回應重播。
- `fallback-logs/devfest-kh/` 是講者機器（Apple M1 Pro／32GB，Ollama，`gemma4:e4b`）上實際跑出的 DevFest 輸出，不是手寫的。
- `scenario3-agent-privilege/attack.py` 會**故意刪除**該次沙盒裡的 `customer_db.json`。每次執行都使用全新的 `sandbox/run-*`，並拒絕路徑逃逸，不會動到你的真實檔案。
- 原始 API 與 debug 輸出刻意顯示 canary；防禦保護的是 `Returned to user`，不是把 debug log 變成可以公開的資料。
- 正規化掃描**擋不住**翻譯、語意改寫或任意多層編碼；`retrieval_rail` 的 regex 只是示範，正式環境應搭配分類器。
- `policy.yaml` 以 JSON 語法寫成（相容 YAML 1.2）；`require_human_confirm` 只代表需要人工確認，不代表已獲授權。

## 目錄

```
common/                  Ollama 呼叫、報告輸出
nemoclaw/                三道防線：output_rail、retrieval_rail、action_rail、secret_scan、policy
scenario1-3/             各場景的 attack／defended／assert_check
tech-demo/               四個技術示範
scripts/                 demo.py（舞台執行器）、check_env.py、run_matrix.py 等
tests/                   單元測試
fallback-logs/           已保存的真實輸出（備援）
webdemo/                 會眾用的本機互動網頁與 API
AUDIENCE-PACKAGE.md      會眾發佈範圍與檔案清單
```

## 授權

[MIT](LICENSE)
