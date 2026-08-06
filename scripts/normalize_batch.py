"""
normalize_batch.py

Converts raw AI extraction batches into the official
Sports Collectible Schema v1.0.

Usage:

python normalize_batch.py batch0001_raw.json batch0001.json

"""

from pathlib import Path
import json
import sys

# ------------------------------
# Constants
# ------------------------------

INSERT_NAMES = {
    "Triple Threat",
    "Buzzer Beater",
    "Milestones",
    "Sizzlin' Sophs",
    "Up Close & Personal",
    "On Deck",
    "You Crash the Deck",
    "Commemorative Issue '94"
}

POSITION_MAP = {
    "QUARTERBACK": "QB",
    "RUNNING BACK": "RB",
    "FULLBACK": "FB",
    "WIDE RECEIVER": "WR",
    "TIGHT END": "TE",
    "CENTER": "C",
    "GUARD": "G",
    "TACKLE": "T",
    "LINEBACKER": "LB",
    "DEFENSIVE END": "DE",
    "DEFENSIVE TACKLE": "DT",
    "SAFETY": "S",
    "CORNERBACK": "CB",

    "POINT GUARD": "PG",
    "SHOOTING GUARD": "SG",
    "SMALL FORWARD": "SF",
    "POWER FORWARD": "PF",
    "CENTER": "C",

    "PITCHER": "P",
    "CATCHER": "C",
    "FIRST BASE": "1B",
    "SECOND BASE": "2B",
    "THIRD BASE": "3B",
    "SHORTSTOP": "SS",
    "LEFT FIELD": "LF",
    "CENTER FIELD": "CF",
    "RIGHT FIELD": "RF"
}

# ------------------------------
# Helper Functions
# ------------------------------

def move(obj, old_key, new_key):
    """Rename dictionary key if present."""
    if old_key in obj:
        obj[new_key] = obj.pop(old_key)


def normalize_card(record):

    # -----------------------------------
    # Rename sections
    # -----------------------------------

    move(record, "descriptive_metadata", "card")
    move(record, "text", "ocr")
    move(record, "provenance", "pipeline")

    # -----------------------------------
    # Remove inventory data
    # -----------------------------------

    record.pop("operations", None)

    # -----------------------------------
    # Notes
    # -----------------------------------

    notes = []

    if "ocr" in record:

        catalog = record["ocr"].pop("catalog_notes", None)

        if catalog:
            notes.append(catalog)

        move(record["ocr"], "ocr_front", "front")
        move(record["ocr"], "ocr_back", "back")

    record["notes"] = notes

    # -----------------------------------
    # Pipeline
    # -----------------------------------

    if "pipeline" in record:

        move(record["pipeline"], "source_batch", "batch")
        move(record["pipeline"], "generated_by", "extractor")

        record["pipeline"].pop("generated_at", None)

    # -----------------------------------
    # Card defaults
    # -----------------------------------

    card = record["card"]

    card.setdefault("language", "English")
    card.setdefault("copyright", None)

    # -----------------------------------
    # Title cleanup
    # -----------------------------------

    classification = record["attributes"]["classification"]

    if classification == "Base":
        card["title"] = None

    # -----------------------------------
    # Better classification
    # -----------------------------------

    subset = card.get("subset")

    if subset in INSERT_NAMES:
        record["attributes"]["classification"] = "Insert"

    if subset and "Checklist" in subset:
        record["attributes"]["classification"] = "Checklist"

    # -----------------------------------
    # Subject Positions
    # -----------------------------------

    ocr_text = ""

    if "ocr" in record:
        ocr_text = (
            (record["ocr"].get("front") or "")
            + " "
            + (record["ocr"].get("back") or "")
        ).upper()

    for subject in record["subjects"]:

        if subject["type"] != "player":
            continue

        if "position" not in subject:
            subject["position"] = None

        for phrase, abbreviation in POSITION_MAP.items():

            if phrase in ocr_text:
                subject["position"] = abbreviation
                break

    return record


# ------------------------------
# Main
# ------------------------------

def main():

    if len(sys.argv) != 3:
        print("Usage:")
        print("python normalize_batch.py input.json output.json")
        return

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    with open(input_file, encoding="utf8") as f:
        data = json.load(f)

    normalized = []

    for record in data:
        normalized.append(normalize_card(record))

    with open(output_file, "w", encoding="utf8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)

    print()
    print(f"Normalized {len(normalized)} records.")
    print(f"Wrote {output_file}")


if __name__ == "__main__":
    main()
