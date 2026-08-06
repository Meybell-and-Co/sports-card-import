"""
Scout & Steward

Module:
    migrate_legacy_batch.py

Purpose:
    Migrates legacy flat-format extraction batches into the canonical
    Sports Collectible Schema.

Responsibilities:
    - Load a legacy JSON batch
    - Convert flat records into canonical nested records
    - Preserve identifiers, filenames, OCR, notes, and review status
    - Infer player positions from OCR using project configuration
    - Write a canonical batch for schema validation

Usage:
    python migrate_legacy_batch.py input.json output.json

Author:
    Meybell & Co.

Version:
    1.0.0
"""

import argparse
import re
from pathlib import Path
from typing import Any, cast

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
            "Migrate a legacy Scout & Steward extraction batch "
            "into the canonical schema."
        )
    )

    parser.add_argument(
        "input_file",
        type=Path,
        help="Legacy flat-format JSON batch.",
    )

    parser.add_argument(
        "output_file",
        type=Path,
        help="Destination for the canonical JSON batch.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------
# General Helpers
# ---------------------------------------------------------------------

def optional_string(value: Any) -> str | None:
    """
    Return a stripped string or None.

    Args:
        value:
            Value to normalize.

    Returns:
        Non-empty string or None.
    """

    if not isinstance(value, str):
        return None

    stripped = value.strip()

    if not stripped:
        return None

    return stripped


def boolean_value(value: Any) -> bool:
    """
    Convert a legacy boolean-like field into a strict boolean.

    Only an explicit True value becomes True. Null and missing legacy
    values become False.

    Args:
        value:
            Legacy value.

    Returns:
        Normalized boolean.
    """

    return value is True


def normalize_confidence(value: Any) -> str:
    """
    Normalize extraction confidence.

    Args:
        value:
            Legacy confidence value.

    Returns:
        High, Medium, or Low.
    """

    if not isinstance(value, str):
        return "Low"

    normalized = value.strip().casefold()

    confidence_map = {
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    }

    return confidence_map.get(
        normalized,
        "Low",
    )


# ---------------------------------------------------------------------
# Position Helpers
# ---------------------------------------------------------------------

def get_sport_positions(
    sport: str | None,
    positions: PositionConfig,
) -> dict[str, str]:
    """
    Return configured positions for a sport.

    Matching is case-insensitive.

    Args:
        sport:
            Sport name.

        positions:
            Position configuration grouped by sport.

    Returns:
        Position map for the matching sport.
    """

    if sport is None:
        return {}

    normalized_sport = sport.casefold()

    for sport_name, position_map in positions.items():
        if sport_name.casefold() == normalized_sport:
            return position_map

    return {}


def infer_position(
    ocr_text: str,
    position_map: dict[str, str],
) -> str | None:
    """
    Infer a position abbreviation from OCR.

    Longer position names are checked first so specific phrases such as
    'Wide Receiver' take priority over shorter overlapping phrases.

    Args:
        ocr_text:
            OCR text to search.

        position_map:
            Full position names mapped to abbreviations.

    Returns:
        Position abbreviation or None.
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


# ---------------------------------------------------------------------
# Condition Helpers
# ---------------------------------------------------------------------

def infer_severity(observation: str) -> str | None:
    """
    Infer severity only when the wording states it explicitly.

    Args:
        observation:
            Legacy condition observation.

    Returns:
        Explicit severity or None.
    """

    normalized = observation.casefold()

    for severity in (
        "heavy",
        "moderate",
        "minor",
        "light",
    ):
        if re.search(
            rf"\b{severity}\b",
            normalized,
        ):
            return severity

    return None


def build_condition_observations(
    record: JsonObject,
) -> list[JsonObject]:
    """
    Convert legacy observable notes into condition observations.

    Args:
        record:
            Legacy record.

    Returns:
        Canonical condition observations.
    """

    legacy_observations = record.get(
        "observable_notes"
    )

    if not isinstance(legacy_observations, list):
        return []

    observations: list[JsonObject] = []

    for item in legacy_observations:
        observation = optional_string(item)

        if observation is None:
            continue

        observations.append(
            {
                "type": observation,
                "severity": infer_severity(
                    observation
                ),
            }
        )

    return observations


# ---------------------------------------------------------------------
# Notes Helpers
# ---------------------------------------------------------------------

def append_note(
    notes: list[str],
    value: Any,
    prefix: str | None = None,
) -> None:
    """
    Append one normalized note when present.

    Args:
        notes:
            Destination note list.

        value:
            Potential note value.

        prefix:
            Optional prefix added to the note.
    """

    note = optional_string(value)

    if note is None:
        return

    if prefix is not None:
        note = f"{prefix}: {note}"

    notes.append(note)


def build_notes(record: JsonObject) -> list[str]:
    """
    Combine legacy notes and production notes.

    Args:
        record:
            Legacy record.

    Returns:
        Canonical note list.
    """

    notes: list[str] = []

    legacy_notes = record.get("notes")

    if isinstance(legacy_notes, list):
        for note in legacy_notes:
            append_note(notes, note)

    else:
        append_note(notes, legacy_notes)

    production_notes = record.get(
        "production_notes"
    )

    if isinstance(production_notes, list):
        for note in production_notes:
            append_note(
                notes,
                note,
                prefix="Production note",
            )

    return notes


# ---------------------------------------------------------------------
# Classification Helpers
# ---------------------------------------------------------------------

def classification_from_subset(
    subset: str | None,
    insert_sets: InsertSetConfig,
) -> str | None:
    """
    Return a configured classification for a subset.

    Args:
        subset:
            Legacy subset name.

        insert_sets:
            Known subset classifications.

    Returns:
        Configured classification or None.
    """

    if subset is None:
        return None

    normalized_subset = subset.casefold()

    for subset_name, configuration in insert_sets.items():
        if subset_name.casefold() != normalized_subset:
            continue

        return optional_string(
            configuration.get(
                "classification"
            )
        )

    return None


def determine_classification(
    record: JsonObject,
    insert_sets: InsertSetConfig,
) -> str:
    """
    Determine the canonical classification.

    Args:
        record:
            Legacy record.

        insert_sets:
            Known subset classifications.

    Returns:
        Canonical classification.
    """

    if boolean_value(record.get("parallel")):
        return "Parallel"

    subset = optional_string(
        record.get("subset")
    )

    configured = classification_from_subset(
        subset,
        insert_sets,
    )

    if configured is not None:
        return configured

    legacy_insert = optional_string(
        record.get("insert")
    )

    configured = classification_from_subset(
        legacy_insert,
        insert_sets,
    )

    if configured is not None:
        return configured

    ocr_back = optional_string(
        record.get("ocr_back")
    )

    if (
        ocr_back is not None
        and "FOOTBALL CARD GAME" in ocr_back.upper()
    ):
        return "Game Card"

    if legacy_insert is not None:
        return "Insert"

    return "Base"


# ---------------------------------------------------------------------
# Subject Helpers
# ---------------------------------------------------------------------

def build_subjects(
    record: JsonObject,
    positions: PositionConfig,
) -> list[JsonObject]:
    """
    Convert legacy player and team fields into subjects.

    Args:
        record:
            Legacy record.

        positions:
            Position configuration grouped by sport.

    Returns:
        Canonical subject list.
    """

    player = optional_string(
        record.get("player")
    )
    team = optional_string(
        record.get("team")
    )
    sport = optional_string(
        record.get("sport")
    )

    if player is not None:
        ocr_front = optional_string(
            record.get("ocr_front")
        )
        ocr_back = optional_string(
            record.get("ocr_back")
        )

        ocr_text = " ".join(
            part
            for part in (
                ocr_front,
                ocr_back,
            )
            if part is not None
        )

        position = infer_position(
            ocr_text,
            get_sport_positions(
                sport,
                positions,
            ),
        )

        return [
            {
                "type": "player",
                "name": player,
                "team": team,
                "position": position,
            }
        ]

    if team is not None:
        return [
            {
                "type": "team",
                "name": team,
                "team": None,
                "position": None,
            }
        ]

    return []


# ---------------------------------------------------------------------
# Record Migration
# ---------------------------------------------------------------------

def migrate_record(
    record: JsonObject,
    batch_name: str,
    record_number: int,
    insert_sets: InsertSetConfig,
    positions: PositionConfig,
) -> JsonObject:
    """
    Convert one legacy record into canonical schema format.

    Args:
        record:
            Legacy record.

        batch_name:
            Source batch identifier.

        insert_sets:
            Known subset classifications.

        positions:
            Position configuration grouped by sport.

    Returns:
        Canonical collectible record.
    """

    validation = record.get("validation")

    if not isinstance(validation, dict):
        validation = {}

    item_id = optional_string(
        record.get("item_id")
        or record.get("sys_card_id")
        or record.get("file")
    )
    if item_id is None:
        item_id = (
            f"MIG_{batch_name}_{record_number:04d}"
        )
    front_filename = optional_string(
        record.get("sys_front_filename")
    )
    back_filename = optional_string(
        record.get("sys_back_filename")
    )
    sport = optional_string(
        record.get("sport")
    )
    subset = optional_string(
        record.get("subset")
    )

    legacy_insert = optional_string(
        record.get("insert")
    )

    if subset is None:
        subset = legacy_insert

    classification = determine_classification(
        record,
        insert_sets,
    )

    title: str | None = None

    if classification != "Base":
        title = legacy_insert

    return {
        "schema_version": "1.0.0",
        "item_id": item_id,
        "entity": {
            "entity_type": "Trading Card",
            "sport": sport,
        },
        "images": {
            "front": {
                "filename": front_filename,
                "path": None,
            },
            "back": {
                "filename": back_filename,
                "path": None,
            },
        },
        "card": {
            "year": record.get("year")
            if isinstance(record.get("year"), int)
            else None,
            "manufacturer": optional_string(
                record.get("manufacturer")
            ),
            "brand": None,
            "set": optional_string(
                record.get("set")
            ),
            "subset": subset,
            "title": title,
            "card_number": record.get(
                "card_number"
            ),
            "language": "English",
            "copyright": None,
        },
        "subjects": build_subjects(
            record,
            positions,
        ),
        "attributes": {
            "classification": classification,
            "rookie": boolean_value(
                record.get("rookie")
            ),
            "parallel": boolean_value(
                record.get("parallel")
            ),
            "autograph": False,
            "memorabilia": False,
            "serial_numbered": False,
        },
        "condition": {
            "overall": None,
            "observations": (
                build_condition_observations(
                    record
                )
            ),
        },
        "ocr": {
            "front": optional_string(
                record.get("ocr_front")
            ),
            "back": optional_string(
                record.get("ocr_back")
            ),
        },
        "notes": build_notes(record),
        "pipeline": {
            "batch": batch_name,
            "extractor": "legacy-flat-v1",
            "confidence": normalize_confidence(
                validation.get("confidence")
            ),
            "review_required": boolean_value(
                validation.get(
                    "review_required"
                )
            ),
        },
    }


def migrate_batch(
    data: Any,
    batch_name: str,
    insert_sets: InsertSetConfig,
    positions: PositionConfig,
) -> list[JsonObject]:
    """
    Convert an entire legacy batch.

    Args:
        data:
            Parsed legacy batch data.

        batch_name:
            Source batch identifier.

        record_number:
            One-based position of the record in the source batch.

        insert_sets:
            Known subset classifications.

        positions:
            Position configuration grouped by sport.

    Returns:
        Canonical record list.

    Raises:
        ValueError:
            If the input is not an array of objects.
    """

    if not isinstance(data, list):
        raise ValueError(
            "The legacy batch must contain a JSON array."
        )

    migrated: list[JsonObject] = []

    for index, item in enumerate(
        data,
        start=1,
    ):
        if not isinstance(item, dict):
            raise ValueError(
                f"Record {index} must be a JSON object."
            )

        migrated.append(
            migrate_record(
                item,
                batch_name,
                index,
                insert_sets,
                positions,
            )
        )

    return migrated


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> int:
    """
    Run the legacy batch migration.

    Returns:
        Process exit code.
    """

    arguments = parse_arguments()
    app = App("migrate_legacy_batch")

    insert_sets = cast(
        InsertSetConfig,
        app.config["insert_sets"],
    )
    positions = cast(
        PositionConfig,
        app.config["positions"],
    )

    batch_name = (
        arguments.input_file.stem
        .removesuffix("_raw")
        .removesuffix("_legacy")
    )

    try:
        legacy_data = load_json(
            arguments.input_file
        )

        migrated = migrate_batch(
            legacy_data,
            batch_name,
            insert_sets,
            positions,
        )

        save_json(
            arguments.output_file,
            migrated,
        )

    except (
        OSError,
        ValueError,
    ) as error:
        app.logger.error(
            "Legacy migration failed: %s",
            error,
        )
        return 1

    app.logger.info(
        "Migrated %d records.",
        len(migrated),
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
    "build_condition_observations",
    "build_notes",
    "build_subjects",
    "determine_classification",
    "infer_position",
    "main",
    "migrate_batch",
    "migrate_record",
]


if __name__ == "__main__":
    raise SystemExit(main())
