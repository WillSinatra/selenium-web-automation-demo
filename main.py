#!/usr/bin/env python3
"""
Web Automation Toolkit — CLI entry point.

Commands
--------
screenshot  Capture a full-page screenshot of any URL.
workflow    Run batch form-filling workflows from a CSV file.
validate    Validate a CSV input file before processing.
fill        Fill a form with explicit key:value field pairs.

Quick start
-----------
    python main.py screenshot --url https://example.com --label homepage
    python main.py workflow   --input sample_data/sample_forms.csv
    python main.py validate   --input sample_data/sample_forms.csv
    python main.py fill       --url https://... --field "name:John" --submit
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from colorama import Fore, Style, init
from tqdm import tqdm

import config
from modules.browser import close_browser, get_browser
from modules.form_filler import build_demo_form_data, fill_form, submit_form
from modules.logger import get_logger
from modules.reporter import save_excel_report
from modules.screenshot_manager import capture_screenshot, navigate_and_capture
from modules.validators import (
    validate_csv_schema,
    validate_file_exists,
    validate_non_empty_dataset,
    validate_url,
)
from modules.workflow_handler import run_workflow

init(autoreset=True)
logger = get_logger("main")


# ── UI helpers ───────────────────────────────────────────────────────────────

def _banner() -> None:
    """Print the application ASCII banner."""
    print(
        f"\n{Fore.CYAN}"
        "╔══════════════════════════════════════════════════════╗\n"
        "║       🌐  Web Automation Toolkit  v1.0.0             ║\n"
        "║       Built with Playwright · Python 3.11+           ║\n"
        "╚══════════════════════════════════════════════════════╝"
        f"{Style.RESET_ALL}\n"
    )


def _separator() -> None:
    print(f"{Fore.CYAN}{'─' * 56}{Style.RESET_ALL}")


def _ok(msg: str) -> None:
    print(f"{Fore.GREEN}✓  {msg}{Style.RESET_ALL}")


def _err(msg: str) -> None:
    print(f"{Fore.RED}✗  {msg}{Style.RESET_ALL}")


def _warn(msg: str) -> None:
    print(f"{Fore.YELLOW}⚠  {msg}{Style.RESET_ALL}")


# ── Result persistence ────────────────────────────────────────────────────────

def _save_results(results: list[dict]) -> Path:
    """Persist workflow results to ``output/results.xlsx``.

    Args:
        results: List of result dicts produced during a workflow run.

    Returns:
        :class:`Path` to the saved Excel file.
    """
    return save_excel_report(results)


# ── Results table ────────────────────────────────────────────────────────────

def _print_results_table(results: list[dict]) -> None:
    """Print a colour-coded bordered ASCII summary table to the terminal.

    Columns: #, URL, Status, Success, Time
    Header row: cyan bold
    Success rows: green
    Failure rows: red
    Footer: totals summary
    """
    # Column widths
    W_IDX     =  4
    W_URL     = 48
    W_STATUS  =  9
    W_SUCCESS =  9
    W_TIME    =  8

    CYAN_BOLD = Fore.CYAN + Style.BRIGHT
    RST       = Style.RESET_ALL

    # Total inner width between the two outer pipes
    # Each col contributes: space + width + space  (+  pipe separator between cols)
    INNER = W_IDX + W_URL + W_STATUS + W_SUCCESS + W_TIME + 4 * 3 + 4  # 5 cols × 2 spaces + 4 cross pipes

    def _sep(corner: str = "+", cross: str = "+", h: str = "-") -> str:
        parts = [
            h * (W_IDX + 2),
            h * (W_URL + 2),
            h * (W_STATUS + 2),
            h * (W_SUCCESS + 2),
            h * (W_TIME + 2),
        ]
        return corner + cross.join(parts) + corner

    def _row(idx: str, url: str, status: str, success: str, time_s: str) -> str:
        return (
            f"| {idx:<{W_IDX}} "
            f"| {url:<{W_URL}} "
            f"| {status:<{W_STATUS}} "
            f"| {success:<{W_SUCCESS}} "
            f"| {time_s:<{W_TIME}} |"
        )

    sep = _sep()
    print(f"\n{CYAN_BOLD}{sep}{RST}")
    print(f"{CYAN_BOLD}{_row('#', 'URL', 'Status', 'Success', 'Time')}{RST}")
    print(f"{CYAN_BOLD}{sep}{RST}")

    for i, r in enumerate(results, start=1):
        url       = str(r.get("url", ""))[:W_URL]
        status    = str(r.get("status", ""))[:W_STATUS]
        is_ok     = bool(r.get("success"))
        success_s = "\u2713 Yes" if is_ok else "\u2717 No"
        ts        = str(r.get("timestamp", ""))
        time_s    = ts[11:19] if len(ts) >= 19 else ts[:W_TIME]  # HH:MM:SS
        color     = Fore.GREEN if is_ok else Fore.RED
        print(f"{color}{_row(str(i), url, status, success_s, time_s)}{RST}")

    print(f"{CYAN_BOLD}{sep}{RST}")

    # Footer
    total   = len(results)
    ok      = sum(1 for r in results if r.get("success"))
    fail    = total - ok
    footer  = f"  Total: {total}   \u2713 Success: {ok}   \u2717 Failed: {fail}"
    # The inner content width (everything between outer |s, excluding them)
    inner_w = W_IDX + W_URL + W_STATUS + W_SUCCESS + W_TIME + 4 * 3 + 4
    print(f"{CYAN_BOLD}| {footer:<{inner_w}} |{RST}")
    print(f"{CYAN_BOLD}{sep}{RST}\n")


# ── Command handlers ──────────────────────────────────────────────────────────

def cmd_screenshot(args: argparse.Namespace) -> None:
    """Capture and save a full-page screenshot.

    Args:
        args: Parsed CLI arguments (url, label, no_headless).
    """
    if not validate_url(args.url):
        _err(f"Invalid URL: {args.url}")
        sys.exit(1)

    headless = not args.no_headless
    print(f"{Fore.CYAN}📸  Capturing screenshot…{Style.RESET_ALL}")
    print(f"    URL   : {args.url}")
    print(f"    Label : {args.label}")
    _separator()

    playwright, browser, context, page = get_browser(headless=headless)
    try:
        path = navigate_and_capture(page, args.url, args.label)
        _ok(f"Screenshot saved \u2192 {path.resolve()}")
    except Exception as exc:
        logger.error(f"Screenshot command failed: {exc}")
        _err(f"Screenshot failed: {exc}")
        sys.exit(1)
    finally:
        close_browser(playwright, browser)


def cmd_workflow(args: argparse.Namespace) -> None:
    """Run batch workflows from a CSV file.

    Args:
        args: Parsed CLI arguments (input, url, no_headless).
    """
    input_path = Path(args.input)
    url_override: str | None = args.url
    headless = not args.no_headless

    if not validate_file_exists(input_path):
        _err(f"File not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path, encoding=config.ENCODING)

    if not validate_csv_schema(df) or not validate_non_empty_dataset(df):
        _err("CSV validation failed — see log for details.")
        sys.exit(1)

    # ── Demo URL guard ────────────────────────────────────────────────────────
    _DEMO_URL = "https://www.selenium.dev/selenium/web/web-form.html"
    if url_override:
        _non_demo = url_override.rstrip("/") != _DEMO_URL.rstrip("/")
    else:
        _csv_urls = df["url"].dropna().unique().tolist() if "url" in df.columns else []
        _non_demo = any(u.rstrip("/") != _DEMO_URL.rstrip("/") for u in _csv_urls)

    if _non_demo:
        _warn(
            "Warning: This tool is optimized for "
            "https://www.selenium.dev/selenium/web/web-form.html\n"
            "   Other URLs may not have compatible form fields."
        )
        answer = input("Continue anyway? (y/n): ").strip().lower()
        if answer != "y":
            print("Workflow cancelled. Use the demo URL for best results.")
            sys.exit(0)

    print(f"{Fore.CYAN}⚙️   Running workflows…{Style.RESET_ALL}")
    print(f"    Input  : {input_path}")
    print(f"    Rows   : {len(df)}")
    _separator()

    results: list[dict] = []
    playwright, browser, context, _ = get_browser(headless=headless)

    try:
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing", unit="row"):
            target_url = url_override or str(row.get("url", config.BASE_URL))

            if not validate_url(target_url):
                logger.warning(f"Skipping invalid URL: {target_url}")
                results.append({
                    "timestamp":     datetime.now().isoformat(),
                    "url":           target_url,
                    "status":        "skipped",
                    "success":       False,
                    "error_message": "Invalid URL",
                })
                continue

            # Build form data from CSV columns mapped to demo form selectors
            workflow_data = build_demo_form_data(row)

            page = context.new_page()
            try:
                success, exec_summary = run_workflow(page, target_url, workflow_data)
                results.append({
                    "timestamp":     datetime.now().isoformat(),
                    "url":           target_url,
                    "status":        "success" if success else "warning",
                    "success":       success,
                    "error_message": exec_summary.get("result_message", ""),
                })
                icon = f"{Fore.GREEN}✓" if success else f"{Fore.YELLOW}⚠"
                name = row.get("label", row.get("text_input", "Row"))
                print(f"  {icon} {name} — {target_url[:50]}{Style.RESET_ALL}")

            except Exception as exc:
                logger.error(f"Workflow error: {exc}")
                results.append({
                    "timestamp":     datetime.now().isoformat(),
                    "url":           target_url,
                    "status":        "error",
                    "success":       False,
                    "error_message": str(exc),
                })
            finally:
                page.close()

    finally:
        close_browser(playwright, browser)

    output_path = _save_results(results)
    _separator()
    _print_results_table(results)
    print(f"\n  {Fore.CYAN}📄  Report   → {output_path}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}📁  Screenshots → {config.SCREENSHOTS_DIR}{Style.RESET_ALL}")
    print(f"\n{Fore.GREEN}✓ Workflow complete. Results saved to output/results.xlsx{Style.RESET_ALL}")


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate a CSV input file and report per-check results.

    Args:
        args: Parsed CLI arguments (input).
    """
    input_path = Path(args.input)

    print(f"{Fore.CYAN}🔍  Validating input file…{Style.RESET_ALL}")
    print(f"    File: {input_path}")
    _separator()

    checks: list[tuple[str, bool]] = []

    if not validate_file_exists(input_path):
        _err("File not found.")
        sys.exit(1)
    checks.append(("File exists", True))

    df = pd.read_csv(input_path, encoding=config.ENCODING)

    checks.append(("Schema valid",       validate_csv_schema(df)))
    checks.append(("Non-empty dataset",  validate_non_empty_dataset(df)))

    url_issues = 0
    if "url" in df.columns:
        for url_val in df["url"].dropna():
            if not validate_url(str(url_val)):
                url_issues += 1
    checks.append(("URL format valid", url_issues == 0))

    print(f"\n  {'Check':<32} Result")
    print(f"  {'─' * 44}")
    all_passed = True
    for check_name, passed in checks:
        icon = f"{Fore.GREEN}✓ PASS" if passed else f"{Fore.RED}✗ FAIL"
        print(f"  {check_name:<32} {icon}{Style.RESET_ALL}")
        if not passed:
            all_passed = False

    _separator()
    if all_passed:
        _ok(f"All checks passed — {len(df)} row(s) ready to process.")
    else:
        _err("Some validations failed.  Review the issues above.")
        sys.exit(1)


def cmd_fill(args: argparse.Namespace) -> None:
    """Fill a form using explicit --field selector:value pairs.

    Args:
        args: Parsed CLI arguments (url, field, submit, no_headless).
    """
    if not validate_url(args.url):
        _err(f"Invalid URL: {args.url}")
        sys.exit(1)

    # Parsear pares selector:valor desde --field
    form_data: dict[str, str] = {}
    for field_str in args.field or []:
        if ":" not in field_str:
            _warn(f"Ignoring malformed --field value: '{field_str}' (expected selector:value)")
            continue
        key, _, value = field_str.partition(":")
        form_data[key.strip()] = value.strip()

    if not form_data:
        _err("No valid fields provided.  Use --field 'selector:value'")
        sys.exit(1)

    headless = not args.no_headless
    print(f"{Fore.CYAN}📝  Filling form…{Style.RESET_ALL}")
    print(f"    URL    : {args.url}")
    print(f"    Fields : {len(form_data)}")
    _separator()

    playwright, browser, context, page = get_browser(headless=headless)
    try:
        page.goto(args.url, timeout=config.TIMEOUT, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=config.TIMEOUT)

        success, summary = fill_form(page, form_data)

        if args.submit:
            submit_form(page)
            try:
                page.wait_for_load_state("networkidle", timeout=config.TIMEOUT)
            except Exception:
                pass
            shot = capture_screenshot(page, "after_submit")
            print(f"    Result screenshot → {shot}")

        print(f"\n    Fields filled : {Fore.GREEN}{summary['filled_count']}{Style.RESET_ALL}")
        print(f"    Fields failed : {Fore.RED}{summary['failed_count']}{Style.RESET_ALL}")

        if success:
            _ok("Form filled successfully!")
        else:
            _warn("Form filled with some issues — check screenshots.")

    except Exception as exc:
        logger.error(f"fill command failed: {exc}")
        _err(f"Error: {exc}")
        sys.exit(1)
    finally:
        close_browser(playwright, browser)


# ── Argument parser ───────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="web_automation_toolkit",
        description=(
            "🌐 Web Automation Toolkit — Professional browser automation utility\n"
            "   Powered by Playwright and Python 3.11+"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py screenshot --url https://example.com --label homepage\n"
            "  python main.py workflow   --input sample_data/sample_forms.csv\n"
            "  python main.py validate   --input sample_data/sample_forms.csv\n"
            "  python main.py fill       --url https://example.com --field \'input[name=q]:hello\'\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # ── screenshot ────────────────────────────────────────────────────────────
    p_ss = sub.add_parser("screenshot", help="Capture a full-page screenshot of a URL")
    p_ss.add_argument("--url",         required=True, help="Target URL")
    p_ss.add_argument("--label",       default="capture", help="Label embedded in the filename")
    p_ss.add_argument("--no-headless", action="store_true", help="Show the browser window")

    # ── workflow ──────────────────────────────────────────────────────────────
    p_wf = sub.add_parser("workflow", help="Run batch form workflows from a CSV file")
    p_wf.add_argument("--input",       required=True, help="Path to the input CSV file")
    p_wf.add_argument("--url",         default=None,  help="Override the URL for every row")
    p_wf.add_argument("--no-headless", action="store_true", help="Show the browser window")

    # ── validate ──────────────────────────────────────────────────────────────
    p_va = sub.add_parser("validate", help="Validate a CSV file before processing")
    p_va.add_argument("--input", required=True, help="Path to the input CSV file")

    # ── fill ──────────────────────────────────────────────────────────────────
    p_fi = sub.add_parser("fill", help="Fill a form with explicit field:value pairs")
    p_fi.add_argument("--url",         required=True, help="Target URL")
    p_fi.add_argument(
        "--field",
        action="append",
        metavar="SELECTOR:VALUE",
        help="Field mapping — can be specified multiple times",
    )
    p_fi.add_argument("--submit",      action="store_true", help="Submit the form after filling")
    p_fi.add_argument("--no-headless", action="store_true", help="Show the browser window")

    return parser


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate command handler."""
    _banner()
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    logger.info(f"Command dispatched: {args.command}")

    dispatch = {
        "screenshot": cmd_screenshot,
        "workflow":   cmd_workflow,
        "validate":   cmd_validate,
        "fill":       cmd_fill,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
