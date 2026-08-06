"""
Scout & Steward

Module:
    normalize_batch.py

Purpose:
    Converts raw AI extraction batches into the official
    Sports Collectible Schema.

Responsibilities:
    - Normalize record structure
    - Apply card defaults
    - Normalize card classifications
    - Infer single-player positions from OCR
    - Write normalized batch data

Usage:
    python normalize_batch.py input.json output.json

Author:
    Meybell & Co.

Version:
    1.0.0
"""

import argparse
import re
from pathlib import Path
from typing import Any, MutableMapping, cast

from common.app import App
from common.io import load_json, save_json
from common.validation import is_blank


# ---------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------

JsonObject = dict[str, Any]
InsertSetConfig = dict[str, dict[str, str]]
PositionConfig = dict[str, dict[str, str]]


# ---------------------------------------------------------------------
# Command-Line Arguments
# ---------------------------------------------------------------------

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Normalize a raw Scout & Steward extraction batch."
        )
    )

    parser.add_argument(
        "input_file",
        type=Path,
        help="Raw extraction batch JSON file.",
    )

    parser.add_argument(
        "output_file",
        type=Path,
        help="Destination for the normalized batch JSON file.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------
# Dictionary Helpers
# ---------------------------------------------------------------------

def move_key(
    obj: MutableMapping[str, Any],
    old_key: str,
    new_key: str,
) -> None:
    """
    Rename a dictionary key when the original key is present.

    Args:
        obj:
            Dictionary containing the key.

        old_key:
            Existing key name.

        new_key:
            Replacement key name.
    """

    if old_key in obj:
        obj[new_key] = obj.pop(old_key)


def require_object(
    record: JsonObject,
    key: str,
) -> JsonObject:
    """
    Return a required dictionary section from a record.

    Args:
        record:
            Record containing the section.

        key:
            Required section name.

    Returns:
        Requested dictionary section.

    Raises:
        ValueError:
            If the section is missing or is not a dictionary.
    """

    value = record.get(key)

    if not isinstance(value, dict):
        raise ValueError(
            f"Record requires an object named '{key}'."
        )

    return value


def require_list(
    record: JsonObject,
    key: str,
) -> list[Any]:
    """
    Return a required list section from a record.

    Args:
        record:
            Record containing the section.

        key:
            Required section name.

    Returns:
        Requested list section.

    Raises:
        ValueError:
            If the section is missing or is not a list.
    """

    value = record.get(key)

    if not isinstance(value, list):
        raise ValueError(
            f"Record requires a list named '{key}'."
        )

    return value


# ---------------------------------------------------------------------
# Structural Normalization
# ---------------------------------------------------------------------

def normalize_structure(record: JsonObject) -> None:
    """
    Normalize the top-level structure of a card record.

    Args:
        record:
            Card record to normalize.
    """

    move_key(
        record,
        "descriptive_metadata",
        "card",
    )
    move_key(
        record,
        "text",
        "ocr",
    )
    move_key(
        record,
        "provenance",
        "pipeline",
    )

    record.pop("operations", None)

    normalize_ocr(record)
    normalize_pipeline(record)


def normalize_ocr(record: JsonObject) -> None:
    """
    Normalize OCR fields and extract catalog notes.

    Args:
        record:
            Card record to normalize.
    """

    notes: list[str] = []

    ocr = record.get("ocr")

    if isinstance(ocr, dict):
        catalog_notes = ocr.pop(
            "catalog_notes",
            None,
        )

        if isinstance(catalog_notes, str):
            if not is_blank(catalog_notes):
                notes.append(catalog_notes.strip())

        move_key(
            ocr,
            "ocr_front",
            "front",
        )
        move_key(
            ocr,
            "ocr_back",
            "back",
        )

    record["notes"] = notes


def normalize_pipeline(record: JsonObject) -> None:
    """
    Normalize pipeline provenance fields.

    Args:
        record:
            Card record to normalize.
    """

    pipeline = record.get("pipeline")

    if not isinstance(pipeline, dict):
        return

    move_key(
        pipeline,
        "source_batch",
        "batch",
    )
    move_key(
        pipeline,
        "generated_by",
        "extractor",
    )

    pipeline.pop("generated_at", None)


# ---------------------------------------------------------------------
# Card Normalization
# ---------------------------------------------------------------------

def normalize_card_defaults(record: JsonObject) -> None:
    """
    Apply required defaults and basic card cleanup.

    Args:
        record:
            Card record to normalize.
    """

    card = require_object(record, "card")
    attributes = require_object(
        record,
        "attributes",
    )

    card.setdefault(
        "language",
        "English",
    )
    card.setdefault(
        "copyright",
        None,
    )

    if attributes.get("classification") == "Base":
        card["title"] = None


def normalize_classification(
    record: JsonObject,
    insert_sets: InsertSetConfig,
) -> None:
    """
    Normalize classification using the insert-set configuration.

    Args:
        record:
            Card record to normalize.

        insert_sets:
            Known subset names and their classifications.
    """

    card = require_object(record, "card")
    attributes = require_object(
        record,
        "attributes",
    )

    subset = card.get("subset")

    if not isinstance(subset, str):
        return

    normalized_subset = subset.strip().casefold()

    for subset_name, subset_config in insert_sets.items():
        if subset_name.casefold() != normalized_subset:
            continue

        classification = subset_config.get(
            "classification"
        )

        if classification:
            attributes["classification"] = classification

        return


# ---------------------------------------------------------------------
# Position Normalization
# ---------------------------------------------------------------------

def get_ocr_text(record: JsonObject) -> str:
    """
    Combine front and back OCR into searchable text.

    Args:
        record:
            Card record containing OCR data.

    Returns:
        Combined OCR text.
    """

    ocr = record.get("ocr")

    if not isinstance(ocr, dict):
        return ""

    front = ocr.get("front")
    back = ocr.get("back")

    front_text = front if isinstance(front, str) else ""
    back_text = back if isinstance(back, str) else ""

    return f"{front_text} {back_text}".strip()


def get_sport_positions(
    sport: str,
    positions: PositionConfig,
) -> dict[str, str]:
    """
    Return the configured position map for a sport.

    Sport matching is case-insensitive.

    Args:
        sport:
            Sport name from the card record.

        positions:
            Position mappings grouped by sport.

    Returns:
        Matching position map, or an empty dictionary.
    """

    normalized_sport = sport.strip().casefold()

    for sport_name, position_map in positions.items():
        if sport_name.casefold() == normalized_sport:
            return position_map

    return {}


def infer_position(
    ocr_text: str,
    position_map: dict[str, str],
) -> str | None:
    """
    Infer one position abbreviation from OCR text.

    Longer phrases are checked first so specific terms such as
    'Shooting Guard' are matched before broader terms such as 'Guard'.

    Args:
        ocr_text:
            Combined OCR text.

        position_map:
            Full position names mapped to abbreviations.

    Returns:
        Position abbreviation when found; otherwise None.
    """

    phrases = sorted(
        position_map,
        key=len,
        reverse=True,
    )

    for phrase in phrases:
        pattern = rf"\b{re.escape(phrase)}\b"

        if re.search(
            pattern,
            ocr_text,
            flags=re.IGNORECASE,
        ):
            return position_map[phrase]

    return None


def normalize_positions(
    record: JsonObject,
    positions: PositionConfig,
) -> None:
    """
    Infer a player position when the card has one player subject.

    Existing positions are preserved. Position inference is skipped for
    multiplayer cards because OCR text cannot reliably associate each
    position with the correct player.

    Args:
        record:
            Card record to normalize.

        positions:
            Position mappings grouped by sport.
    """

    attributes = require_object(
        record,
        "attributes",
    )
    subjects = require_list(
        record,
        "subjects",
    )

    player_subjects = [
        subject
        for subject in subjects
        if isinstance(subject, dict)
        and subject.get("type") == "player"
    ]

    for subject in player_subjects:
        subject.setdefault("position", None)

    if len(player_subjects) != 1:
        return

    player = player_subjects[0]

    if not is_blank(player.get("position")):
        return

    sport = attributes.get("sport")

    if not isinstance(sport, str):
        return

    position_map = get_sport_positions(
        sport,
        positions,
    )

    if not position_map:
        return

    inferred_position = infer_position(
        get_ocr_text(record),
        position_map,
    )

    if inferred_position is not None:
        player["position"] = inferred_position


# ---------------------------------------------------------------------
# Record Normalization
# ---------------------------------------------------------------------

def normalize_card(
    record: JsonObject,
    insert_sets: InsertSetConfig,
    positions: PositionConfig,
) -> JsonObject:
    """
    Normalize one card record.

    Args:
        record:
            Raw card record.

        insert_sets:
            Known subset classifications.

        positions:
            Position mappings grouped by sport.

    Returns:
        Normalized card record.
    """

    normalize_structure(record)
    normalize_card_defaults(record)
    normalize_classification(
        record,
        insert_sets,
    )
    normalize_positions(
        record,
        positions,
    )

    return record


def normalize_batch(
    data: Any,
    insert_sets: InsertSetConfig,
    positions: PositionConfig,
) -> list[JsonObject]:
    """
    Normalize every record in a raw extraction batch.

    Args:
        data:
            Parsed raw batch data.

        insert_sets:
            Known subset classifications.

        positions:
            Position mappings grouped by sport.

    Returns:
        List of normalized card records.

    Raises:
        ValueError:
            If the batch is not a list or contains invalid records.
    """

    if not isinstance(data, list):
        raise ValueError(
            "The input batch must contain a JSON array."
        )

    normalized: list[JsonObject] = []

    for index, item in enumerate(
        data,
        start=1,
    ):
        if not isinstance(item, dict):
            raise ValueError(
                f"Record {index} must be a JSON object."
            )

        try:
            normalized.append(
                normalize_card(
                    item,
                    insert_sets,
                    positions,
                )
            )

        except ValueError as error:
            raise ValueError(
                f"Record {index}: {error}"
            ) from error

    return normalized


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> int:
    """
    Run batch normalization.

    Returns:
        Process exit code.
    """

    arguments = parse_arguments()
    app = App("normalize_batch")

    insert_sets = cast(
        InsertSetConfig,
        app.config["insert_sets"],
    )
    positions = cast(
        PositionConfig,
        app.config["positions"],
    )

    try:
        raw_data = load_json(arguments.input_file)

        normalized = normalize_batch(
            raw_data,
            insert_sets,
            positions,
        )

        save_json(
            arguments.output_file,
            normalized,
        )

    except (
        OSError,
        ValueError,
    ) as error:
        app.logger.error(
            "Normalization failed: %s",
            error,
        )
        return 1

    app.logger.info(
        "Normalized %d records.",
        len(normalized),
    )
    app.logger.info(
        "Wrote %s",
        arguments.output_file,
    )

    return 0


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

__all__ = [
    "infer_position",
    "main",
    "normalize_batch",
    "normalize_card",
    "normalize_classification",
    "normalize_positions",
    "normalize_structure",
]


if __name__ == "__main__":
    raise SystemExit(main())
