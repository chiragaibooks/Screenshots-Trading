# ─────────────────────────────────────────────────────────────
#  CAPTURE SCHEDULE  — edit these times to change the window
#  Format: (hour, minute)  in IST  24-hour clock
#  Each window runs for exactly 10 minutes (10 screenshots, 1/min)
# ─────────────────────────────────────────────────────────────
SCHEDULE = {
    "Monday":    (9,  15),   # 09:15 – 09:25
    "Tuesday":   (11,  0),   # 11:00 – 11:10
    "Wednesday": (14,  5),   # 14:05 – 14:15
    "Thursday":  (10, 30),   # 10:30 – 10:40
    "Friday":    (13, 20),   # 13:20 – 13:30
}

# ─────────────────────────────────────────────────────────────
#  OTHER SETTINGS  — rarely need changing
# ─────────────────────────────────────────────────────────────
TOTAL_SHOTS  = 10     # screenshots per session
INTERVAL_SEC = 60     # seconds between screenshots
TRADINGVIEW_URL = "https://in.tradingview.com/symbols/NSE-NIFTY/"
