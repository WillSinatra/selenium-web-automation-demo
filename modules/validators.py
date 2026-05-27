"""
modules/validators.py — Input validation utilities.

All validator functions return a boolean and log descriptive messages
so callers can make informed decisions without inspecting internals.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from modules.logger import get_logger

logger = get_logger(__name__)

# Columnas mínimas requeridas en el CSV de entrada
REQUIRED_CSV_COLUMNS: list[str] = ["url", "text_input", "email_input", "label"]

# Columnas opcionales permitidas (si faltan, no fallan la validación)
OPTIONAL_CSV_COLUMNS: list[str] = [
    "password_input",
    "textarea_input",
    "dropdown_value",
    "checkbox",
]

# Regex simple para validar URLs HTTP/HTTPS
_URL_PATTERN = re.compile(
    r"^https?://"               # scheme
    r"([a-zA-Z0-9.-]+)"         # host
    r"(:\d+)?"                  # optional port
    r"(/[^\s]*)?$",             # optional path
    re.IGNORECASE,
)


def validate_url(url: str) -> bool:
    """Check that *url* is a well-formed HTTP or HTTPS address.

    Args:
        url: String to validate.

    Returns:
        ``True`` if valid, ``False`` otherwise.
    """
    if not url or not _URL_PATTERN.match(url.strip()):
        logger.warning(f"Invalid URL: '{url}'")
        return False
    return True


def validate_csv_schema(df: pd.DataFrame) -> bool:
    """Verify that *df* contains all required columns.

    Args:
        df: DataFrame loaded from the user-supplied CSV.

    Returns:
        ``True`` when all required columns are present.
    """
    normalized_columns = {str(col).strip().lower() for col in df.columns}

    missing = [
        col for col in REQUIRED_CSV_COLUMNS
        if col.strip().lower() not in normalized_columns
    ]
    if missing:
        logger.error(f"CSV is missing required columns: {missing}")
        return False

    missing_optional = [
        col for col in OPTIONAL_CSV_COLUMNS
        if col.strip().lower() not in normalized_columns
    ]
    if missing_optional:
        logger.warning(f"CSV optional columns not found: {missing_optional}")

    logger.info("CSV schema validation passed.")
    return True


def validate_required_fields(data: dict[str, str], required: list[str]) -> bool:
    """Check that all *required* keys exist and are non-empty in *data*.

    Args:
        data:     Dictionary of field name → value.
        required: List of field names that must be present and non-empty.

    Returns:
        ``True`` when every required field has a non-empty value.
    """
    for field in required:
        if not str(data.get(field, "")).strip():
            logger.warning(f"Required field missing or empty: '{field}'")
            return False
    return True


def validate_non_empty_dataset(df: pd.DataFrame) -> bool:
    """Ensure the DataFrame contains at least one data row.

    Args:
        df: DataFrame to check.

    Returns:
        ``True`` when *df* has one or more rows.
    """
    if df.empty:
        logger.error("Dataset is empty — no rows to process.")
        return False
    logger.info(f"Dataset contains {len(df)} row(s).")
    return True


def validate_file_exists(path: Path) -> bool:
    """Confirm that a file exists at *path*.

    Args:
        path: File path to check.

    Returns:
        ``True`` if the file exists.
    """
    if not path.is_file():
        logger.error(f"File not found: {path}")
        return False
    return True
