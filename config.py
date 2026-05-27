"""
config.py — Global configuration for Web Automation Toolkit.

All paths use pathlib.Path for cross-platform compatibility.
"""
from pathlib import Path

# ── Base directory ────────────────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).parent

# ── Target URLs ───────────────────────────────────────────────────────────────
BASE_URL: str = "https://www.selenium.dev/selenium/web/web-form.html"

# ── Output directories ────────────────────────────────────────────────────────
OUTPUT_DIR: Path = BASE_DIR / "output"
SCREENSHOTS_DIR: Path = BASE_DIR / "screenshots"
LOG_DIR: Path = BASE_DIR / "logs"

# ── Data paths ────────────────────────────────────────────────────────────────
FORM_DATA_PATH: Path = BASE_DIR / "sample_data" / "sample_forms.csv"

# ── Format settings ───────────────────────────────────────────────────────────
DATE_FORMAT: str = "%Y%m%d_%H%M%S"
ENCODING: str = "utf-8"

# ── Browser settings ──────────────────────────────────────────────────────────
TIMEOUT: int = 35000          # Milliseconds
HEADLESS_MODE: bool = True
VIEWPORT_WIDTH: int = 1280
VIEWPORT_HEIGHT: int = 800

# ── Retry settings ────────────────────────────────────────────────────────────
MAX_RETRIES: int = 2
