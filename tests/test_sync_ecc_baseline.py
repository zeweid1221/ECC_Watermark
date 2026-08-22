from __future__ import annotations

import inspect
from pathlib import Path
import random
import unittest

from baselines.sync_ecc import (
    SyncEccConfig,
    SyncEccSchedule,
    SyncEccWatermark,
    assign_insertions_to_neighbor_block,
    apply_sync_attacks,
    build_vt_codebook,
    evaluate_sync_blocks,
    nearest_codeword_candidates,
    vt_syndrome,
)
from watermark_project.config import GenerationProtocolConfig, ModelConfig
from watermark_project.modeling import build_language_model


class SyncEccBaselineTests(unittest.TestCase):
    def setUp(self):
        self.config = SyncEccConfig()
        self.schedule = SyncEccSchedule(512, self.config)

    def test_matches_accepted_source_key_schedule_fixture(self):
        expected_buckets = [
            7, 5, 4, 4, 6, 6, 3, 5, 1, 7, 2, 2, 0, 0, 1, 3,
            3, 1, 0, 1, 2, 2, 7, 6, 5, 3, 6, 7, 4, 4, 5, 4,
        ]
        expected_sync = [3, 1, 2, 0, 2, 2, 1, 3, 0, 3, 1, 0, 2, 1, 0, 1]
        self.assertEqual(self.schedule.base_bucket_ids[:32].tolist(), expected_buckets)
        self.assertEqual([self.schedule.sync_symbol(i) for i in range(16)], expected_sync)
        self.assertEqual(self.schedule.bucket_permutation(0), [1, 4, 0, 2, 7, 6, 3, 5])
        self.assertEqual(self.schedule.bucket_permutation(1), [6, 3, 1, 7, 0, 2, 5, 4])
        self.assertEqual(self.schedule.bucket_permutation(7), [1, 7, 2, 0, 4, 6, 5, 3])

    def test_vt4_codebook_matches_accepted_protocol(self):
        codebook = build_vt_codebook(7, 4)
        self.assertEqual(len(codebook), 16)
        self.assertEqual(codebook[0], [0, 0, 0, 0, 1, 0, 1])
        self.assertEqual(codebook[-1], [1, 1, 1, 1, 1, 1, 1])
        self.assertTrue(all(vt_syndrome(word) % 8 == 4 for word in codebook))

    def _tokens_for_codewords(self, codewords):
        result = []
        for step, bit in enumerate(bit for word in codewords for bit in word):
            target_bucket = int(bit) * self.config.sigma_size + self.schedule.sync_symbol(step)
            base_bucket = self.schedule.base_bucket_for_target(target_bucket, step)
            token_id = next(
                token
                for token in range(self.schedule.vocab_size)
                if int(self.schedule.base_bucket_ids[token]) == base_bucket
            )
            result.append(token_id)
        return result

    def test_clean_alignment_and_indel_detection(self):
        model = build_language_model(ModelConfig(backend="mock", mock_vocab_size=512))
        method = SyncEccWatermark(
            model,
            self.config,
            GenerationProtocolConfig(ascii_token_filter=False),
        )
        codewords = [self.schedule.codebook[3], self.schedule.codebook[10]]
        clean = self._tokens_for_codewords(codewords)
        clean_detection = method.detect(clean, expected_blocks=2)
        self.assertEqual(clean_detection.alignment.distance, 0)
        self.assertEqual(clean_detection.predicted_blocks, [])

        deleted = clean[:3] + clean[4:]
        deletion_detection = method.detect(deleted, expected_blocks=2)
        self.assertIn(0, deletion_detection.predicted_blocks)
        self.assertTrue(
            any(
                abs(position - 3) <= 1
                for position in deletion_detection.alignment.deletion_expected_positions
            )
        )

        inserted = clean[:9] + [clean[0]] + clean[9:]
        insertion_detection = method.detect(inserted, expected_blocks=2)
        self.assertGreaterEqual(insertion_detection.alignment.distance, 1)
        self.assertTrue(insertion_detection.predicted_blocks)

    def test_hard_generation_and_attack_evaluation(self):
        prompts = [
            "Structured watermark evaluation compares detection reliability and language quality.",
            "Synchronization strings can recover positions after sparse insertions and deletions.",
        ]
        model = build_language_model(
            ModelConfig(backend="mock", mock_vocab_size=256),
            corpus_texts=prompts,
        )
        method = SyncEccWatermark(
            model,
            self.config,
            GenerationProtocolConfig(
                sampling="sample",
                top_k=40,
                top_p=0.9,
                ascii_token_filter=False,
            ),
        )
        codewords = method.schedule.sample_codewords(1, 3)[0]
        generated = method.generate_one(
            prompts[0],
            codewords=codewords,
            logit_bias=20,
            hard=True,
            max_new_tokens=21,
            seed=7,
        )
        self.assertEqual(len(generated.generated_token_ids), 21)
        self.assertEqual(generated.tag_adherence, 1.0)
        self.assertEqual(generated.clean_vt_valid_rate, 1.0)
        self.assertEqual(method.detect(generated.generated_token_ids, 3).predicted_blocks, [])

        usable = [
            token
            for token in range(model.vocab_size)
            if token not in set(model.all_special_ids)
        ]
        attacked = apply_sync_attacks(
            generated.block_tokens,
            edit_rate=1.0,
            max_edits_per_block=1,
            edit_count_mode="fixed_k",
            attack_type="delete",
            vocab_ids=usable,
            schedule=method.schedule,
            rng=random.Random(19),
        )
        detection = method.detect(attacked.observed_token_ids, 3)
        evaluation = evaluate_sync_blocks(detection, attacked.gt_events_per_block, 3)
        self.assertEqual(evaluation["TP"] + evaluation["FN"], 3)
        self.assertGreater(evaluation["TP"], 0)

    def test_vt_candidates_are_separate_from_sync_block_alarm(self):
        codeword = self.schedule.codebook[3]
        observed = codeword[:2] + codeword[3:]
        selected, distance, candidates = nearest_codeword_candidates(
            observed,
            self.schedule.codebook,
            self.config.block_len,
        )
        self.assertEqual(selected, codeword)
        self.assertEqual(distance, 1)
        self.assertTrue(candidates)
        self.assertTrue(all(edit_type == "delete" for edit_type, _ in candidates))

    def test_insertions_prefer_previous_neighbor_block(self):
        self.assertEqual(
            assign_insertions_to_neighbor_block([-1, 0, -1, 1, -1]),
            [0, 0, 0, 1, 1],
        )

    def test_public_baseline_has_no_bytecode_or_legacy_loader(self):
        source = inspect.getsource(__import__("baselines.sync_ecc", fromlist=["*"]))
        self.assertNotIn("SourcelessFileLoader", source)
        self.assertNotIn("legacy_runtime", source)
        self.assertNotIn(".pyc", source)

    def test_msi_launcher_locks_full_lfqa_protocol(self):
        root = Path(__file__).resolve().parents[1]
        launcher = (root / "msi" / "run_qwen3_sync_ecc_lfqa.slurm").read_text(
            encoding="utf-8"
        )
        required_fragments = [
            "--model-profile \"$PROFILE\"",
            "--num-samples 256",
            "--logit-bias-values \"2,5,20\"",
            "--target-blocks 18",
            "--attack-types \"insert,delete,substitute\"",
            "--edit-rates \"0.2,0.4,0.6,0.8\"",
            "--attack-max-edits-per-blocks \"1,2,3\"",
            "--strict-interior-insertions",
            "python -m unittest tests.test_sync_ecc_baseline -v",
            "python scripts/validate_sync_ecc_lfqa_results.py",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, launcher)
        self.assertNotIn("legacy_runtime", launcher)
        self.assertNotIn(".pyc", launcher)


if __name__ == "__main__":
    unittest.main()
