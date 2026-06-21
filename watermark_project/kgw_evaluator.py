from __future__ import annotations

from typing import Any, Dict, List, Sequence

import numpy as np

from .config import KGWConfig
from .edits import EditEvent
from .kgw_generator import green_mask_for_seed, row_seed_from_suffix


def token_scores_red(
    token_ids: Sequence[int],
    config: KGWConfig,
    vocab_size: int,
) -> np.ndarray:
    scores = np.zeros(len(token_ids), dtype=np.float32)
    generated_prefix: List[int] = []
    for idx, token_id in enumerate(token_ids):
        row_seed = row_seed_from_suffix(generated_prefix, config.seed_count, config.seed_offset)
        green = green_mask_for_seed(row_seed, vocab_size)
        scores[idx] = float(0.0 if green[int(token_id)] else 1.0)
        generated_prefix.append(int(token_id))
    return scores


def evaluate_kgw_blocks(
    original_blocks: Sequence[Sequence[int]],
    observed_blocks: Sequence[Sequence[int]],
    origin_maps_per_block: Sequence[Sequence[int]],
    gt_events_per_block: Sequence[Sequence[EditEvent]],
    config: KGWConfig,
    vocab_size: int,
) -> Dict[str, Any]:
    full_sequence = [token for block in observed_blocks for token in block]
    red_scores = token_scores_red(full_sequence, config, vocab_size)
    ptr = 0
    tp = fp = fn = tn = 0
    token_tp = token_fp = token_fn = token_tn = 0
    block_scores: List[float] = []
    block_preds: List[int] = []
    for original_block, block, origin_map, events in zip(
        original_blocks,
        observed_blocks,
        origin_maps_per_block,
        gt_events_per_block,
    ):
        block_len = len(block)
        block_slice = red_scores[ptr : ptr + block_len]
        ptr += block_len
        pred = int(np.any(block_slice > 0.0))
        label = int(len(events) > 0)
        score = float(np.mean(block_slice)) if block_len > 0 else 0.0
        block_scores.append(score)
        block_preds.append(pred)
        if label and pred:
            tp += 1
        elif label and not pred:
            fn += 1
        elif (not label) and pred:
            fp += 1
        else:
            tn += 1

        token_counts = evaluate_kgw_token_anomalies(original_block, block_slice, origin_map, events)
        token_tp += token_counts["token_tp"]
        token_fp += token_counts["token_fp"]
        token_fn += token_counts["token_fn"]
        token_tn += token_counts["token_tn"]

    token_precision = token_tp / (token_tp + token_fp) if (token_tp + token_fp) > 0 else 0.0
    token_recall = token_tp / (token_tp + token_fn) if (token_tp + token_fn) > 0 else 0.0
    token_f1 = (
        2.0 * token_precision * token_recall / (token_precision + token_recall)
        if (token_precision + token_recall) > 0
        else 0.0
    )
    token_far = token_fp / (token_fp + token_tn) if (token_fp + token_tn) > 0 else 0.0
    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "block_tpr": tp / (tp + fn) if (tp + fn) > 0 else 0.0,
        "block_far": fp / (fp + tn) if (fp + tn) > 0 else 0.0,
        "mean_red_score": float(np.mean(block_scores)) if block_scores else 0.0,
        "mean_candidate_size": float("nan"),
        "codeword_recovery_acc": float("nan"),
        "localization_acc_overall": float("nan"),
        "loc_total_overall": 0,
        "event_coverage_overall": float("nan"),
        "event_coverage_sub": float("nan"),
        "event_coverage_insert": float("nan"),
        "event_coverage_delete": float("nan"),
        "event_total_overall": int(sum(len(x) for x in gt_events_per_block)),
        "event_total_sub": int(sum(1 for events in gt_events_per_block for ev in events if ev.etype == "sub")),
        "event_total_insert": int(sum(1 for events in gt_events_per_block for ev in events if ev.etype == "insert")),
        "event_total_delete": int(sum(1 for events in gt_events_per_block for ev in events if ev.etype == "delete")),
        "mean_observed_block_len": float(np.mean([len(block) for block in observed_blocks])) if observed_blocks else 0.0,
        "token_tp": token_tp,
        "token_fp": token_fp,
        "token_fn": token_fn,
        "token_tn": token_tn,
        "token_precision": token_precision,
        "token_recall": token_recall,
        "token_f1": token_f1,
        "token_far": token_far,
    }


def evaluate_kgw_token_anomalies(
    original_block: Sequence[int],
    observed_red_scores: Sequence[float],
    origin_map: Sequence[int],
    events: Sequence[EditEvent],
) -> Dict[str, int]:
    # Deterministic convention:
    # - original token positions are evaluated through the origin map
    # - deleted original tokens become positives with no surviving observed token
    # - inserted observed tokens are evaluated as extra positions with origin -1
    predicted_positive_by_origin = {
        int(src_idx): False for src_idx in range(len(original_block))
    }
    inserted_predictions: List[bool] = []
    for src_idx, red_score in zip(origin_map, observed_red_scores):
        suspicious = bool(red_score > 0.0)
        if int(src_idx) >= 0:
            predicted_positive_by_origin[int(src_idx)] = predicted_positive_by_origin.get(int(src_idx), False) or suspicious
        else:
            inserted_predictions.append(suspicious)

    positive_origins = set()
    inserted_count = 0
    for event in events:
        if event.etype == "insert":
            inserted_count += 1
        elif event.loc[0] == "payload":
            origin_idx = int(event.loc[1])
            positive_origins.add(origin_idx)

    token_tp = token_fp = token_fn = token_tn = 0
    for origin_idx in range(len(original_block)):
        pred = predicted_positive_by_origin.get(origin_idx, False)
        label = origin_idx in positive_origins
        if label and pred:
            token_tp += 1
        elif label and not pred:
            token_fn += 1
        elif (not label) and pred:
            token_fp += 1
        else:
            token_tn += 1

    for suspicious in inserted_predictions[:inserted_count]:
        if suspicious:
            token_tp += 1
        else:
            token_fn += 1
    for suspicious in inserted_predictions[inserted_count:]:
        if suspicious:
            token_fp += 1
        else:
            token_tn += 1

    return {
        "token_tp": token_tp,
        "token_fp": token_fp,
        "token_fn": token_fn,
        "token_tn": token_tn,
    }
