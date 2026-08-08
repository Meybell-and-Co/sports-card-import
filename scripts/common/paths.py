"""
Scout & Steward

Module:
    paths.py

Purpose:
    Defines canonical filesystem paths used throughout the project.

Responsibilities:
    - Locate project directories
    - Eliminate hard-coded paths
    - Provide a single source of truth for filesystem locations

Author:
    Meybell & Co.

Version:
    1.0.0
"""

from pathlib import Path

# ------------------------------------------------------------------
# Project Root
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ------------------------------------------------------------------
# Top-Level Directories
# ------------------------------------------------------------------

CONFIG_DIR = PROJECT_ROOT / "config"

DOCS_DIR = PROJECT_ROOT / "docs"

LOGS_DIR = PROJECT_ROOT / "logs"

PROCESSED_DIR = PROJECT_ROOT / "processed"

PROMPTS_DIR = PROJECT_ROOT / "prompts"

RAW_DIR = PROJECT_ROOT / "raw"

SCHEMA_DIR = PROJECT_ROOT / "schema"

SCRIPTS_DIR = PROJECT_ROOT / "scripts"

TEMPLATES_DIR = PROJECT_ROOT / "templates"

# ------------------------------------------------------------------
# Processed Subdirectories
# ------------------------------------------------------------------

BATCHES_DIR = PROCESSED_DIR / "batches"

DATABASE_DIR = PROCESSED_DIR / "database"

EXPORTS_DIR = PROCESSED_DIR / "exports"

REPORTS_DIR = PROCESSED_DIR / "reports"

# ------------------------------------------------------------------
# Frequently Used Files
# ------------------------------------------------------------------

PRIMARY_INVENTORY_FILE = PROCESSED_DIR / "primary_inventory.json"

PIPELINE_CONFIG = CONFIG_DIR / "pipeline.json"

SCHEMA_FILE = SCHEMA_DIR / "sports-card.schema.json"
