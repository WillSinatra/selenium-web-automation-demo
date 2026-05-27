"""
modules/logger.py — Centralized logging with colored console output.

Usage:
    from modules.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Hello!")
"""

import logging
from pathlib import Path

from colorama import Fore, Style, init

import config

# Inicializa colorama para Windows
init(autoreset=True)

# Mapeo de niveles de log a colores de consola
_LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG:    Fore.CYAN,
    logging.INFO:     Fore.GREEN,
    logging.WARNING:  Fore.YELLOW,
    logging.ERROR:    Fore.RED,
    logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
}


class _ColoredFormatter(logging.Formatter):
    """Custom formatter that injects ANSI color codes for console output."""

    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelno, "")
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger instance.

    Creates file handler (logs/app.log) and colored console handler
    on first call.  Subsequent calls return the cached logger.

    Args:
        name: Logger name — typically ``__name__``.

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)

    # Evita agregar handlers duplicados si el logger ya fue configurado
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── File handler ─────────────────────────────────────────────────────────
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(
        config.LOG_DIR / "app.log",
        encoding=config.ENCODING,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # ── Console handler (colored) ─────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        _ColoredFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
