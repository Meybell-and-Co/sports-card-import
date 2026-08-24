"""Add canonical R2 URLs to normalized image records.

Dry-run is the default. Use --apply only after the reported gate passes.
Exact filenames are preserved as R2 object keys; extensions are never changed.
"""

from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path
import re
import tempfile

from jsonschema import Draft202012Validator

from common.load_config import load_config


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_DIR = PROJECT_ROOT / "processed" / "batches"
SCHEMA_FILE = PROJECT_ROOT / "schema" / "sports-card.schema.json"
BATCH_PATTERN = re.compile(r"^batch\d{4}\.json$")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json_atomic(path: Path, data) -> None:
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.stem}_",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        temporary_path.replace(path)
    except Exception:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
        raise


def migrate_record(record: dict, public_base: str) -> tuple[int, int, int]:
    images = record.get("images") or {}
    added_front = 0
    added_back = 0
    missing = 0

    for side_name in ("front", "back"):
        side = images.get(side_name) or {}
        filename = side.get("filename")
        if filename:
            if not side.get("url"):
                side["url"] = f"{public_base.rstrip('/')}/{Path(filename).name}"
                if side_name == "front":
                    added_front += 1
                else:
                    added_back += 1
        else:
            missing += 1

    return added_front, added_back, missing


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    arguments = parser.parse_args()

    constants = load_config("constants.json")
    public_base = constants["storage"]["public_image_base_url"]
    schema = load_json(SCHEMA_FILE)
    validator = Draft202012Validator(schema)
    batch_files = sorted(
        path for path in BATCH_DIR.iterdir()
        if path.is_file() and BATCH_PATTERN.fullmatch(path.name)
    )

    records = []
    staged = []
    front_urls = 0
    back_urls = 0
    missing_media = 0
    validation_errors = []

    for batch_file in batch_files:
        batch = load_json(batch_file)
        for index, record in enumerate(batch):
            added_front, added_back, missing = migrate_record(record, public_base)
            front_urls += int(bool((record.get("images") or {}).get("front", {}).get("url")))
            back_urls += int(bool((record.get("images") or {}).get("back", {}).get("url")))
            missing_media += missing
            for error in validator.iter_errors(record):
                validation_errors.append(
                    f"{batch_file.name}[{index}]: {error.message}"
                )
        records.extend(batch)
        staged.append((batch_file, batch))

    item_ids = [record.get("item_id") for record in records]
    missing_item_ids = sum(
        not isinstance(item_id, str) or not item_id.strip()
        for item_id in item_ids
    )
    counts = Counter(
        item_id for item_id in item_ids
        if isinstance(item_id, str) and item_id.strip()
    )
    duplicate_item_ids = sorted(
        item_id for item_id, count in counts.items() if count > 1
    )
    gate_passed = (
        not validation_errors
        and missing_item_ids == 0
        and not duplicate_item_ids
    )

    print(f"mode={'APPLY' if arguments.apply else 'DRY-RUN'}")
    print(f"public_base={public_base.rstrip('/')}")
    print(f"batches={len(batch_files)}")
    print(f"records={len(records)}")
    print(f"front_urls={front_urls}")
    print(f"back_urls={back_urls}")
    print(f"missing_media={missing_media}")
    print(f"missing_item_ids={missing_item_ids}")
    print(f"duplicate_item_ids={len(duplicate_item_ids)}")
    print(f"schema_validation_errors={len(validation_errors)}")
    print(f"gate_passed={str(gate_passed).lower()}")

    for item_id in duplicate_item_ids:
        print(f"duplicate: {item_id}")
    for error in validation_errors[:20]:
        print(f"schema: {error}")

    if arguments.apply:
        if not gate_passed:
            print("Refusing to apply: dry-run gate did not pass.")
            return 1
        for batch_file, batch in staged:
            write_json_atomic(batch_file, batch)
        print(f"applied_batches={len(staged)}")

    return 0 if gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
