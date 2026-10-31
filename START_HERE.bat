@echo off
REM ====== REVON Hybrid Motorcycle Management System - one-click start (Windows) ======
title REVON TMS
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3.10+ is required: https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^) & pause & exit /b 1)
if not exist venv ( python -m venv venv )
call venv\Scripts\activate
pip install -q -r requirements.txt
echo.
set /p MYSQL_PASSWORD=Enter your MySQL root password (or just press Enter to use built-in SQLite): 
if "%MYSQL_PASSWORD%"=="" ( set DB_ENGINE=sqlite ) else ( set DB_ENGINE=mysql )
if "%DB_ENGINE%"=="mysql" ( python app.py --init-mysql )
start "" http://127.0.0.1:5000
python app.py
pause
