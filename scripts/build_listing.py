"""
build_listing.py

Reads master.json and generates listing.json.

Usage:
    python scripts/build_listing.py
"""

from pathlib import Path
import json

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MASTER_FILE = PROJECT_ROOT / "processed" / "master.json"
LISTING_FILE = PROJECT_ROOT / "processed" / "listing.json"

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

CATEGORY_ID = 261328

DEFAULT_CONDITION = "Very Good"

SHIPPING_MODE = "flat"
SHIPPING_AMOUNT = 9.75

RETURNS_ACCEPTED = False

# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def build_title(card):
    """Generate a clean eBay title."""

    parts = []

    year = card.get("year")
    set_name = card.get("set")
    manufacturer = card.get("manufacturer")

    # If the set already contains the year, don't repeat it.
    if year:
        if not (set_name and str(year) in set_name):
            parts.append(str(year))

    # Prefer the full set name.
    if set_name:
        parts.append(set_name)

    elif manufacturer:
        parts.append(manufacturer)

    if card.get("card_number"):
        parts.append(f"#{card['card_number']}")

    if card.get("player"):
        parts.append(card["player"])

    if card.get("team"):
        parts.append(card["team"])

    return " ".join(parts)

# ---------------------------------------------------------------------
# Load Inventory
# ---------------------------------------------------------------------

with open(MASTER_FILE, "r", encoding="utf-8") as f:
    inventory = json.load(f)

# ---------------------------------------------------------------------
# Build Listings
# ---------------------------------------------------------------------

listings = []

for card in inventory:

    listing = {

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

            "picture_urls": [],

            "approval": {
                "approved": False,
                "approved_by": None,
                "approved_at": None
            }

        }

    }

    listings.append(listing)

# ---------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------

with open(LISTING_FILE, "w", encoding="utf-8") as f:
    json.dump(listings, f, indent=2)

# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------

print(f"Built {len(listings)} listing(s).")
print(f"Saved to {LISTING_FILE}")
