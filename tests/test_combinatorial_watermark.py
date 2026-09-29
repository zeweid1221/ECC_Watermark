from __future__ import annotations

import unittest

import numpy as np

from baselines.combinatorial_watermark import (
    CombinatorialConfig,
    CombinatorialWatermark,
    calibrate_lower_tail_threshold,
    calibrate_strict_lower_tail_threshold,
    complete_mismatch_threshold,
    context_color_vector,
    context_token_color,
    cyclic_window_indicators,
    evaluate_combinatorial_blocks,
    local_edit_scores,
)
from watermark_project.config import GenerationProtocolConfig, ModelConfig
from watermark_project.modeling import MockLanguageModel


class CombinatorialWatermarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prompts = [
            "Why does touching an injured area sometimes reduce discomfort?",
            "How can software updates improve the security of a webcam?",
        ]
        self.model = MockLanguageModel(
            ModelConfig(
                backend="mock",
                model_name="mock-combinatorial",
                mock_vocab_size=96,
                max_prompt_tokens=128,
            ),
            self.prompts,
        )
        self.protocol = GenerationProtocolConfig(
            sampling="greedy",
            prompt_style="plain",
            use_chat_template=False,
            ascii_token_filter=False,
        )

    def test_context_partition_is_total_deterministic_and_contextual(self) -> None:
        first = context_color_vector(101, 7, 3779, 4)
        second = context_color_vector(101, 7, 3779, 4)
        changed = context_color_vector(101, 8, 3779, 4)
        self.assertTrue(np.array_equal(first, second))
        self.assertFalse(np.array_equal(first, changed))
        self.assertEqual(set(first.tolist()), {0, 1, 2, 3})
        for token_id, color in enumerate(first):
            self.assertEqual(
                int(color),
                context_token_color(token_id, 7, 3779, 4),
            )

    def test_ab_and_acadbcbd_cyclic_windows(self) -> None:
        ab = cyclic_window_indicators([1, 0, 1, 0], (0, 1), 2)
        self.assertEqual(ab.tolist(), [1, 1, 1])
        acadbcbd = (0, 2, 0, 3, 1, 2, 1, 3)
        rotated = acadbcbd[3:] + acadbcbd[:3]
        indicators = cyclic_window_indicators(rotated, acadbcbd, 8)
        self.assertEqual(indicators.tolist(), [1])
        corrupted = list(rotated)
        corrupted[4] = (corrupted[4] + 1) % 4
        self.assertEqual(
            cyclic_window_indicators(corrupted, acadbcbd, 8).tolist(),
            [0],
        )

    def test_local_scores_and_threshold(self) -> None:
        scores = local_edit_scores(4, [1, 0, 1], 2)
        self.assertEqual(scores.tolist(), [1.0, 0.5, 0.5, 1.0])
        threshold = calibrate_lower_tail_threshold(
            [0.25, 0.5, 0.75, 1.0],
            0.25,
        )
        self.assertEqual(threshold, 0.25)
        strict_threshold = calibrate_strict_lower_tail_threshold(
            [0.25, 0.5, 0.75, 1.0],
            0.25,
        )
        self.assertEqual(strict_threshold, 0.5)

    def test_original_threshold_maps_strict_token_alarms_to_blocks(self) -> None:
        for threshold_mode in (
            "fixed_complete_mismatch",
            "clean_type_i_0.1",
            "original_token",
        ):
            evaluation = evaluate_combinatorial_blocks(
                original_blocks=[[10, 11], [12, 13]],
                observed_blocks=[[10, 11], [12, 13]],
                origin_maps_per_block=[[0, 1], [0, 1]],
                gt_events_per_block=[[], []],
                local_scores=[0.5, 0.8, 0.49, 0.8],
                token_threshold=0.5,
                threshold_mode=threshold_mode,
            )
            self.assertEqual(evaluation["pred_blocks"], [0, 1])
            self.assertEqual(evaluation["FP"], 1)
            self.assertEqual(evaluation["TN"], 1)

    def test_complete_mismatch_threshold_depends_only_on_pattern_length(self) -> None:
        self.assertEqual(complete_mismatch_threshold("AB"), 0.5)
        self.assertEqual(complete_mismatch_threshold("ACADBCBD"), 0.125)

    def test_generation_has_exact_evaluation_blocks_for_both_patterns(self) -> None:
        for pattern in ("AB", "ACADBCBD"):
            method = CombinatorialWatermark(
                self.model,
                CombinatorialConfig(
                    pattern_name=pattern,
                    evaluation_block_len=8,
                ),
                self.protocol,
            )
            result = method.generate_one(
                self.prompts[0],
                logit_bias=5.0,
                target_blocks=3,
                max_new_tokens=24,
                seed=123,
            )
            self.assertEqual(len(result.generated_token_ids), 24)
            self.assertEqual(len(result.block_tokens), 3)
            self.assertTrue(all(len(block) == 8 for block in result.block_tokens))
            rescored = method.score_tokens(
                result.generated_token_ids,
                result.prompt_token_ids[-1],
            )
            self.assertEqual(rescored["colors"], result.generated_colors)


if __name__ == "__main__":
    unittest.main()
