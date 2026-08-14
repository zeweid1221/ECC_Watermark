from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.run_global_watermark_verification import (
    TokenizerOnlyModel,
    build_payload_distance_lookup,
    estimate_block_count,
    score_serialized_phase,
)
from watermark_project.ecc_detector import EccCodebook


class GlobalWatermarkVerificationTests(unittest.TestCase):
    @patch("scripts.run_global_watermark_verification.AutoTokenizer.from_pretrained")
    def test_final_text_tokenizer_splits_literal_special_tokens(self, load_tokenizer) -> None:
        TokenizerOnlyModel("test-model", local_files_only=True)

        load_tokenizer.assert_called_once_with(
            "test-model",
            use_fast=True,
            local_files_only=True,
            split_special_tokens=True,
        )

    def test_block_count_is_estimated_from_final_token_length(self) -> None:
        self.assertEqual(estimate_block_count(144, 7), 18)
        self.assertEqual(estimate_block_count(140, 7), 18)
        self.assertEqual(estimate_block_count(148, 7), 19)

    def test_serialized_distance_uses_payload_and_boundary_evidence(self) -> None:
        codebook = EccCodebook(block_len=7, vt_a=6)
        lookup = build_payload_distance_lookup(codebook)
        exact_sequence = codebook.feasible[0] + [codebook.boundary_symbol]
        exact = score_serialized_phase(
            exact_sequence,
            phase=0,
            estimated_blocks=1,
            tolerance=0,
            codebook=codebook,
            payload_distance_lookup=lookup,
        )
        self.assertIsNotNone(exact)
        self.assertEqual(exact["raw_alignment_cost"], 0)
        self.assertEqual(exact["global_score"], 1.0)

        wrong_boundary = score_serialized_phase(
            codebook.feasible[0] + [0],
            phase=0,
            estimated_blocks=1,
            tolerance=0,
            codebook=codebook,
            payload_distance_lookup=lookup,
        )
        self.assertIsNotNone(wrong_boundary)
        self.assertEqual(wrong_boundary["raw_alignment_cost"], 1)
        self.assertEqual(wrong_boundary["block_costs"][0]["boundary_cost"], 1)


if __name__ == "__main__":
    unittest.main()
