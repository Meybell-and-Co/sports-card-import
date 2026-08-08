"""
Scout & Steward

Module:
    migrate_early_canonical_batch.py

Purpose:
    Migrates early canonical-format batches into the current
    Sports Collectible Schema v1.0.

Usage:
    python scripts/migrate_early_canonical_batch.py input.json output.json
"""

import argparse
from pathlib import Path
from typing import Any

from common.app import App
from common.io import load_json, save_json


JsonObject = dict[str, Any]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Migrate an early canonical Scout & Steward batch "
            "into the current canonical schema."
        )
    )

    parser.add_argument(
        "input_file",
        type=Path,
        help="Early canonical JSON batch.",
    )

    parser.add_argument(
        "output_file",
        type=Path,
        help="Destination for migrated JSON batch.",
    )

    return parser.parse_args()


def normalize_confidence(value: Any) -> str:
    """Convert legacy confidence values to High, Medium, or Low."""

    if isinstance(value, str):
        normalized = value.strip().casefold()

        if normalized == "high":
            return "High"
        if normalized == "medium":
            return "Medium"
        if normalized == "low":
            return "Low"

    if isinstance(value, (int, float)):
        if value >= 0.90:
            return "High"
        if value >= 0.70:
            return "Medium"

    return "Low"


def normalize_classification(value: Any) -> str:
    """Convert early generic classifications to current values."""

    allowed = {
        "Base",
        "Insert",
        "Parallel",
        "Checklist",
        "Promotional",
        "Game Card",
        "Proof",
        "Sample",
        "Sticker",
        "Team Set",
        "Oddball",
        "Other",
    }

    if isinstance(value, str) and value in allowed:
        return value

    if value == "Sports Trading Card":
        return "Base"

    return "Other"


def migrate_subjects(value: Any) -> list[JsonObject]:
    """Add required subject type while preserving existing subject data."""

    if not isinstance(value, list):
        return []

    migrated: list[JsonObject] = []

    for subject in value:
        if not isinstance(subject, dict):
            continue

        migrated_subject = dict(subject)

        if "type" not in migrated_subject:
            if migrated_subject.get("name"):
                migrated_subject["type"] = "player"
            else:
                migrated_subject["type"] = "team"

        migrated.append(migrated_subject)

    return migrated


def migrate_record(record: JsonObject) -> JsonObject:
    """
    Migrate one early-canonical record.

    Existing canonical data is preserved wherever possible.
    """

    migrated = dict(record)

    # Preserve images exactly as extracted.
    # This is intentional because visual inspection may have determined
    # that _a/_b filename conventions were reversed.
    migrated["images"] = record.get("images", {})

    migrated["subjects"] = migrate_subjects(
        record.get("subjects")
    )

    attributes = dict(
        record.get("attributes", {})
        if isinstance(record.get("attributes"), dict)
        else {}
    )

    attributes["classification"] = normalize_classification(
        attributes.get("classification")
    )

    attributes["parallel"] = (
        attributes.get("parallel") is True
    )

    attributes["rookie"] = (
        attributes.get("rookie") is True
    )

    migrated["attributes"] = attributes

    pipeline = dict(
        record.get("pipeline", {})
        if isinstance(record.get("pipeline"), dict)
        else {}
    )

    pipeline["confidence"] = normalize_confidence(
        pipeline.get("confidence")
    )

    pipeline["review_required"] = (
        pipeline.get("review_required") is True
    )

    migrated["pipeline"] = pipeline

    return migrated


def migrate_batch(data: Any) -> list[JsonObject]:
    """Migrate an entire early-canonical batch."""

    if not isinstance(data, list):
        raise ValueError(
            "The batch must contain a JSON array."
        )

    migrated: list[JsonObject] = []

    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"Record {index} must be a JSON object."
            )

        migrated.append(
            migrate_record(item)
        )

    return migrated


def main() -> int:
    arguments = parse_arguments()
    app = App("migrate_early_canonical_batch")

    try:
        data = load_json(arguments.input_file)

        migrated = migrate_batch(data)

        save_json(
            arguments.output_file,
            migrated,
        )

    except (OSError, ValueError) as error:
        app.logger.error(
            "Early canonical migration failed: %s",
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


if __name__ == "__main__":
    raise SystemExit(main())
