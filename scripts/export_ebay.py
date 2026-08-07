"""
export_ebay_csv.py

Reads listing.json and exports an eBay upload CSV.

Usage:
    python scripts/export_ebay_csv.py
"""

from pathlib import Path
import json
import csv

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LISTING_FILE = PROJECT_ROOT / "processed" / "listings.json"
OUTPUT_FILE = PROJECT_ROOT / "processed" / "exports" / "ebay-upload.csv"

# ---------------------------------------------------------------------
# Load Listings
# ---------------------------------------------------------------------

with open(LISTING_FILE, "r", encoding="utf-8") as f:
    listings = json.load(f)

# ---------------------------------------------------------------------
# CSV Columns
# ---------------------------------------------------------------------

FIELDNAMES = [
    "SKU",
    "Category",
    "Title",
    "Description",
    "Price",
    "Condition",
    "ShippingType",
    "ShippingServiceCost",
    "ReturnsAccepted",
    "PictureURL"
]

# ---------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as csvfile:

    writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)

    writer.writeheader()

    for item in listings:

        inventory = item["inventory"]
        listing = item["listing"]

        writer.writerow({

            "SKU":
                inventory["item_id"],

            "Category":
                listing["category_id"],

            "Title":
                listing["title"],

            "Description":
                "",

            "Price":
                listing["pricing"]["approved_price"]
                or listing["pricing"]["recommended_price"]
                or "",

            "Condition":
                listing["condition"]["approved"]
                or listing["condition"]["recommended"],

            "ShippingType":
                listing["shipping"]["mode"],

            "ShippingServiceCost":
                listing["shipping"]["amount"],

            "ReturnsAccepted":
                "ReturnsNotAccepted"
                if not listing["returns"]["accepted"]
                else "ReturnsAccepted",

            "PictureURL":
                "|".join(listing["picture_urls"])

        })

# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------

print(f"Exported {len(listings)} listings.")
print(f"Saved to {OUTPUT_FILE}")
