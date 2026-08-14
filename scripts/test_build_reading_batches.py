"""Focused tests for batch-chart integration in the reading-batch builder."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_reading_batches
from common.batch_chart import read_chart


class BuildReadingBatchesTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.output_root = self.root / "reading-batches"
        self.prompt_path = self.root / "READING-INSTRUCTIONS.md"
        self.prompt_path.write_text("reading instructions\n", encoding="utf-8")
        self.source_a = self.root / "source_a.jpg"
        self.source_b = self.root / "source_b.jpg"
        self.source_a.write_bytes(b"source-a")
        self.source_b.write_bytes(b"source-b")
        self.cards = [
            {
                "a": self.source_a,
                "b": self.source_b,
                "pair_key": "pair-001",
                "position": {"kind": "test", "slot": "01"},
                "provenance": "test",
            }
        ]

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _build(self):
        with patch.object(build_reading_batches, "OUTPUT_ROOT", self.output_root), patch.object(
            build_reading_batches,
            "READING_PROMPT",
            self.prompt_path,
        ), patch.object(
            build_reading_batches,
            "shower_pair",
            return_value={"status": "UNCHANGED"},
        ):
            return build_reading_batches.build_batches(self.cards, start_number=99)

    def test_successful_build_writes_ready_chart_without_manifest_changes(self):
        created = self._build()
        batch_root = self.output_root / "batch0099"
        manifest_path = batch_root / "manifest.json"
        chart_path = batch_root / "batch-chart.json"

        self.assertEqual(created, [("batch0099", 1)])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            set(manifest),
            {"batch_id", "purpose", "card_count", "cards"},
        )
        self.assertEqual(manifest["card_count"], 1)
        self.assertTrue(chart_path.exists())

        chart = read_chart(chart_path)
        self.assertEqual(chart["current"]["status"], "Ready")
        self.assertEqual(
            [entry["status"] for entry in chart["history"]],
            ["Queued", "Preparing", "Processing", "Checking", "Ready"],
        )
        self.assertNotIn("Done", [entry["status"] for entry in chart["history"]])

    def test_manifest_check_failure_leaves_chart_before_ready(self):
        with patch.object(
            build_reading_batches,
            "validate_written_manifest",
            side_effect=RuntimeError("manifest check failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "manifest check failed"):
                self._build()

        chart_path = self.output_root / "batch0099" / "batch-chart.json"
        chart = read_chart(chart_path)
        self.assertEqual(chart["current"]["status"], "Checking")
        self.assertEqual(
            [entry["status"] for entry in chart["history"]],
            ["Queued", "Preparing", "Processing", "Checking"],
        )


if __name__ == "__main__":
    unittest.main()
