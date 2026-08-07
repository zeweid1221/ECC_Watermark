from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from itertools import product
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

from .edits import EditEvent


def vt_syndrome(bits: Sequence[int]) -> int:
    return sum((i + 1) * int(bits[i]) for i in range(len(bits))) % (len(bits) + 1)


def hamming_parity_check(n: int) -> np.ndarray:
    r = int(np.ceil(np.log2(n + 1)))
    rows = []
    for i in range(r):
        row = []
        for j in range(1, n + 1):
            row.append((j >> i) & 1)
        rows.append(row)
    return np.array(rows, dtype=int) % 2


def hamming_ok(bits: Sequence[int], parity: np.ndarray) -> bool:
    x = np.array(bits, dtype=int)
    return np.all((parity @ x) % 2 == 0)


def feasible_codewords(block_len: int, vt_a: int) -> List[List[int]]:
    parity = hamming_parity_check(block_len)
    out: List[List[int]] = []
    for x in product([0, 1], repeat=block_len):
        bits = list(x)
        if vt_syndrome(bits) == vt_a and hamming_ok(bits, parity):
            out.append(bits)
    return out


@dataclass
class ParsedBlock:
    block_tokens: List[int]
    flag: bool
    etype: str
    candidates: List[Tuple[str, int]]
    decoded_codeword: Optional[List[int]]
    is_boundary_edited: bool = False
    boundary_edit_type: Optional[str] = None
    info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EccCodebook:
    block_len: int
    vt_a: int
    boundary_symbol: int = 2
    feasible: List[List[int]] = field(init=False)
    feasible_set: Set[Tuple[int, ...]] = field(init=False)

    def __post_init__(self) -> None:
        self.feasible = feasible_codewords(self.block_len, self.vt_a)
        self.feasible_set = {tuple(x) for x in self.feasible}


@dataclass
class EccDecoderConfig:
    decoder_max_edits_per_block: int
    boundary_edit_modes: Tuple[str, ...] = ("delete", "sub")


def split_structural_seq_into_blocks(structural_seq: Sequence[int], boundary_symbol: int) -> Tuple[List[List[int]], List[int], int]:
    blocks: List[List[int]] = []
    tail: List[int] = []
    cur: List[int] = []
    empty_boundary_count = 0
    for sym in structural_seq:
        if int(sym) == int(boundary_symbol):
            if cur:
                blocks.append(cur)
            else:
                empty_boundary_count += 1
            cur = []
        else:
            cur.append(int(sym))
    tail = cur
    return blocks, tail, empty_boundary_count


def decode_clean_structural_sequence(structural_seq: Sequence[int], codebook: EccCodebook) -> Dict[str, Any]:
    blocks, tail_bits, empty_boundary_count = split_structural_seq_into_blocks(structural_seq, codebook.boundary_symbol)
    valid_blocks = [block for block in blocks if len(block) == codebook.block_len and tuple(block) in codebook.feasible_set]
    invalid_blocks = [block for block in blocks if not (len(block) == codebook.block_len and tuple(block) in codebook.feasible_set)]
    return {
        "blocks_closed_by_boundary": blocks,
        "valid_blocks": valid_blocks,
        "invalid_blocks": invalid_blocks,
        "tail_bits": tail_bits,
        "empty_boundary_count": empty_boundary_count,
        "num_closed_blocks": len(blocks),
    }


def split_by_boundary_with_meta(seq: Sequence[int], boundary_symbol: int) -> List[Dict[str, Any]]:
    raw_segments = []
    cur: List[int] = []
    segment_start = 0
    for index, token in enumerate(seq):
        if int(token) == int(boundary_symbol):
            raw_segments.append(
                {
                    "tokens": cur,
                    "ended_with_boundary": True,
                    "token_start": int(segment_start),
                    "token_end_exclusive": int(index),
                    "boundary_index": int(index),
                }
            )
            cur = []
            segment_start = int(index) + 1
        else:
            cur.append(int(token))
    if cur or (len(seq) > 0 and int(seq[-1]) != int(boundary_symbol)):
        raw_segments.append(
            {
                "tokens": cur,
                "ended_with_boundary": False,
                "token_start": int(segment_start),
                "token_end_exclusive": int(len(seq)),
                "boundary_index": None,
            }
        )
    return raw_segments


def _loc_sort_key(loc: Tuple[str, int]) -> Tuple[int, int]:
    order = {"payload": 0, "gap": 1, "boundary": 2}
    return (order.get(loc[0], 99), int(loc[1]))


def _levenshtein_distance_dp(ref_t: Tuple[int, ...], obs_t: Tuple[int, ...]) -> Tuple[Tuple[int, ...], ...]:
    n, m = len(ref_t), len(obs_t)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i
    for j in range(1, m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sub_cost = 0 if ref_t[i - 1] == obs_t[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + sub_cost)
    return tuple(tuple(row) for row in dp)


def optimal_edit_location_union(ref_t: Tuple[int, ...], obs_t: Tuple[int, ...]) -> Tuple[Tuple[str, int], ...]:
    dp = _levenshtein_distance_dp(ref_t, obs_t)
    n, m = len(ref_t), len(obs_t)

    @lru_cache(None)
    def collect(i: int, j: int) -> frozenset:
        if i == 0 and j == 0:
            return frozenset()
        cur = dp[i][j]
        out = set()
        if i > 0 and j > 0:
            sub_cost = 0 if ref_t[i - 1] == obs_t[j - 1] else 1
            if dp[i - 1][j - 1] + sub_cost == cur:
                prev = set(collect(i - 1, j - 1))
                if sub_cost == 1:
                    prev.add(("payload", i - 1))
                out.update(prev)
        if i > 0 and dp[i - 1][j] + 1 == cur:
            prev = set(collect(i - 1, j))
            prev.add(("payload", i - 1))
            out.update(prev)
        if j > 0 and dp[i][j - 1] + 1 == cur:
            prev = set(collect(i, j - 1))
            prev.add(("gap", i))
            out.update(prev)
        return frozenset(out)

    return tuple(sorted(collect(n, m), key=_loc_sort_key))


def best_codewords_by_edit_distance(
    obs_t: Tuple[int, ...],
    payload_budget: int,
    codebook: EccCodebook,
) -> Tuple[Optional[int], Tuple[Tuple[int, ...], ...], Tuple[Tuple[str, int], ...]]:
    best_dist: Optional[int] = None
    best_codewords: List[Tuple[int, ...]] = []
    for ref in codebook.feasible:
        ref_t = tuple(ref)
        dp = _levenshtein_distance_dp(ref_t, obs_t)
        dist = dp[len(ref_t)][len(obs_t)]
        if dist > payload_budget:
            continue
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_codewords = [ref_t]
        elif dist == best_dist:
            best_codewords.append(ref_t)
    if best_dist is None:
        return None, tuple(), tuple()
    best_codewords = sorted(set(best_codewords))
    cand_union = set()
    for ref_t in best_codewords:
        cand_union.update(optimal_edit_location_union(ref_t, obs_t))
    return best_dist, tuple(best_codewords), tuple(sorted(cand_union, key=_loc_sort_key))


def min_codeword_edit_distance(obs_t: Sequence[int], codebook: EccCodebook) -> int:
    obs_tuple = tuple(int(x) for x in obs_t)
    best_dist: Optional[int] = None
    for ref in codebook.feasible:
        ref_t = tuple(ref)
        dp = _levenshtein_distance_dp(ref_t, obs_tuple)
        dist = dp[len(ref_t)][len(obs_tuple)]
        if best_dist is None or dist < best_dist:
            best_dist = dist
    return int(best_dist if best_dist is not None else len(obs_tuple))


@dataclass
class MultiBlockMatch:
    payload_obs: List[int]
    boundary_state: str
    consumed: int
    payload_distance: int
    total_distance: int
    best_codewords: List[List[int]]
    payload_candidates: List[Tuple[str, int]]
    boundary_sub_value: Optional[int] = None


def match_one_block_multiple(
    payload_obs: List[int],
    boundary_state: str,
    decoder_config: EccDecoderConfig,
    codebook: EccCodebook,
    consumed: Optional[int] = None,
    boundary_sub_value: Optional[int] = None,
) -> Optional[MultiBlockMatch]:
    if boundary_state not in {"intact", "delete", "sub"}:
        return None
    if boundary_state == "delete" and "delete" not in decoder_config.boundary_edit_modes:
        return None
    if boundary_state == "sub" and "sub" not in decoder_config.boundary_edit_modes:
        return None
    boundary_cost = 0 if boundary_state == "intact" else 1
    payload_budget = decoder_config.decoder_max_edits_per_block - boundary_cost
    if payload_budget < 0:
        return None
    obs_t = tuple(payload_obs)
    best_dist, best_codewords_t, payload_cands_t = best_codewords_by_edit_distance(obs_t, payload_budget, codebook)
    if best_dist is None:
        return None
    total_distance = best_dist + boundary_cost
    if total_distance > decoder_config.decoder_max_edits_per_block:
        return None
    return MultiBlockMatch(
        payload_obs=payload_obs.copy(),
        boundary_state=boundary_state,
        consumed=len(payload_obs) if consumed is None else consumed,
        payload_distance=best_dist,
        total_distance=total_distance,
        best_codewords=[list(x) for x in best_codewords_t],
        payload_candidates=list(payload_cands_t),
        boundary_sub_value=boundary_sub_value,
    )


def parsed_block_from_multi_match(match: MultiBlockMatch, block_len: int) -> ParsedBlock:
    candidates = list(match.payload_candidates)
    if match.boundary_state in {"delete", "sub"}:
        candidates.append(("boundary", block_len))
    candidates = sorted(set(candidates), key=_loc_sort_key)
    decoded_codeword = match.best_codewords[0].copy() if match.best_codewords else None
    flag = match.total_distance > 0
    return ParsedBlock(
        block_tokens=match.payload_obs.copy(),
        flag=flag,
        etype="none" if not flag else "multi",
        candidates=candidates,
        decoded_codeword=decoded_codeword,
        is_boundary_edited=match.boundary_state in {"delete", "sub"},
        boundary_edit_type=match.boundary_state if match.boundary_state in {"delete", "sub"} else None,
        info={
            "mode": "multiple_alignment",
            "boundary_state": match.boundary_state,
            "consumed": match.consumed,
            "payload_distance": match.payload_distance,
            "total_distance": match.total_distance,
            "best_codewords": [cw.copy() for cw in match.best_codewords],
            "num_best_codewords": len(match.best_codewords),
            "boundary_sub_value": match.boundary_sub_value,
        },
    )


def _multiple_path_score(path: Tuple[ParsedBlock, ...]) -> Tuple[int, int, int, int, int]:
    total_distance = sum(int(p.info.get("total_distance", 0)) for p in path)
    boundary_edits = sum(1 for p in path if p.is_boundary_edited)
    boundary_subs = sum(1 for p in path if p.boundary_edit_type == "sub")
    num_blocks = len(path)
    total_candidate_size = sum(len(p.candidates) for p in path)
    return (total_distance, boundary_edits, boundary_subs, num_blocks, total_candidate_size)


def parse_segment_multiple(
    seg: Sequence[int],
    segment_ends_with_boundary: bool,
    decoder_config: EccDecoderConfig,
    codebook: EccCodebook,
) -> Optional[List[ParsedBlock]]:
    if len(seg) == 0:
        return None
    seg_t = tuple(int(x) for x in seg)
    min_payload_len = max(0, codebook.block_len - decoder_config.decoder_max_edits_per_block)
    max_payload_len = codebook.block_len + decoder_config.decoder_max_edits_per_block

    @lru_cache(None)
    def dfs(i: int) -> Tuple[Optional[Tuple[ParsedBlock, ...]], Optional[Tuple[int, int, int, int, int]]]:
        if i == len(seg_t):
            return tuple(), (0, 0, 0, 0, 0)
        if i > len(seg_t):
            return None, None
        rem = len(seg_t) - i
        candidates: List[Tuple[Tuple[ParsedBlock, ...], Tuple[int, int, int, int, int]]] = []

        if segment_ends_with_boundary:
            for p_len in range(min_payload_len, max_payload_len + 1):
                if p_len <= 0:
                    continue
                if p_len == rem:
                    payload_obs = list(seg_t[i : i + p_len])
                    match = match_one_block_multiple(payload_obs, "intact", decoder_config, codebook, consumed=p_len)
                    if match is not None:
                        pb = parsed_block_from_multi_match(match, codebook.block_len)
                        pb.info = {**pb.info, "segment_role": "final_intact"}
                        path = (pb,)
                        candidates.append((path, _multiple_path_score(path)))

        if "delete" in decoder_config.boundary_edit_modes:
            for p_len in range(min_payload_len, max_payload_len + 1):
                if p_len <= 0 or i + p_len > len(seg_t):
                    continue
                payload_obs = list(seg_t[i : i + p_len])
                match = match_one_block_multiple(payload_obs, "delete", decoder_config, codebook, consumed=p_len)
                if match is None:
                    continue
                if i + p_len == len(seg_t):
                    if not segment_ends_with_boundary:
                        pb = parsed_block_from_multi_match(match, codebook.block_len)
                        pb.info = {**pb.info, "segment_role": "final_boundary_delete"}
                        path = (pb,)
                        candidates.append((path, _multiple_path_score(path)))
                else:
                    suffix_path, _ = dfs(i + p_len)
                    if suffix_path is not None and len(suffix_path) > 0:
                        pb = parsed_block_from_multi_match(match, codebook.block_len)
                        pb.info = {**pb.info, "segment_role": "interior_boundary_delete"}
                        path = (pb,) + suffix_path
                        candidates.append((path, _multiple_path_score(path)))

        if "sub" in decoder_config.boundary_edit_modes:
            for p_len in range(min_payload_len, max_payload_len + 1):
                if p_len <= 0:
                    continue
                consumed = p_len + 1
                if i + consumed > len(seg_t):
                    continue
                payload_obs = list(seg_t[i : i + p_len])
                bval = seg_t[i + p_len]
                match = match_one_block_multiple(
                    payload_obs,
                    "sub",
                    decoder_config,
                    codebook,
                    consumed=consumed,
                    boundary_sub_value=bval,
                )
                if match is None:
                    continue
                if i + consumed == len(seg_t):
                    if not segment_ends_with_boundary:
                        pb = parsed_block_from_multi_match(match, codebook.block_len)
                        pb.info = {**pb.info, "segment_role": "final_boundary_sub"}
                        path = (pb,)
                        candidates.append((path, _multiple_path_score(path)))
                else:
                    suffix_path, _ = dfs(i + consumed)
                    if suffix_path is not None and len(suffix_path) > 0:
                        pb = parsed_block_from_multi_match(match, codebook.block_len)
                        pb.info = {**pb.info, "segment_role": "interior_boundary_sub"}
                        path = (pb,) + suffix_path
                        candidates.append((path, _multiple_path_score(path)))

        if not candidates:
            return None, None
        best_path, best_score = min(candidates, key=lambda x: x[1])
        return best_path, best_score

    best_path, _ = dfs(0)
    return list(best_path) if best_path is not None else None


def detect_sequence_multiple(
    seq: Sequence[int],
    decoder_config: EccDecoderConfig,
    codebook: EccCodebook,
) -> List[ParsedBlock]:
    raw_segments = split_by_boundary_with_meta(seq, codebook.boundary_symbol)
    parsed_blocks: List[ParsedBlock] = []
    for seg_meta in raw_segments:
        tokens = seg_meta["tokens"]
        ended_with_boundary = seg_meta["ended_with_boundary"]
        if len(tokens) == 0:
            parsed_blocks.append(
                ParsedBlock(
                    block_tokens=[],
                    flag=True,
                    etype="invalid",
                    candidates=[],
                    decoded_codeword=None,
                    info={
                        "mode": "empty_segment_multiple",
                        "ended_with_boundary": ended_with_boundary,
                        "observed_span_start": int(seg_meta["token_start"]),
                        "observed_span_end_exclusive": int(seg_meta["token_end_exclusive"]),
                        "observed_boundary_index": seg_meta["boundary_index"],
                    },
                )
            )
            continue
        local = parse_segment_multiple(tokens, ended_with_boundary, decoder_config, codebook)
        if local is None:
            parsed_blocks.append(
                ParsedBlock(
                    block_tokens=list(tokens),
                    flag=True,
                    etype="invalid",
                    candidates=[],
                    decoded_codeword=None,
                    info={
                        "mode": "segment_parse_failed_multiple",
                        "ended_with_boundary": ended_with_boundary,
                        "observed_span_start": int(seg_meta["token_start"]),
                        "observed_span_end_exclusive": int(seg_meta["token_end_exclusive"]),
                        "observed_boundary_index": seg_meta["boundary_index"],
                    },
                )
            )
            continue
        local_consumed = 0
        for local_index, pb in enumerate(local):
            consumed = int(pb.info.get("consumed", len(pb.block_tokens)))
            span_start = int(seg_meta["token_start"]) + local_consumed
            span_end = min(
                int(seg_meta["token_end_exclusive"]),
                span_start + max(0, consumed),
            )
            pb.info = {
                **pb.info,
                "segment_mode": "multiple_parse",
                "ended_with_boundary": ended_with_boundary,
                "observed_span_start": int(span_start),
                "observed_span_end_exclusive": int(span_end),
                "observed_boundary_index": (
                    seg_meta["boundary_index"]
                    if local_index == len(local) - 1 and ended_with_boundary
                    else None
                ),
            }
            parsed_blocks.append(pb)
            local_consumed += max(0, consumed)
    return parsed_blocks


def evaluate_predictions_multiple(
    original_payload_blocks: Sequence[Sequence[int]],
    gt_events_per_block: Sequence[Sequence[EditEvent]],
    pred_blocks: Sequence[ParsedBlock],
    tolerance: int = 0,
    codebook: Optional[EccCodebook] = None,
) -> Dict[str, Any]:
    tp = fp = fn = tn = 0
    codeword_rec_total = 0
    codeword_rec_hit = 0
    block_loc_total = 0
    block_loc_hit = 0
    event_loc_total = 0
    event_loc_hit = 0
    by_type_event_total = Counter()
    by_type_event_hit = Counter()
    cand_size_counter = Counter()
    cand_size_sum = 0
    cand_size_n = 0
    num_pred_blocks = len(pred_blocks)
    num_gt_blocks = len(gt_events_per_block)
    m = min(len(original_payload_blocks), len(pred_blocks))

    for i in range(m):
        gt_events = gt_events_per_block[i]
        gt_edited = len(gt_events) > 0
        pred = pred_blocks[i]
        pred_edited = parsed_block_exceeds_tolerance(pred, tolerance=tolerance, codebook=codebook)
        if gt_edited and pred_edited:
            tp += 1
        elif gt_edited and not pred_edited:
            fn += 1
        elif (not gt_edited) and pred_edited:
            fp += 1
        else:
            tn += 1
        if gt_edited:
            codeword_rec_total += 1
            best_codewords = pred.info.get("best_codewords", [])
            if tuple(original_payload_blocks[i]) in {tuple(x) for x in best_codewords} or pred.decoded_codeword == list(original_payload_blocks[i]):
                codeword_rec_hit += 1
            block_loc_total += 1
            if all(ev.loc in pred.candidates for ev in gt_events):
                block_loc_hit += 1
            for ev in gt_events:
                event_loc_total += 1
                by_type_event_total[ev.etype] += 1
                if ev.loc in pred.candidates:
                    event_loc_hit += 1
                    by_type_event_hit[ev.etype] += 1
            cand_size = len(pred.candidates)
            cand_size_counter[cand_size] += 1
            cand_size_sum += cand_size
            cand_size_n += 1

    for i in range(m, len(pred_blocks)):
        if parsed_block_exceeds_tolerance(pred_blocks[i], tolerance=tolerance, codebook=codebook):
            fp += 1

    for i in range(m, len(gt_events_per_block)):
        if len(gt_events_per_block[i]) > 0:
            fn += 1
        else:
            tn += 1

    return {
        "num_gt_blocks": num_gt_blocks,
        "num_pred_blocks": num_pred_blocks,
        "block_count_match": num_gt_blocks == num_pred_blocks,
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "block_tpr": tp / (tp + fn) if (tp + fn) > 0 else 0.0,
        "block_far": fp / (fp + tn) if (fp + tn) > 0 else 0.0,
        "codeword_recovery_hit": codeword_rec_hit,
        "codeword_recovery_total": codeword_rec_total,
        "codeword_recovery_acc": codeword_rec_hit / codeword_rec_total if codeword_rec_total > 0 else 0.0,
        "block_loc_hit": block_loc_hit,
        "localization_acc_overall": block_loc_hit / block_loc_total if block_loc_total > 0 else 0.0,
        "loc_total_overall": block_loc_total,
        "event_loc_hit": event_loc_hit,
        "event_coverage_overall": event_loc_hit / event_loc_total if event_loc_total > 0 else 0.0,
        "event_coverage_sub": by_type_event_hit["sub"] / by_type_event_total["sub"] if by_type_event_total["sub"] > 0 else 0.0,
        "event_coverage_insert": by_type_event_hit["insert"] / by_type_event_total["insert"] if by_type_event_total["insert"] > 0 else 0.0,
        "event_coverage_delete": by_type_event_hit["delete"] / by_type_event_total["delete"] if by_type_event_total["delete"] > 0 else 0.0,
        "event_total_overall": event_loc_total,
        "event_total_sub": by_type_event_total["sub"],
        "event_total_insert": by_type_event_total["insert"],
        "event_total_delete": by_type_event_total["delete"],
        "mean_candidate_size": cand_size_sum / cand_size_n if cand_size_n > 0 else 0.0,
        "candidate_size_hist": dict(sorted(cand_size_counter.items())),
    }


def evaluate_predictions_with_provenance(
    original_payload_blocks: Sequence[Sequence[int]],
    gt_events_per_block: Sequence[Sequence[EditEvent]],
    pred_blocks: Sequence[ParsedBlock],
    observed_provenance: Sequence[Dict[str, Any]],
    tolerance: int = 0,
    codebook: Optional[EccCodebook] = None,
) -> Dict[str, Any]:
    """Evaluate parsed spans against source blocks without assuming one parse per block.

    Detector parsing is completed before this function is called. Provenance is
    used only to merge parsed structural spans back to the fixed source-block
    evaluation units and never to influence decoding.
    """

    num_gt_blocks = len(gt_events_per_block)
    block_len = len(original_payload_blocks[0]) if original_payload_blocks else 7
    source_pred_flags = [False] * num_gt_blocks
    source_candidates: List[Set[Tuple[str, int]]] = [set() for _ in range(num_gt_blocks)]
    source_decoded_codewords: List[Set[Tuple[int, ...]]] = [set() for _ in range(num_gt_blocks)]
    parsed_to_source_blocks: List[List[int]] = []
    unassigned_suspicious_parses = 0

    def provenance_indices_for_pred(pred: ParsedBlock) -> List[int]:
        start = pred.info.get("observed_span_start")
        end = pred.info.get("observed_span_end_exclusive")
        indices: List[int] = []
        if start is not None and end is not None:
            indices.extend(
                range(
                    max(0, int(start)),
                    min(len(observed_provenance), max(int(start), int(end))),
                )
            )
        boundary_index = pred.info.get("observed_boundary_index")
        if boundary_index is not None and 0 <= int(boundary_index) < len(observed_provenance):
            indices.append(int(boundary_index))
        return sorted(set(indices))

    def source_blocks_for_indices(indices: Sequence[int]) -> List[int]:
        return sorted(
            {
                int(observed_provenance[index]["original_block_id"])
                for index in indices
                if observed_provenance[index].get("original_block_id") is not None
                and 0 <= int(observed_provenance[index]["original_block_id"]) < num_gt_blocks
            }
        )

    for pred in pred_blocks:
        observed_indices = provenance_indices_for_pred(pred)
        source_blocks = source_blocks_for_indices(observed_indices)
        parsed_to_source_blocks.append(source_blocks)
        pred_edited = parsed_block_exceeds_tolerance(
            pred,
            tolerance=tolerance,
            codebook=codebook,
        )
        if pred_edited and not source_blocks:
            unassigned_suspicious_parses += 1
        for block_id in source_blocks:
            source_pred_flags[block_id] = source_pred_flags[block_id] or pred_edited
            if pred.decoded_codeword is not None:
                source_decoded_codewords[block_id].add(tuple(int(x) for x in pred.decoded_codeword))
            for candidate in pred.info.get("best_codewords", []):
                source_decoded_codewords[block_id].add(tuple(int(x) for x in candidate))
            # Decoder candidates are coordinates in the feasible reference
            # codeword, not offsets into the observed span. Preserve those
            # coordinates when assigning a parsed span to its source block(s).
            for kind, raw_position in pred.candidates:
                position = int(raw_position)
                if kind == "payload" and 0 <= position < block_len:
                    source_candidates[block_id].add(("payload", position))
                elif kind == "gap" and 0 <= position <= block_len:
                    source_candidates[block_id].add(("gap", position))
                elif kind == "boundary":
                    source_candidates[block_id].add(("boundary", block_len))

    tp = fp = fn = tn = 0
    event_loc_total = event_loc_hit = 0
    block_loc_total = block_loc_hit = 0
    codeword_rec_total = codeword_rec_hit = 0
    by_type_event_total = Counter()
    by_type_event_hit = Counter()
    cand_size_counter = Counter()
    candidate_sizes: List[int] = []
    for block_id, gt_events in enumerate(gt_events_per_block):
        gt_edited = bool(gt_events)
        pred_edited = bool(source_pred_flags[block_id])
        if gt_edited and pred_edited:
            tp += 1
        elif gt_edited:
            fn += 1
        elif pred_edited:
            fp += 1
        else:
            tn += 1
        if not gt_edited:
            continue
        codeword_rec_total += 1
        if tuple(int(x) for x in original_payload_blocks[block_id]) in source_decoded_codewords[block_id]:
            codeword_rec_hit += 1
        block_loc_total += 1
        if all(ev.loc in source_candidates[block_id] for ev in gt_events):
            block_loc_hit += 1
        for event in gt_events:
            event_loc_total += 1
            by_type_event_total[event.etype] += 1
            if event.loc in source_candidates[block_id]:
                event_loc_hit += 1
                by_type_event_hit[event.etype] += 1
        candidate_size = len(source_candidates[block_id])
        candidate_sizes.append(candidate_size)
        cand_size_counter[candidate_size] += 1

    return {
        "num_gt_blocks": num_gt_blocks,
        "num_pred_blocks": len(pred_blocks),
        "block_count_match": num_gt_blocks == len(pred_blocks),
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "block_tpr": tp / (tp + fn) if (tp + fn) > 0 else 0.0,
        "block_far": fp / (fp + tn) if (fp + tn) > 0 else 0.0,
        "codeword_recovery_hit": codeword_rec_hit,
        "codeword_recovery_total": codeword_rec_total,
        "codeword_recovery_acc": codeword_rec_hit / codeword_rec_total if codeword_rec_total else 0.0,
        "block_loc_hit": block_loc_hit,
        "localization_acc_overall": block_loc_hit / block_loc_total if block_loc_total else 0.0,
        "loc_total_overall": block_loc_total,
        "event_loc_hit": event_loc_hit,
        "event_coverage_overall": event_loc_hit / event_loc_total if event_loc_total else 0.0,
        "event_coverage_sub": by_type_event_hit["sub"] / by_type_event_total["sub"] if by_type_event_total["sub"] else 0.0,
        "event_coverage_insert": by_type_event_hit["insert"] / by_type_event_total["insert"] if by_type_event_total["insert"] else 0.0,
        "event_coverage_delete": by_type_event_hit["delete"] / by_type_event_total["delete"] if by_type_event_total["delete"] else 0.0,
        "event_total_overall": event_loc_total,
        "event_total_sub": by_type_event_total["sub"],
        "event_total_insert": by_type_event_total["insert"],
        "event_total_delete": by_type_event_total["delete"],
        "mean_candidate_size": sum(candidate_sizes) / len(candidate_sizes) if candidate_sizes else 0.0,
        "candidate_size_hist": dict(sorted(cand_size_counter.items())),
        "source_pred_flags": [int(x) for x in source_pred_flags],
        "source_candidate_locations": [
            [[kind, int(index)] for kind, index in sorted(locations, key=_loc_sort_key)]
            for locations in source_candidates
        ],
        "parsed_to_source_blocks": parsed_to_source_blocks,
        "unassigned_suspicious_parses": int(unassigned_suspicious_parses),
    }


def parsed_block_exceeds_tolerance(
    pred: ParsedBlock,
    tolerance: int = 0,
    codebook: Optional[EccCodebook] = None,
) -> bool:
    if pred.is_boundary_edited:
        return True
    payload_distance = pred.info.get("payload_distance")
    if payload_distance is None and codebook is not None:
        payload_distance = min_codeword_edit_distance(pred.block_tokens, codebook)
    if payload_distance is None:
        return bool(pred.flag)
    return int(payload_distance) > int(tolerance)
