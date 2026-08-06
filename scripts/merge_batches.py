"""
merge_batches.py

Combines all batch JSON files into a single master.json inventory.

Usage:
    python scripts/merge_batches.py
"""

from pathlib import Path
import json

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = PROJECT_ROOT / "processed"

BATCH_DIR = PROCESSED_DIR / "batches"
MASTER_FILE = PROCESSED_DIR / "master.json"

# ---------------------------------------------------------------------
# Load all batch files
# ---------------------------------------------------------------------

all_cards = []

batch_files = sorted(BATCH_DIR.glob("batch*.json"))

print(f"Found {len(batch_files)} batch file(s).")

for batch_file in batch_files:
    print(f"Reading {batch_file.name}")

    try:
        with open(batch_file, "r", encoding="utf-8") as f:
            cards = json.load(f)
    except json.JSONDecodeError:
        print(f"❌ {batch_file.name} is not valid JSON.")
        continue

    all_cards.extend(cards)

# ---------------------------------------------------------------------
# Check for duplicate Card IDs
# ---------------------------------------------------------------------

seen = set()

for card in all_cards:

    card_id = card["sys_card_id"]

    if card_id in seen:
        raise ValueError(f"Duplicate sys_card_id found: {card_id}")

    seen.add(card_id)

# ---------------------------------------------------------------------
# Sort cards
# ---------------------------------------------------------------------

all_cards.sort(key=lambda c: c["sys_card_id"])

# ---------------------------------------------------------------------
# Write master.json
# ---------------------------------------------------------------------

with open(MASTER_FILE, "w", encoding="utf-8") as f:
    json.dump(all_cards, f, indent=2)

print(f"\nMerged {len(all_cards)} cards.")
print(f"Saved to {MASTER_FILE}")
