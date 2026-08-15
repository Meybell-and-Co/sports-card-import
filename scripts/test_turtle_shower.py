import json
from pathlib import Path

import pytest
from PIL import Image

from turtle_shower import (
    shower_batch,
    validate_reading_batch,
)


def make_batch(tmp_path: Path, batch_id: str = "batch-test") -> Path:
    batch = tmp_path / batch_id
    images = batch / "images"
    images.mkdir(parents=True)

    manifest = {
        "batch_id": batch_id,
        "purpose": "AI sports-card reading",
        "card_count": 1,
    }

    (batch / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    return batch


def test_validate_reading_batch_accepts_valid_batch(tmp_path):
    batch = make_batch(tmp_path)

    manifest = validate_reading_batch(batch)

    assert manifest["batch_id"] == "batch-test"
    assert manifest["purpose"] == "AI sports-card reading"


def test_validate_reading_batch_rejects_missing_manifest(tmp_path):
    batch = tmp_path / "not-a-reading-batch"
    batch.mkdir()

    with pytest.raises(RuntimeError, match="manifest not found"):
        validate_reading_batch(batch)


def test_validate_reading_batch_rejects_wrong_purpose(tmp_path):
    batch = make_batch(tmp_path)

    manifest_path = batch / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["purpose"] = "source imagery"

    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="not identified"):
        validate_reading_batch(batch)


def test_validate_reading_batch_rejects_mismatched_batch_id(tmp_path):
    batch = make_batch(tmp_path)

    manifest_path = batch / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["batch_id"] = "some-other-batch"

    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="does not match"):
        validate_reading_batch(batch)


def test_shower_pair_swaps_known_sides_with_unknown_rotation(tmp_path):
    from turtle_shower import shower_pair

    a_path = tmp_path / "card_a.jpg"
    b_path = tmp_path / "card_b.jpg"

    # Distinct solid images let us prove which source became which output.
    Image.new("RGB", (20, 30), (255, 0, 0)).save(a_path)
    Image.new("RGB", (40, 50), (0, 0, 255)).save(b_path)

    result = shower_pair(
        a_path,
        b_path,
        {
            "front_source": "b",
            "back_source": "a",
            "a_rotation_clockwise": None,
            "b_rotation_clockwise": None,
        },
    )

    with Image.open(a_path) as new_a:
        assert new_a.size == (40, 50)

    with Image.open(b_path) as new_b:
        assert new_b.size == (20, 30)

    assert result["side_swap_applied"] is True
