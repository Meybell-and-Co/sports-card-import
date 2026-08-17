"""Index generic memorabilia photos and publish deterministic WebP derivatives."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image


GROUPS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "2008-mlb-all-star-game-pin-set": ("pin set", "2008-mlb-all-star-game-pin-set", ("2008-mlb-all-star-game-pin-set",)),
    "1985-mlb-world-series-ticket-stubs": ("ticket stubs", "85-mlb-world-series-stubs", ("85-mlb-world-series-stubs",)),
    "1990-kc-royals-yearbook": ("yearbook", "90-kc-royals-yearbook", ("90-kc-royals-yearbook",)),
    "1993-george-brett-final-home-game": ("ticket stub", "93-george-brett-final-home-game", ("93-george-brett-final-home-game",)),
    "1998-ncaa-womens-final-four-ticket-stubs": ("ticket stubs", "98-ncaa-womens-ff-ticket-stubs", ("98-ncaa-womens-ff-ticket-stubs",)),
    "1998-world-series-pennant": ("pennant", "98-world-series-pennant", ("98-world-series-pennant",)),
    "1996-atlanta-summer-games-publication": ("publication", "atlanta-summer-games-96", ("atlanta-summer-games-96",)),
    "bryan-barker-chiefs-signed-photograph": ("signed photograph", "bryan-barker-chiefs-signed-photo-bw", ("bryan-barker-chiefs-signed-photo-bw",)),
    "2002-cmh-golf-classic-publication": ("publication", "cmh-golf-classic-2002-bhcc", ("cmh-golf-classic-2002-bhcc",)),
    "george-brett-3000-hit-souvenir": ("souvenir publication", "george-brett-3000-hit-souvenir", ("george-brett-3000-hit-souvenir",)),
    "george-brett-1993-number-retired": ("commemorative publication", "george-brett-93-number-retired", ("george-brett-93-number-retired",)),
    "jj-birden-signed-card": ("signed card", "jj-birden-card-signed", ("jj-birden-card-signed",)),
    "jj-birden-chiefs-signed-photograph": ("signed photograph", "jj-birden-chiefs-signed-photo-bw", ("jj-birden-chiefs-signed-photo-bw",)),
    "1985-kc-royals-championship-pennant": ("pennant", "kc-royals-85-championship-pennant", ("kc-royals-85-championship-pennant",)),
    "1993-kc-royals-scorecard": ("scorecard", "kc-royals-93-scorecard", ("kc-royals-93-scorecard",)),
    "kc-royals-kemper-commemorative-coin": ("commemorative coin", "kc-royals-kemper-25-coin", ("kc-royals-kemper-25-coin",)),
    "kc-royals-25th-anniversary-pin": ("pin", "kc-royals-pin-25", ("kc-royals-pin-25",)),
    "kevin-siers-dej-memorial-original-drawing": ("original drawing", "kevin-siers-dej-memorial-drawing", ("kevin-siers-dej-memorial-drawing",)),
    "mlb-25-patch": ("patch", "mlb-25-patch", ("mlb-25-patch",)),
    "1998-mlb-all-star-game-nyc-patch": ("patch", "mlb-all-star-game-98-nyc-patch", ("mlb-all-star-game-98-nyc-patch",)),
    "mlb-all-star-game-ticket-stub-and-program": ("ticket stub and program", "mlb-all-star-game-stub-and-program", ("mlb-all-star-game-stub-and-program",)),
    "2001-nascar-illustrated-earnhardt-memorial": ("magazine", "nascar-illustrated-earnhardt-memorial-2001", ("nascar-illustrated-earnhardt-memorial-2001",)),
    "2001-sports-illustrated-dale-earnhardt-memorial": ("magazine", "si-dale-earnhardt-memorial-2001", ("si-dale-earnhardt-memorial-2001",)),
    "2001-sports-illustrated-fiery-family-earnhardt-special": ("special issue", "si-fiery-family-earnhardt-special-2001", ("si-fiery-family-earnhardt-special-2001",)),
    "1980-sports-illustrated-kc-royals": ("magazine", "si-june-1980-kc-royals", ("si-june-1980-kc-royals",)),
    "2002-salt-lake-city-winter-games-pin-set": ("pin set", "slc-2002-winter-games-pin-set", ("slc-2002-winter-games-pin-set",)),
    "2001-time-earnhardt-memorial": ("magazine", "time-earnhardt-memorial-2001", ("time-earnhardt-memorial-2001",)),
    "toronto-blue-jays-hot-wheels-die-cast-vehicle": ("die-cast vehicle", "toronto-blue-jays-hot-wheels", ("toronto-blue-jays-hot-wheels",)),
    "toronto-blue-jays-25th-anniversary-patch": ("patch", "toronto-blue-jays-patch-25th", ("toronto-blue-jays-patch-25th",)),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("processed/generic-memorabilia"))
    parser.add_argument("--bucket", default="scout-and-steward")
    parser.add_argument("--public-base-url", required=True)
    parser.add_argument("--publish", action="store_true")
    return parser.parse_args()


def source_files(source: Path) -> list[Path]:
    return sorted(
        path for path in source.iterdir()
        if path.is_file() and path.suffix.lower() == ".jpg"
    )


def assigned_groups(files: list[Path]) -> tuple[dict[str, list[Path]], list[str]]:
    grouped: dict[str, list[Path]] = {slug: [] for slug in GROUPS}
    unassigned: list[str] = []
    for path in files:
        matches = [
            slug for slug, (_, _, prefixes) in GROUPS.items()
            if any(path.stem.lower().startswith(prefix) for prefix in prefixes)
        ]
        if len(matches) == 1:
            grouped[matches[0]].append(path)
        else:
            unassigned.append(path.name)
    return {slug: paths for slug, paths in grouped.items() if paths}, unassigned


def derivative_name(source_name: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", Path(source_name).stem.lower()).strip("-")
    return f"{stem}.webp"


def create_derivative(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image.save(destination, "WEBP", quality=92, method=6)


def publish_derivative(bucket: str, key: str, path: Path) -> None:
    npx = "npx.cmd" if sys.platform == "win32" else "npx"
    subprocess.run(
        [
            npx, "wrangler", "r2", "object", "put",
            f"{bucket}/{key}", "--file", str(path),
            "--content-type", "image/webp", "--remote",
        ],
        check=True,
    )


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    files = source_files(source)
    grouped, unassigned = assigned_groups(files)
    if unassigned:
        raise SystemExit("Unassigned source files: " + ", ".join(unassigned))

    media_root = output / "derivatives"
    objects: list[dict[str, Any]] = []
    derivative_count = 0
    for slug, paths in grouped.items():
        object_type, stem, _ = GROUPS[slug]
        media: list[dict[str, str]] = []
        for path in paths:
            filename = derivative_name(path.name)
            derivative = media_root / filename
            create_derivative(path, derivative)
            key = f"generic-memorabilia/{filename}"
            if args.publish:
                publish_derivative(args.bucket, key, derivative)
            media.append({
                "source_filename": path.name,
                "derivative_filename": filename,
                "r2_key": key,
                "r2_url": f"{args.public_base_url.rstrip('/')}/{key}",
            })
            derivative_count += 1
        objects.append({
            "slug": slug,
            "object_type": object_type,
            "source_stem": stem,
            "media": media,
            "status": "ready_for_visual_reading",
            "ambiguity": None,
        })

    output.mkdir(parents=True, exist_ok=True)
    inventory = {
        "inventory_type": "generic_memorabilia",
        "phase": 1,
        "source_directory": str(source),
        "source_jpg_count": len(files),
        "object_count": len(objects),
        "derivative_count": derivative_count,
        "objects": objects,
        "ambiguous_groupings": [],
        "unassigned_files": unassigned,
    }
    (output / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    (output / "source-manifest.json").write_text(json.dumps({"files": [path.name for path in files]}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_jpg_count": len(files),
        "object_count": len(objects),
        "derivative_count": derivative_count,
        "unassigned_files": unassigned,
        "published": args.publish,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
