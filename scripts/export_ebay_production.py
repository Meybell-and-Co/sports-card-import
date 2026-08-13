"""
Scout & Steward

Module:
    export_ebay_golden_test.py

Purpose:
    Exports a small, controlled set of listings using eBay Seller Hub's
    category-template field names for end-to-end import testing.

Responsibilities:
    - Select the five golden-test inventory records
    - Translate Scout & Steward fields into eBay template fields
    - Apply temporary test price and shipping values
    - Export a separate eBay-ready test CSV
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
    PROJECT_ROOT
    / "processed"
    / "listings.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "processed"
    / "exports"
    / "ebay-production.csv"
)


# ---------------------------------------------------------------------
# Golden Test Records
# ---------------------------------------------------------------------

GOLDEN_TEST_ITEM_IDS = {
    "FBPU_0001",
    "FBPU_0002",
    "FBPU_0003",
    "FBPU_0004",
    "FBPU_0005",
}


# ---------------------------------------------------------------------
# Golden Test Listing Defaults
# ---------------------------------------------------------------------

TEST_ACTION = "Add"

TEST_CATEGORY_ID = 261328

TEST_CONDITION_ID = 4000
TEST_CARD_CONDITION = 400012

TEST_FORMAT = "FixedPrice"
TEST_DURATION = "GTC"

TEST_PRICE = 25.00
TEST_QUANTITY = 1

TEST_LOCATION = "Kansas City, MO"

TEST_SHIPPING_TYPE = "Flat"
TEST_SHIPPING_SERVICE = "USPSPriority"
TEST_SHIPPING_COST = 0.00

TEST_DISPATCH_TIME_MAX = 1

TEST_RETURNS_ACCEPTED = "ReturnsNotAccepted"


# ---------------------------------------------------------------------
# eBay Template Columns
# ---------------------------------------------------------------------

FIELDNAMES = [
    "*Action(SiteID=US|Country=US|Currency=USD|Version=1193|CC=UTF-8)",
    "CustomLabel",
    "*Category",
    "*Title",
    "*ConditionID",
    "CD:Card Condition - (ID: 40001)",
    "*C:Sport",
    "C:Player/Athlete",
    "C:Manufacturer",
    "C:Season",
    "C:Set",
    "C:Team",
    "C:Autographed",
    "C:Card Number",
    "C:Type",
    "C:Year Manufactured",
    "C:Language",
    "PicURL",
    "*Description",
    "*Format",
    "*Duration",
    "*StartPrice",
    "*Quantity",
    "*Location",
    "ShippingType",
    "ShippingService-1:Option",
    "ShippingService-1:Cost",
    "*DispatchTimeMax",
    "*ReturnsAcceptedOption",
]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def build_description(inventory: dict) -> str:
    """
    Build a simple, deterministic HTML description.

    eBay Seller Hub accepts HTML in the Description field. Keeping the
    generated HTML on one line avoids CSV formatting problems.
    """

    card = inventory.get("card") or {}
    subjects = inventory.get("subjects") or []
    condition = inventory.get("condition") or {}

    subject = subjects[0] if subjects else {}

    player = subject.get("name") or ""
    team = subject.get("team") or ""
    year = card.get("year") or ""
    set_name = card.get("set") or ""
    card_number = card.get("card_number") or ""

    observations = condition.get("observations") or []

    condition_items = "".join(
        f"<li>{observation.get('type')}</li>"
        for observation in observations
        if observation.get("type")
    )

    if not condition_items:
        condition_items = "<li>Please review photos for condition.</li>"

    display_set = set_name

    if year and set_name:
        if str(year).casefold() not in set_name.casefold():
            display_set = f"{year} {set_name}"
    elif year:
        display_set = str(year)

    return (
        f"<p><strong>{display_set}</strong></p>"
        f"<ul>"
        f"<li>Player: {player}</li>"
        f"<li>Team: {team}</li>"
        f"<li>Card Number: {card_number}</li>"
        f"</ul>"
        f"<p><strong>Condition Notes</strong></p>"
        f"<ul>{condition_items}</ul>"
        f"<p>Please review all photos carefully before purchase.</p>"
    )


# ---------------------------------------------------------------------
# Load Listings
# ---------------------------------------------------------------------

with LISTINGS_FILE.open(
    "r",
    encoding="utf-8",
) as file:
    listings = json.load(file)


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Select Production Records
# ---------------------------------------------------------------------

test_listings = [
    item
    for item in listings
    if item["listing"].get("picture_urls")
]

skipped_listings = [
    item
    for item in listings
    if not item["listing"].get("picture_urls")
]

test_listings.sort(
    key=lambda item: item["item_id"]
)

if skipped_listings:
    print(
        "Skipped listings without images: "
        + ", ".join(
            item["item_id"]
            for item in skipped_listings
        )
    )

# ---------------------------------------------------------------------
# Validate Golden Test Records
# ---------------------------------------------------------------------

for item in test_listings:
    listing = item["listing"]

    if not listing.get("picture_urls"):
        raise ValueError(
            f"{item['item_id']} has no picture URLs."
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
        extrasaction="ignore",
    )

    writer.writeheader()

    for item in test_listings:

        inventory = item["inventory"]
        listing = item["listing"]

        entity = inventory.get("entity") or {}
        card = inventory.get("card") or {}
        subjects = inventory.get("subjects") or []
        attributes = inventory.get("attributes") or {}

        primary_subject = (
            subjects[0]
            if subjects
            else {}
        )

        writer.writerow({
            "*Action(SiteID=US|Country=US|Currency=USD|Version=1193|CC=UTF-8)":
                TEST_ACTION,

            "CustomLabel":
                inventory["item_id"],

            "*Category":
                TEST_CATEGORY_ID,

            "*Title":
                listing["title"],

            "*ConditionID":
                TEST_CONDITION_ID,

            "CD:Card Condition - (ID: 40001)":
                TEST_CARD_CONDITION,

            "*C:Sport":
                entity.get("sport") or "",

            "C:Player/Athlete":
                primary_subject.get("name") or "",

            "C:Manufacturer":
                card.get("manufacturer") or "",

            "C:Season":
                card.get("year") or "",

            "C:Set":
                card.get("set") or "",

            "C:Team":
                primary_subject.get("team") or "",

            "C:Autographed":
                "Yes"
                if attributes.get("autograph")
                else "No",

            "C:Card Number":
                card.get("card_number") or "",

            "C:Type":
                entity.get("entity_type") or "",

            "C:Year Manufactured":
                card.get("year") or "",

            "C:Language":
                card.get("language") or "",

            "PicURL":
                "|".join(
                    listing["picture_urls"]
                ),

            "*Description":
                build_description(inventory),

            "*Format":
                TEST_FORMAT,

            "*Duration":
                TEST_DURATION,

            "*StartPrice":
                f"{TEST_PRICE:.2f}",

            "*Quantity":
                TEST_QUANTITY,

            "*Location":
                TEST_LOCATION,

            "ShippingType":
                TEST_SHIPPING_TYPE,

            "ShippingService-1:Option":
                TEST_SHIPPING_SERVICE,

            "ShippingService-1:Cost":
                f"{TEST_SHIPPING_COST:.2f}",

            "*DispatchTimeMax":
                TEST_DISPATCH_TIME_MAX,

            "*ReturnsAcceptedOption":
                TEST_RETURNS_ACCEPTED,
        })


# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------

print(
    f"Exported {len(test_listings)} "
    "production listing(s)."
)

print(
    f"Price: ${TEST_PRICE:.2f}"
)

print(
    "Shipping: Free"
)

print(
    f"Condition ID: {TEST_CONDITION_ID}"
)

print(
    f"Card Condition Descriptor: {TEST_CARD_CONDITION}"
)

print(
    f"Saved to: {OUTPUT_FILE}"
)