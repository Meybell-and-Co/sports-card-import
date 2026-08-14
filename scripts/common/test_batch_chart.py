"""Focused tests for the Turtle batch chart."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.common.batch_chart import (
    BatchChartError,
    create_chart,
    read_chart,
    update_chart,
)


class BatchChartTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.chart_path = Path(self.temporary_directory.name) / "batch-chart.json"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_create_read_and_valid_status_history(self):
        create_chart(self.chart_path, "turtle-2026-08-14-001", "2026-08-14T09:00:00+00:00")

        chart = read_chart(self.chart_path)
        self.assertEqual(chart["batch_id"], "turtle-2026-08-14-001")
        self.assertEqual(chart["current"]["status"], "Queued")
        self.assertEqual(chart["history"][0]["status"], "Queued")

        for index, status in enumerate(
            ("Preparing", "Processing", "Checking", "Ready", "Done"),
            start=1,
        ):
            update_chart(
                self.chart_path,
                status,
                step_result="passed",
                changed_at=f"2026-08-14T09:0{index}:00+00:00",
            )

        chart = read_chart(self.chart_path)
        self.assertEqual(
            [entry["status"] for entry in chart["history"]],
            ["Queued", "Preparing", "Processing", "Checking", "Ready", "Done"],
        )
        self.assertEqual(chart["current"]["step_result"], "passed")
        self.assertEqual(chart["status_changed_at"], "2026-08-14T09:05:00+00:00")

    def test_failure_and_review_can_return_to_processing_check(self):
        create_chart(self.chart_path, "review-case")
        update_chart(self.chart_path, "Preparing")
        update_chart(self.chart_path, "Processing")
        update_chart(self.chart_path, "Checking")
        update_chart(
            self.chart_path,
            "Needs Review",
            step_result="failed",
            note="One pair needs a human orientation check.",
            needs_review=True,
            review_location="review/inbox/review-case",
        )

        chart = read_chart(self.chart_path)
        self.assertEqual(chart["current"]["status"], "Needs Review")
        self.assertTrue(chart["current"]["needs_review"])
        self.assertEqual(chart["current"]["step_result"], "failed")
        self.assertEqual(chart["current"]["review_location"], "review/inbox/review-case")
        self.assertEqual(len(chart["history"]), 5)

        update_chart(self.chart_path, "Checking", step_result="passed")
        self.assertEqual(read_chart(self.chart_path)["current"]["status"], "Checking")

    def test_rejects_invalid_status_transition_and_malformed_update(self):
        create_chart(self.chart_path, "validation-case")
        original = self.chart_path.read_text(encoding="utf-8")

        with self.assertRaises(BatchChartError):
            update_chart(self.chart_path, "Done", step_result="passed")
        with self.assertRaises(BatchChartError):
            update_chart(self.chart_path, "Preparing", needs_review="yes")
        with self.assertRaises(BatchChartError):
            update_chart(self.chart_path, "Needs Review", step_result="failed")
        with self.assertRaises(BatchChartError):
            update_chart(self.chart_path, "Not A Status")

        self.assertEqual(self.chart_path.read_text(encoding="utf-8"), original)

    def test_persists_across_separate_cli_executions(self):
        module = Path(__file__).with_name("batch_chart.py")
        commands = [
            ["create", "separate-execution-case"],
            ["update", "Preparing"],
            ["update", "Processing"],
            ["read"],
        ]
        for command in commands:
            result = subprocess.run(
                [sys.executable, str(module), str(self.chart_path), *command],
                check=True,
                capture_output=True,
                text=True,
            )

        chart = json.loads(result.stdout)
        self.assertEqual(chart["current"]["status"], "Processing")
        self.assertEqual(
            [entry["status"] for entry in chart["history"]],
            ["Queued", "Preparing", "Processing"],
        )


if __name__ == "__main__":
    unittest.main()
