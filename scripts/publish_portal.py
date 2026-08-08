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

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from common.app import App
from common.io import load_json

def calculate_source_version(path) -> str:
    """
    Calculate a deterministic SHA-256 fingerprint for canonical inventory.
    """

    return hashlib.sha256(path.read_bytes()).hexdigest()

def create_publication(
    source_version: str,
    item_count: int,
) -> dict[str, Any]:
    """
    Create metadata describing one Portal publication attempt.
    """

    published_at = (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )

    return {
        "publication_id": str(uuid4()),
        "source_version": source_version,
        "status": "started",
        "item_count": item_count,
        "published_at": published_at,
        "completed_at": None,
        "error_message": None,
    }

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

def validate_inventory(inventory: list[dict[str, Any]]) -> None:
    """
    Validate canonical inventory requirements for Portal publication.
    """

    item_ids: set[str] = set()

    for index, item in enumerate(inventory):
        item_id = item.get("item_id")

        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError(
                f"Inventory item at index {index} has no valid item_id."
            )

        if item_id in item_ids:
            raise ValueError(
                f"Duplicate item_id in primary inventory: {item_id}"
            )

        item_ids.add(item_id)

def create_snapshot(
    projected_item: dict[str, Any],
    publication_id: str,
    created_at: str,
) -> dict[str, Any]:
    """
    Create one Portal inventory snapshot from a projected item.
    """

    return {
        "snapshot_id": str(uuid4()),
        "publication_id": publication_id,
        **projected_item,
        "created_at": created_at,
    }

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

        source_version = calculate_source_version(
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

        validate_inventory(inventory)

        projected_items = [
            project_item(item)
            for item in inventory
        ]

        publication = create_publication(
            source_version,
            len(projected_items),
        )

        snapshots = [
            create_snapshot(
                projected_item,
                publication["publication_id"],
                publication["published_at"],
            )
            for projected_item in projected_items
        ]

        print(f"Source version: {source_version}")
        print(f"Canonical items: {len(inventory)}")
        print(f"Projected items: {len(projected_items)}")
        snapshot_ids = {
            snapshot["snapshot_id"]
            for snapshot in snapshots
        }

        publication_ids = {
            snapshot["publication_id"]
            for snapshot in snapshots
        }

        snapshot_timestamps = {
            snapshot["created_at"]
            for snapshot in snapshots
        }

        print(f"Snapshots: {len(snapshots)}")
        print(f"Unique snapshot IDs: {len(snapshot_ids)}")
        print(
            "Publication linkage:",
            publication_ids == {publication["publication_id"]},
        )

        print(
            "Timestamp linkage:",
            snapshot_timestamps == {publication["published_at"]},
        )

        print(
            "First item:",
            json.dumps(
                projected_items[0],
                indent=2,
                ensure_ascii=False,
            ),
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
