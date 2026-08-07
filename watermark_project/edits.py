from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


@dataclass
class EditEvent:
    etype: str
    loc: Tuple[str, int]
    value_before: Optional[int] = None
    value_after: Optional[int] = None


def sample_num_edits(max_edits_per_block: int, mode: str, rng: random.Random) -> int:
    if max_edits_per_block <= 1:
        return 1
    if mode == "uniform_1_to_k":
        return rng.randint(1, max_edits_per_block)
    if mode == "fixed_k":
        return max_edits_per_block
    raise ValueError(f"Unknown edit count mode: {mode}")


def apply_edits_to_payload_blocks(
    payload_blocks: List[List[int]],
    edit_rate: float,
    allow_boundary_edit: bool,
    boundary_edit_modes: Tuple[str, ...],
    max_edits_per_block: int,
    edit_count_mode: str,
    boundary_symbol: int = 2,
    rng: Optional[random.Random] = None,
) -> Tuple[List[List[int]], List[List[EditEvent]], List[int]]:
    rng = rng or random.Random()
    observed_serialized_blocks: List[List[int]] = []
    gt_events_per_block: List[List[EditEvent]] = []
    observed_full_sequence: List[int] = []

    for payload in payload_blocks:
        serialized = payload.copy() + [boundary_symbol]
        events: List[EditEvent] = []
        if rng.random() < edit_rate:
            n_edits = sample_num_edits(max_edits_per_block, edit_count_mode, rng)
            for _ in range(n_edits):
                serialized, ev = _apply_one_edit_to_serialized_block(
                    serialized,
                    boundary_symbol=boundary_symbol,
                    allow_boundary_edit=allow_boundary_edit,
                    boundary_edit_modes=boundary_edit_modes,
                    rng=rng,
                )
                if ev is not None:
                    events.append(ev)
        observed_serialized_blocks.append(serialized)
        gt_events_per_block.append(events)
        observed_full_sequence.extend(serialized)
    return observed_serialized_blocks, gt_events_per_block, observed_full_sequence


def apply_edits_to_payload_blocks_with_provenance(
    payload_blocks: List[List[int]],
    edit_rate: float,
    allow_boundary_edit: bool,
    boundary_edit_modes: Tuple[str, ...],
    max_edits_per_block: int,
    edit_count_mode: str,
    boundary_symbol: int = 2,
    rng: Optional[random.Random] = None,
) -> Tuple[List[List[int]], List[List[EditEvent]], List[int], List[Dict[str, Any]]]:
    rng = rng or random.Random()
    observed_blocks: List[List[int]] = []
    gt_events: List[List[EditEvent]] = []
    provenance: List[Dict[str, Any]] = []
    observed_sequence: List[int] = []

    for block_id, payload in enumerate(payload_blocks):
        block_len = len(payload)
        original_serialized = payload.copy() + [boundary_symbol]
        observed_block = original_serialized.copy()
        origins: List[Dict[str, Any]] = [
            {
                "kind": "payload",
                "original_payload_index": int(index),
                "original_value": int(symbol),
            }
            for index, symbol in enumerate(payload)
        ]
        origins.append(
            {
                "kind": "boundary",
                "original_payload_index": None,
                "original_value": int(boundary_symbol),
            }
        )

        if rng.random() < edit_rate:
            n_edits = sample_num_edits(max_edits_per_block, edit_count_mode, rng)
            for insertion_id in range(n_edits):
                observed_block, origins = _apply_one_edit_with_provenance(
                    observed_block,
                    origins,
                    boundary_symbol=boundary_symbol,
                    allow_boundary_edit=allow_boundary_edit,
                    boundary_edit_modes=boundary_edit_modes,
                    insertion_id=insertion_id,
                    block_len=block_len,
                    rng=rng,
                )

        # Ground truth describes the final structural difference, not an edit
        # history that may have canceled itself.
        if observed_block == original_serialized:
            block_events: List[EditEvent] = []
        else:
            block_events = _net_edit_events_from_origins(
                payload,
                observed_block,
                origins,
                boundary_symbol=boundary_symbol,
            )

        observed_blocks.append(observed_block)
        gt_events.append(block_events)
        observed_sequence.extend(observed_block)
        for local_index, (symbol, origin) in enumerate(zip(observed_block, origins)):
            kind = str(origin["kind"])
            if kind == "payload":
                local_original_index = int(origin["original_payload_index"])
            elif kind == "boundary":
                local_original_index = block_len
            else:
                local_original_index = int(origin["original_gap"])
            provenance.append(
                {
                    "origin": "synthetic_block_attack",
                    "original_block_id": int(block_id),
                    "original_structural_index": int(block_id * (block_len + 1) + local_original_index),
                    "original_symbol_kind": kind,
                    "original_payload_index": origin.get("original_payload_index"),
                    "original_gap": origin.get("original_gap"),
                    "edited_structural_symbol": int(symbol),
                    "edited_structural_index": len(provenance),
                    "edited_local_index": int(local_index),
                }
            )
    if len(provenance) != len(observed_sequence):
        raise RuntimeError("Synthetic edit provenance length does not match observed sequence.")
    return observed_blocks, gt_events, observed_sequence, provenance


def _original_gap_for_insertion(
    origins: Sequence[Dict[str, Any]],
    current_gap: int,
    block_len: int,
) -> int:
    right_payload = [
        int(item["original_payload_index"])
        for item in origins[current_gap:]
        if item.get("kind") == "payload"
    ]
    if right_payload:
        return max(0, min(block_len, min(right_payload)))
    left_payload = [
        int(item["original_payload_index"])
        for item in origins[:current_gap]
        if item.get("kind") == "payload"
    ]
    if left_payload:
        return max(0, min(block_len, max(left_payload) + 1))
    return 0


def _apply_one_edit_with_provenance(
    serialized: List[int],
    origins: List[Dict[str, Any]],
    boundary_symbol: int,
    allow_boundary_edit: bool,
    boundary_edit_modes: Tuple[str, ...],
    insertion_id: int,
    block_len: int,
    rng: random.Random,
) -> Tuple[List[int], List[Dict[str, Any]]]:
    x = serialized.copy()
    source = [dict(item) for item in origins]
    boundary_positions = [i for i, token in enumerate(x) if token == boundary_symbol]
    boundary_idx = boundary_positions[-1] if boundary_positions else None
    edit_type = rng.choice(["sub", "insert", "delete"])

    if edit_type == "insert":
        max_gap = len(x) if boundary_idx is None else boundary_idx
        gap = rng.randint(0, max_gap)
        bit = rng.randint(0, 1)
        original_gap = _original_gap_for_insertion(source, gap, block_len)
        x = x[:gap] + [bit] + x[gap:]
        source = source[:gap] + [
            {
                "kind": "insert",
                "original_payload_index": None,
                "original_gap": int(original_gap),
                "insertion_id": int(insertion_id),
                "original_value": None,
            }
        ] + source[gap:]
        return x, source

    if edit_type == "sub":
        payload_positions = [i for i, token in enumerate(x) if token in (0, 1)]
        candidates = payload_positions.copy()
        if allow_boundary_edit and "sub" in boundary_edit_modes and boundary_idx is not None:
            candidates.append(boundary_idx)
        if not candidates:
            return x, source
        pos = rng.choice(candidates)
        before = x[pos]
        x[pos] = 1 - before if before in (0, 1) else rng.choice([0, 1])
        return x, source

    payload_positions = [i for i, token in enumerate(x) if token in (0, 1)]
    candidates = payload_positions.copy()
    if allow_boundary_edit and "delete" in boundary_edit_modes and boundary_idx is not None:
        candidates.append(boundary_idx)
    if not candidates:
        return x, source
    pos = rng.choice(candidates)
    del x[pos]
    del source[pos]
    return x, source


def _net_edit_events_from_origins(
    original_payload: Sequence[int],
    observed_serialized: Sequence[int],
    origins: Sequence[Dict[str, Any]],
    boundary_symbol: int,
) -> List[EditEvent]:
    current_originals: Dict[Tuple[str, int], Tuple[int, Dict[str, Any]]] = {}
    insertions: List[Tuple[int, Dict[str, Any]]] = []
    for symbol, origin in zip(observed_serialized, origins):
        kind = str(origin["kind"])
        if kind == "payload":
            key = ("payload", int(origin["original_payload_index"]))
            current_originals[key] = (int(symbol), origin)
        elif kind == "boundary":
            current_originals[("boundary", len(original_payload))] = (int(symbol), origin)
        elif kind == "insert":
            insertions.append((int(symbol), origin))

    events: List[EditEvent] = []
    for index, before in enumerate(original_payload):
        current = current_originals.get(("payload", index))
        if current is None:
            events.append(EditEvent("delete", ("payload", index), value_before=int(before)))
        elif int(current[0]) != int(before):
            events.append(
                EditEvent(
                    "sub",
                    ("payload", index),
                    value_before=int(before),
                    value_after=int(current[0]),
                )
            )

    boundary_current = current_originals.get(("boundary", len(original_payload)))
    if boundary_current is None:
        events.append(
            EditEvent(
                "delete",
                ("boundary", len(original_payload)),
                value_before=int(boundary_symbol),
            )
        )
    elif int(boundary_current[0]) != int(boundary_symbol):
        events.append(
            EditEvent(
                "sub",
                ("boundary", len(original_payload)),
                value_before=int(boundary_symbol),
                value_after=int(boundary_current[0]),
            )
        )

    for symbol, origin in insertions:
        events.append(
            EditEvent(
                "insert",
                ("gap", int(origin["original_gap"])),
                value_after=int(symbol),
            )
        )
    return events


def _apply_one_edit_to_serialized_block(
    serialized: List[int],
    boundary_symbol: int,
    allow_boundary_edit: bool,
    boundary_edit_modes: Tuple[str, ...],
    rng: random.Random,
) -> Tuple[List[int], Optional[EditEvent]]:
    x = serialized.copy()
    boundary_positions = [i for i, token in enumerate(x) if token == boundary_symbol]
    boundary_idx = boundary_positions[-1] if boundary_positions else None
    edit_type = rng.choice(["sub", "insert", "delete"])

    if edit_type == "insert":
        max_gap = len(x) if boundary_idx is None else boundary_idx
        gap = rng.randint(0, max_gap)
        bit = rng.randint(0, 1)
        x = x[:gap] + [bit] + x[gap:]
        return x, EditEvent("insert", ("gap", gap), value_after=bit)

    if edit_type == "sub":
        payload_positions = [i for i, token in enumerate(x) if token in (0, 1)]
        candidates = payload_positions.copy()
        if allow_boundary_edit and "sub" in boundary_edit_modes and boundary_idx is not None:
            candidates.append(boundary_idx)
        if not candidates:
            return x, None
        pos = rng.choice(candidates)
        before = x[pos]
        after = 1 - before if before in (0, 1) else rng.choice([0, 1])
        x[pos] = after
        if boundary_idx is not None and pos == boundary_idx:
            return x, EditEvent("sub", ("boundary", len(serialized) - 1), value_before=before, value_after=after)
        payload_index = sum(1 for token in x[:pos] if token in (0, 1))
        return x, EditEvent("sub", ("payload", payload_index), value_before=before, value_after=after)

    payload_positions = [i for i, token in enumerate(x) if token in (0, 1)]
    candidates = payload_positions.copy()
    if allow_boundary_edit and "delete" in boundary_edit_modes and boundary_idx is not None:
        candidates.append(boundary_idx)
    if not candidates:
        return x, None
    pos = rng.choice(candidates)
    before = x[pos]
    if boundary_idx is not None and pos == boundary_idx:
        del x[pos]
        return x, EditEvent("delete", ("boundary", len(serialized) - 1), value_before=before)
    payload_index = sum(1 for token in x[:pos] if token in (0, 1))
    del x[pos]
    return x, EditEvent("delete", ("payload", payload_index), value_before=before)


def apply_token_edits_to_blocks(
    token_blocks: List[List[int]],
    edit_rate: float,
    max_edits_per_block: int,
    edit_count_mode: str,
    vocab_ids: Sequence[int],
    rng: Optional[random.Random] = None,
) -> Dict[str, object]:
    rng = rng or random.Random()
    observed_blocks: List[List[int]] = []
    gt_events_per_block: List[List[EditEvent]] = []
    origin_maps_per_block: List[List[int]] = []
    full_sequence: List[int] = []

    usable_vocab = [int(x) for x in vocab_ids]
    for block in token_blocks:
        cur = block.copy()
        origin = list(range(len(block)))
        events: List[EditEvent] = []
        if rng.random() < edit_rate:
            n_edits = sample_num_edits(max_edits_per_block, edit_count_mode, rng)
            for _ in range(n_edits):
                cur, origin, ev = _apply_one_token_edit(cur, origin, usable_vocab, rng)
                if ev is not None:
                    events.append(ev)
        observed_blocks.append(cur)
        origin_maps_per_block.append(origin)
        gt_events_per_block.append(events)
        full_sequence.extend(cur)
    return {
        "observed_blocks": observed_blocks,
        "origin_maps_per_block": origin_maps_per_block,
        "gt_events_per_block": gt_events_per_block,
        "observed_full_sequence": full_sequence,
    }


def _apply_one_token_edit(
    tokens: List[int],
    origin_map: List[int],
    vocab_ids: Sequence[int],
    rng: random.Random,
) -> Tuple[List[int], List[int], Optional[EditEvent]]:
    if not vocab_ids:
        raise ValueError("vocab_ids must not be empty.")
    x = tokens.copy()
    origin = origin_map.copy()
    etype = rng.choice(["sub", "insert", "delete"])

    if etype == "insert":
        gap = rng.randint(0, len(x))
        new_token = int(rng.choice(vocab_ids))
        x = x[:gap] + [new_token] + x[gap:]
        origin = origin[:gap] + [-1] + origin[gap:]
        return x, origin, EditEvent("insert", ("gap", gap), value_after=new_token)

    if etype == "sub":
        if not x:
            return x, origin, None
        pos = rng.randrange(len(x))
        before = x[pos]
        replacement_pool = [token_id for token_id in vocab_ids if int(token_id) != before]
        if not replacement_pool:
            return x, origin, None
        after = int(rng.choice(replacement_pool))
        x[pos] = after
        return x, origin, EditEvent("sub", ("payload", pos), value_before=before, value_after=after)

    if not x:
        return x, origin, None
    pos = rng.randrange(len(x))
    before = x[pos]
    del x[pos]
    del origin[pos]
    return x, origin, EditEvent("delete", ("payload", pos), value_before=before)
