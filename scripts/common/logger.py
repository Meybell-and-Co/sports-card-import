"""
Scout & Steward

Module:
    logger.py

Purpose:
    Standardized logging for the Scout & Steward pipeline.

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

from common.paths import LOGS_DIR

from common.io import ensure_directory

# ---------------------------------------------------------------------
# Logger Factory
# ---------------------------------------------------------------------

def get_logger(name: str):

    ensure_directory(LOGS_DIR)

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    logfile = LOGS_DIR / f"{name}.log"

    file_handler = logging.FileHandler(
        logfile,
        encoding="utf-8"
    )

    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.addHandler(console_handler)

    return logger
