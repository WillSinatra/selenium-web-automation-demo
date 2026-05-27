"""
modules/browser.py — Playwright browser session management.

Provides a factory function for creating a browser instance and a
graceful teardown helper.
"""

from __future__ import annotations

import random
import time

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Route,
    sync_playwright,
)

import config
from modules.logger import get_logger

logger = get_logger(__name__)

_STEALTH_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_WEBDRIVER_HIDE_SCRIPT = (
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
)


def _stealth_delay(route: Route) -> None:
    """Intercept document navigations and add a human-like random delay."""
    if route.request.resource_type == "document":
        time.sleep(random.uniform(1.5, 3.0))
    route.continue_()


def get_browser(
    headless: bool = config.HEADLESS_MODE,
) -> tuple[Playwright, Browser, BrowserContext, Page]:
    """Initialize a stealth-configured Chromium browser session.

    Args:
        headless: Run browser without a visible window when ``True``.

    Returns:
        A 4-tuple of ``(playwright, browser, context, page)`` ready for use.
    """
    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-notifications",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ],
    )

    context: BrowserContext = browser.new_context(
        viewport={"width": 1400, "height": 900},
        user_agent=_STEALTH_UA,
        ignore_https_errors=True,
    )
    context.set_default_timeout(config.TIMEOUT)

    # Hide navigator.webdriver for every page spawned from this context
    context.add_init_script(_WEBDRIVER_HIDE_SCRIPT)

    # Add a human-like delay before each top-level document navigation
    context.route("**/*", _stealth_delay)

    page: Page = context.new_page()

    logger.info(f"Browser initialized — headless={headless}, stealth=True")
    return playwright, browser, context, page


def close_browser(playwright: Playwright, browser: Browser) -> None:
    """Gracefully close the browser and stop the Playwright instance.

    Args:
        playwright: Active :class:`Playwright` instance.
        browser:    Active :class:`Browser` instance.
    """
    try:
        browser.close()
        playwright.stop()
        logger.info("Browser closed successfully.")
    except Exception as exc:
        logger.warning(f"Error closing browser: {exc}")
