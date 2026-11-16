@echo off
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
 echo Please run Install-Web-Demo.bat first.
 pause
 exit /b 1
)
venv\Scripts\python.exe webdemo\server.py --open
pause
