"""
Scout & Steward

Module:
    validate_schema.py

Purpose:
    Validates normalized Scout & Steward batch records against the
    canonical Sports Collectible Schema.

Responsibilities:
    - Load the canonical JSON Schema
    - Load a normalized batch
    - Validate each record independently
    - Report validation errors clearly
    - Return an appropriate process exit code

Usage:
    python validate_schema.py batch0001.json

Author:
    Meybell & Co.

Version:
    1.0.0
"""

import argparse
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from common.app import App
from common.io import load_json


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
            "Validate a normalized Scout & Steward batch against "
            "the canonical Sports Collectible Schema."
        )
    )

    parser.add_argument(
        "batch_file",
        type=Path,
        help="Normalized batch JSON file to validate.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------

def format_error_path(error: ValidationError) -> str:
    """
    Format the location of a schema validation error.

    Args:
        error:
            JSON Schema validation error.

    Returns:
        Dot-separated path to the invalid value.
    """

    if not error.absolute_path:
        return "<record>"

    return ".".join(
        str(part)
        for part in error.absolute_path
    )


def validate_batch_structure(data: Any) -> list[dict[str, Any]]:
    """
    Confirm that the input file contains an array of record objects.

    Args:
        data:
            Parsed JSON batch data.

    Returns:
        Batch records.

    Raises:
        ValueError:
            If the batch is not an array or contains non-object items.
    """

    if not isinstance(data, list):
        raise ValueError(
            "The batch file must contain a JSON array."
        )

    records: list[dict[str, Any]] = []

    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"Record {index} must be a JSON object."
            )

        records.append(item)

    return records


def collect_validation_errors(
    records: list[dict[str, Any]],
    validator: Draft202012Validator,
) -> list[tuple[int, ValidationError]]:
    """
    Validate every record and collect schema errors.

    Args:
        records:
            Normalized collectible records.

        validator:
            Configured JSON Schema validator.

    Returns:
        Record numbers paired with validation errors.
    """

    errors: list[tuple[int, ValidationError]] = []

    for record_number, record in enumerate(
        records,
        start=1,
    ):
        record_errors = sorted(
            validator.iter_errors(record),
            key=lambda error: (
                list(error.absolute_path),
                error.message,
            ),
        )

        for error in record_errors:
            errors.append(
                (record_number, error)
            )

    return errors


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> int:
    """
    Validate a normalized batch against the canonical schema.

    Returns:
        Process exit code.
    """

    arguments = parse_arguments()
    app = App("validate_schema")

    try:
        schema = load_json(
            app.paths.SCHEMA_FILE
        )

        Draft202012Validator.check_schema(
            schema
        )

        validator = Draft202012Validator(
            schema
        )

        batch_data = load_json(
            arguments.batch_file
        )

        records = validate_batch_structure(
            batch_data
        )

    except (
        OSError,
        ValueError,
        SchemaError,
    ) as error:
        app.logger.error(
            "Validation could not start: %s",
            error,
        )
        return 1

    app.logger.info(
        "Loaded schema: %s",
        app.paths.SCHEMA_FILE,
    )

    app.logger.info(
        "Loaded %d records from %s",
        len(records),
        arguments.batch_file,
    )

    errors = collect_validation_errors(
        records,
        validator,
    )

    if errors:
        for record_number, error in errors:
            app.logger.error(
                "Record %d | %s | %s",
                record_number,
                format_error_path(error),
                error.message,
            )

        invalid_records = {
            record_number
            for record_number, _ in errors
        }

        app.logger.error(
            "Schema validation failed: "
            "%d error(s) across %d record(s).",
            len(errors),
            len(invalid_records),
        )

        return 1

    app.logger.info(
        "All %d records passed schema validation.",
        len(records),
    )

    return 0


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

__all__ = [
    "collect_validation_errors",
    "format_error_path",
    "main",
    "validate_batch_structure",
]


if __name__ == "__main__":
    raise SystemExit(main())
