"""
Scout & Steward

Module:
    io.py

Purpose:
    Provides standardized file input and output operations for the
    Scout & Steward pipeline.

Responsibilities:
    - Read text files
    - Write text files
    - Read JSON files
    - Write JSON files
    - Ensure directories exist

Author:
    Meybell & Co.

Version:
    1.0.0
"""

import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------
# Directory Helpers
# ---------------------------------------------------------------------

def ensure_directory(path: Path) -> None:
    """
    Create a directory if it does not already exist.

    Args:
        path:
            Directory to create.
    """

    path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# Text Files
# ---------------------------------------------------------------------

def read_text(path: Path) -> str:
    """
    Read and return the contents of a UTF-8 text file.

    Args:
        path:
            File to read.

    Returns:
        File contents as text.
    """

    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """
    Write text to a UTF-8 file.

    Creates the parent directory when necessary.

    Args:
        path:
            Destination file.

        content:
            Text to write.
    """

    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------
# JSON Files
# ---------------------------------------------------------------------

def load_json(path: Path) -> Any:
    """
    Load and return JSON data from a file.

    Args:
        path:
            JSON file to read.

    Returns:
        Parsed JSON data.
    """

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(
    path: Path,
    data: Any,
    indent: int = 2,
) -> None:
    """
    Write JSON data to a file.

    Creates the parent directory when necessary.

    Args:
        path:
            Destination JSON file.

        data:
            JSON-serializable data to write.

        indent:
            Number of spaces used for indentation.
    """

    ensure_directory(path.parent)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=indent,
            ensure_ascii=False,
        )
        file.write("\n")


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

__all__ = [
    "ensure_directory",
    "load_json",
    "read_text",
    "save_json",
    "write_text",
]
