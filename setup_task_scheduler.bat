@echo off
:: ─────────────────────────────────────────────────────────────────────────────
::  NIFTY Automation — Windows Task Scheduler Setup
::  Run this ONCE as Administrator to register all 5 weekday tasks.
::  Each task launches run.bat at the configured start time; main.py then
::  waits internally until the exact minute before capturing.
:: ─────────────────────────────────────────────────────────────────────────────
NET SESSION >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Please run this script as Administrator.
    pause & exit /b 1
)

:: ── Edit this path if you move the project folder ────────────────────────────
SET SCRIPT_DIR=%~dp0
SET BAT_FILE=%SCRIPT_DIR%run.bat
:: ─────────────────────────────────────────────────────────────────────────────

:: Times must match SCHEDULE in config.py  (24-hour HH:MM)
SET MON_TIME=09:10
SET TUE_TIME=10:55
SET WED_TIME=14:00
SET THU_TIME=10:25
SET FRI_TIME=13:15

:: Start 5 minutes early so pip/playwright checks finish before capture begins

CALL :register "NIFTY_Monday"    MON %MON_TIME%
CALL :register "NIFTY_Tuesday"   TUE %TUE_TIME%
CALL :register "NIFTY_Wednesday" WED %WED_TIME%
CALL :register "NIFTY_Thursday"  THU %THU_TIME%
CALL :register "NIFTY_Friday"    FRI %FRI_TIME%

echo.
echo [DONE] All tasks registered. View them in Task Scheduler (taskschd.msc).
pause
exit /b 0


:register
SET TASK_NAME=%~1
SET DAY=%~2
SET START_TIME=%~3

schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

schtasks /Create ^
  /TN "%TASK_NAME%" ^
  /TR "cmd /c \"%BAT_FILE%\"" ^
  /SC WEEKLY ^
  /D %DAY% ^
  /ST %START_TIME% ^
  /RL HIGHEST ^
  /F

IF ERRORLEVEL 1 (
    echo [ERROR] Failed to register %TASK_NAME%
) ELSE (
    echo [OK] Registered: %TASK_NAME%  every %DAY% at %START_TIME%
)
EXIT /B
