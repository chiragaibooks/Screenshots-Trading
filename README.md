# NIFTY TradingView Option Chain Automation

Captures TradingView NIFTY screenshots every minute for a 10-minute window on each weekday,
extracts option Greeks via Groq vision, saves structured data, and auto-pushes to GitHub.

## Project Structure

```
config.py                  ← ALL schedule times live here — edit this to change windows
main.py                    ← Orchestrator
scraper.py                 ← Playwright browser automation
parser.py                  ← Groq vision extraction
run.bat                    ← Start manually (double-click)
setup_task_scheduler.bat   ← Register Windows Task Scheduler tasks (run once as Admin)
requirements.txt
.env.example
```

## Setup

### 1. Prerequisites
- Python 3.10+
- Git configured with a remote GitHub repo
- A [Groq API key](https://console.groq.com/)

### 2. Configure environment
```
copy .env.example .env
```
Edit `.env`:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GITHUB_REPO_PATH=C:\path\to\your\git\repo
```

### 3. Initialize Git repo (if not already)
```
git init
git remote add origin https://github.com/<user>/<repo>.git
```

## Changing Capture Times

Open `config.py` — it is the **only file you need to edit**:

```python
SCHEDULE = {
    "Monday":    (9,  15),   # 09:15 – 09:25
    "Tuesday":   (11,  0),   # 11:00 – 11:10
    "Wednesday": (14,  5),   # 14:05 – 14:15
    "Thursday":  (10, 30),   # 10:30 – 10:40
    "Friday":    (13, 20),   # 13:20 – 13:30
}
```

After changing times, re-run `setup_task_scheduler.bat` as Administrator to update the tasks.

## Run Manually

Double-click `run.bat` — installs deps, sets up Playwright, starts automation.

## Automate with Windows Task Scheduler

1. Right-click `setup_task_scheduler.bat` → **Run as administrator**
2. It registers 5 weekly tasks (one per weekday) in Task Scheduler
3. Each task launches `run.bat` 5 minutes before the capture window
4. Verify in **Task Scheduler** (`taskschd.msc`) under Task Scheduler Library

> The tasks are named: `NIFTY_Monday`, `NIFTY_Tuesday`, `NIFTY_Wednesday`, `NIFTY_Thursday`, `NIFTY_Friday`

To remove all tasks:
```
schtasks /Delete /TN "NIFTY_Monday"    /F
schtasks /Delete /TN "NIFTY_Tuesday"   /F
schtasks /Delete /TN "NIFTY_Wednesday" /F
schtasks /Delete /TN "NIFTY_Thursday"  /F
schtasks /Delete /TN "NIFTY_Friday"    /F
```

## Output Structure

```
screenshots/
  2026-08-25/
    09-15-00.png  ...  09-24-00.png
data/
  2026-08-25/
    options.csv     ← one row per CE/PE per strike per timestamp
    options.json    ← full parsed response per screenshot
```

## CSV Columns

`symbol, timestamp, spot_price, strike, expiry, type, delta, gamma, theta, vega, rho, iv, volume, ltp`

## Notes

- Browser opens **once** per session and stays open for all 10 screenshots (faster, avoids repeated logins).
- Only values **visible in the screenshot** are extracted — nulls are used for anything not shown.
- Groq model: `meta-llama/llama-4-scout-17b-16e-instruct` (vision capable).
- Git push runs automatically after all 10 captures complete.
