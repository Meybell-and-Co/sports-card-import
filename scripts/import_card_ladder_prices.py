"""
Scout & Steward

Module:
    import_card_ladder_prices.py

Purpose:
    Import Cy's calibrated Card Ladder values and create a validated
    Scout & Steward price map for eBay repricing.

Pricing rule:
    eBay price = Card Ladder Current Value + $10.00 shipping allowance

Canonical primary inventory is never modified.
"""

from pathlib import Path
from decimal import Decimal, InvalidOperation
import csv
import json
import re


# ---------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_INPUT_FILE = (
    PROJECT_ROOT
    / "imports"
    / "card-ladder"
    / "Collection - Card Ladder (3).csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "processed"
    / "card_ladder_prices.json"
)


# ---------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------

FREE_SHIPPING_ALLOWANCE = Decimal("10.00")


# ---------------------------------------------------------------------
# Scout & Steward ID
# ---------------------------------------------------------------------

ITEM_ID_PATTERN = re.compile(
    r"Scout\s*&\s*Steward\s*\|\s*(\S+)",
    re.IGNORECASE,
)


def extract_item_id(notes: str | None) -> str:
    """
    Extract the canonical Scout & Steward item_id from Card Ladder Notes.
    """

    match = ITEM_ID_PATTERN.search(str(notes or ""))

    if not match:
        raise ValueError(
            f"Could not extract Scout & Steward item_id from Notes: "
            f"{notes!r}"
        )

    return match.group(1).strip()


def parse_current_value(value: str | None) -> Decimal:
    """
    Parse Card Ladder Current Value as currency.
    """

    cleaned = (
        str(value or "")
        .strip()
        .replace("$", "")
        .replace(",", "")
    )

    if not cleaned:
        raise ValueError("Card Ladder Current Value is blank.")

    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(
            f"Invalid Card Ladder Current Value: {value!r}"
        ) from exc

    if amount < 0:
        raise ValueError(
            f"Card Ladder Current Value cannot be negative: {value!r}"
        )

    return amount.quantize(Decimal("0.01"))


def main() -> None:

    if not DEFAULT_INPUT_FILE.exists():
        raise FileNotFoundError(
            "\nCard Ladder export not found.\n\n"
            f"Expected:\n{DEFAULT_INPUT_FILE}\n\n"
            "Place Cy's Card Ladder CSV there and run again."
        )

    prices = {}
    duplicate_ids = []

    with DEFAULT_INPUT_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as csvfile:

        reader = csv.DictReader(csvfile)

        required_columns = {
            "Notes",
            "Current Value",
        }

        missing_columns = (
            required_columns
            - set(reader.fieldnames or [])
        )

        if missing_columns:
            raise ValueError(
                "Card Ladder CSV is missing required column(s): "
                + ", ".join(sorted(missing_columns))
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            try:
                item_id = extract_item_id(
                    row.get("Notes")
                )

                card_ladder_value = parse_current_value(
                    row.get("Current Value")
                )

            except ValueError as exc:
                raise ValueError(
                    f"Row {row_number}: {exc}"
                ) from exc

            if item_id in prices:
                duplicate_ids.append(item_id)
                continue

            ebay_price = (
                card_ladder_value
                + FREE_SHIPPING_ALLOWANCE
            ).quantize(Decimal("0.01"))

            prices[item_id] = {
                "card_ladder_value":
                    f"{card_ladder_value:.2f}",

                "shipping_allowance":
                    f"{FREE_SHIPPING_ALLOWANCE:.2f}",

                "ebay_price":
                    f"{ebay_price:.2f}",
            }

    if duplicate_ids:
        raise ValueError(
            "Duplicate Scout & Steward item_id(s) in Card Ladder export: "
            + ", ".join(sorted(set(duplicate_ids)))
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            prices,
            file,
            indent=2,
            ensure_ascii=False,
        )

        file.write("\n")

    print(
        f"Imported {len(prices)} Card Ladder price(s)."
    )

    print(
        f"Shipping allowance: "
        f"${FREE_SHIPPING_ALLOWANCE:.2f}"
    )

    print(
        "Pricing rule: "
        "Card Ladder value + shipping allowance = eBay price"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()

