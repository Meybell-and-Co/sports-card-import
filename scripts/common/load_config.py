"""
Scout & Steward

Module:
    load_config.py

Purpose:
    Loads all configuration files used throughout the Scout & Steward
    pipeline.

Responsibilities:
    - Locate configuration files
    - Load JSON configuration
    - Provide shared project configuration

Author:
    Meybell & Co.

Version:
    1.0.0
"""

from pathlib import Path
from typing import Any
import json

# ---------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = PROJECT_ROOT / "config"

# ---------------------------------------------------------------------
# Configuration Files
# ---------------------------------------------------------------------

CONFIG_FILES = {
    "classifications": "classifications.json",
    "domains": "domains.json",
    "insert_sets": "insert_sets.json",
    "manufacturers": "manufacturers.json",
    "pipeline": "pipeline.json",
    "positions": "positions.json",
}

# ---------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------

def _load(filename: str) -> Any:
    """
    Load a JSON configuration file.

    Args:
        filename:
            Name of the JSON file inside the config directory.

    Returns:
        Parsed JSON.

    Raises:
        FileNotFoundError:
            If the configuration file does not exist.

        RuntimeError:
            If the JSON is invalid.
    """

    filepath = CONFIG_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(
            f"Missing configuration file: {filepath}"
        )

    try:
        with filepath.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Invalid JSON in configuration file: {filepath}"
        ) from error


# ---------------------------------------------------------------------
# Public Functions
# ---------------------------------------------------------------------

def load_all_configs() -> dict[str, Any]:
    """
    Load every configuration file used by Scout & Steward.

    Returns:
        Dictionary containing all project configuration.
    """

    return {
        key: _load(filename)
        for key, filename in CONFIG_FILES.items()
    }


# ---------------------------------------------------------------------
# Shared Configuration
# ---------------------------------------------------------------------

CONFIG = load_all_configs()

# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

__all__ = [
    "CONFIG",
    "CONFIG_DIR",
    "CONFIG_FILES",
    "PROJECT_ROOT",
    "load_all_configs",
]
