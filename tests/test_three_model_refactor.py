from __future__ import annotations

import unittest
import random
from pathlib import Path
from unittest.mock import patch

from scripts.build_qwen3_fixed_partition import word_to_single_token_id
from scripts.run_llm_editor_experiment import (
    apply_validated_token_edits_with_provenance,
    build_editor_prompt,
    build_gt_events_from_validated,
    build_text_units_from_generated_tokens,
    is_exact_token_id_noop,
    prepare_resume_records,
    retry_feedback_for_error,
    validate_and_translate_instructions,
)
from watermark_project.config import (
    AttackConfig,
    ECCConfig,
    GenerationProtocolConfig,
    GenerationSetting,
    ModelConfig,
)
from watermark_project.deployment_detection import (
    reconstruct_detector_alignment_from_final_text,
)
from watermark_project.ecc_detector import (
    EccCodebook,
    EccDecoderConfig,
    ParsedBlock,
    evaluate_predictions_multiple,
    evaluate_predictions_with_provenance,
)
from watermark_project.ecc_generator import EccGenerator
from watermark_project.edits import (
    EditEvent,
    apply_edits_to_payload_blocks,
    apply_edits_to_payload_blocks_with_provenance,
)
from watermark_project.experiment import (
    evaluate_ecc_generations,
    generation_time_ecc_blocks,
)
from watermark_project.modeling import MockLanguageModel
from watermark_project.partitioning import (
    build_vocabulary_partition,
    load_vocabulary_partition,
    save_vocabulary_partition,
    validate_vocabulary_partition,
)
from watermark_project.ppl import compute_generation_perplexities


class ThreeModelRefactorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.texts = [
            "Camera security protects people from remote access through careful software updates.",
            "People instinctively protect an injured body part to reduce movement and discomfort.",
        ]
        self.model = MockLanguageModel(
            ModelConfig(
                backend="mock",
                model_name="mock-refactor",
                mock_vocab_size=100,
                max_prompt_tokens=128,
            ),
            self.texts,
        )
        self.ecc = ECCConfig(block_len=7, vt_a=6, target_boundary_pool=6)
        self.partition = build_vocabulary_partition(self.model, self.texts, self.ecc)
        self.generator = EccGenerator(self.model, self.partition, self.ecc)
        self.protocol = GenerationProtocolConfig(
            stop_after="closed_blocks",
            sampling="greedy",
            prompt_style="plain",
            use_chat_template=False,
            ascii_token_filter=False,
        )

    def generate(self, mode: str, bias: float, target_blocks: int = 2):
        return self.generator.generate_one(
            self.texts[0],
            GenerationSetting(
                scheme="ecc",
                watermark_mode=mode,
                adaptive=True,
                target_blocks=target_blocks,
                max_new_tokens=64,
                seed=123,
                logit_bias=bias,
            ),
            protocol=self.protocol,
        )

    def test_boundary_candidate_encoding_preserves_leading_space(self) -> None:
        class WhitespaceSensitiveTokenizer:
            @staticmethod
            def encode(text, add_special_tokens=False):
                del add_special_tokens
                return [9] if text == " candidate" else [1, 2]

        class CleaningAdapter:
            tokenizer = WhitespaceSensitiveTokenizer()

            def encode(self, text, add_special_tokens=False):
                return self.tokenizer.encode(
                    text.strip(),
                    add_special_tokens=add_special_tokens,
                )

        token_id, encoded_form = word_to_single_token_id(
            CleaningAdapter(),
            "candidate",
        )
        self.assertEqual(token_id, 9)
        self.assertEqual(encoded_form, " candidate")

    def test_closed_block_stop_and_hard_feasibility(self) -> None:
        soft = self.generate("soft", 0.0)
        self.assertEqual(len(soft.generated_token_ids), 16)
        self.assertEqual(len(soft.runtime_state.block_summaries), 2)
        self.assertEqual(soft.stop_reason, "target_closed_blocks")
        hard = self.generate("hard", 20.0)
        self.assertEqual(len(hard.runtime_state.block_summaries), 2)
        self.assertTrue(
            all(item["is_valid_closed_block"] for item in hard.runtime_state.block_summaries)
        )
        with self.assertRaisesRegex(ValueError, "need at least 16"):
            self.generator.generate_one(
                self.texts[0],
                GenerationSetting("ecc", "soft", True, 2, 15, 123, 0.0),
                protocol=self.protocol,
            )

    def test_partition_identity_and_semantic_guard(self) -> None:
        output_dir = Path("outputs/test_partition_roundtrip")
        save_vocabulary_partition(self.partition, output_dir)
        loaded = load_vocabulary_partition(output_dir)
        validate_vocabulary_partition(
            loaded,
            self.model,
            require_semantic_split=True,
        )
        other = MockLanguageModel(
            ModelConfig(
                backend="mock",
                model_name="different-model",
                mock_vocab_size=100,
            ),
            self.texts,
        )
        with self.assertRaisesRegex(ValueError, "different model"):
            validate_vocabulary_partition(loaded, other)

    def test_boundary_edit_and_same_bucket_noop_are_accepted(self) -> None:
        result = self.generate("hard", 20.0)
        blocks = [
            list(item["bits_prefix_capped"])
            for item in result.runtime_state.block_summaries
        ]
        units, token_ids, _, _ = build_text_units_from_generated_tokens(
            self.model,
            result.generated_token_ids,
            result.generated_bucket_seq,
            blocks,
        )
        boundary = next(unit for unit in units if unit.approx_bucket_id == 2)
        replacement_id = self.partition.bucket0_ids[0]
        parsed = {
            "edits": [
                {
                    "op": "substitute",
                    "index": boundary.index,
                    "original_text": boundary.surface,
                    "new_content": self.model.token_surface(replacement_id),
                    "reason": "boundary regression",
                }
            ]
        }
        validated, error = validate_and_translate_instructions(
            parsed,
            "grammar_polish",
            "benign",
            units,
            token_ids,
            blocks,
            self.partition,
            self.model,
            2,
            1,
            2,
            0.9,
        )
        self.assertIsNone(error)
        edited_ids, observed, provenance = apply_validated_token_edits_with_provenance(
            token_ids,
            units,
            validated,
            self.partition,
        )
        self.assertEqual(
            observed,
            [int(self.partition.token_to_bucket[token_id]) for token_id in edited_ids],
        )
        self.assertEqual(len(provenance), len(observed))

        payload = next(unit for unit in units if unit.approx_bucket_id in (0, 1))
        bucket = (
            self.partition.bucket0_ids
            if payload.approx_bucket_id == 0
            else self.partition.bucket1_ids
        )
        same_bucket_id = next(
            token_id
            for token_id in bucket
            if token_id != payload.token_id
            and self.model.token_surface(token_id) != payload.surface
        )
        parsed["edits"][0] = {
            "op": "substitute",
            "index": payload.index,
            "original_text": payload.surface,
            "new_content": self.model.token_surface(same_bucket_id),
            "reason": "same bucket regression",
        }
        validated, error = validate_and_translate_instructions(
            parsed,
            "clarity_improvement",
            "benign",
            units,
            token_ids,
            blocks,
            self.partition,
            self.model,
            2,
            1,
            2,
            0.9,
        )
        self.assertIsNone(error)
        edited_ids, observed, _ = apply_validated_token_edits_with_provenance(
            token_ids,
            units,
            validated,
            self.partition,
        )
        self.assertNotEqual(edited_ids[payload.index], token_ids[payload.index])
        self.assertEqual(observed[payload.index], result.generated_bucket_seq[payload.index])
        self.assertEqual(
            sum(len(events) for events in build_gt_events_from_validated(validated, len(blocks))),
            1,
        )

        parsed["edits"][0] = {
            "op": "substitute",
            "index": payload.index,
            "original_text": payload.surface,
            "new_content": "different alias",
            "reason": "exact token ID no-op regression",
        }
        with patch(
            "scripts.run_llm_editor_experiment.tokenize_new_content",
            return_value=[payload.token_id],
        ):
            validated, error = validate_and_translate_instructions(
                parsed,
                "clarity_improvement",
                "benign",
                units,
                token_ids,
                blocks,
                self.partition,
                self.model,
                2,
                1,
                2,
                0.9,
            )
        self.assertEqual(validated, [])
        self.assertEqual(error, "substitute_same_token_id")

        with patch(
            "scripts.run_llm_editor_experiment.tokenize_new_content",
            return_value=[payload.token_id, same_bucket_id],
        ):
            validated, error = validate_and_translate_instructions(
                parsed,
                "clarity_improvement",
                "benign",
                units,
                token_ids,
                blocks,
                self.partition,
                self.model,
                2,
                1,
                2,
                0.9,
            )
        self.assertIsNone(error)
        self.assertTrue(is_exact_token_id_noop(payload.token_id, [payload.token_id]))
        self.assertFalse(
            is_exact_token_id_noop(
                payload.token_id,
                [payload.token_id, same_bucket_id],
            )
        )

        editor_prompt = build_editor_prompt(
            prompt=self.texts[0],
            suffix_text=result.suffix_text,
            motivation="grammar_polish",
            intent_label="benign",
            units=units,
            max_edited_blocks=2,
        )
        self.assertIn("bucket_id is 0, 1, or 2", editor_prompt)
        self.assertIn("STRICT NO-OP RULE", editor_prompt)
        retry_prompt = build_editor_prompt(
            prompt=self.texts[0],
            suffix_text=result.suffix_text,
            motivation="grammar_polish",
            intent_label="benign",
            units=units,
            max_edited_blocks=2,
            retry_feedback=retry_feedback_for_error("substitute_no_text_change"),
        )
        self.assertIn("same normalized text", retry_prompt)
        token_retry_prompt = build_editor_prompt(
            prompt=self.texts[0],
            suffix_text=result.suffix_text,
            motivation="grammar_polish",
            intent_label="benign",
            units=units,
            max_edited_blocks=2,
            retry_feedback=retry_feedback_for_error("substitute_same_token_id"),
        )
        self.assertIn("exactly the selected original token ID", token_retry_prompt)

    def test_retry_skipped_resume_retains_only_accepted_rows(self) -> None:
        details = [
            {
                "sequence_index": 0,
                "motivation": "grammar_polish",
                "used": True,
            },
            {
                "sequence_index": 1,
                "motivation": "claim_distortion",
                "used": False,
                "skip_reason": "substitute_no_text_change",
            },
        ]
        instructions = [
            {
                "sequence_index": 0,
                "motivation": "grammar_polish",
                "used": True,
            },
            {
                "sequence_index": 1,
                "motivation": "claim_distortion",
                "used": False,
            },
        ]
        retained_details, retained_instructions, completed = prepare_resume_records(
            details,
            instructions,
            retry_skipped=True,
        )
        self.assertEqual(len(retained_details), 1)
        self.assertEqual(len(retained_instructions), 1)
        self.assertEqual(completed, {(0, "grammar_polish")})

    def test_provenance_merges_split_parses_to_source_blocks(self) -> None:
        codebook = EccCodebook(7, 6)
        blocks = [codebook.feasible[0], codebook.feasible[1]]
        gt = [[], [EditEvent("sub", ("payload", 0), 0, 1)]]
        predictions = [
            ParsedBlock(
                blocks[0][:3],
                False,
                "none",
                [],
                blocks[0],
                info={
                    "payload_distance": 0,
                    "observed_span_start": 0,
                    "observed_span_end_exclusive": 3,
                },
            ),
            ParsedBlock(
                blocks[0][3:],
                False,
                "none",
                [],
                blocks[0],
                info={
                    "payload_distance": 0,
                    "observed_span_start": 3,
                    "observed_span_end_exclusive": 8,
                    "observed_boundary_index": 7,
                },
            ),
            ParsedBlock(
                blocks[1],
                True,
                "sub",
                [("payload", 0)],
                blocks[1],
                info={
                    "payload_distance": 1,
                    "observed_span_start": 8,
                    "observed_span_end_exclusive": 15,
                    "observed_boundary_index": 15,
                },
            ),
        ]
        provenance = [
            {
                "original_block_id": index // 8,
                "original_structural_index": index,
            }
            for index in range(16)
        ]
        old = evaluate_predictions_multiple(blocks, gt, predictions, 0, codebook)
        new = evaluate_predictions_with_provenance(
            blocks,
            gt,
            predictions,
            provenance,
            0,
            codebook,
        )
        self.assertEqual((old["TP"], old["FP"], old["FN"]), (0, 1, 1))
        self.assertEqual((new["TP"], new["FP"], new["FN"]), (1, 0, 0))
        self.assertEqual(new["parsed_to_source_blocks"], [[0], [0], [1]])
        self.assertEqual(new["event_coverage_overall"], 1.0)

    def test_synthetic_provenance_preserves_attacked_sequence_and_net_gt(self) -> None:
        codebook = EccCodebook(7, 6)
        blocks = [codebook.feasible[0], codebook.feasible[1]]
        found_net_zero = False
        for seed in range(2000):
            old = apply_edits_to_payload_blocks(
                blocks,
                edit_rate=1.0,
                allow_boundary_edit=True,
                boundary_edit_modes=("delete", "sub"),
                max_edits_per_block=3,
                edit_count_mode="fixed_k",
                boundary_symbol=2,
                rng=random.Random(seed),
            )
            new = apply_edits_to_payload_blocks_with_provenance(
                blocks,
                edit_rate=1.0,
                allow_boundary_edit=True,
                boundary_edit_modes=("delete", "sub"),
                max_edits_per_block=3,
                edit_count_mode="fixed_k",
                boundary_symbol=2,
                rng=random.Random(seed),
            )
            self.assertEqual(old[0], new[0])
            self.assertEqual(old[2], new[2])
            self.assertEqual(len(new[2]), len(new[3]))
            for block_id, (payload, observed, old_events, net_events) in enumerate(
                zip(blocks, old[0], old[1], new[1])
            ):
                if old_events and observed == payload + [2]:
                    found_net_zero = True
                    self.assertEqual(net_events, [], msg=f"block={block_id}, seed={seed}")
            if found_net_zero:
                break
        self.assertTrue(found_net_zero)

    def test_core_runner_uses_final_net_edit_ground_truth(self) -> None:
        result = self.generate("hard", 20.0, target_blocks=2)
        blocks = generation_time_ecc_blocks(result, self.ecc.block_len, max_blocks=2)
        attack = AttackConfig(
            edit_rate=1.0,
            allow_boundary_edit=True,
            boundary_edit_modes=("delete", "sub"),
            attack_max_edits_per_block=3,
            edit_count_mode="fixed_k",
        )
        calibration_seed = None
        old_positive = net_positive = 0
        for seed in range(2000):
            old = apply_edits_to_payload_blocks(
                blocks,
                edit_rate=attack.edit_rate,
                allow_boundary_edit=attack.allow_boundary_edit,
                boundary_edit_modes=attack.boundary_edit_modes,
                max_edits_per_block=attack.attack_max_edits_per_block,
                edit_count_mode=attack.edit_count_mode,
                boundary_symbol=self.generator.codebook.boundary_symbol,
                rng=random.Random(seed),
            )
            new = apply_edits_to_payload_blocks_with_provenance(
                blocks,
                edit_rate=attack.edit_rate,
                allow_boundary_edit=attack.allow_boundary_edit,
                boundary_edit_modes=attack.boundary_edit_modes,
                max_edits_per_block=attack.attack_max_edits_per_block,
                edit_count_mode=attack.edit_count_mode,
                boundary_symbol=self.generator.codebook.boundary_symbol,
                rng=random.Random(seed),
            )
            old_positive = sum(bool(events) for events in old[1])
            net_positive = sum(bool(events) for events in new[1])
            if net_positive < old_positive:
                calibration_seed = seed
                break
        self.assertIsNotNone(calibration_seed)

        summary, details = evaluate_ecc_generations(
            [result],
            self.generator,
            attack,
            decoder_budget=3,
            seed=int(calibration_seed),
            target_blocks=2,
            tolerance=0,
        )
        self.assertEqual(summary["TP"] + summary["FN"], net_positive)
        self.assertLess(summary["TP"] + summary["FN"], old_positive)
        self.assertEqual(summary["gt_semantics"], "final_net_structural_edits")
        self.assertEqual(
            summary["candidate_coordinate_system"],
            "feasible_reference_codeword",
        )
        self.assertEqual(details[0]["gt_semantics"], "final_net_structural_edits")

    def test_reference_candidate_survives_deleted_observed_tail(self) -> None:
        codebook = EccCodebook(7, 6)
        block = codebook.feasible[0]
        gt = [[EditEvent("delete", ("payload", 6), block[6], None)]]
        prediction = ParsedBlock(
            block_tokens=block[:6],
            flag=True,
            etype="delete",
            candidates=[("payload", 6)],
            decoded_codeword=block,
            info={
                "payload_distance": 1,
                "observed_span_start": 0,
                "observed_span_end_exclusive": 6,
            },
        )
        provenance = [
            {
                "original_block_id": 0,
                "original_structural_index": index,
            }
            for index in range(6)
        ]
        result = evaluate_predictions_with_provenance(
            [block],
            gt,
            [prediction],
            provenance,
            0,
            codebook,
        )
        self.assertEqual(result["event_loc_hit"], 1)
        self.assertEqual(result["source_candidate_locations"], [[["payload", 6]]])

    def test_dual_ppl_and_final_text_reconstruction(self) -> None:
        result = self.generate("hard", 20.0)
        ppl = compute_generation_perplexities(
            self.model,
            [result.prompt_token_ids],
            [result.generated_token_ids],
        )
        self.assertTrue(all(value > 0 for value in ppl.values()))
        reconstructed = reconstruct_detector_alignment_from_final_text(
            result.suffix_text,
            self.model,
            self.partition,
            self.generator.codebook,
            EccDecoderConfig(3, ("delete", "sub")),
            tolerance=0,
        )
        self.assertEqual(
            reconstructed["edited_structural_sequence"],
            result.structural_seq,
        )
        self.assertTrue(reconstructed["pred_blocks_detailed"])
        self.assertTrue(reconstructed["detector_aligned_block_text_spans"])


if __name__ == "__main__":
    unittest.main()
