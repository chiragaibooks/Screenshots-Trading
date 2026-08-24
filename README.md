# NIFTY TradingView Option Chain Automation

Captures TradingView NIFTY screenshots every minute for a 10-minute window on each weekday, extracts option Greeks via Groq vision, saves structured data, and auto-pushes to GitHub.

## Output Structure

```
screenshots/
  2026-08-25/
    09-15-00.png  ...  09-24-00.png
data/
  2026-08-25/
    options.csv
    options.json
```

## CSV Columns

`symbol, timestamp, spot_price, strike, expiry, type, delta, gamma, theta, vega, rho, iv, volume, ltp`
