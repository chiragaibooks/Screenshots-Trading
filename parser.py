"""
parser.py — Parse the TradingView NIFTY options-chain HTML saved by scraper.py.

Table structure (one <tr> per strike row):
  td[0]  CE delta
  td[1]  CE BE (breakeven)
  td[2]  CE IV  (e.g. "11.53%")
  td[3]  CE Theor
  td[4]  CE Bid×Ask  (fused text, split on × / Î character)
  td[5]  CE Distance from spot
  td[6]  CE Volume
  td[7]  Strike  (the number appears twice inside the cell, take first occurrence)
  td[8]  PE Volume
  td[9]  PE Distance from spot
  td[10] PE Bid×Ask
  td[11] PE Theor
  td[12] PE IV
  td[13] PE BE
  td[14] PE Delta  (may be absent if row has only 14 tds)
"""

import re
from bs4 import BeautifulSoup


# ── helpers ────────────────────────────────────────────────────────────────────

def _num(text: str):
    """Convert a display number string to float, or None if not parseable."""
    if not text:
        return None
    # Remove thousand separators, strip whitespace, replace unicode minus
    cleaned = (text.replace(",", "")
                   .replace("\u2212", "-")   # unicode minus sign
                   .replace("\u2013", "-")   # en-dash
                   .strip())
    # Strip trailing % if present
    cleaned = cleaned.rstrip("%").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _split_bid_ask(text: str):
    """
    Split a fused bid×ask cell like '253.60×256.00' or '253.60Î256.00'.
    Returns (bid, ask) as floats or (None, None).
    """
    # The separator is × (U+00D7) or its cp1252 encoding Î
    parts = re.split(r'[×\xd7Î]', text)
    if len(parts) == 2:
        return _num(parts[0]), _num(parts[1])
    return None, None


def _clean_strike(text: str):
    """
    The strike cell contains the number twice (one for each side).
    e.g. '23,80023,800'  → 23800
    """
    cleaned = text.replace(",", "").strip()
    half = len(cleaned) // 2
    # Both halves should be identical; take the first
    first = cleaned[:half]
    try:
        return int(first)
    except ValueError:
        return _num(cleaned)


# ── main parse function ────────────────────────────────────────────────────────

def parse_html(html_path: str, timestamp: str) -> dict:
    """
    Parse the saved options-chain HTML and return a structured dict.

    Returns:
    {
        "symbol":     "NIFTY",
        "timestamp":  "HH:MM:SS",
        "expiry":     "September 8",
        "html_file":  "<path>",
        "options": [
            {
                "strike": 23800,
                "expiry": "September 8",
                "ce": {"delta": 0.75, "be": 24113.25, "iv": 11.53,
                       "theor": 313.25, "bid": 253.60, "ask": 256.00,
                       "distance": 255.80, "volume": 2610010},
                "pe": {"delta": -0.25, "be": 23742.55, "iv": 11.53,
                       "theor": 57.45, "bid": 57.05, "ask": 57.90,
                       "distance": 255.80, "volume": 21864245}
            },
            ...
        ]
    }
    """
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    result = {
        "symbol":    "NIFTY",
        "timestamp": timestamp,
        "expiry":    None,
        "html_file": html_path,
        "options":   [],
    }

    table = soup.find("table", class_=re.compile(r"table-"))
    if not table:
        result["parse_error"] = "option chain table not found"
        return result

    current_expiry = None

    for row in table.find_all("tr"):
        tds = row.find_all("td")

        # ── expiry label row (single cell, no option data) ─────────────────
        if len(tds) == 1:
            text = tds[0].get_text(separator=" ", strip=True)
            # Match only proper month-name dates: "September 8", "October 2" etc.
            # Reject anything like "NIFTY 23 Sep..." which is a contract label
            m = re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\b', text)
            if m:
                current_expiry = f"{m.group(1)} {m.group(2)}"
                if result["expiry"] is None:
                    result["expiry"] = current_expiry
            continue

        # ── data row (14 or 15 tds) ─────────────────────────────────────────
        if len(tds) < 14:
            continue

        ce_bid, ce_ask = _split_bid_ask(tds[4].get_text(strip=True))
        pe_bid, pe_ask = _split_bid_ask(tds[10].get_text(strip=True))

        strike_raw = tds[7].get_text(strip=True)
        strike     = _clean_strike(strike_raw)

        pe_delta_raw = tds[14].get_text(strip=True) if len(tds) > 14 else ""

        option = {
            "strike": strike,
            "expiry": current_expiry,
            "ce": {
                "delta":    _num(tds[0].get_text(strip=True)),
                "be":       _num(tds[1].get_text(strip=True)),
                "iv":       _num(tds[2].get_text(strip=True)),   # strips %
                "theor":    _num(tds[3].get_text(strip=True)),
                "bid":      ce_bid,
                "ask":      ce_ask,
                "distance": _num(tds[5].get_text(strip=True)),
                "volume":   _num(tds[6].get_text(strip=True)),
            },
            "pe": {
                "delta":    _num(pe_delta_raw),
                "be":       _num(tds[13].get_text(strip=True)),
                "iv":       _num(tds[12].get_text(strip=True)),
                "theor":    _num(tds[11].get_text(strip=True)),
                "bid":      pe_bid,
                "ask":      pe_ask,
                "distance": _num(tds[9].get_text(strip=True)),
                "volume":   _num(tds[8].get_text(strip=True)),
            },
        }
        result["options"].append(option)

    return result
