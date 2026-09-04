"""
run_once.py — Run one 10-capture session right now, no schedule check.

Output structure:
  screenshots/<date>/<HHMM>/           session folder (named by start time)
      <HHMMSS>/                        one subfolder per capture
          screenshot.png
          page.html
          options.json
  options/<date>/<HHMM>.csv            single CSV with all 10 timestamps
"""
import os, csv, json, sys
from datetime import datetime, timezone, timedelta
from scraper import open_browser, close_browser
from parser import parse_html
from main import flatten_rows, CSV_HEADERS, run_session

sys.stdout.reconfigure(encoding="utf-8")

REPO_PATH = os.path.dirname(os.path.abspath(__file__))
IST       = timezone(timedelta(hours=5, minutes=30))

now          = datetime.now(IST)
date_str     = now.strftime("%Y-%m-%d")
session_name = now.strftime("%H%M")            # e.g. "0940"

session_dir = os.path.join(REPO_PATH, "screenshots", date_str, session_name)
opts_dir    = os.path.join(REPO_PATH, "options",     date_str)
csv_path    = os.path.join(opts_dir, f"{session_name}.csv")

os.makedirs(session_dir, exist_ok=True)
os.makedirs(opts_dir,    exist_ok=True)

print(f"[RUN] One-shot session  {session_name}  ({date_str})")
print(f"[RUN] Screenshots : {session_dir}")
print(f"[RUN] CSV         : {csv_path}")
print()

print("[1/2] Opening browser ...")
pw, browser, page = open_browser()

print("[2/2] Running 10-capture session ...")
print()
all_parsed = run_session(pw, browser, page, session_dir, csv_path, date_str)
close_browser(pw, browser)

# Print summary table
print()
print(f"Session {session_name} — {len(all_parsed)} captures")
for p in all_parsed:
    strikes = p.get("options", [])
    print(f"  {p['timestamp']}  {len(strikes)} strikes  expiry={p.get('expiry')}")

print()
print(f"CSV saved : {csv_path}")
print("[DONE] Complete.")
