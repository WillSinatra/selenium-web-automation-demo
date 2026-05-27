"""
modules/screenshot_manager.py — Screenshot capture and file management.

Screenshots are saved to the configured SCREENSHOTS_DIR with
timestamped filenames in the format: YYYYMMDD_HHMMSS_label.png

Post-processing via Pillow:
  - Professional overlay banner at the bottom (label | URL | timestamp)
  - 3 px border in #2E4057 around the full image
"""

from __future__ import annotations

import random
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import Page

import config
from modules.logger import get_logger

logger = get_logger(__name__)

# ── Visual constants ──────────────────────────────────────────────────────────
_BORDER_COLOR  = (46, 64, 87)   # #2E4057
_BORDER_PX     = 3
_BANNER_HEIGHT = 40
_BANNER_FONT_SIZE = 14

# Candidate system fonts (Windows → Linux fallbacks)
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _build_path(label: str, suffix: str = "") -> Path:
    """Build a unique screenshot file path.

    Args:
        label:  Human-readable label embedded in the filename.
        suffix: Optional extra suffix before the extension.

    Returns:
        Absolute :class:`Path` for the screenshot file.
    """
    config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime(config.DATE_FORMAT)
    safe_label = label.strip().replace(" ", "_").lower()
    filename = f"{timestamp}_{safe_label}{suffix}.png"
    return config.SCREENSHOTS_DIR / filename


def _load_font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    """Return a PIL font at the requested *size*, falling back gracefully."""
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    # Pillow ≥ 10.1 supports load_default(size=…)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _add_overlay(filepath: Path, label: str, url: str) -> None:
    """Post-process a saved PNG: add a bottom banner and a border.

    Args:
        filepath: Path to the raw PNG screenshot (modified in-place).
        label:    Screenshot label shown in the banner.
        url:      Page URL shown in the banner.
    """
    img = Image.open(filepath).convert("RGB")
    w, h = img.size
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Banner ────────────────────────────────────────────────────────────────
    with_banner = Image.new("RGB", (w, h + _BANNER_HEIGHT), _BORDER_COLOR)
    with_banner.paste(img, (0, 0))

    draw = ImageDraw.Draw(with_banner)
    font = _load_font(_BANNER_FONT_SIZE)

    banner_text = f"  {label}  |  {url}  |  {timestamp}"
    text_y = h + (_BANNER_HEIGHT - _BANNER_FONT_SIZE) // 2
    draw.text((10, text_y), banner_text, fill=(255, 255, 255), font=font)

    # ── Border ────────────────────────────────────────────────────────────────
    bw = w + 2 * _BORDER_PX
    bh = h + _BANNER_HEIGHT + 2 * _BORDER_PX
    bordered = Image.new("RGB", (bw, bh), _BORDER_COLOR)
    bordered.paste(with_banner, (_BORDER_PX, _BORDER_PX))

    bordered.save(filepath, "PNG")


def navigate_and_capture(page: Page, url: str, label: str) -> Path:
    """Navigate to *url* with a resilient multi-fallback strategy and capture a screenshot.

    Navigation stages (each in its own try/except — never raises on partial load):
      1. goto with wait_until='commit' (fires on first byte — works on any site)
      2. wait_for_load_state('domcontentloaded', 30 s)
      3. If that fails → wait_for_load_state('load', 15 s)
      4. If that fails → fixed wait_for_timeout(5 000 ms)
      5. Always: settling wait_for_timeout(2 500 ms)
      6. Take screenshot regardless of which stage succeeded.

    Args:
        page:  Active Playwright :class:`Page` (browser already open).
        url:   Target URL to navigate to.
        label: Descriptive label for the filename.

    Returns:
        Absolute :class:`Path` where the final screenshot was saved.
    """
    fallback_used = False

    # Generous timeouts — must be set before any navigation
    page.set_default_timeout(90_000)
    page.set_default_navigation_timeout(90_000)

    # Realistic HTTP headers to reduce bot-detection fingerprinting
    page.set_extra_http_headers({
        "Accept-Language":         "es-AR,es;q=0.9,en;q=0.8,en-US;q=0.7",
        "Accept":                  "text/html,application/xhtml+xml,application/xhtml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding":         "gzip, deflate, br",
        "Connection":              "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })

    # Human-like random delay before navigation
    page.wait_for_timeout(random.randint(800, 2000))

    # ── Step 1: Navigate ('commit' fires on first byte — never hangs) ─────────
    page.goto(url, timeout=90_000, wait_until="commit")

    # ── Step 2: Progressive load-state fallbacks ──────────────────────────────
    try:
        page.wait_for_load_state("domcontentloaded", timeout=30_000)
    except Exception:
        fallback_used = True
        logger.warning(f"domcontentloaded timed out for {url} — trying load fallback")
        try:
            page.wait_for_load_state("load", timeout=15_000)
        except Exception:
            logger.warning(f"load fallback also timed out for {url} — using fixed delay")
            page.wait_for_timeout(5_000)

    # ── Step 3: Fixed settling delay (always) ─────────────────────────────────
    page.wait_for_timeout(2_500)

    # ── Step 4: Capture (always proceeds, regardless of load stage) ───────────
    page.set_viewport_size({"width": 1400, "height": 900})
    filepath = _build_path(label)
    page.screenshot(path=str(filepath), full_page=True)
    logger.info(f"Screenshot saved: {filepath.name}")

    current_url = page.url or url
    _add_overlay(filepath, label, current_url)

    print(f"  \U0001f4f8  Screenshot saved \u2192 {filepath.resolve()}")
    if fallback_used:
        print("  \u26a0  Page may not have fully loaded, screenshot captured anyway.")
    else:
        print("  \u2713  Screenshot captured successfully.")

    return filepath


def capture_screenshot(page: Page, label: str) -> Path:
    """Capture a full-page screenshot with post-processing overlay.

    Waits for the page to fully load, resizes the viewport to 1400×900,
    takes the raw screenshot, then applies the Pillow overlay pipeline.

    Args:
        page:  Active Playwright :class:`Page`.
        label: Descriptive label for the filename.

    Returns:
        :class:`Path` where the final screenshot was saved.
    """
    # Wait for full page load
    try:
        page.wait_for_function(
            "document.readyState === 'complete'",
            timeout=10_000,
        )
    except Exception:
        pass  # proceed even if the check times out

    time.sleep(1.5)

    # Consistent viewport for all captures
    page.set_viewport_size({"width": 1400, "height": 900})

    filepath = _build_path(label)
    page.screenshot(path=str(filepath), full_page=True)
    logger.info(f"Screenshot saved: {filepath.name}")

    # Post-process: banner + border via Pillow
    current_url = page.url or ""
    _add_overlay(filepath, label, current_url)

    print(f"  📸  Screenshot saved → {filepath}")
    return filepath


def capture_element_screenshot(page: Page, selector: str, label: str) -> Path:
    """Capture a screenshot scoped to a specific DOM element.

    Args:
        page:     Active Playwright :class:`Page`.
        selector: CSS selector identifying the target element.
        label:    Descriptive label for the filename.

    Returns:
        :class:`Path` where the screenshot was saved.
    """
    filepath = _build_path(label, suffix="_element")
    element = page.locator(selector).first
    element.screenshot(path=str(filepath))
    logger.info(f"Element screenshot saved: {filepath.name}")
    return filepath
