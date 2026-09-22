from __future__ import annotations

import unittest

import numpy as np

from watermark_project.config import ECCConfig, GenerationProtocolConfig, GenerationSetting, ModelConfig, RunConfig
from watermark_project.ecc_generator import EccGenerator
from watermark_project.modeling import MockLanguageModel
from watermark_project.partitioning import (
    build_payload_buckets,
    build_payload_buckets_paper_main,
    build_payload_buckets_quality_variant_lsh,
    build_vocabulary_partition,
    validate_vocabulary_partition,
)


class BoundaryFractionProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.texts = [
            "A boundary-aware ECC watermark should preserve fluent explanatory text.",
            "Adaptive generation keeps each partial payload near a feasible codeword.",
            "The remaining vocabulary is divided evenly between two payload symbols.",
        ]
        self.model = MockLanguageModel(
            ModelConfig(backend="mock", model_name="fraction-test", mock_vocab_size=240),
            self.texts,
        )

    def test_default_partition_assigns_one_eighth_to_boundary(self) -> None:
        config = ECCConfig(block_len=7, vt_a=6)
        first = build_vocabulary_partition(self.model, self.texts, config)
        second = build_vocabulary_partition(self.model, self.texts, config)
        eligible = self.model.vocab_size - len(set(self.model.all_special_ids))
        expected_boundary = round(eligible / 8)

        self.assertEqual(len(first.boundary_ids), expected_boundary)
        self.assertLessEqual(abs(len(first.bucket0_ids) - len(first.bucket1_ids)), 1)
        self.assertEqual(
            len(first.bucket0_ids) + len(first.bucket1_ids) + len(first.boundary_ids),
            eligible,
        )
        self.assertEqual(first.metadata["boundary_allocation_strategy"], "eligible_vocab_fraction")
        self.assertEqual(first.metadata["payload_split_strategy"], "quality_variant_lsh")
        self.assertAlmostEqual(first.metadata["boundary_vocab_fraction_requested"], 1.0 / 8.0)
        np.testing.assert_array_equal(first.token_to_bucket, second.token_to_bucket)
        validate_vocabulary_partition(first, self.model, require_semantic_split=True)

    def test_explicit_fixed_boundary_count_remains_available(self) -> None:
        partition = build_vocabulary_partition(
            self.model,
            self.texts,
            ECCConfig(block_len=7, vt_a=6, target_boundary_pool=6),
        )
        self.assertEqual(len(partition.boundary_ids), 6)
        self.assertEqual(partition.metadata["boundary_allocation_strategy"], "fixed_count")

    def test_semantic_group_orientation_balances_payload_counts_globally(self) -> None:
        eligible = [
            token_id
            for token_id in range(self.model.vocab_size)
            if token_id not in set(self.model.all_special_ids)
        ][:9]
        semantic_groups = {
            group_id: eligible[group_id * 3 : (group_id + 1) * 3]
            for group_id in range(3)
        }
        freq = np.zeros(self.model.vocab_size, dtype=np.int64)
        for members in semantic_groups.values():
            freq[members] = np.array([9, 5, 1], dtype=np.int64)

        bucket0, bucket1 = build_payload_buckets(
            model=self.model,
            freq=freq,
            boundary_ids=[],
            config=ECCConfig(block_len=7, vt_a=6),
            semantic_groups=semantic_groups,
        )

        self.assertLessEqual(abs(len(bucket0) - len(bucket1)), 1)
        self.assertEqual(set(bucket0) | set(bucket1), set(eligible))
        self.assertFalse(set(bucket0) & set(bucket1))

    def test_paper_main_and_quality_variant_lsh_preserve_distinct_group_orientation(self) -> None:
        eligible = [
            token_id
            for token_id in range(self.model.vocab_size)
            if token_id not in set(self.model.all_special_ids)
        ][:4]
        semantic_groups = {0: eligible[:2], 1: eligible[2:]}
        freq = np.zeros(self.model.vocab_size, dtype=np.int64)
        freq[eligible] = np.array([10, 1, 9, 1], dtype=np.int64)

        paper0, paper1 = build_payload_buckets_paper_main(
            model=self.model,
            freq=freq,
            boundary_ids=[],
            config=ECCConfig(payload_split_strategy="paper_main"),
            semantic_groups=semantic_groups,
        )
        quality0, quality1 = build_payload_buckets_quality_variant_lsh(
            model=self.model,
            freq=freq,
            boundary_ids=[],
            config=ECCConfig(payload_split_strategy="quality_variant_lsh"),
            semantic_groups=semantic_groups,
        )

        paper_mass_gap = abs(int(freq[paper0].sum()) - int(freq[paper1].sum()))
        quality_mass_gap = abs(int(freq[quality0].sum()) - int(freq[quality1].sum()))
        self.assertGreater(paper_mass_gap, quality_mass_gap)
        self.assertEqual(set(paper0) | set(paper1), set(eligible))
        self.assertEqual(set(quality0) | set(quality1), set(eligible))

    def test_paper_main_strategy_is_recorded_in_partition_metadata(self) -> None:
        partition = build_vocabulary_partition(
            self.model,
            self.texts,
            ECCConfig(
                target_boundary_pool=6,
                payload_split_strategy="paper_main",
            ),
        )
        self.assertEqual(partition.metadata["payload_split_strategy"], "paper_main")

    def test_default_adaptive_generation_closes_feasible_blocks(self) -> None:
        config = ECCConfig(block_len=7, vt_a=6)
        partition = build_vocabulary_partition(self.model, self.texts, config)
        generator = EccGenerator(self.model, partition, config)
        setting = GenerationSetting(
            scheme="ecc",
            watermark_mode="hard",
            adaptive=True,
            target_blocks=3,
            max_new_tokens=32,
            seed=20260813,
            logit_bias=20.0,
        )
        result = generator.generate_one(
            self.texts[0],
            setting,
            protocol=GenerationProtocolConfig(
                stop_after="closed_blocks",
                sampling="greedy",
                prompt_style="plain",
                use_chat_template=False,
                ascii_token_filter=False,
            ),
        )
        self.assertEqual(len(result.runtime_state.block_summaries), 3)
        self.assertTrue(
            all(block["is_valid_closed_block"] for block in result.runtime_state.block_summaries)
        )
        self.assertEqual(RunConfig(output_dir="unused").ecc_adaptive_modes, [True])


if __name__ == "__main__":
    unittest.main()
