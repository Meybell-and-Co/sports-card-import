"""
Scout & Steward AI Reading Batch Builder

Manifest-driven builder for 4UP production output.

DEFAULT MODE:
    AUDIT ONLY. Makes no filesystem changes.

BUILD MODE:
    python scripts/build_reading_batches.py --build

Source authority:
    production-4up-manifest.csv

Production rules:
- READY rows must contain exactly four a-crops and four b-crops.
- READY crops pair by crop number.
- MANUAL rows use the two filenames recorded in manual_reason.
- DEBUG imagery is never reading material.
- Loose WebP pairs are reported as supplemental photography.
- Source imagery is never modified.
- Existing reading batches are never overwritten.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import defaultdict

from turtle_shower import shower_pair
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_ROOT = Path(
    r"C:\Users\Meybells\Downloads\incoming-assets"
    r"\inventory-photos\s-and-s-sports-memorabilia"
    r"\4UP\processed"
)

PRODUCTION_MANIFEST = SOURCE_ROOT / "production-4up-manifest.csv"

CANONICAL_BATCH_ROOT = PROJECT_ROOT / "processed" / "batches"
OUTPUT_ROOT = PROJECT_ROOT / "working" / "reading-batches"
READING_PROMPT = PROJECT_ROOT / "prompts" / "SPORTS-CARD-EXTRACTION-V2.md"

CARDS_PER_BATCH = 20


CROP_PATTERN = re.compile(
    r"^(?P<pair_key>.+)_(?P<side>[ab])_crop_(?P<slot>\d{2})\.jpg$",
    re.IGNORECASE,
)

MANUAL_PATTERN = re.compile(
    r"^(?P<pair_key>.+)_(?P<side>[ab])_(?P<quadrant>UL|UR|LL|LR)\.jpg$",
    re.IGNORECASE,
)

WEBP_PATTERN = re.compile(
    r"^(?P<pair_key>.+)_(?P<side>[ab])\.webp$",
    re.IGNORECASE,
)

BATCH_PATTERN = re.compile(
    r"^batch(?P<number>\d{4})\.json$",
    re.IGNORECASE,
)


def load_manifest():
    if not PRODUCTION_MANIFEST.exists():
        raise RuntimeError(
            "STOP: Production manifest not found:\n"
            f"{PRODUCTION_MANIFEST}"
        )

    with PRODUCTION_MANIFEST.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    if not rows:
        raise RuntimeError(
            "STOP: Production manifest is empty."
        )

    required = {
        "pair_key",
        "aliases",
        "a_source",
        "b_source",
        "status",
        "crop_files",
        "manual_files",
        "manual_reason",
    }

    missing = required - set(rows[0])

    if missing:
        raise RuntimeError(
            "STOP: Manifest missing columns: "
            + ", ".join(sorted(missing))
        )

    return rows


def discover_machine_crops():
    crops = defaultdict(
        lambda: defaultdict(dict)
    )

    for path in SOURCE_ROOT.glob("*.jpg"):
        if "_DEBUG" in path.name.upper():
            continue

        match = CROP_PATTERN.match(path.name)

        if not match:
            continue

        pair_key = match.group("pair_key")
        side = match.group("side").lower()
        slot = match.group("slot")

        if side in crops[pair_key][slot]:
            raise RuntimeError(
                "STOP: Duplicate machine crop:\n"
                f"{pair_key} slot {slot} side {side}"
            )

        crops[pair_key][slot][side] = path

    return crops


def parse_manual_row(row):
    filenames = [
        value.strip()
        for value in row["manual_reason"].split("|")
        if value.strip()
    ]

    if len(filenames) != 2:
        raise RuntimeError(
            "STOP: MANUAL row must identify exactly "
            "two files in manual_reason:\n"
            f"{row['pair_key']}: {row['manual_reason']}"
        )

    sides = {}

    for filename in filenames:
        recorded_path = SOURCE_ROOT / filename

        candidates = [
            recorded_path.with_suffix(".jpg"),
            recorded_path.with_suffix(".webp"),
        ]

        existing = [
            candidate
            for candidate in candidates
            if candidate.exists()
        ]

        if len(existing) == 0:
            raise RuntimeError(
                "STOP: Manual crop missing in supported formats:\n"
                f"{recorded_path.stem} (.jpg or .webp)"
            )

        if len(existing) > 1:
            raise RuntimeError(
                "STOP: Ambiguous manual crop exists in multiple formats:\n"
                + "\n".join(str(path) for path in existing)
            )

        path = existing[0]

        match = MANUAL_PATTERN.match(filename)

        if not match:
            raise RuntimeError(
                "STOP: Manual filename does not match "
                "expected quadrant convention:\n"
                f"{filename}"
            )

        side = match.group("side").lower()
        quadrant = match.group("quadrant").upper()

        if match.group("pair_key") != row["pair_key"]:
            raise RuntimeError(
                "STOP: Manual filename pair_key mismatch:\n"
                f"Manifest: {row['pair_key']}\n"
                f"File:     {filename}"
            )

        if side in sides:
            raise RuntimeError(
                "STOP: Duplicate manual side:\n"
                f"{row['pair_key']} side {side}"
            )

        sides[side] = {
            "path": path,
            "quadrant": quadrant,
        }

    if set(sides) != {"a", "b"}:
        raise RuntimeError(
            "STOP: Manual pair does not contain "
            "exactly one a and one b:\n"
            f"{row['pair_key']}"
        )

    return {
        "pair_key": row["pair_key"],
        "position": {
            "kind": "manual_quadrants",
            "a": sides["a"]["quadrant"],
            "b": sides["b"]["quadrant"],
        },
        "a": sides["a"]["path"],
        "b": sides["b"]["path"],
        "provenance": "manual_crop",
    }


def build_roster(rows, machine_crops):
    cards = []
    ready_pairs = 0
    manual_pairs = 0
    manifest_keys = set()

    for row in rows:
        pair_key = row["pair_key"].strip()
        status = row["status"].strip().upper()

        if not pair_key:
            raise RuntimeError(
                "STOP: Manifest contains blank pair_key."
            )

        if pair_key in manifest_keys:
            raise RuntimeError(
                "STOP: Duplicate manifest pair_key:\n"
                f"{pair_key}"
            )

        manifest_keys.add(pair_key)

        if status == "READY":
            ready_pairs += 1

            slots = machine_crops.get(
                pair_key,
                {},
            )

            if len(slots) != 4:
                raise RuntimeError(
                    "STOP: READY pair does not have "
                    "exactly four crop slots:\n"
                    f"{pair_key}: {sorted(slots)}"
                )

            for slot in sorted(slots):
                sides = slots[slot]

                if set(sides) != {"a", "b"}:
                    raise RuntimeError(
                        "STOP: Incomplete READY crop pair:\n"
                        f"{pair_key} slot {slot}: "
                        f"{sorted(sides)}"
                    )

                cards.append(
                    {
                        "pair_key": pair_key,
                        "position": {
                            "kind": "crop_slot",
                            "slot": slot,
                        },
                        "a": sides["a"],
                        "b": sides["b"],
                        "provenance": "turtle_crop",
                    }
                )

        elif status == "MANUAL":
            manual_pairs += 1
            cards.append(
                parse_manual_row(row)
            )

        else:
            raise RuntimeError(
                "STOP: Unknown production status:\n"
                f"{pair_key}: {status}"
            )

    extra_machine_keys = (
        set(machine_crops) - manifest_keys
    )

    if extra_machine_keys:
        raise RuntimeError(
            "STOP: Machine crops exist without "
            "manifest rows:\n"
            + "\n".join(
                sorted(extra_machine_keys)
            )
        )

    return cards, ready_pairs, manual_pairs


def discover_supplemental_webps():
    grouped = defaultdict(dict)

    for path in SOURCE_ROOT.glob("*.webp"):
        match = WEBP_PATTERN.match(path.name)

        if not match:
            continue

        pair_key = match.group("pair_key")
        side = match.group("side").lower()

        if side in grouped[pair_key]:
            raise RuntimeError(
                "STOP: Duplicate supplemental WebP side:\n"
                f"{pair_key} side {side}"
            )

        grouped[pair_key][side] = path

    complete = []
    incomplete = []

    for pair_key, sides in sorted(grouped.items()):
        if set(sides) == {"a", "b"}:
            complete.append(
                {
                    "pair_key": pair_key,
                    "a": sides["a"],
                    "b": sides["b"],
                }
            )
        else:
            incomplete.append(
                {
                    "pair_key": pair_key,
                    "sides": sorted(sides),
                }
            )

    if incomplete:
        details = "\n".join(
            f"{item['pair_key']}: {item['sides']}"
            for item in incomplete
        )

        raise RuntimeError(
            "STOP: Incomplete supplemental WebP pairs:\n"
            + details
        )

    return complete


def next_batch_number():
    numbers = []

    if CANONICAL_BATCH_ROOT.exists():
        for path in CANONICAL_BATCH_ROOT.iterdir():
            if not path.is_file():
                continue

            match = BATCH_PATTERN.match(path.name)

            if match:
                numbers.append(
                    int(match.group("number"))
                )

    return max(numbers, default=0) + 1


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def build_batches(cards, start_number=None):
    if not READING_PROMPT.exists():
        raise RuntimeError(
            "STOP: AI reading prompt not found:\n"
            f"{READING_PROMPT}"
        )

    if start_number is None:
        start_number = next_batch_number()

    if start_number < 1:
        raise RuntimeError(
            "STOP: Batch number must be 1 or greater."
        )

    if OUTPUT_ROOT.exists():
        existing = list(OUTPUT_ROOT.iterdir())

        if existing:
            raise RuntimeError(
                "STOP: Reading-batch output is not empty:\n"
                f"{OUTPUT_ROOT}"
            )

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    created = []

    for offset, group in enumerate(
        chunked(cards, CARDS_PER_BATCH)
    ):
        batch_number = start_number + offset
        batch_id = f"batch{batch_number:04d}"

        batch_root = OUTPUT_ROOT / batch_id
        image_root = batch_root / "images"

        if batch_root.exists():
            raise RuntimeError(
                "STOP: Batch already exists:\n"
                f"{batch_root}"
            )

        image_root.mkdir(
            parents=True,
            exist_ok=False,
        )

        shutil.copy2(
            READING_PROMPT,
            batch_root / "READING-INSTRUCTIONS.md",
        )

        manifest_cards = []

        for ordinal, card in enumerate(
            group,
            start=1,
        ):
            reading_id = (
                f"{batch_id}_card{ordinal:03d}"
            )

            a_ext = card["a"].suffix.lower()
            b_ext = card["b"].suffix.lower()

            a_name = f"{reading_id}_a{a_ext}"
            b_name = f"{reading_id}_b{b_ext}"

            shutil.copy2(
                card["a"],
                image_root / a_name,
            )

            shutil.copy2(
                card["b"],
                image_root / b_name,
            )

            shower = shower_pair(
                image_root / a_name,
                image_root / b_name,
            )

            manifest_cards.append(
                {
                    "reading_id": reading_id,
                    "source_pair_key": card["pair_key"],
                    "position": card["position"],
                    "provenance": card["provenance"],
                    "images": {
                        "a": a_name,
                        "b": b_name,
                    },
                    "source_files": {
                        "a": card["a"].name,
                        "b": card["b"].name,
                    },
                    "normalization": shower,
                }
            )

        manifest = {
            "batch_id": batch_id,
            "purpose": "AI sports-card reading",
            "card_count": len(manifest_cards),
            "cards": manifest_cards,
        }

        with (
            batch_root / "manifest.json"
        ).open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as file:
            json.dump(
                manifest,
                file,
                indent=2,
                ensure_ascii=False,
            )
            file.write("\n")

        created.append(
            (batch_id, len(group))
        )

    return created


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--build",
        action="store_true",
        help="Create reading batches after audit passes.",
    )

    parser.add_argument(
        "--start-batch",
        type=int,
        default=None,
        help=(
            "Explicit first reading-batch number. "
            "Useful for controlled regression rebuilds. "
            "Existing output is never overwritten."
        ),
    )

    args = parser.parse_args()

    if args.start_batch is not None and not args.build:
        parser.error(
            "--start-batch requires --build"
        )

    print()
    print("=== AI READING BATCH AUDIT ===")
    print(f"Source: {SOURCE_ROOT}")
    print()

    rows = load_manifest()
    machine_crops = discover_machine_crops()

    (
        cards,
        ready_pairs,
        manual_pairs,
    ) = build_roster(
        rows,
        machine_crops,
    )

    supplemental = discover_supplemental_webps()

    turtle_cards = sum(
        card["provenance"] == "turtle_crop"
        for card in cards
    )

    manual_cards = sum(
        card["provenance"] == "manual_crop"
        for card in cards
    )

    print(f"Manifest rows:           {len(rows)}")
    print(f"READY scan pairs:        {ready_pairs}")
    print(f"MANUAL scan pairs:       {manual_pairs}")
    print()
    print(f"Turtle card pairs:       {turtle_cards}")
    print(f"Manual card pairs:       {manual_cards}")
    print(f"READING ROSTER:          {len(cards)}")
    print()
    print(
        f"Supplemental WebP pairs: {len(supplemental)}"
    )

    for item in supplemental:
        print(
            f"  SUPPLEMENTAL: {item['pair_key']}"
        )

    batch_count = (
        len(cards) + CARDS_PER_BATCH - 1
    ) // CARDS_PER_BATCH

    print()
    print(f"Cards per batch:         {CARDS_PER_BATCH}")
    print(f"Projected batches:       {batch_count}")
    print(
        f"First batch:             "
        f"batch{(args.start_batch or next_batch_number()):04d}"
    )

    if not args.build:
        print()
        print("AUDIT ONLY.")
        print("NO FILES WERE CREATED OR MODIFIED.")
        return

    print()
    print("=== BUILDING ===")

    created = build_batches(cards, args.start_batch)

    for batch_id, count in created:
        print(f"{batch_id}: {count} cards")

    print()
    print(f"Created batches: {len(created)}")
    print(f"Created cards:   {len(cards)}")
    print()
    print("SOURCE IMAGERY WAS NOT MODIFIED.")


if __name__ == "__main__":
    main()






