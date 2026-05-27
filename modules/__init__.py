"""
modules — Web Automation Toolkit core package.

Public re-exports for convenience:
    from modules import get_logger, get_browser, capture_screenshot
"""
from modules.logger import get_logger
from modules.browser import get_browser, close_browser
from modules.screenshot_manager import capture_screenshot, capture_element_screenshot
from modules.validators import (
    validate_url,
    validate_csv_schema,
    validate_required_fields,
    validate_non_empty_dataset,
    validate_file_exists,
)

__all__ = [
    "get_logger",
    "get_browser",
    "close_browser",
    "capture_screenshot",
    "capture_element_screenshot",
    "validate_url",
    "validate_csv_schema",
    "validate_required_fields",
    "validate_non_empty_dataset",
    "validate_file_exists",
]
