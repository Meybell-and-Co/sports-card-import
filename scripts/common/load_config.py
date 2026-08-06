"""
load_config.py

Loads all configuration files for the Scout & Steward pipeline.

Every script should import the shared `config` dictionary rather than
opening configuration files directly.

Example:

    from common.load_config import config

    positions = config["positions"]
"""

from pathlib import Path
import json


# ---------------------------------------------------------
# Project Root
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = PROJECT_ROOT / "config"


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------

def _load(filename: str):
    """
    Load a JSON configuration file.
    """

    filepath = CONFIG_DIR / filename

    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------
# Public Configuration Dictionary
# ---------------------------------------------------------

config = {

    "pipeline": _load("pipeline.json"),

    "positions": _load("positions.json"),

    "classifications": _load("classifications.json"),

    "insert_sets": _load("insert_sets.json"),

    "manufacturers": _load("manufacturers.json"),

    "domains": _load("domains.json")

}
