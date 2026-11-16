#!/bin/zsh
cd -- "${0:A:h}" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if [[ ! -x venv/bin/python ]]; then
  echo '請先雙擊 Install-Web-Demo.command 安裝。'
  read 'done?按 Enter 結束。'
  exit 1
fi
venv/bin/python webdemo/server.py --open
read 'done?服務已停止。按 Enter 結束。'
