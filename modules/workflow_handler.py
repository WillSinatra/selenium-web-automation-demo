"""
modules/workflow_handler.py — End-to-end browser workflow execution.

Orchestrates navigation → form filling → submission → result detection
with retry logic and screenshot capture at every stage.
"""

from __future__ import annotations

from playwright.sync_api import Page

import config
from modules.form_filler import fill_form, submit_form
from modules.logger import get_logger
from modules.screenshot_manager import capture_screenshot

logger = get_logger(__name__)

# Indicadores de éxito/fallo buscados en el contenido de la página
_SUCCESS_INDICATORS = [
    "success", "thank you", "submitted", "confirmed",
    "received", "complete", "gracias", "enviado", "form submitted",
]
_FAILURE_INDICATORS = [
    "error", "invalid", "failed", "required field",
    "please fill", "validation", "alert-danger",
]


def run_workflow(
    page: Page,
    url: str,
    workflow_data: dict[str, str],
) -> tuple[bool, dict]:
    """Execute a complete form-filling workflow on *url*.

    Stages
    ------
    1. Navigate to the target URL (with retry).
    2. Fill form fields from *workflow_data*.
    3. Submit the form.
    4. Detect success / failure in the resulting page.

    Args:
        page:          Fresh Playwright :class:`Page` instance.
        url:           Target URL to automate.
        workflow_data: CSS-selector → value mapping for form fields.

    Returns:
        A 2-tuple ``(success, summary)`` where *summary* contains
        step completion info, screenshots captured, and error messages.
    """
    summary: dict = {
        "url":             url,
        "steps_completed": [],
        "screenshots":     [],
        "errors":          [],
        "success":         False,
        "result_message":  "",
    }

    # ── Step 1 · Navigation ──────────────────────────────────────────────────
    nav_ok = False
    for attempt in range(1, config.MAX_RETRIES + 2):
        try:
            logger.info(f"Navigating to {url}  (attempt {attempt})")
            page.goto(url, timeout=config.TIMEOUT, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=config.TIMEOUT)
            nav_ok = True
            break
        except Exception as exc:
            logger.warning(f"Navigation attempt {attempt} failed: {exc}")
            if attempt > config.MAX_RETRIES:
                summary["errors"].append(f"Navigation failed after {attempt} attempt(s): {exc}")
                return False, summary

    if not nav_ok:
        return False, summary

    shot = capture_screenshot(page, "01_navigation")
    summary["screenshots"].append(str(shot))
    summary["steps_completed"].append("navigation")

    # ── Step 2 · Form filling ────────────────────────────────────────────────
    fill_ok, fill_summary = fill_form(page, workflow_data)
    summary["fill_summary"] = fill_summary
    summary["steps_completed"].append("form_fill")

    if not fill_ok:
        logger.warning(
            f"{fill_summary['failed_count']} field(s) could not be filled."
        )

    shot = capture_screenshot(page, "02_filled_form")
    summary["screenshots"].append(str(shot))

    # ── Step 3 · Submission ──────────────────────────────────────────────────
    if submit_form(page):
        summary["steps_completed"].append("form_submit")
        try:
            page.wait_for_load_state("networkidle", timeout=config.TIMEOUT)
        except Exception:
            pass  # La página puede no emitir networkidle en SPAs

    shot = capture_screenshot(page, "03_after_submit")
    summary["screenshots"].append(str(shot))

    # ── Step 4 · Result detection ────────────────────────────────────────────
    success, message = _detect_result(page)
    summary["result_message"] = message
    summary["success"] = success
    summary["steps_completed"].append("result_detection")

    if success:
        logger.info(f"Workflow SUCCESS — {message}")
    else:
        logger.warning(f"Workflow result uncertain — {message}")

    return success, summary


def _detect_result(page: Page) -> tuple[bool, str]:
    """Scan the current page for success or failure indicators.

    Args:
        page: Active Playwright :class:`Page` after form submission.

    Returns:
        A 2-tuple ``(success, message)`` describing what was found.
    """
    try:
        content = page.content().lower()
        current_url = page.url.lower()

        for indicator in _SUCCESS_INDICATORS:
            if indicator in content or indicator in current_url:
                return True, f"Success indicator found: '{indicator}'"

        for indicator in _FAILURE_INDICATORS:
            if indicator in content:
                return False, f"Failure indicator found: '{indicator}'"

        # Sin indicadores claros → asumimos éxito tentativo
        return True, "No failure indicators detected — assuming success."

    except Exception as exc:
        return False, f"Result detection error: {exc}"
