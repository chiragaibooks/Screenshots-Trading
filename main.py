import os, csv, json, time, subprocess
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

from config import SCHEDULE, TOTAL_SHOTS, INTERVAL_SEC
from scraper import open_browser, take_screenshot, close_browser
from parser import parse_screenshot

load_dotenv()

IST       = timezone(timedelta(hours=5, minutes=30))
REPO_PATH = os.environ.get("GITHUB_REPO_PATH", os.path.dirname(os.path.abspath(__file__)))

CSV_HEADERS = ["symbol", "timestamp", "spot_price", "strike", "expiry", "type",
               "delta", "gamma", "theta", "vega", "rho", "iv", "volume", "ltp"]


def ist_now() -> datetime:
    return datetime.now(IST)


def get_todays_window() -> tuple[int, int] | None:
    day = ist_now().strftime("%A")          # e.g. "Monday"
    return SCHEDULE.get(day)               # (hour, minute) or None


def wait_until(hour: int, minute: int):
    now    = ist_now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now < target:
        secs = (target - now).total_seconds()
        print(f"[INFO] Waiting {secs:.0f}s until {hour:02d}:{minute:02d} IST ...")
        time.sleep(secs)


def git_push(date_str: str):
    for cmd in [
        ["git", "-C", REPO_PATH, "add", "."],
        ["git", "-C", REPO_PATH, "commit", "-m", f"Auto: NIFTY data {date_str}"],
        ["git", "-C", REPO_PATH, "push"],
    ]:
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(f"[GIT] {cmd[2]}: {r.stdout.strip() or r.stderr.strip()}")


def flatten_rows(base: dict, opt: dict) -> list[dict]:
    rows = []
    for side in ("ce", "pe"):
        d = opt.get(side) or {}
        rows.append({
            "symbol":    base.get("symbol"),
            "timestamp": base.get("timestamp"),
            "spot_price":base.get("spot_price"),
            "strike":    opt.get("strike"),
            "expiry":    opt.get("expiry"),
            "type":      side.upper(),
            "delta":     d.get("delta"),
            "gamma":     d.get("gamma"),
            "theta":     d.get("theta"),
            "vega":      d.get("vega"),
            "rho":       d.get("rho"),
            "iv":        d.get("iv"),
            "volume":    d.get("volume"),
            "ltp":       d.get("ltp"),
        })
    return rows


def run():
    window = get_todays_window()
    if window is None:
        print(f"[INFO] No capture scheduled for {ist_now().strftime('%A')}. Exiting.")
        return

    h, m = window
    print(f"[INFO] Today's window: {h:02d}:{m:02d} IST  ({TOTAL_SHOTS} shots, 1/min)")
    wait_until(h, m)

    date_str  = ist_now().strftime("%Y-%m-%d")
    shots_dir = os.path.join(REPO_PATH, "screenshots", date_str)
    data_dir  = os.path.join(REPO_PATH, "data", date_str)
    os.makedirs(shots_dir, exist_ok=True)
    os.makedirs(data_dir,  exist_ok=True)

    csv_path  = os.path.join(data_dir, "options.csv")
    json_path = os.path.join(data_dir, "options.json")

    all_records = []
    csv_file    = open(csv_path, "w", newline="", encoding="utf-8")
    writer      = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS)
    writer.writeheader()

    pw, browser, page = open_browser()
    try:
        for i in range(TOTAL_SHOTS):
            ts_label = ist_now().strftime("%H:%M:%S")
            print(f"[{ts_label}] Shot {i+1}/{TOTAL_SHOTS} ...")

            img_path = take_screenshot(page, shots_dir)
            parsed   = parse_screenshot(img_path, ts_label)
            parsed["screenshot"] = img_path
            all_records.append(parsed)

            for opt in parsed.get("options", []):
                writer.writerows(flatten_rows(parsed, opt))
            csv_file.flush()

            if i < TOTAL_SHOTS - 1:
                print(f"[{ts_label}] Waiting {INTERVAL_SEC}s ...")
                time.sleep(INTERVAL_SEC)
    finally:
        close_browser(pw, browser)
        csv_file.close()

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(all_records, jf, indent=2, ensure_ascii=False)

    print(f"[DONE] CSV  → {csv_path}")
    print(f"[DONE] JSON → {json_path}")
    git_push(date_str)
    print("[DONE] All done.")


if __name__ == "__main__":
    run()
