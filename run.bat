@echo off
TITLE NIFTY TradingView Automation
cd /d "%~dp0"

python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python not found. Add Python 3.10+ to PATH.
    pause & exit /b 1
)

IF NOT EXIST ".env" (
    copy ".env.example" ".env"
    echo [SETUP] .env created. Fill in GROQ_API_KEY and GITHUB_REPO_PATH, then re-run.
    notepad ".env"
    pause & exit /b 0
)

pip install -r requirements.txt --quiet
playwright install chromium --quiet

python main.py
echo.
echo [DONE] Session complete.
pause
