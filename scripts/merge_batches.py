"""
merge_batches.py

Combines all normalized batch JSON files into the canonical
primary inventory.

Business rules:
    - Every batch must contain valid JSON.
    - Every batch must pass schema validation.
    - Every item_id must be unique across all batches.
    - The primary inventory is replaced only after the entire merge succeeds.
    - Existing batch files remain the source records.

Usage:
    python scripts/merge_batches.py
"""

from collections import Counter
from pathlib import Path
import json
import os
import tempfile

from jsonschema import Draft202012Validator


# ---------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "processed"
BATCH_DIR = PROCESSED_DIR / "batches"

PRIMARY_INVENTORY_FILE = PROCESSED_DIR / "primary_inventory.json"

SCHEMA_CANDIDATES = [
    PROJECT_ROOT / "config" / "sports-card.schema.json",
    PROJECT_ROOT / "schema" / "sports-card.schema.json",
    PROJECT_ROOT / "schemas" / "sports-card.schema.json",
    PROJECT_ROOT / "sports-card.schema.json",
]


# ---------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------

def find_schema_file() -> Path:
    """
    Locate the canonical sports-card schema.

    Returns:
        Path to the first matching schema file.

    Raises:
        FileNotFoundError:
            If the schema cannot be found.
    """

    for schema_path in SCHEMA_CANDIDATES:
        if schema_path.exists():
            return schema_path

    searched_locations = "\n".join(
        f"    - {path}" for path in SCHEMA_CANDIDATES
    )

    raise FileNotFoundError(
        "Could not find sports-card.schema.json.\n"
        "Searched:\n"
        f"{searched_locations}"
    )


def load_json(filepath: Path):
    """
    Load and parse a JSON file.

    Args:
        filepath:
            JSON file to load.

    Returns:
        Parsed JSON data.

    Raises:
        RuntimeError:
            If the file cannot be read or contains invalid JSON.
    """

    try:
        with filepath.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"{filepath.name} contains invalid JSON.\n"
            f"Line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error

    except OSError as error:
        raise RuntimeError(
            f"Could not read {filepath}: {error}"
        ) from error


def format_validation_path(error) -> str:
    """
    Convert a jsonschema error path into a readable location.
    """

    if not error.absolute_path:
        return "<root>"

    return ".".join(str(part) for part in error.absolute_path)


def validate_batch(
    cards: list,
    schema: dict,
    batch_file: Path,
) -> None:
    """
    Validate one batch against the canonical schema.

    Supports either:
        - a schema whose root represents an array of cards, or
        - a schema whose root represents one card object.

    Args:
        cards:
            Card records loaded from the batch.
        schema:
            Canonical JSON schema.
        batch_file:
            Batch file being validated.

    Raises:
        ValueError:
            If the batch structure or card data is invalid.
    """

    if not isinstance(cards, list):
        raise ValueError(
            f"{batch_file.name} must contain a JSON array."
        )

    if schema.get("type") == "array":
        validator = Draft202012Validator(schema)
        errors = sorted(
            validator.iter_errors(cards),
            key=lambda error: list(error.absolute_path),
        )

    else:
        validator = Draft202012Validator(schema)
        errors = []

        for index, card in enumerate(cards):
            for error in validator.iter_errors(card):
                error.absolute_path.appendleft(index)
                errors.append(error)

        errors.sort(key=lambda error: list(error.absolute_path))

    if not errors:
        return

    error_lines = []

    for error in errors:
        location = format_validation_path(error)

        error_lines.append(
            f"    - {location}: {error.message}"
        )

    error_report = "\n".join(error_lines)

    raise ValueError(
        f"{batch_file.name} failed schema validation:\n"
        f"{error_report}"
    )


def find_duplicate_card_ids(cards: list) -> list[str]:
    """
    Find duplicate item_id values.

    Args:
        cards:
            Combined card records.

    Returns:
        Sorted list of duplicated card IDs.
    """

    card_ids = [
        card.get("item_id")
        for card in cards
        if card.get("item_id") is not None
    ]

    counts = Counter(card_ids)

    return sorted(
        card_id
        for card_id, count in counts.items()
        if count > 1
    )


def write_json_atomically(filepath: Path, data: list) -> None:
    """
    Write JSON without risking a partially written inventory file.

    The completed temporary file replaces the destination only after
    serialization succeeds.
    """

    filepath.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=filepath.parent,
            prefix=f".{filepath.stem}_",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

            json.dump(
                data,
                temporary_file,
                indent=2,
                ensure_ascii=False,
            )

            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        temporary_path.replace(filepath)

    except Exception:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()

        raise


# ---------------------------------------------------------------------
# Merge Process
# ---------------------------------------------------------------------

def main() -> None:
    """
    Build primary_inventory.json from all normalized batch files.
    """

    print("\nScout & Steward — Primary Inventory Merge")
    print("-----------------------------------------")

    schema_file = find_schema_file()
    schema = load_json(schema_file)

    batch_files = sorted(
    path
    for path in BATCH_DIR.glob("batch*.json")
    if not path.stem.endswith(("_raw", "_legacy", "_migrated"))
)

    if not batch_files:
        raise FileNotFoundError(
            f"No batch files were found in:\n{BATCH_DIR}"
        )

    print(f"Schema: {schema_file.name}")
    print(f"Found:  {len(batch_files)} batch file(s)\n")

    all_cards = []

    for batch_file in batch_files:
        print(f"Reading and validating {batch_file.name}...")

        cards = load_json(batch_file)
        validate_batch(cards, schema, batch_file)

        all_cards.extend(cards)

        print(f"    ✓ {len(cards)} card(s)")

    duplicate_ids = find_duplicate_card_ids(all_cards)

    if duplicate_ids:
        duplicate_report = "\n".join(
            f"    - {card_id}" for card_id in duplicate_ids
        )

        raise ValueError(
            "Duplicate item_id values were found:\n"
            f"{duplicate_report}\n\n"
            "The primary inventory was not changed."
        )

    all_cards.sort(
        key=lambda card: card["item_id"]
    )

    # Validate the complete inventory before writing it.
    validate_batch(
        all_cards,
        schema,
        Path("combined primary inventory"),
    )

    write_json_atomically(
        PRIMARY_INVENTORY_FILE,
        all_cards,
    )

    print("\n-----------------------------------------")
    print("✓ Merge successful")
    print(f"Batch files: {len(batch_files)}")
    print(f"Total cards: {len(all_cards)}")
    print(f"Saved to:   {PRIMARY_INVENTORY_FILE}")


# ---------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print("\n-----------------------------------------")
        print("❌ MERGE FAILED")
        print(error)
        print("\nprimary_inventory.json was not changed.")
        raise SystemExit(1)
