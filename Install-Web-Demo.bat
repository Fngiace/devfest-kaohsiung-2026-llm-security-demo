@echo off
cd /d "%~dp0"
set PY_CMD=
py -3.12 --version >nul 2>&1 && set PY_CMD=py -3.12
if not defined PY_CMD (
  py -3 --version >nul 2>&1 && set PY_CMD=py -3
)
if not defined PY_CMD (
  python --version >nul 2>&1 && set PY_CMD=python
)
if not defined PY_CMD (
  echo Install Python 3.12 from python.org first.
  pause
  exit /b 1
)
%PY_CMD% -m venv venv
if errorlevel 1 goto failed
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
where ollama >nul 2>&1
if errorlevel 1 (
  echo Python environment ready (Offline Replay mode available).
  echo To run LIVE mode, install Ollama from ollama.com and re-run this script.
  pause
  exit /b 0
)
ollama pull gemma4:e4b
if errorlevel 1 goto failed
echo Ready. Double-click Start-Web-Demo.bat.
pause
exit /b 0
:failed
echo Installation failed. Check the message above and retry.
pause
exit /b 1
