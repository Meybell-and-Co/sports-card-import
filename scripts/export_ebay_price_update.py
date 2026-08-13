"""
Scout & Steward

Module:
    export_ebay_price_update.py

Purpose:
    Create an eBay Seller Hub price-revision CSV for the current
    Scout & Steward production listings.

Pricing rule:
    eBay price = Card Ladder Current Value + $10 shipping allowance

Safety:
    - Canonical inventory is never modified.
    - Card Ladder data is never modified.
    - Existing eBay template is never modified.
    - Only production listings are exported.
    - Historical golden-test duplicate listings are excluded.
"""

from pathlib import Path
from decimal import Decimal
import csv
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRICES_FILE = (
    PROJECT_ROOT
    / "processed"
    / "card_ladder_prices.json"
)

TEMPLATES_DIR = (
    PROJECT_ROOT
    / "templates"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "processed"
    / "exports"
    / "ebay-price-update.csv"
)

EXPECTED_PRODUCTION_COUNT = 101

GOLDEN_TEST_IDS = {
    "FBPU_0001",
    "FBPU_0002",
    "FBPU_0003",
    "FBPU_0004",
    "FBPU_0005",
}


def find_ebay_template() -> Path:
    matches = sorted(
        TEMPLATES_DIR.glob(
            "eBay-edit-price-quantity-template-*.csv"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not matches:
        raise FileNotFoundError(
            "No eBay edit-price-quantity template found in "
            f"{TEMPLATES_DIR}"
        )

    return matches[0]


def money(value) -> Decimal:
    return Decimal(
        str(value)
        .strip()
        .replace("$", "")
        .replace(",", "")
    ).quantize(Decimal("0.01"))


def main() -> None:

    with PRICES_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        prices = json.load(file)

    template_file = find_ebay_template()

    with template_file.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        raw_rows = list(csv.reader(file))

    required = {
        "Action",
        "Item number",
        "Start price",
        "Custom label (SKU)",
    }

    header_index = None

    for index, row in enumerate(raw_rows):
        normalized = {
            str(value).strip()
            for value in row
        }

        if required.issubset(normalized):
            header_index = index
            break

    if header_index is None:
        raise ValueError(
            "Could not locate the eBay listing header row."
        )

    fieldnames = raw_rows[header_index]

    rows = [
        dict(zip(fieldnames, row))
        for row in raw_rows[header_index + 1:]
        if any(
            str(value).strip()
            for value in row
        )
    ]

    print(
        f"eBay header found on row {header_index + 1}."
    )

    by_sku = {}

    for row in rows:
        sku = str(
            row.get("Custom label (SKU)") or ""
        ).strip()

        if sku in prices:
            by_sku.setdefault(
                sku,
                [],
            ).append(row)

    selected = []

    for sku, candidates in sorted(by_sku.items()):

        if len(candidates) == 1:
            selected.append(candidates[0])
            continue

        if sku not in GOLDEN_TEST_IDS:
            raise ValueError(
                f"Unexpected duplicate eBay SKU: {sku} "
                f"({len(candidates)} listings)"
            )

        # The five historical golden-test listings were repriced
        # to $14.00. Production copies came from the later $25 batch.
        production_candidates = [
            row
            for row in candidates
            if money(row["Start price"])
            != Decimal("14.00")
        ]

        if len(production_candidates) != 1:
            raise ValueError(
                f"Could not uniquely identify production listing "
                f"for duplicate SKU {sku}."
            )

        selected.append(
            production_candidates[0]
        )

    selected_skus = {
        str(row["Custom label (SKU)"]).strip()
        for row in selected
    }

    if len(selected) != EXPECTED_PRODUCTION_COUNT:
        raise ValueError(
            "Production listing count mismatch. "
            f"Expected {EXPECTED_PRODUCTION_COUNT}, "
            f"found {len(selected)}."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_rows = []

    for source_row in selected:

        sku = str(
            source_row["Custom label (SKU)"]
        ).strip()

        new_price = prices[sku]["ebay_price"]

        output_rows.append({
            "Action": "Revise",
            "Item number": source_row["Item number"],
            "Start price": new_price,
            "Custom label (SKU)": sku,
        })

    output_rows.sort(
        key=lambda row: row["Custom label (SKU)"]
    )

    output_fields = [
        "Action",
        "Item number",
        "Start price",
        "Custom label (SKU)",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=output_fields,
        )

        writer.writeheader()
        writer.writerows(output_rows)

    unused_prices = (
        set(prices)
        - selected_skus
    )

    print(
        f"eBay source rows: {len(rows)}"
    )
    print(
        f"Card Ladder prices: {len(prices)}"
    )
    print(
        f"Production listings selected: {len(selected)}"
    )
    print(
        f"Historical golden-test listings excluded: "
        f"{len(GOLDEN_TEST_IDS)}"
    )
    print(
        f"Priced canonical items without production listing: "
        f"{len(unused_prices)}"
    )
    print(
        "Pricing rule: Card Ladder value + $10.00 = eBay price"
    )
    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()


