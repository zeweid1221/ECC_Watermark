from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Sequence, Tuple

import pandas as pd

from .config import AttackConfig, GenerationSetting, RunConfig
from .ecc_detector import EccDecoderConfig, detect_sequence_multiple, evaluate_predictions_multiple
from .ecc_generator import EccGenerationResult, EccGenerator
from .edits import apply_edits_to_payload_blocks, apply_token_edits_to_blocks
from .io_utils import ensure_dir, save_dataframe, save_prompts, to_jsonable, write_json
from .kgw_evaluator import evaluate_kgw_blocks
from .kgw_generator import KgwGenerationResult, KgwGenerator
from .modeling import build_language_model, sample_prompts_from_config
from .partitioning import build_vocabulary_partition
from .ppl import compute_text_perplexity


def evaluate_ecc_generations(
    results: Sequence[EccGenerationResult],
    generator: EccGenerator,
    attack: AttackConfig,
    decoder_budget: int,
    seed: int,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    detail_rows: List[Dict[str, Any]] = []
    used_sequences = 0
    skipped_sequences = 0
    valid_blocks_total = 0
    tp = fp = fn = tn = 0
    codeword_hits = codeword_total = 0
    loc_hits = loc_total = 0
    event_hits = event_total = 0
    event_sub_hit = event_sub_total = 0
    event_ins_hit = event_ins_total = 0
    event_del_hit = event_del_total = 0
    cand_weighted_sum = 0.0
    cand_weighted_n = 0
    for idx, result in enumerate(results):
        original_payload_blocks = [list(block) for block in result.decoded_clean["valid_blocks"]]
        if not original_payload_blocks:
            skipped_sequences += 1
            detail_rows.append({"sequence_index": idx, "used": False, "skip_reason": "no_valid_blocks"})
            continue
        used_sequences += 1
        valid_blocks_total += len(original_payload_blocks)
        rng = random.Random(seed + idx)
        _, gt_events_per_block, observed_sequence = apply_edits_to_payload_blocks(
            payload_blocks=original_payload_blocks,
            edit_rate=attack.edit_rate,
            allow_boundary_edit=attack.allow_boundary_edit,
            boundary_edit_modes=attack.boundary_edit_modes,
            max_edits_per_block=attack.attack_max_edits_per_block,
            edit_count_mode=attack.edit_count_mode,
            boundary_symbol=generator.codebook.boundary_symbol,
            rng=rng,
        )
        pred_blocks = detect_sequence_multiple(
            observed_sequence,
            decoder_config=EccDecoderConfig(
                decoder_max_edits_per_block=decoder_budget,
                boundary_edit_modes=attack.boundary_edit_modes,
            ),
            codebook=generator.codebook,
        )
        ev = evaluate_predictions_multiple(original_payload_blocks, gt_events_per_block, pred_blocks)
        tp += ev["TP"]
        fp += ev["FP"]
        fn += ev["FN"]
        tn += ev["TN"]
        codeword_hits += ev["codeword_recovery_hit"]
        codeword_total += ev["codeword_recovery_total"]
        loc_hits += ev["block_loc_hit"]
        loc_total += ev["loc_total_overall"]
        event_hits += ev["event_loc_hit"]
        event_total += ev["event_total_overall"]
        event_sub_hit += ev["event_coverage_sub"] * ev["event_total_sub"]
        event_sub_total += ev["event_total_sub"]
        event_ins_hit += ev["event_coverage_insert"] * ev["event_total_insert"]
        event_ins_total += ev["event_total_insert"]
        event_del_hit += ev["event_coverage_delete"] * ev["event_total_delete"]
        event_del_total += ev["event_total_delete"]
        cand_weighted_sum += ev["mean_candidate_size"] * ev["loc_total_overall"]
        cand_weighted_n += ev["loc_total_overall"]
        detail_rows.append(
            {
                "sequence_index": idx,
                "used": True,
                "num_valid_blocks": len(original_payload_blocks),
                "TP": ev["TP"],
                "FP": ev["FP"],
                "FN": ev["FN"],
                "TN": ev["TN"],
                "block_tpr": ev["block_tpr"],
                "block_far": ev["block_far"],
                "codeword_recovery_acc": ev["codeword_recovery_acc"],
                "localization_acc_overall": ev["localization_acc_overall"],
            }
        )
    summary = {
        "num_sequences_total": len(results),
        "num_sequences_used": used_sequences,
        "num_sequences_skipped": skipped_sequences,
        "mean_valid_blocks_per_used_sequence": valid_blocks_total / used_sequences if used_sequences > 0 else 0.0,
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "block_tpr": tp / (tp + fn) if (tp + fn) > 0 else 0.0,
        "block_far": fp / (fp + tn) if (fp + tn) > 0 else 0.0,
        "codeword_recovery_acc": codeword_hits / codeword_total if codeword_total > 0 else 0.0,
        "localization_acc_overall": loc_hits / loc_total if loc_total > 0 else 0.0,
        "loc_total_overall": loc_total,
        "event_coverage_overall": event_hits / event_total if event_total > 0 else 0.0,
        "event_coverage_sub": event_sub_hit / event_sub_total if event_sub_total > 0 else 0.0,
        "event_coverage_insert": event_ins_hit / event_ins_total if event_ins_total > 0 else 0.0,
        "event_coverage_delete": event_del_hit / event_del_total if event_del_total > 0 else 0.0,
        "event_total_overall": event_total,
        "event_total_sub": event_sub_total,
        "event_total_insert": event_ins_total,
        "event_total_delete": event_del_total,
        "mean_candidate_size": cand_weighted_sum / cand_weighted_n if cand_weighted_n > 0 else 0.0,
    }
    return summary, detail_rows


def evaluate_kgw_generations(
    results: Sequence[KgwGenerationResult],
    generator: KgwGenerator,
    attack: AttackConfig,
    seed: int,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    detail_rows: List[Dict[str, Any]] = []
    used_sequences = 0
    skipped_sequences = 0
    valid_blocks_total = 0
    tp = fp = fn = tn = 0
    token_tp = token_fp = token_fn = token_tn = 0
    mean_red_score_sum = 0.0
    mean_red_score_n = 0
    mean_obs_len_sum = 0.0
    mean_obs_len_n = 0
    vocab_ids = [
        token_id for token_id in range(generator.model.vocab_size)
        if token_id not in set(generator.model.all_special_ids)
    ]
    for idx, result in enumerate(results):
        if not result.block_tokens:
            skipped_sequences += 1
            detail_rows.append({"sequence_index": idx, "used": False, "skip_reason": "no_blocks"})
            continue
        used_sequences += 1
        valid_blocks_total += len(result.block_tokens)
        attacked = apply_token_edits_to_blocks(
            token_blocks=[list(block) for block in result.block_tokens],
            edit_rate=attack.edit_rate,
            max_edits_per_block=attack.attack_max_edits_per_block,
            edit_count_mode=attack.edit_count_mode,
            vocab_ids=vocab_ids,
            rng=random.Random(seed + idx),
        )
        ev = evaluate_kgw_blocks(
            original_blocks=[list(block) for block in result.block_tokens],
            observed_blocks=attacked["observed_blocks"],
            origin_maps_per_block=attacked["origin_maps_per_block"],
            gt_events_per_block=attacked["gt_events_per_block"],
            config=generator.config,
            vocab_size=generator.model.vocab_size,
        )
        tp += ev["TP"]
        fp += ev["FP"]
        fn += ev["FN"]
        tn += ev["TN"]
        token_tp += ev["token_tp"]
        token_fp += ev["token_fp"]
        token_fn += ev["token_fn"]
        token_tn += ev["token_tn"]
        mean_red_score_sum += ev["mean_red_score"] * len(attacked["observed_blocks"])
        mean_red_score_n += len(attacked["observed_blocks"])
        mean_obs_len_sum += ev["mean_observed_block_len"] * len(attacked["observed_blocks"])
        mean_obs_len_n += len(attacked["observed_blocks"])
        detail_rows.append(
            {
                "sequence_index": idx,
                "used": True,
                "num_valid_blocks": len(result.block_tokens),
                "TP": ev["TP"],
                "FP": ev["FP"],
                "FN": ev["FN"],
                "TN": ev["TN"],
                "block_tpr": ev["block_tpr"],
                "block_far": ev["block_far"],
                "mean_red_score": ev["mean_red_score"],
                "token_tp": ev["token_tp"],
                "token_fp": ev["token_fp"],
                "token_fn": ev["token_fn"],
                "token_tn": ev["token_tn"],
                "token_precision": ev["token_precision"],
                "token_recall": ev["token_recall"],
                "token_f1": ev["token_f1"],
                "token_far": ev["token_far"],
            }
        )
    token_precision = token_tp / (token_tp + token_fp) if (token_tp + token_fp) > 0 else 0.0
    token_recall = token_tp / (token_tp + token_fn) if (token_tp + token_fn) > 0 else 0.0
    token_f1 = (
        2.0 * token_precision * token_recall / (token_precision + token_recall)
        if (token_precision + token_recall) > 0
        else 0.0
    )
    summary = {
        "num_sequences_total": len(results),
        "num_sequences_used": used_sequences,
        "num_sequences_skipped": skipped_sequences,
        "mean_valid_blocks_per_used_sequence": valid_blocks_total / used_sequences if used_sequences > 0 else 0.0,
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "block_tpr": tp / (tp + fn) if (tp + fn) > 0 else 0.0,
        "block_far": fp / (fp + tn) if (fp + tn) > 0 else 0.0,
        "codeword_recovery_acc": math.nan,
        "localization_acc_overall": math.nan,
        "loc_total_overall": 0,
        "event_coverage_overall": math.nan,
        "event_coverage_sub": math.nan,
        "event_coverage_insert": math.nan,
        "event_coverage_delete": math.nan,
        "event_total_overall": 0,
        "event_total_sub": 0,
        "event_total_insert": 0,
        "event_total_delete": 0,
        "mean_candidate_size": math.nan,
        "mean_red_score": mean_red_score_sum / mean_red_score_n if mean_red_score_n > 0 else 0.0,
        "mean_observed_block_len": mean_obs_len_sum / mean_obs_len_n if mean_obs_len_n > 0 else 0.0,
        "token_tp": token_tp,
        "token_fp": token_fp,
        "token_fn": token_fn,
        "token_tn": token_tn,
        "token_precision": token_precision,
        "token_recall": token_recall,
        "token_f1": token_f1,
        "token_far": token_fp / (token_fp + token_tn) if (token_fp + token_tn) > 0 else 0.0,
    }
    return summary, detail_rows


def run_experiment(run_config: RunConfig) -> Dict[str, Any]:
    ensure_dir(run_config.output_dir)
    prompt_rng = random.Random(run_config.prompts.prompt_seed)
    prompts = sample_prompts_from_config(run_config.prompts, prompt_rng)
    if not prompts:
        raise RuntimeError("No prompts were loaded. Provide inline prompts, a prompt file, or a dataset.")
    model = build_language_model(run_config.model, corpus_texts=prompts)
    save_prompts(f"{run_config.output_dir}/prompts.txt", prompts)

    summary_rows: List[Dict[str, Any]] = []
    ecc_detail_rows: List[Dict[str, Any]] = []
    kgw_detail_rows: List[Dict[str, Any]] = []
    detailed_payload: Dict[str, Any] = {"prompts": prompts, "settings": []}

    if "ecc" in run_config.schemes:
        partition = build_vocabulary_partition(model, prompts, run_config.ecc)
        generator = EccGenerator(model, partition, run_config.ecc)
        for watermark_mode in run_config.watermark_modes:
            for adaptive in run_config.ecc_adaptive_modes:
                setting = GenerationSetting(
                    scheme="ecc",
                    watermark_mode=watermark_mode,
                    adaptive=adaptive,
                    target_blocks=run_config.target_blocks,
                    max_new_tokens=run_config.max_new_tokens,
                    seed=run_config.generation_seed + (17 if adaptive else 53),
                )
                generated = generator.generate_many(prompts, setting)
                ppl = compute_text_perplexity(model, [x.suffix_text for x in generated], max_length=run_config.max_new_tokens)
                setting_key = f"ecc_{watermark_mode}_{'adaptive' if adaptive else 'nonadaptive'}"
                detailed_payload["settings"].append(
                    {
                        "setting_key": setting_key,
                        "scheme": "ecc",
                        "watermark_mode": watermark_mode,
                        "adaptive": adaptive,
                        "ppl": ppl,
                        "generated": [
                            {
                                "prompt": res.prompt,
                                "suffix_text": res.suffix_text,
                                "structural_seq": res.structural_seq,
                                "valid_blocks": res.decoded_clean["valid_blocks"],
                                "chosen_codewords": res.runtime_state.chosen_codewords,
                            }
                            for res in generated
                        ],
                    }
                )
                for attack_budget in run_config.attack_max_edits_per_blocks:
                    for edit_rate in run_config.edit_rates:
                        attack = AttackConfig(
                            edit_rate=edit_rate,
                            allow_boundary_edit=run_config.allow_boundary_edit,
                            boundary_edit_modes=run_config.boundary_edit_modes,
                            attack_max_edits_per_block=attack_budget,
                            edit_count_mode=run_config.edit_count_mode,
                        )
                        summary, detail_rows = evaluate_ecc_generations(
                            results=generated,
                            generator=generator,
                            attack=attack,
                            decoder_budget=run_config.decoder_max_edits_per_block,
                            seed=run_config.generation_seed + int(edit_rate * 1000) + 10000 * attack_budget,
                        )
                        row = {
                            "scheme": "ecc",
                            "watermark_mode": watermark_mode,
                            "adaptive": adaptive,
                            "logit_bias": setting.resolved_logit_bias(),
                            "edit_rate": edit_rate,
                            "attack_max_edits_per_block": attack_budget,
                            "edit_count_mode": run_config.edit_count_mode,
                            "decoder_budget": run_config.decoder_max_edits_per_block,
                            "ppl": ppl,
                            "token_tp": math.nan,
                            "token_fp": math.nan,
                            "token_fn": math.nan,
                            "token_tn": math.nan,
                            "token_precision": math.nan,
                            "token_recall": math.nan,
                            "token_f1": math.nan,
                            "token_far": math.nan,
                            **summary,
                        }
                        summary_rows.append(row)
                        for detail in detail_rows:
                            ecc_detail_rows.append({**row, **detail})

    if "kgw" in run_config.schemes:
        generator = KgwGenerator(model, run_config.kgw)
        for watermark_mode in run_config.watermark_modes:
            setting = GenerationSetting(
                scheme="kgw",
                watermark_mode=watermark_mode,
                adaptive=None,
                target_blocks=run_config.target_blocks,
                max_new_tokens=run_config.max_new_tokens,
                seed=run_config.generation_seed + 211,
            )
            generated = generator.generate_many(prompts, setting)
            ppl = compute_text_perplexity(model, [x.suffix_text for x in generated], max_length=run_config.max_new_tokens)
            setting_key = f"kgw_{watermark_mode}"
            detailed_payload["settings"].append(
                {
                    "setting_key": setting_key,
                    "scheme": "kgw",
                    "watermark_mode": watermark_mode,
                    "adaptive": None,
                    "ppl": ppl,
                    "generated": [
                        {
                            "prompt": res.prompt,
                            "suffix_text": res.suffix_text,
                            "num_blocks": len(res.block_tokens),
                        }
                        for res in generated
                    ],
                }
            )
            for attack_budget in run_config.attack_max_edits_per_blocks:
                for edit_rate in run_config.edit_rates:
                    attack = AttackConfig(
                        edit_rate=edit_rate,
                        allow_boundary_edit=False,
                        boundary_edit_modes=run_config.boundary_edit_modes,
                        attack_max_edits_per_block=attack_budget,
                        edit_count_mode=run_config.edit_count_mode,
                    )
                    summary, detail_rows = evaluate_kgw_generations(
                        results=generated,
                        generator=generator,
                        attack=attack,
                        seed=run_config.generation_seed + int(edit_rate * 1000) + 10000 * attack_budget,
                    )
                    row = {
                        "scheme": "kgw",
                        "watermark_mode": watermark_mode,
                        "adaptive": None,
                        "logit_bias": setting.resolved_logit_bias(),
                        "edit_rate": edit_rate,
                        "attack_max_edits_per_block": attack_budget,
                        "edit_count_mode": run_config.edit_count_mode,
                        "decoder_budget": None,
                        "ppl": ppl,
                        **summary,
                    }
                    summary_rows.append(row)
                    for detail in detail_rows:
                        kgw_detail_rows.append({**row, **detail})

    summary_df = pd.DataFrame(summary_rows)
    ecc_detail_df = pd.DataFrame(ecc_detail_rows)
    kgw_detail_df = pd.DataFrame(kgw_detail_rows)
    save_dataframe(summary_df, f"{run_config.output_dir}/summary", save_parquet=run_config.save_parquet)
    if not ecc_detail_df.empty:
        save_dataframe(ecc_detail_df, f"{run_config.output_dir}/ecc_details", save_parquet=run_config.save_parquet)
    if not kgw_detail_df.empty:
        save_dataframe(kgw_detail_df, f"{run_config.output_dir}/kgw_details", save_parquet=run_config.save_parquet)
    for attack_budget in run_config.attack_max_edits_per_blocks:
        attack_summary_df = summary_df[summary_df["attack_max_edits_per_block"] == attack_budget].copy()
        if not attack_summary_df.empty:
            save_dataframe(
                attack_summary_df,
                f"{run_config.output_dir}/summary_attack{attack_budget}",
                save_parquet=run_config.save_parquet,
            )
        if not ecc_detail_df.empty:
            attack_ecc_df = ecc_detail_df[ecc_detail_df["attack_max_edits_per_block"] == attack_budget].copy()
            if not attack_ecc_df.empty:
                save_dataframe(
                    attack_ecc_df,
                    f"{run_config.output_dir}/ecc_details_attack{attack_budget}",
                    save_parquet=run_config.save_parquet,
                )
        if not kgw_detail_df.empty:
            attack_kgw_df = kgw_detail_df[kgw_detail_df["attack_max_edits_per_block"] == attack_budget].copy()
            if not attack_kgw_df.empty:
                save_dataframe(
                    attack_kgw_df,
                    f"{run_config.output_dir}/kgw_details_attack{attack_budget}",
                    save_parquet=run_config.save_parquet,
                )
    write_json(f"{run_config.output_dir}/run_config.json", run_config)
    if run_config.save_detailed_json:
        write_json(f"{run_config.output_dir}/detailed_results.json", detailed_payload)
    return {
        "prompts": prompts,
        "model_device": getattr(model, "resolved_device", run_config.model.device),
        "quantization_mode": getattr(model, "quantization_mode", "none"),
        "used_4bit": getattr(model, "used_4bit", False),
        "summary_df": summary_df,
        "ecc_detail_df": ecc_detail_df,
        "kgw_detail_df": kgw_detail_df,
        "detailed_payload": detailed_payload,
    }
