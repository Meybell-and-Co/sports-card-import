"""
Scout & Steward

Module:
    validation.py

Purpose:
    Shared validation helpers for the Scout & Steward pipeline.

Responsibilities:
    - Validate files
    - Validate JSON
    - Validate simple values

Author:
    Meybell & Co.

Version:
    1.0.0
"""

from pathlib import Path
import json


# ---------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------

def file_exists(path: Path) -> bool:
    """
    Return True if the file exists.
    """
    return path.is_file()


def directory_exists(path: Path) -> bool:
    """
    Return True if the directory exists.
    """
    return path.is_dir()


# ---------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------

def is_valid_json(path: Path) -> bool:
    """
    Return True if the file contains valid JSON.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            json.load(f)
        return True

    except Exception:
        return False


# ---------------------------------------------------------------------
# Values
# ---------------------------------------------------------------------

def is_blank(value) -> bool:
    """
    Returns True for None or empty strings.
    """

    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    return False


def has_key(obj: dict, key: str) -> bool:
    """
    Safe dictionary key lookup.
    """

    return key in obj
