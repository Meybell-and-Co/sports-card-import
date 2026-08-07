"""
Scout & Steward

Module:
    export_ebay_golden_test.py

Purpose:
    Exports a small, controlled set of listings for end-to-end
    eBay import testing.

Responsibilities:
    - Select the approved golden-test inventory records
    - Apply temporary test pricing and shipping values
    - Export a separate eBay test CSV
    - Leave canonical inventory and generated listings unchanged

Author:
    Meybell & Co.

Version:
    1.0.0
"""

from pathlib import Path
import csv
import json


# ---------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LISTINGS_FILE = (
    PROJECT_ROOT / "processed" / "listings.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "processed"
    / "exports"
    / "ebay-golden-test.csv"
)


# ---------------------------------------------------------------------
# Golden Test Configuration
# ---------------------------------------------------------------------

GOLDEN_TEST_ITEM_IDS = {
    "FBPU_0001",
    "FBPU_0002",
    "FBPU_0003",
    "FBPU_0004",
    "FBPU_0005",
}

TEST_PRICE = 14.00
TEST_SHIPPING_COST = 0.00


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
    "PictureURL",
]


# ---------------------------------------------------------------------
# Load Listings
# ---------------------------------------------------------------------

with LISTINGS_FILE.open("r", encoding="utf-8") as file:
    listings = json.load(file)


# ---------------------------------------------------------------------
# Select Golden Test Records
# ---------------------------------------------------------------------

test_listings = [
    item
    for item in listings
    if item["item_id"] in GOLDEN_TEST_ITEM_IDS
]

found_ids = {
    item["item_id"]
    for item in test_listings
}

missing_ids = sorted(
    GOLDEN_TEST_ITEM_IDS - found_ids
)

if missing_ids:
    raise ValueError(
        "Golden-test item(s) missing from listings.json: "
        + ", ".join(missing_ids)
    )

test_listings.sort(
    key=lambda item: item["item_id"]
)


# ---------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

with OUTPUT_FILE.open(
    "w",
    newline="",
    encoding="utf-8-sig",
) as csvfile:

    writer = csv.DictWriter(
        csvfile,
        fieldnames=FIELDNAMES,
    )

    writer.writeheader()

    for item in test_listings:

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
                f"{TEST_PRICE:.2f}",

            "Condition":
                listing["condition"]["approved"]
                or listing["condition"]["recommended"],

            "ShippingType":
                listing["shipping"]["mode"],

            "ShippingServiceCost":
                f"{TEST_SHIPPING_COST:.2f}",

            "ReturnsAccepted":
                "ReturnsNotAccepted"
                if not listing["returns"]["accepted"]
                else "ReturnsAccepted",

            "PictureURL":
                "|".join(
                    listing["picture_urls"]
                ),
        })


# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------

print(
    f"Exported {len(test_listings)} "
    "golden-test listing(s)."
)

print(
    f"Test price: ${TEST_PRICE:.2f}"
)

print(
    "Shipping: Free"
)

print(
    f"Saved to: {OUTPUT_FILE}"
)
