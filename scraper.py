import os
from datetime import datetime
from playwright.sync_api import sync_playwright, Browser, Page
from config import TRADINGVIEW_URL


def _dismiss_popups(page: Page):
    for sel in ["button[aria-label='Close']", ".js-dialog-close", "[data-name='close-button']"]:
        try:
            page.locator(sel).first.click(timeout=2000)
        except Exception:
            pass


def open_browser() -> tuple:
    """Launch browser and open the TradingView NIFTY options-chain page."""
    pw      = sync_playwright().start()
    browser = pw.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-IN",
        timezone_id="Asia/Kolkata",
    )

    page = context.new_page()

    # Block ALL font file requests — prevents screenshot from hanging
    for pattern in ["**/*.woff", "**/*.woff2", "**/*.ttf", "**/*.otf", "**/*.eot",
                    "**/fonts.googleapis.com/**", "**/fonts.gstatic.com/**"]:
        page.route(pattern, lambda r: r.abort())

    page.goto(TRADINGVIEW_URL, wait_until="domcontentloaded", timeout=60000)
    _dismiss_popups(page)
    page.wait_for_timeout(8000)   # let JS render the option chain table
    return pw, browser, page


def capture(page: Page, save_dir: str) -> dict:
    """
    Capture a snapshot into save_dir.

    Screenshot: scrolls to and captures the full option chain table —
                no page header/nav, just the data.
    HTML:       full rendered page for offline parsing.

    Returns dict with file paths.
    """
    os.makedirs(save_dir, exist_ok=True)
    _dismiss_popups(page)

    img_path  = os.path.join(save_dir, "screenshot.png")
    html_path = os.path.join(save_dir, "page.html")

    # Scroll the option chain table into view and screenshot just that element.
    # This removes all page chrome (header, nav, ads) from the image.
    try:
        # The options chain lives inside a div with class containing "chain-"
        chain = page.locator("div[class*='chain-']").first
        chain.scroll_into_view_if_needed(timeout=5000)
        page.wait_for_timeout(500)
        chain.screenshot(path=img_path, timeout=60000)
    except Exception:
        # Fallback: capture full visible viewport if element not found
        page.locator("body").screenshot(path=img_path, timeout=60000)

    # Full rendered HTML (always save the whole page for parsing)
    html = page.content()
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return {"screenshot": img_path, "html": html_path}


def close_browser(pw, browser: Browser):
    browser.close()
    pw.stop()
