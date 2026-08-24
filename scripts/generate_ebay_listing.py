"""
generate_ebay_listing.py

Reads the canonical primary inventory and generates draft eBay listing
records.

The generated listing file is a derived artifact. The primary inventory
remains the source of truth.

Business rules:
    - primary.json must contain valid JSON.
    - The root value must be a JSON array.
    - Every inventory record must contain a unique item_id.
    - Every generated listing must have a non-empty title.
    - eBay titles must not exceed 80 characters.
    - listing.json is replaced only after the entire build succeeds.

Usage:
    python scripts/generate_ebay_listing.py
"""

from collections import Counter
from pathlib import Path
import json
import os
import tempfile
from typing import Any
from common.load_config import load_config


# ---------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRIMARY_FILE = PROJECT_ROOT / "processed" / "primary_inventory.json"
LISTING_FILE = PROJECT_ROOT / "processed" / "listings.json"

CONSTANTS = load_config("constants.json")

PUBLIC_IMAGE_BASE_URL = (
    CONSTANTS["storage"]["public_image_base_url"]
)

# ---------------------------------------------------------------------
# Listing Configuration
# ---------------------------------------------------------------------

CATEGORY_ID = CONSTANTS["ebay"]["default_category_id"]

DEFAULT_CONDITION = CONSTANTS["ebay"]["default_condition"]

SHIPPING_MODE = CONSTANTS["ebay"]["shipping_mode"]
SHIPPING_AMOUNT = CONSTANTS["ebay"]["shipping_amount"]

RETURNS_ACCEPTED = CONSTANTS["ebay"]["returns_accepted"]

EBAY_TITLE_MAX_LENGTH = CONSTANTS["ebay"]["title_max_length"]


# ---------------------------------------------------------------------
# Inventory Helpers
# ---------------------------------------------------------------------

def load_inventory(filepath: Path) -> list[dict[str, Any]]:
    """
    Load and validate the primary inventory file.

    Args:
        filepath:
            Path to primary_inventory.json.

    Returns:
        A list of inventory records.

    Raises:
        FileNotFoundError:
            If primary_inventory.json does not exist.

        RuntimeError:
            If primary_inventory.json contains invalid JSON.

        ValueError:
            If the JSON root is not an array or contains invalid records.
    """

    if not filepath.exists():
        raise FileNotFoundError(
            f"Primary inventory does not exist: {filepath}"
        )

    try:
        with filepath.open("r", encoding="utf-8") as file:
            inventory = json.load(file)

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Primary inventory contains invalid JSON: "
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(inventory, list):
        raise ValueError(
            "Primary inventory must contain a JSON array."
        )

    for index, card in enumerate(inventory, start=1):
        if not isinstance(card, dict):
            raise ValueError(
                f"Inventory record {index} must be a JSON object."
            )

    return inventory


def validate_item_ids(inventory: list[dict[str, Any]]) -> None:
    """
    Confirm that every inventory record has a unique item_id.

    Args:
        inventory:
            Inventory records loaded from primary_inventory.json.

    Raises:
        ValueError:
            If an item_id is missing, blank, or duplicated.
    """

    item_ids = []

    for index, card in enumerate(inventory, start=1):
        item_id = card.get("item_id")

        if item_id is None or not str(item_id).strip():
            raise ValueError(
                f"Inventory record {index} is missing a valid item_id."
            )

        item_ids.append(str(item_id).strip())

    duplicate_ids = sorted(
        item_id
        for item_id, count in Counter(item_ids).items()
        if count > 1
    )

    if duplicate_ids:
        formatted_ids = ", ".join(duplicate_ids)

        raise ValueError(
            f"Duplicate item_id value(s) found: {formatted_ids}"
        )


# ---------------------------------------------------------------------
# Title Helpers
# ---------------------------------------------------------------------

def clean_text(value: Any) -> str | None:
    """
    Convert a value into clean, single-spaced text.

    Args:
        value:
            Value to normalize.

    Returns:
        Clean text, or None when the value is blank.
    """

    if value is None:
        return None

    cleaned = " ".join(str(value).split())

    return cleaned or None


def truncate_title(title: str) -> str:
    """
    Shorten a title to the eBay title-length limit.

    The function prefers removing complete trailing words rather than
    cutting through a word.

    Args:
        title:
            Full generated listing title.

    Returns:
        A title no longer than EBAY_TITLE_MAX_LENGTH characters.
    """

    if len(title) <= EBAY_TITLE_MAX_LENGTH:
        return title

    shortened = title[:EBAY_TITLE_MAX_LENGTH].rsplit(" ", 1)[0].rstrip()

    if not shortened:
        shortened = title[:EBAY_TITLE_MAX_LENGTH].rstrip()

    return shortened


def build_title(card: dict[str, Any]) -> str:
    """
    Generate a deterministic eBay listing title from the canonical schema.

    Title order:
        year
        set
        card number
        primary subject
        team

    Args:
        card:
            A primary inventory record.

    Returns:
        A cleaned eBay title no longer than 80 characters.

    Raises:
        ValueError:
            If no usable title fields are available.
    """

    parts = []

    card_data = card.get("card") or {}
    subjects = card.get("subjects") or []

    year = clean_text(card_data.get("year"))
    set_name = clean_text(card_data.get("set"))
    manufacturer = clean_text(card_data.get("manufacturer"))
    card_number = clean_text(card_data.get("card_number"))

    primary_subject = subjects[0] if subjects else {}

    player = clean_text(primary_subject.get("name"))
    team = clean_text(primary_subject.get("team"))

    # Do not repeat the year if the set name already contains it.
    if year:
        if not set_name or year.casefold() not in set_name.casefold():
            parts.append(year)

    if set_name:
        parts.append(set_name)

    elif manufacturer:
        parts.append(manufacturer)

    if card_number:
        if card_number.startswith("#"):
            parts.append(card_number)
        else:
            parts.append(f"#{card_number}")

    if player:
        parts.append(player)

    if team:
        parts.append(team)

    title = " ".join(parts).strip()

    if not title:
        item_id = card.get("item_id", "unknown")

        raise ValueError(
            f"Could not generate a title for item_id {item_id}."
        )

    return truncate_title(title)

# ---------------------------------------------------------------------
# Image Helpers
# ---------------------------------------------------------------------

def build_picture_urls(card: dict[str, Any]) -> list[str]:
    """
    Read canonical image URLs, deriving them from exact legacy filenames only
    when a stored URL is unavailable.

    Args:
        card:
            A primary inventory record.

    Returns:
        Public image URLs in front-then-back order.
    """

    images = card.get("images") or {}

    picture_urls = []

    for side_name in ("front", "back"):
        side = images.get(side_name) or {}
        url = side.get("url")
        if url:
            picture_urls.append(url)
            continue

        filename = side.get("filename")
        if filename:
            picture_urls.append(
                f"{PUBLIC_IMAGE_BASE_URL.rstrip('/')}/{Path(filename).name}"
            )

    return picture_urls

# ---------------------------------------------------------------------
# Listing Builder
# ---------------------------------------------------------------------

def build_listing(card: dict[str, Any]) -> dict[str, Any]:
    """
    Build one draft listing record.

    Args:
        card:
            A primary inventory record.

    Returns:
        A generated listing record.
    """

    return {
        "item_id": card["item_id"],

        # This is a generated snapshot of the source inventory record.
        # primary.json remains the authoritative source.
        "inventory": card,

        "listing": {
            "status": "draft",

            "category_id": CATEGORY_ID,

            "title": build_title(card),

            "condition": {
                "recommended": DEFAULT_CONDITION,
                "approved": None
            },

            "pricing": {
                "recommended_price": None,
                "approved_price": None
            },

            "shipping": {
                "mode": SHIPPING_MODE,
                "amount": SHIPPING_AMOUNT
            },

            "returns": {
                "accepted": RETURNS_ACCEPTED
            },

            "picture_urls": build_picture_urls(card),

            "approval": {
                "approved": False,
                "approved_by": None,
                "approved_at": None
            }
        }
    }


def build_listings(
    inventory: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Generate draft listings for all inventory records.

    Args:
        inventory:
            Validated primary inventory records.

    Returns:
        Generated listing records.
    """

    listings = []

    for card in inventory:
        try:
            listing = build_listing(card)

        except (TypeError, ValueError) as exc:
            item_id = card.get("item_id", "unknown")

            raise ValueError(
                f"Unable to build listing for item_id {item_id}: {exc}"
            ) from exc

        listings.append(listing)

    return listings


# ---------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------

def write_json_atomic(filepath: Path, data: Any) -> None:
    """
    Write JSON to a temporary file and atomically replace the destination.

    Args:
        filepath:
            Final output path.

        data:
            JSON-serializable data.
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
            delete=False
        ) as temporary_file:

            temporary_path = Path(temporary_file.name)

            json.dump(
                data,
                temporary_file,
                indent=2,
                ensure_ascii=False
            )

            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, filepath)

    except Exception:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()

        raise


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> None:
    """
    Generate listing.json from the canonical primary inventory.
    """

    inventory = load_inventory(PRIMARY_FILE)

    validate_item_ids(inventory)

    listings = build_listings(inventory)

    write_json_atomic(LISTING_FILE, listings)

    print(f"Loaded {len(inventory)} inventory record(s).")
    print(f"Built {len(listings)} draft listing(s).")
    print(f"Saved to {LISTING_FILE}")


if __name__ == "__main__":
    main()
