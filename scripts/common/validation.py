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

from typing import Any


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
        with path.open("r", encoding="utf-8") as file:
            json.load(file)
        return True

    except (OSError, json.JSONDecodeError):
        return False


# ---------------------------------------------------------------------
# Values
# ---------------------------------------------------------------------

def is_blank(value: object) -> bool:
    """
    Returns True for None or empty strings.
    """

    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    return False

def has_key(obj: dict[str, Any], key: str) -> bool:

    """
    Safe dictionary key lookup.
    """

    return key in obj

# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

__all__ = [
    "directory_exists",
    "file_exists",
    "has_key",
    "is_blank",
    "is_valid_json",
]
