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
    """Launch browser, open TradingView NIFTY page. Returns (playwright, browser, page)."""
    pw      = sync_playwright().start()
    browser = pw.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-IN",
        timezone_id="Asia/Kolkata",
    )
    page = context.new_page()
    page.goto(TRADINGVIEW_URL, wait_until="networkidle", timeout=60000)
    _dismiss_popups(page)
    page.wait_for_timeout(5000)
    page.evaluate("window.scrollTo(0, 600)")
    page.wait_for_timeout(1000)
    return pw, browser, page


def take_screenshot(page: Page, save_dir: str) -> str:
    """Capture one screenshot into save_dir. Returns file path."""
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, datetime.now().strftime("%H-%M-%S") + ".png")
    _dismiss_popups(page)
    page.screenshot(path=filepath, full_page=False)
    return filepath


def close_browser(pw, browser: Browser):
    browser.close()
    pw.stop()
