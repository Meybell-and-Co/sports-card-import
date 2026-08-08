"""
publish_portal.py

Projects canonical sports-card inventory into the data shape expected
by the Scout & Steward Portal.

The canonical source remains:

    processed/primary_inventory.json

This script does not modify canonical inventory.

Publisher V1:
- Load canonical inventory.
- Validate publication requirements.
- Calculate a deterministic canonical source version.
- Project canonical records into the Portal API shape.
- Build the Portal publish payload.
- Perform a dry run by default.
- Publish only when explicitly invoked with --publish.

Usage:
    python scripts/publish_portal.py
    python scripts/publish_portal.py --publish
"""

import argparse
import hashlib
import json
import os
from typing import Any
from urllib import error, request

from common.app import App
from common.io import load_json


# ---------------------------------------------------------------------
# Source Version
# ---------------------------------------------------------------------


def calculate_source_version(path) -> str:
    """
    Calculate a deterministic SHA-256 fingerprint for canonical inventory.
    """

    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def project_item(item: dict[str, Any]) -> dict[str, Any]:
    """
    Project one canonical inventory item into Portal API fields.

    Publication-specific fields such as snapshot_id, publication_id,
    and created_at are intentionally excluded. The Portal owns those
    values when a publication is persisted.
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
        "card_number": (
            str(card["card_number"])
            if card.get("card_number") is not None
            else None
        ),
        "classification": attributes.get("classification"),
        "image_front_url": None,
        "image_back_url": None,
        "recommended_price_cents": None,
    }


# ---------------------------------------------------------------------
# Publish Payload
# ---------------------------------------------------------------------


def create_publish_payload(
    source_version: str,
    projected_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Create the request payload expected by the Portal publish API.
    """

    return {
        "source_version": source_version,
        "items": projected_items,
    }


# ---------------------------------------------------------------------
# HTTP Transport
# ---------------------------------------------------------------------


def send_publish_payload(
    portal_url: str,
    publish_token: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Send a publication payload to the Portal publish API.
    """

    endpoint = f"{portal_url.rstrip('/')}/api/publish"

    body = json.dumps(payload).encode("utf-8")

    publish_request = request.Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {publish_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Scout-and-Steward-Publisher/1.0",
        },
        method="POST",
    )

    try:
        with request.urlopen(
            publish_request,
            timeout=30,
        ) as response:
            response_body = response.read().decode("utf-8")

    except error.HTTPError as http_error:
        response_body = http_error.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Portal publish failed with HTTP "
            f"{http_error.code}: {response_body}"
        ) from http_error

    except error.URLError as url_error:
        raise RuntimeError(
            f"Portal publish connection failed: "
            f"{url_error.reason}"
        ) from url_error

    try:
        return json.loads(response_body)

    except json.JSONDecodeError as json_error:
        raise RuntimeError(
            "Portal returned a non-JSON response."
        ) from json_error


# ---------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------


def parse_arguments() -> argparse.Namespace:
    """
    Parse publisher command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Project canonical inventory for the Scout & Steward Portal."
        )
    )

    parser.add_argument(
        "--publish",
        action="store_true",
        help=(
            "Send the projected inventory to the Portal. "
            "Without this flag, the script performs a dry run."
        ),
    )

    return parser.parse_args()


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------


def main() -> int:
    arguments = parse_arguments()
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

        payload = create_publish_payload(
            source_version,
            projected_items,
        )

        print(f"Source version: {source_version}")
        print(f"Canonical items: {len(inventory)}")
        print(f"Projected items: {len(projected_items)}")
        print(f"Payload items: {len(payload['items'])}")

        print(
            "First item:",
            json.dumps(
                projected_items[0],
                indent=2,
                ensure_ascii=False,
            ),
        )

        if arguments.publish:
            portal_url = os.environ.get("PORTAL_URL")
            publish_token = os.environ.get("PUBLISH_TOKEN")

            if not portal_url:
                raise ValueError(
                    "PORTAL_URL environment variable is required "
                    "when using --publish."
                )

            if not publish_token:
                raise ValueError(
                    "PUBLISH_TOKEN environment variable is required "
                    "when using --publish."
                )

            response = send_publish_payload(
                portal_url,
                publish_token,
                payload,
            )

            print(
                "Publish response:",
                json.dumps(
                    response,
                    indent=2,
                    ensure_ascii=False,
                ),
            )

    except (OSError, ValueError, TypeError, RuntimeError) as error:
        app.logger.error(
            "Portal projection failed: %s",
            error,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
