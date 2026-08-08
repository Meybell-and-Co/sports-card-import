"""
publish_portal.py

Projects canonical sports-card inventory into the data shape expected
by the Scout & Steward Portal.

The canonical source remains:

    processed/primary_inventory.json

This script does not modify canonical inventory.

Publisher V1:
    - Load canonical inventory.
    - Project canonical records into Portal snapshot records.
    - Print one projected record for inspection.
    - Perform no network or D1 writes.

Usage:
    python scripts/publish_portal.py
"""

import json
from typing import Any

from common.app import App
from common.io import load_json


# ---------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------


def get_primary_subject(item: dict[str, Any]) -> dict[str, Any]:
    """
    Return the primary player subject for a canonical inventory item.

    If no player subject exists, return an empty dictionary.
    """

    subjects = item.get("subjects") or []

    for subject in subjects:
        if subject.get("type") == "player":
            return subject

    return {}


def project_item(item: dict[str, Any]) -> dict[str, Any]:
    """
    Project one canonical inventory item into Portal snapshot fields.

    Publication-specific fields such as snapshot_id, publication_id,
    and created_at are intentionally excluded at this stage.
    """

    card = item.get("card") or {}
    attributes = item.get("attributes") or {}
    subject = get_primary_subject(item)

    return {
        "item_id": item.get("item_id"),
        "player_name": subject.get("name"),
        "team": subject.get("team"),
        "year": card.get("year"),
        "manufacturer": card.get("manufacturer"),
        "set_name": card.get("set"),
        "card_number": card.get("card_number"),
        "classification": attributes.get("classification"),
        "image_front_url": None,
        "image_back_url": None,
        "recommended_price_cents": None,
    }


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------


def main() -> int:
    app = App("publish_portal")

    try:
        inventory = load_json(
            app.paths.PRIMARY_INVENTORY_FILE
        )

        if not isinstance(inventory, list):
            raise ValueError(
                "Primary inventory must contain a JSON array."
            )

        if not inventory:
            raise ValueError(
                "Primary inventory contains no items."
            )

        projected = project_item(inventory[0])

        print(
            json.dumps(
                projected,
                indent=2,
                ensure_ascii=False,
            )
        )

    except (OSError, ValueError, TypeError) as error:
        app.logger.error(
            "Portal projection failed: %s",
            error,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
