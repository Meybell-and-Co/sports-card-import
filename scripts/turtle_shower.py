"""
Turtle Shower

Pre-reader normalization for Scout & Steward card imagery.

Responsibilities:
- Work only on reading-batch copies.
- Never modify source imagery.
- Normalize front/back presentation when confidently detectable.
- Normalize readable orientation when confidently detectable.
- Preserve uncertain imagery unchanged.
- Return provenance describing every action.

IMPORTANT:
This module corrects PRESENTATION, never IDENTITY.
"""

from __future__ import annotations

from pathlib import Path


def shower_pair(
    a_path: Path,
    b_path: Path,
) -> dict:
    """
    Normalize one working reading pair.

    This first implementation establishes the interface and provenance
    contract. Detection/correction logic is added independently so the
    batch builder never needs to know how Turtle Shower makes decisions.

    Files passed here MUST already be disposable working copies.
    """

    if not a_path.exists():
        raise RuntimeError(
            f"STOP: Turtle Shower missing a-side:\n{a_path}"
        )

    if not b_path.exists():
        raise RuntimeError(
            f"STOP: Turtle Shower missing b-side:\n{b_path}"
        )

    return {
        "status": "UNCHANGED",
        "side_check": "NOT_YET_IMPLEMENTED",
        "side_swap_applied": False,
        "orientation_check": "NOT_YET_IMPLEMENTED",
        "a_rotation_applied": 0,
        "b_rotation_applied": 0,
        "review_required": False,
    }
