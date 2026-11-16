#!/bin/zsh
cd -- "${0:A:h}" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
chmod +x Start-Web-Demo.command Demo.command 2>/dev/null || true
xattr -d com.apple.quarantine Start-Web-Demo.command Demo.command 2>/dev/null || true
PYTHON=$(command -v python3.12 || command -v python3)
if [[ -z "$PYTHON" ]]; then
  echo '請先安裝 Python 3.12（python.org 或 brew install python@3.12），再執行本安裝程式。'
  read 'done?按 Enter 結束。'
  exit 1
fi
"$PYTHON" -m venv venv && venv/bin/python -m pip install -r requirements.txt || exit 1
if ! command -v ollama >/dev/null; then
  echo '已完成 Python 環境安裝（可直接使用「離線重播」）。'
  echo '若要執行本機 LIVE 實測，請安裝 Ollama（ollama.com）後重新執行本安裝程式。'
  read 'done?按 Enter 結束。'
  exit 0
fi
if ! curl -fsS http://127.0.0.1:11434/api/version >/dev/null; then
  ollama serve > /tmp/devfest-ollama.log 2>&1 &
  sleep 3
fi
ollama pull gemma4:e4b || exit 1
echo '安裝完成！請雙擊 Start-Web-Demo.command（網頁互動版）或 Demo.command（終端機版）。'
read 'done?按 Enter 結束。'
