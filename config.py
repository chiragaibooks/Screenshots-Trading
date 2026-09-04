# ─────────────────────────────────────────────────────────────
#  CAPTURE SCHEDULE
#  Mon-Fri, 09:15 to 15:30 IST
#  Each session = 10 consecutive captures, 1 per minute (10 min window)
# ─────────────────────────────────────────────────────────────

MARKET_DAYS   = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}

MARKET_START  = (9,  15)   # 09:15 IST
MARKET_END    = (15, 30)   # 15:30 IST

TOTAL_SHOTS   = 10         # captures per session
INTERVAL_SEC  = 60         # seconds between captures

TRADINGVIEW_URL = "https://in.tradingview.com/symbols/NSE-NIFTY/options-chain/"
