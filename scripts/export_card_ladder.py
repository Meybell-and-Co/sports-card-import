"""
export_card_ladder.py

Exports canonical primary inventory to a Card Ladder-compatible CSV.

Card Ladder query text is an integration concern. Canonical inventory
is never modified to accommodate Card Ladder search behavior.
"""

from pathlib import Path
import csv
import json
import re

from generate_ebay_listing import build_picture_urls


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRIMARY_FILE = (
    PROJECT_ROOT / "processed" / "primary_inventory.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "processed"
    / "exports"
    / "card-ladder-import.csv"
)


FIELDNAMES = [
    "Date Purchased",
    "Player",
    "Year",
    "Set",
    "Variation",
    "Number",
    "Category",
    "Condition",
    "Investment",
    "Ladder ID",
    "Query",
    "Image",
    "Back Image",
    "Grader",
    "Grade",
    "Serial Number",
    "Date Sold",
    "Sold Price",
    "Notes",
    "Quantity",
]


def player_subjects(item):
    return [
        subject
        for subject in (item.get("subjects") or [])
        if subject.get("type") == "player"
        and subject.get("name")
    ]


def surname(name):
    """
    Return the final whitespace-delimited name component.

    Card Ladder multiplayer queries perform more reliably with
    surnames only.
    """
    parts = str(name).strip().split()

    return parts[-1] if parts else ""


def build_card_ladder_query(item):
    """
    Build Card Ladder's Custom Sales Query.

    These normalization rules are based on observed Card Ladder
    query-validation behavior and affect export text only.
    """
    card = item.get("card") or {}

    year = card.get("year")
    set_name = str(card.get("set") or "").strip()
    variation = str(
        card.get("subset")
        or card.get("title")
        or ""
    ).strip()
    number = str(card.get("card_number") or "").strip()

    players = player_subjects(item)
    player_names = [
        str(player["name"]).strip()
        for player in players
    ]

    query_set = set_name

    # Card Ladder rejects this wording for 1994 Topps records.
    if year == 1994 and set_name == "Topps Baseball":
        query_set = "Topps"

    # Multiplayer queries validate more reliably using surnames only.
    if len(player_names) > 1:
        query_names = " ".join(
            surname(name)
            for name in player_names
        )
    else:
        query_names = " ".join(player_names)

    parts = [
        str(year or "").strip(),
        query_set,
        variation,
        number,
        query_names,
    ]

    query = " ".join(
        part for part in parts if part
    )

    # Defensive cleanup: Card Ladder rejects slash-separated names.
    query = query.replace("/", " ")

    return re.sub(r"\s+", " ", query).strip()


def build_row(item):
    card = item.get("card") or {}
    entity = item.get("entity") or {}
    players = player_subjects(item)

    player_names = " / ".join(
        str(player["name"]).strip()
        for player in players
    )

    picture_urls = build_picture_urls(item)

    front_image = (
        picture_urls[0]
        if len(picture_urls) >= 1
        else ""
    )

    back_image = (
        picture_urls[1]
        if len(picture_urls) >= 2
        else ""
    )

    variation = (
        card.get("subset")
        or card.get("title")
        or ""
    )

    return {
        "Date Purchased": "",
        "Player": player_names,
        "Year": card.get("year") or "",
        "Set": card.get("set") or "",
        "Variation": variation,
        "Number": card.get("card_number") or "",
        "Category": entity.get("sport") or "",
        "Condition": "Raw",
        "Investment": "",
        "Ladder ID": "",
        "Query": build_card_ladder_query(item),
        "Image": front_image,
        "Back Image": back_image,
        "Grader": "",
        "Grade": "",
        "Serial Number": "",
        "Date Sold": "",
        "Sold Price": "",
        "Notes": (
            f"Scout & Steward | {item['item_id']}"
        ),
        "Quantity": 1,
    }


def main():
    with open(PRIMARY_FILE, "r", encoding="utf-8") as f:
        inventory = json.load(f)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    rows = [
        build_row(item)
        for item in inventory
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=FIELDNAMES,
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Loaded {len(inventory)} canonical record(s)."
    )
    print(
        f"Exported {len(rows)} Card Ladder row(s)."
    )
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
