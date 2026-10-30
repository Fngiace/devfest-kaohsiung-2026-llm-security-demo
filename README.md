# DevFest 2026 高雄｜LLM 安全實戰示範

議程：**它拒絕了，但思考鏈出賣了它**（2026-11-14，40 分鐘）。

在 Apple M2 上以本機 Ollama `gemma4:e4b` 重驗三場景，並提供原始 API、fail-open、正規化機密掃描、評測工具與權限稽核的 terminal demo。

目前驗收狀態與實測限制以 [REPORT.md](REPORT.md) 為準；不要把程式已寫好視為模型實測通過。

## 先看成果

- [執行報告](REPORT.md)：各階段狀態、證據、偏離與待決事項。
- [現場操作表](RUNSHEET-devfest-kh.md)：暖機、精確指令、預期畫面與備援。
- [時間表](timing-m2.md)：八支腳本三次實跑中位數與建議。
- [規格](devfest-kh-2026-live-demo-SDD-M2.md)：本次執行依據。
- `evidence/`：真實 CLI 輸出、API 回應、assertions 與計時。
- `fallback-logs/devfest-kh/`：本機實測備援文字；`screenshots/` 是手動截圖用文字素材。

## 現場執行

```sh
venv/bin/python scripts/check_env.py
venv/bin/python scripts/warmup.py
venv/bin/python -m pytest -v
sh tech-demo/d_harness/run_d.sh
```

其餘命令依 RUNSHEET；模型實測失敗或未重現的段落不可宣稱成功。

## 一次性安裝（需網路，台下完成）

```sh
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
ollama pull gemma4:e4b
```

模型不可替換；pull 失敗依 SDD 停止。既有 requirements 不升級。安裝、下載、GitHub 同步需網路；推論固定 `http://localhost:11434`，不使用雲端 API 或 LLM 裁判。

## 安全與證據界線

- 機密是展示用 canary，資料是新建 sandbox 裡的假客戶資料。
- `scenario3-agent-privilege/attack.py` 會故意刪除該次 sandbox 的 `customer_db.json`；每個程序使用全新的 `sandbox/run-*`，拒絕路徑逃逸。
- M6 fixture 是合成資料，執行第一行均有警語。上游 `--replay` 也不是本機實測，不能當作本次成功證據。
- 原始 API 與 debug 輸出刻意展示 canary；防禦保護的是 `Returned to user`，不是把 debug log 變成可以公開的安全資料。
- `policy.yaml` 使用 YAML 1.2 相容的 JSON 語法。實際執行記錄在 `audit/actions.jsonl`；`confirm` 不代表已獲授權。
- 正規化掃描不能防止翻譯、語意改寫或任意多層編碼。
- 本專案保留 [COSCUP 原始 README](docs/COSCUP-README.md) 與完整 Git 歷史；基線為 `d713626`。原始 fallback 不改寫。

## 環境鎖的 commit 定義

`env-lock.json` 記錄最後修改執行程式路徑的 commit，而非包含鎖檔本身的報告 commit，並逐檔比對來源 SHA-256、模型完整 digest、runtime、Python 與安裝套件。純證據提交不會造成自我參照；程式或環境改變會使 `check_env.py` 非零退出。
