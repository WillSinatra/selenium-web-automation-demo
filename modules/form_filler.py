"""
modules/form_filler.py — Web form detection and auto-filling.

Supports text inputs, textareas, <select> dropdowns, checkboxes,
and radio buttons via CSS-selector-keyed dictionaries.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page

from modules.logger import get_logger
from modules.screenshot_manager import capture_screenshot

logger = get_logger(__name__)


def fill_form(
    page: Page,
    form_data: dict[str, str],
) -> tuple[bool, dict]:
    """Fill a web form using selector → value mappings.

    Takes a screenshot before and after filling so every run is
    visually traceable.

    Args:
        page:      Active Playwright :class:`Page` already loaded at the
                   target URL.
        form_data: Mapping of CSS selector (or field name) to the value
                   that should be entered.

    Returns:
        A 2-tuple ``(success, summary)`` where *success* is ``True`` when
        every field was filled without errors, and *summary* is a dict
        containing ``filled``, ``failed``, ``total``, etc.
    """
    filled: list[str] = []
    failed: list[str] = []

    capture_screenshot(page, "before_fill")

    for selector, value in form_data.items():
        # Omitir campos vacíos para no borrar valores por defecto del formulario
        if not str(value).strip():
            logger.debug(f"Skipping empty field: {selector}")
            continue

        try:
            locator = page.locator(selector).first
            tag_name: str = locator.evaluate("el => el.tagName.toLowerCase()")
            input_type: str = locator.evaluate("el => (el.type || \'\').toLowerCase()")

            if tag_name == "select":
                locator.select_option(str(value))
                logger.info(f"[DROPDOWN]  {selector} = {value}")

            elif input_type == "checkbox":
                should_check = str(value).lower() in ("true", "yes", "1", "on")
                locator.check() if should_check else locator.uncheck()
                logger.info(f"[CHECKBOX]  {selector} = {value}")

            elif input_type == "radio":
                locator.check()
                logger.info(f"[RADIO]     {selector}")

            elif tag_name == "textarea":
                locator.fill(str(value))
                logger.info(f"[TEXTAREA]  {selector} = {str(value)[:40]}…")

            else:
                locator.fill(str(value))
                logger.info(f"[INPUT]     {selector} = {value}")

            filled.append(selector)

        except Exception as exc:
            logger.warning(f"Could not fill '{selector}': {exc}")
            failed.append(selector)

    capture_screenshot(page, "after_fill")

    summary = {
        "filled":        filled,
        "failed":        failed,
        "total":         len(form_data),
        "filled_count":  len(filled),
        "failed_count":  len(failed),
    }
    return len(failed) == 0, summary


# ── Demo form helper ─────────────────────────────────────────────────────────

DEMO_URL = "https://www.selenium.dev/selenium/web/web-form.html"


def build_demo_form_data(row) -> dict[str, str]:
    """Build a CSS-selector → value mapping for the Selenium demo form.

    Maps the CSV columns produced by sample_data/sample_forms.csv to the
    correct input selectors for DEMO_URL.

    Args:
        row: A pandas Series (or any mapping) representing one CSV row.

    Returns:
        Dict of CSS selector → value ready to pass to :func:`fill_form`.
    """
    return {
        "input[name='my-text']":        str(row.get("text_input",     "")),
        "input[name='my-email']":       str(row.get("email_input",    "")),
        "input[name='my-password']":    str(row.get("password_input", "")),
        "textarea[name='my-textarea']": str(row.get("textarea_input", "")),
        "select[name='my-select']":     str(row.get("dropdown_value", "1")),
        "input[name='my-check']":       str(row.get("checkbox",       "false")),
    }


def submit_form(
    page: Page,
    submit_selector: str = "button[type='submit']",
) -> bool:
    """Click the form submit button.

    Args:
        page:             Active Playwright :class:`Page`.
        submit_selector:  CSS selector for the submit control.

    Returns:
        ``True`` if the click succeeded, ``False`` on error.
    """
    try:
        page.locator(submit_selector).first.click()
        logger.info("Form submitted successfully.")
        return True
    except Exception as exc:
        logger.error(f"Form submission failed: {exc}")
        return False
