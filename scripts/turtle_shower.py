"""
Turtle Shower

Pre-reader normalization for Scout & Steward card imagery.

Responsibilities:
- Work only on reading-batch copies.
- Never modify source imagery.
- Apply only explicitly declared presentation corrections.
- Normalize front/back presentation when declared.
- Normalize readable orientation when declared.
- Preserve uncertain imagery unchanged.
- Return provenance describing every action.

IMPORTANT:
This module corrects PRESENTATION, never IDENTITY.

Turtle Shower does not infer front/back or rotation.
A correction map is authoritative.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from PIL import Image


VALID_SIDES = {"a", "b"}
VALID_ROTATIONS = {0, 90, 180, 270}
REQUIRED_REVIEW_STATUS = "approved"


def validate_correction(
    correction: dict | None,
) -> dict | None:
    """
    Validate one declared presentation correction.

    Missing correction means:
        do nothing.

    Turtle never fills in missing values by inference.
    """

    if correction is None:
        return None

    if not isinstance(correction, dict):
        raise RuntimeError(
            "STOP: Turtle Shower correction must be an object."
        )

    front_source = correction.get("front_source")
    back_source = correction.get("back_source")

    if front_source not in VALID_SIDES:
        raise RuntimeError(
            "STOP: front_source must be 'a' or 'b'."
        )

    if back_source not in VALID_SIDES:
        raise RuntimeError(
            "STOP: back_source must be 'a' or 'b'."
        )

    if front_source == back_source:
        raise RuntimeError(
            "STOP: front_source and back_source "
            "cannot be the same side."
        )

    for key in (
        "a_rotation_clockwise",
        "b_rotation_clockwise",
    ):
        value = correction.get(key)

        if value is None:
            continue

        if value not in VALID_ROTATIONS:
            raise RuntimeError(
                f"STOP: {key} must be 0, 90, 180, 270, or null."
            )

    return {
        "front_source": front_source,
        "back_source": back_source,
        "a_rotation_clockwise": correction.get(
            "a_rotation_clockwise"
        ),
        "b_rotation_clockwise": correction.get(
            "b_rotation_clockwise"
        ),
    }


def rotate_clockwise(
    source: Path,
    destination: Path,
    degrees: int,
) -> None:
    """
    Rotate an image clockwise and write it to destination.

    Pillow uses counterclockwise-positive angles, so clockwise rotation
    requires a negative angle.
    """

    with Image.open(source) as image:
        if degrees == 0:
            shutil.copy2(
                source,
                destination,
            )
            return

        rotated = image.rotate(
            -degrees,
            expand=True,
        )

        rotated.save(
            destination,
            format=image.format,
        )


def shower_pair(
    a_path: Path,
    b_path: Path,
    correction: dict | None = None,
) -> dict:
    """
    Apply one declared presentation correction to a disposable
    working pair.

    The correction map is authoritative.

    No correction means no filesystem changes.
    """

    if not a_path.exists():
        raise RuntimeError(
            f"STOP: Turtle Shower missing a-side:\n{a_path}"
        )

    if not b_path.exists():
        raise RuntimeError(
            f"STOP: Turtle Shower missing b-side:\n{b_path}"
        )

    correction = validate_correction(
        correction
    )

    if correction is None:
        return {
            "status": "UNCHANGED",
            "side_check": "NO_CORRECTION_DECLARED",
            "side_swap_applied": False,
            "orientation_check": "NO_CORRECTION_DECLARED",
            "a_rotation_applied": 0,
            "b_rotation_applied": 0,
            "review_required": False,
        }

    front_source = correction["front_source"]
    back_source = correction["back_source"]

    a_rotation = correction[
        "a_rotation_clockwise"
    ]

    b_rotation = correction[
        "b_rotation_clockwise"
    ]

    a_rotation = (
        0
        if a_rotation is None
        else a_rotation
    )

    b_rotation = (
        0
        if b_rotation is None
        else b_rotation
    )

    side_swap_required = (
        front_source == "b"
        and back_source == "a"
    )

    with tempfile.TemporaryDirectory(
        prefix="turtle-shower-",
        dir=a_path.parent,
    ) as temp_dir:

        temp_root = Path(temp_dir)

        original_a = temp_root / a_path.name
        original_b = temp_root / b_path.name

        shutil.copy2(
            a_path,
            original_a,
        )

        shutil.copy2(
            b_path,
            original_b,
        )

        # Normalize the working pair so:
        #
        #     _a = physical front
        #     _b = physical back
        #
        # The correction map identifies which ORIGINAL supplied side
        # contains each physical side.
        #
        # Rotation belongs to the ORIGINAL supplied side, not the
        # normalized destination filename.

        source_for_a = (
            original_a
            if front_source == "a"
            else original_b
        )

        source_for_b = (
            original_a
            if back_source == "a"
            else original_b
        )

        rotation_for_a = (
            a_rotation
            if front_source == "a"
            else b_rotation
        )

        rotation_for_b = (
            a_rotation
            if back_source == "a"
            else b_rotation
        )

        temp_a = temp_root / "normalized_a"
        temp_b = temp_root / "normalized_b"

        rotate_clockwise(
            source_for_a,
            temp_a,
            rotation_for_a,
        )

        rotate_clockwise(
            source_for_b,
            temp_b,
            rotation_for_b,
        )

        shutil.copy2(
            temp_a,
            a_path,
        )

        shutil.copy2(
            temp_b,
            b_path,
        )

    orientation_changed = (
        a_rotation != 0
        or b_rotation != 0
    )

    changed = (
        side_swap_required
        or orientation_changed
    )

    return {
        "status": (
            "CORRECTED"
            if changed
            else "UNCHANGED"
        ),
        "side_check": (
            "SWAP_APPLIED"
            if side_swap_required
            else "NO_SWAP_REQUIRED"
        ),
        "side_swap_applied": (
            side_swap_required
        ),
        "orientation_check": (
            "ROTATION_APPLIED"
            if orientation_changed
            else "NO_ROTATION_REQUIRED"
        ),
        "a_rotation_applied": a_rotation,
        "b_rotation_applied": b_rotation,
        "review_required": False,
    }


def load_correction_map(
    map_path: Path,
    expected_batch_id: str,
) -> dict:
    """
    Load and fully validate a Turtle presentation-correction map.

    No image files are modified by this function.
    """

    if not map_path.exists():
        raise RuntimeError(
            f"STOP: Correction map not found:\n{map_path}"
        )

    try:
        data = json.loads(
            map_path.read_text(
                encoding="utf-8"
            )
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"STOP: Correction map is not valid JSON:\n{map_path}"
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError(
            "STOP: Correction map root must be an object."
        )

    if data.get("schema_version") != "1.0.0":
        raise RuntimeError(
            "STOP: Unsupported correction-map schema version."
        )

    if data.get("batch_id") != expected_batch_id:
        raise RuntimeError(
            "STOP: Correction-map batch_id does not match "
            f"working batch {expected_batch_id}."
        )

    if data.get("review_status") != REQUIRED_REVIEW_STATUS:
        raise RuntimeError(
            "STOP: Correction map is not approved. "
            f"Expected review_status='{REQUIRED_REVIEW_STATUS}'."
        )

    corrections = data.get("corrections")

    if not isinstance(corrections, dict):
        raise RuntimeError(
            "STOP: Correction map 'corrections' must be an object."
        )

    validated = {}

    for reading_id, correction in corrections.items():
        if not isinstance(reading_id, str) or not reading_id:
            raise RuntimeError(
                "STOP: Correction map contains an invalid reading_id."
            )

        validated[reading_id] = validate_correction(
            correction
        )

    return {
        "schema_version": data["schema_version"],
        "batch_id": data["batch_id"],
        "correction_basis": data.get(
            "correction_basis"
        ),
        "review_status": data["review_status"],
        "corrections": validated,
    }


def validate_reading_batch(batch_root: Path) -> dict:
    """Verify that batch_root is an identified disposable reading batch."""

    manifest_path = batch_root / "manifest.json"

    if not manifest_path.exists():
        raise RuntimeError(
            f"STOP: Reading-batch manifest not found:\n{manifest_path}"
        )

    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"STOP: Reading-batch manifest is not valid JSON:\n{manifest_path}"
        ) from exc

    if not isinstance(manifest, dict):
        raise RuntimeError(
            "STOP: Reading-batch manifest root must be an object."
        )

    if manifest.get("purpose") != "AI sports-card reading":
        raise RuntimeError(
            "STOP: Directory is not identified as an "
            "AI sports-card reading batch."
        )

    if manifest.get("batch_id") != batch_root.name:
        raise RuntimeError(
            "STOP: Reading-batch manifest batch_id does not match "
            f"directory {batch_root.name}."
        )

    return manifest


def shower_batch(
    batch_root: Path,
    correction_map_path: Path,
) -> dict:
    """
    Apply an approved correction map to one disposable reading batch.

    IMPORTANT:
    Every validation and filesystem preflight check completes before
    the first image is modified.
    """

    if not batch_root.exists():
        raise RuntimeError(
            f"STOP: Reading batch not found:\n{batch_root}"
        )

    validate_reading_batch(batch_root)

    batch_id = batch_root.name
    image_root = batch_root / "images"

    if not image_root.exists():
        raise RuntimeError(
            f"STOP: Batch image directory not found:\n{image_root}"
        )

    correction_map = load_correction_map(
        correction_map_path,
        batch_id,
    )

    corrections = correction_map["corrections"]

    if not corrections:
        raise RuntimeError(
            "STOP: Correction map contains no corrections."
        )

    # ------------------------------------------------------------
    # Preflight every correction before touching any image.
    # ------------------------------------------------------------

    pairs = []

    for reading_id, correction in corrections.items():
        a_path = image_root / f"{reading_id}_a.jpg"
        b_path = image_root / f"{reading_id}_b.jpg"

        if not a_path.exists():
            raise RuntimeError(
                "STOP: Missing working a-side:\n"
                f"{a_path}"
            )

        if not b_path.exists():
            raise RuntimeError(
                "STOP: Missing working b-side:\n"
                f"{b_path}"
            )

        if correction is None:
            raise RuntimeError(
                f"STOP: Null correction for {reading_id}."
            )

        pairs.append(
            (
                reading_id,
                a_path,
                b_path,
                correction,
            )
        )

    # ------------------------------------------------------------
    # Apply only after the complete preflight passes.
    # ------------------------------------------------------------

    results = []

    for (
        reading_id,
        a_path,
        b_path,
        correction,
    ) in pairs:

        result = shower_pair(
            a_path,
            b_path,
            correction,
        )

        results.append(
            {
                "reading_id": reading_id,
                **result,
            }
        )

    provenance = {
        "schema_version": "1.0.0",
        "batch_id": batch_id,
        "correction_map": correction_map_path.name,
        "correction_basis": correction_map[
            "correction_basis"
        ],
        "review_status": correction_map[
            "review_status"
        ],
        "card_count": len(results),
        "results": results,
    }

    provenance_path = (
        batch_root
        / "TURTLE-SHOWER-PROVENANCE.json"
    )

    provenance_path.write_text(
        json.dumps(
            provenance,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return provenance


if __name__ == "__main__":
    raise SystemExit(
        "Turtle Shower is a library module. "
        "Use shower_pair() or shower_batch()."
    )
