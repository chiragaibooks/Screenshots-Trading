@echo off
:: Creates a Windows Task Scheduler task that runs main.py
:: Mon-Fri at 09:10 IST automatically
:: Run this file ONCE as Administrator to set it up

set TASK_NAME=NIFTY_Options_Collector
set SCRIPT_DIR=%~dp0
set BAT_FILE=%SCRIPT_DIR%run.bat

:: Create logs folder if not exists
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"

:: Delete existing task if any
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: Create new task — Mon-Fri at 09:10
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "\"%BAT_FILE%\"" ^
  /sc weekly ^
  /d MON,TUE,WED,THU,FRI ^
  /st 09:10 ^
  /ru "%USERNAME%" ^
  /rl HIGHEST ^
  /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Task scheduled successfully.
    echo      Name    : %TASK_NAME%
    echo      Runs    : Mon-Fri at 09:10
    echo      Script  : %BAT_FILE%
    echo      Logs    : %SCRIPT_DIR%logs\main.log
    echo.
    echo To remove it later, run:
    echo   schtasks /delete /tn "%TASK_NAME%" /f
) else (
    echo.
    echo [ERROR] Failed to create task. Make sure you run this as Administrator.
)
pause
