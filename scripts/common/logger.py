"""
Scout & Steward

Module:
    logger.py

Purpose:
    Provides standardized logging for the Scout & Steward pipeline.

Responsibilities:
    - Create named loggers
    - Write timestamped log files
    - Print clean console messages

Author:
    Meybell & Co.

Version:
    1.0.0
"""

import logging

from .io import ensure_directory
from .paths import LOGS_DIR


# ---------------------------------------------------------------------
# Logger Factory
# ---------------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """
    Create or return a configured project logger.

    Each logger writes to both the console and a log file located in the
    project's logs directory. Repeated calls with the same name return the
    existing configured logger.

    Args:
        name:
            Name of the logger and corresponding log file.

    Returns:
        Configured logger instance.
    """

    ensure_directory(LOGS_DIR)

    logger = logging.getLogger(name)

    # Prevent duplicate handlers if this logger already exists.
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logfile = LOGS_DIR / f"{name}.log"

    file_handler = logging.FileHandler(
        logfile,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

__all__ = [
    "get_logger",
]
