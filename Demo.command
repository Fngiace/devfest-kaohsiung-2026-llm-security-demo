#!/bin/zsh
cd -- "${0:A:h}" || exit 1
export PATH="/opt/homebrew/bin:$PATH"
printf '\nDevFest 高雄 2026 — LLM 安全 DEMO\n'
printf '1. 完整示範（LIVE + 明確標示的備援）\n2. 互動選擇場景\n3. 完整備援重播（不需要模型）\n'
read 'choice?請選擇 [1/2/3，預設 1]：'
case "$choice" in
  2) venv/bin/python scripts/demo.py ;;
  3) venv/bin/python scripts/demo.py --rehearse --mode replay ;;
  *) venv/bin/python scripts/demo.py --rehearse --mode auto --timeout 180 ;;
esac
printf '\n示範結束；紀錄位於 evidence/rehearsal/。\n'
read 'finish?按 Enter 關閉視窗。'
