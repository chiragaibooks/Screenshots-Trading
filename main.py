import os, csv, json, time, subprocess, random
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

from config import MARKET_DAYS, MARKET_START, MARKET_END, TOTAL_SHOTS, INTERVAL_SEC
from scraper import open_browser, capture, close_browser
from parser import parse_html

load_dotenv()

IST       = timezone(timedelta(hours=5, minutes=30))
REPO_PATH = os.environ.get("GITHUB_REPO_PATH", os.path.dirname(os.path.abspath(__file__)))

CSV_HEADERS = [
    "symbol", "timestamp", "expiry", "strike", "type",
    "delta", "be", "iv", "theor", "bid", "ask", "distance", "volume",
]


def ist_now() -> datetime:
    return datetime.now(IST)


def is_market_open(now: datetime) -> bool:
    if now.strftime("%A") not in MARKET_DAYS:
        return False
    t = (now.hour, now.minute)
    return MARKET_START <= t <= MARKET_END


def get_random_session_time() -> tuple[int, int]:
    """Pick a random time between 09:15 and 15:20 IST (leaves 10 min buffer before close)."""
    # Total minutes available: 09:15 to 15:20 = 365 minutes
    start_minutes = 9 * 60 + 15   # 555
    end_minutes   = 15 * 60 + 20  # 920
    rand_minutes  = random.randint(start_minutes, end_minutes)
    return rand_minutes // 60, rand_minutes % 60


def wait_for_market_open():
    """Sleep until market is open (today or next weekday)."""
    while True:
        now = ist_now()
        day = now.strftime("%A")
        if day in MARKET_DAYS:
            t = (now.hour, now.minute)
            if t < MARKET_START:
                target = now.replace(hour=MARKET_START[0], minute=MARKET_START[1],
                                     second=0, microsecond=0)
                secs = (target - now).total_seconds()
                print(f"[INFO] Market opens today at 09:15 IST — waiting {secs:.0f}s ...")
                time.sleep(secs)
                return
            elif t <= MARKET_END:
                return
        print(f"[INFO] Market closed ({day} {now.strftime('%H:%M')} IST). Rechecking in 5 min ...")
        time.sleep(300)


def git_push(date_str: str):
    for cmd in [
        ["git", "-C", REPO_PATH, "add", "."],
        ["git", "-C", REPO_PATH, "commit", "-m", f"Auto: NIFTY options {date_str}"],
        ["git", "-C", REPO_PATH, "push"],
    ]:
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(f"[GIT] {cmd[2]}: {r.stdout.strip() or r.stderr.strip()}")


def flatten_rows(parsed: dict) -> list[dict]:
    rows = []
    for opt in parsed.get("options", []):
        for side in ("ce", "pe"):
            d = opt.get(side) or {}
            rows.append({
                "symbol":    parsed.get("symbol"),
                "timestamp": parsed.get("timestamp"),
                "expiry":    opt.get("expiry") or parsed.get("expiry"),
                "strike":    opt.get("strike"),
                "type":      side.upper(),
                "delta":     d.get("delta"),
                "be":        d.get("be"),
                "iv":        d.get("iv"),
                "theor":     d.get("theor"),
                "bid":       d.get("bid"),
                "ask":       d.get("ask"),
                "distance":  d.get("distance"),
                "volume":    d.get("volume"),
            })
    return rows


def run_session(pw, browser, page, session_dir, csv_path, date_str):
    """
    Run one 10-capture session.
    - session_dir : screenshots/<date>/<HHMM>/   raw HTML + PNG per minute
    - csv_path    : options/<date>/<HHMM>.csv     single CSV for all 10 timestamps
    """
    os.makedirs(session_dir, exist_ok=True)

    all_rows   = []
    all_parsed = []

    for i in range(TOTAL_SHOTS):
        now      = ist_now()
        ts_label = now.strftime("%H:%M:%S")
        # Subfolder inside session for each individual capture
        shot_dir = os.path.join(session_dir, now.strftime("%H%M%S"))

        print(f"  [{ts_label}] Capture {i+1}/{TOTAL_SHOTS} ...")

        files  = capture(page, shot_dir)
        parsed = parse_html(files["html"], ts_label)
        n      = len(parsed.get("options", []))
        print(f"  [{ts_label}] {n} strikes  (expiry: {parsed.get('expiry')})")

        # Save per-capture JSON
        with open(os.path.join(shot_dir, "options.json"), "w", encoding="utf-8") as jf:
            json.dump(parsed, jf, indent=2, ensure_ascii=False)

        all_rows.extend(flatten_rows(parsed))
        all_parsed.append(parsed)

        if i < TOTAL_SHOTS - 1:
            next_t    = now + timedelta(seconds=INTERVAL_SEC)
            wait_secs = (next_t - ist_now()).total_seconds()
            if wait_secs > 0:
                print(f"  [{ts_label}] Waiting {wait_secs:.0f}s ...")
                time.sleep(wait_secs)

    # Write single CSV with all 10 timestamps
    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"  [SAVED] {csv_path}  ({len(all_rows)} rows, {TOTAL_SHOTS} timestamps)")
    return all_parsed


def run():
    print("[INFO] NIFTY Options Collector — one random session per market day")

    while True:
        # Wait until market is open
        wait_for_market_open()

        now = ist_now()

        # Pick a random time for today's session
        h, m = get_random_session_time()

        # If random time is still in the future today, wait for it
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if now < target:
            secs = (target - now).total_seconds()
            print(f"[INFO] Today's random session time: {h:02d}:{m:02d} IST — waiting {secs:.0f}s ({secs/60:.1f} min) ...")
            time.sleep(secs)
        else:
            # Random time already passed today — start immediately
            print(f"[INFO] Random time {h:02d}:{m:02d} already passed, starting now ...")

        now      = ist_now()
        date_str = now.strftime("%Y-%m-%d")
        session_name = now.strftime("%H%M")

        shots_day = os.path.join(REPO_PATH, "screenshots", date_str)
        opts_day  = os.path.join(REPO_PATH, "options",     date_str)
        os.makedirs(shots_day, exist_ok=True)
        os.makedirs(opts_day,  exist_ok=True)

        session_dir = os.path.join(shots_day, session_name)
        csv_path    = os.path.join(opts_day,  f"{session_name}.csv")

        print(f"\n[SESSION {session_name}] Starting 10-capture session for {date_str} ...")
        pw, browser, page = open_browser()
        try:
            run_session(pw, browser, page, session_dir, csv_path, date_str)
        finally:
            close_browser(pw, browser)

        print(f"[INFO] Session done. Pushing to git ...")
        git_push(date_str)

        # Sleep until next market day (wait past today's close + buffer)
        now = ist_now()
        # Sleep until tomorrow 00:01, then the while loop will wait for next market open
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=1, second=0, microsecond=0)
        secs = (tomorrow - now).total_seconds()
        print(f"[INFO] Done for {date_str}. Sleeping until tomorrow ({secs/3600:.1f}h) ...")
        time.sleep(secs)


if __name__ == "__main__":
    run()
