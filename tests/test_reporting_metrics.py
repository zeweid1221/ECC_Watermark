from __future__ import annotations

import math
import unittest

from watermark_project.reporting_metrics import (
    coerce_bool,
    document_alarm_metrics,
    editor_structural_visibility_metrics,
)


class ReportingMetricsTests(unittest.TestCase):
    def test_coerce_bool_handles_csv_strings(self):
        self.assertTrue(coerce_bool("True"))
        self.assertTrue(coerce_bool("1"))
        self.assertFalse(coerce_bool("False"))
        self.assertFalse(coerce_bool("0"))
        self.assertFalse(coerce_bool(float("nan")))

    def test_document_alarm_metrics(self) -> None:
        metrics = document_alarm_metrics(
            [
                {"TP": 2, "FP": 0, "FN": 1, "TN": 5},
                {"TP": 1, "FP": 2, "FN": 0, "TN": 4},
            ]
        )
        self.assertEqual(metrics["documents_with_false_alarm"], 1)
        self.assertEqual(metrics["mean_false_blocks_per_document"], 1.0)
        self.assertEqual(metrics["document_false_alarm_rate"], 0.5)
        self.assertEqual(metrics["block_precision"], 3 / 5)

    def test_editor_visibility_separates_same_bucket_substitution(self) -> None:
        token_to_bucket = [0, 1, 0, 1, 2]
        provenance = [
            {
                "origin": "substitute",
                "original_token_index": 0,
                "original_block_id": 0,
                "replacement_offset": 0,
            },
            {"origin": "unchanged", "original_token_index": 1, "original_block_id": 0},
            {
                "origin": "substitute",
                "original_token_index": 2,
                "original_block_id": 1,
                "replacement_offset": 0,
            },
            {"origin": "unchanged", "original_token_index": 3, "original_block_id": 1},
        ]
        metrics = editor_structural_visibility_metrics(
            original_token_ids=[0, 4, 1, 4],
            original_token_block_map=[0, 0, 1, 1],
            edited_structural_symbols=[0, 2, 0, 2],
            edited_token_provenance=provenance,
            gt_block_flags=[1, 1],
            pred_block_flags=[0, 1],
            token_to_bucket=token_to_bucket,
            accepted_edit_json={
                "edits": [
                    {"op": "substitute", "index": 0},
                    {"op": "substitute", "index": 2},
                ]
            },
        )
        self.assertEqual(metrics["num_single_token_same_bucket_substitutions"], 1)
        self.assertEqual(metrics["num_single_token_cross_bucket_substitutions"], 1)
        self.assertEqual(metrics["num_structurally_visible_edited_blocks"], 1)
        self.assertEqual(metrics["num_structurally_invisible_edited_blocks"], 1)
        self.assertEqual(metrics["visible_block_tpr"], 1.0)
        self.assertEqual(metrics["invisible_block_alarm_rate"], 0.0)
        self.assertFalse(math.isnan(metrics["structural_visibility_rate"]))


if __name__ == "__main__":
    unittest.main()
