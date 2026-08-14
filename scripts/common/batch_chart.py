"""Small durable state chart for Turtle processing batches."""

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


STATUSES = (
    "Queued",
    "Preparing",
    "Processing",
    "Checking",
    "Needs Review",
    "Ready",
    "Done",
)

STEP_RESULTS = ("pending", "passed", "failed")

ALLOWED_TRANSITIONS = {
    "Queued": {"Preparing", "Needs Review"},
    "Preparing": {"Processing", "Needs Review"},
    "Processing": {"Checking", "Needs Review"},
    "Checking": {"Ready", "Needs Review"},
    "Needs Review": {"Checking", "Ready"},
    "Ready": {"Done"},
    "Done": set(),
}

SCHEMA_VERSION = 1


class BatchChartError(ValueError):
    """Raised when a batch chart is missing or invalid."""


def _timestamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _require_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise BatchChartError(f"{field} must be a non-empty string")
    return value


def _validate_update(status, step_result, note, needs_review, review_location):
    if status not in STATUSES:
        raise BatchChartError(f"invalid status: {status}")
    if step_result not in STEP_RESULTS:
        raise BatchChartError(f"invalid step result: {step_result}")
    if not isinstance(note, str):
        raise BatchChartError("note must be a string")
    if not isinstance(needs_review, bool):
        raise BatchChartError("needs_review must be a boolean")
    if review_location is not None and not isinstance(review_location, str):
        raise BatchChartError("review_location must be a string or null")
    if status == "Needs Review" and not needs_review:
        raise BatchChartError("Needs Review requires needs_review=true")
    if needs_review and review_location is not None and not review_location.strip():
        raise BatchChartError("review_location must not be empty")
    if status == "Done" and step_result != "passed":
        raise BatchChartError("Done requires step_result=passed")


def _validate_chart(chart):
    if not isinstance(chart, dict):
        raise BatchChartError("chart must be an object")
    if chart.get("schema_version") != SCHEMA_VERSION:
        raise BatchChartError("unsupported chart schema_version")
    _require_text(chart.get("batch_id"), "batch_id")
    _require_text(chart.get("created_at"), "created_at")
    _require_text(chart.get("updated_at"), "updated_at")
    _require_text(chart.get("status_changed_at"), "status_changed_at")
    current = chart.get("current")
    history = chart.get("history")
    if not isinstance(current, dict) or not isinstance(history, list) or not history:
        raise BatchChartError("chart current state and history are required")
    _validate_update(
        current.get("status"),
        current.get("step_result"),
        current.get("note"),
        current.get("needs_review"),
        current.get("review_location"),
    )
    for entry in history:
        if not isinstance(entry, dict):
            raise BatchChartError("history entries must be objects")
        _require_text(entry.get("changed_at"), "history.changed_at")
        _validate_update(
            entry.get("status"),
            entry.get("step_result"),
            entry.get("note"),
            entry.get("needs_review"),
            entry.get("review_location"),
        )


def _write_chart(path, chart):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(chart, handle, indent=2)
            handle.write("\n")
            temporary_path = Path(handle.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def read_chart(path):
    path = Path(path)
    try:
        with path.open(encoding="utf-8") as handle:
            chart = json.load(handle)
    except FileNotFoundError as exc:
        raise BatchChartError(f"chart does not exist: {path}") from exc
    except (json.JSONDecodeError, OSError) as exc:
        raise BatchChartError(f"could not read chart: {path}") from exc
    _validate_chart(chart)
    return chart


def create_chart(path, batch_id, created_at=None):
    path = Path(path)
    if path.exists():
        raise BatchChartError(f"chart already exists: {path}")
    batch_id = _require_text(batch_id, "batch_id")
    created_at = created_at or _timestamp()
    _require_text(created_at, "created_at")
    entry = {
        "status": "Queued",
        "step_result": "pending",
        "note": "",
        "needs_review": False,
        "review_location": None,
        "changed_at": created_at,
    }
    chart = {
        "schema_version": SCHEMA_VERSION,
        "batch_id": batch_id,
        "created_at": created_at,
        "updated_at": created_at,
        "status_changed_at": created_at,
        "current": dict(entry),
        "history": [entry],
    }
    _write_chart(path, chart)
    return chart


def update_chart(
    path,
    status,
    step_result="pending",
    note="",
    needs_review=False,
    review_location=None,
    changed_at=None,
):
    chart = read_chart(path)
    _validate_update(status, step_result, note, needs_review, review_location)
    current_status = chart["current"]["status"]
    if status != current_status and status not in ALLOWED_TRANSITIONS[current_status]:
        raise BatchChartError(
            f"invalid transition: {current_status} -> {status}"
        )
    changed_at = changed_at or _timestamp()
    _require_text(changed_at, "changed_at")
    entry = {
        "status": status,
        "step_result": step_result,
        "note": note,
        "needs_review": needs_review,
        "review_location": review_location,
        "changed_at": changed_at,
    }
    chart["current"] = entry
    chart["updated_at"] = changed_at
    if status != current_status:
        chart["status_changed_at"] = changed_at
    chart["history"].append(dict(entry))
    _validate_chart(chart)
    _write_chart(path, chart)
    return chart


def _build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chart", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create")
    create.add_argument("batch_id")

    commands.add_parser("read")

    update = commands.add_parser("update")
    update.add_argument("status", choices=STATUSES)
    update.add_argument("--step-result", default="pending", choices=STEP_RESULTS)
    update.add_argument("--note", default="")
    update.add_argument("--needs-review", action="store_true")
    update.add_argument("--review-location")
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if args.command == "create":
        chart = create_chart(args.chart, args.batch_id)
    elif args.command == "read":
        chart = read_chart(args.chart)
    else:
        chart = update_chart(
            args.chart,
            args.status,
            step_result=args.step_result,
            note=args.note,
            needs_review=args.needs_review,
            review_location=args.review_location,
        )
    print(json.dumps(chart, indent=2))


if __name__ == "__main__":
    main()
