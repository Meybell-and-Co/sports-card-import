"""
Scout & Steward

Module:
    io.py

Purpose:
    Standardized file input/output for the Scout & Steward pipeline.

Responsibilities:
    - Read text files
    - Write text files
    - Read JSON
    - Write JSON
    - Ensure directories exist

Author:
    Meybell & Co.

Version:
    1.0.0
"""

from pathlib import Path
import json


# ---------------------------------------------------------------------
# Directory Helpers
# ---------------------------------------------------------------------

def ensure_directory(path: Path) -> None:
    """
    Create a directory if it does not already exist.
    """
    path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# Text Files
# ---------------------------------------------------------------------

def read_text(path: Path) -> str:
    """
    Read a UTF-8 text file.
    """
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """
    Write UTF-8 text to disk.
    """
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------
# JSON Files
# ---------------------------------------------------------------------

def load_json(path: Path):
    """
    Load JSON from disk.
    """
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data, indent: int = 2) -> None:
    """
    Save JSON to disk.
    """
    ensure_directory(path.parent)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=indent,
            ensure_ascii=False
        )
        f.write("\n")
