@echo off
cd /d "%~dp0"
python -X utf8 main.py >> logs\main.log 2>&1
