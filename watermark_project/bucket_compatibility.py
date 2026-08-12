from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple


INVALID_PREFIX_POLICIES = {"nearest_feasible", "legacy_unconstrained"}


def build_prefix_to_allowed_bits(
    feasible_codewords: Iterable[Sequence[int]],
) -> Dict[Tuple[int, ...], Set[int]]:
    mapping: Dict[Tuple[int, ...], Set[int]] = defaultdict(set)
    for codeword in feasible_codewords:
        bits = tuple(int(bit) for bit in codeword)
        for index, bit in enumerate(bits):
            mapping[bits[:index]].add(bit)
    return dict(mapping)


def resolve_adaptive_allowed_bits(
    prefix_bits: Sequence[int],
    *,
    feasible_codewords: Iterable[Sequence[int]],
    prefix_to_allowed: Dict[Tuple[int, ...], Set[int]] | None = None,
    invalid_prefix_policy: str = "nearest_feasible",
) -> Tuple[Set[int], str, int]:
    """Resolve the next adaptive bit, recovering from a soft prefix violation.

    Exact prefixes follow the feasible-codeword tree. For an invalid prefix, the
    current protocol retains codewords with minimum prefix Hamming distance and
    continues from their next bits instead of dropping all ECC constraints.
    """
    if invalid_prefix_policy not in INVALID_PREFIX_POLICIES:
        raise ValueError(
            f"Unknown invalid-prefix policy {invalid_prefix_policy!r}; "
            f"expected one of {sorted(INVALID_PREFIX_POLICIES)}."
        )
    codewords = [tuple(int(bit) for bit in codeword) for codeword in feasible_codewords]
    if not codewords:
        raise ValueError("At least one feasible codeword is required.")
    prefix = tuple(int(bit) for bit in prefix_bits)
    if len(prefix) >= len(codewords[0]):
        return set(), "complete", 0
    if any(len(codeword) != len(codewords[0]) for codeword in codewords):
        raise ValueError("All feasible codewords must have the same length.")

    mapping = prefix_to_allowed or build_prefix_to_allowed_bits(codewords)
    exact = set(mapping.get(prefix, set()))
    if exact:
        return exact, "exact", 0
    if invalid_prefix_policy == "legacy_unconstrained":
        return {0, 1}, "legacy_unconstrained", -1

    distances = [
        sum(observed != expected for observed, expected in zip(prefix, codeword))
        for codeword in codewords
    ]
    minimum_distance = min(distances)
    allowed = {
        int(codeword[len(prefix)])
        for codeword, distance in zip(codewords, distances)
        if distance == minimum_distance
    }
    if not allowed:
        raise RuntimeError("Nearest-feasible prefix recovery produced no next bit.")
    return allowed, "nearest_feasible", int(minimum_distance)


def reconstruct_admissible_steps(
    generated_bucket_sequence: Sequence[int],
    *,
    feasible_codewords: Iterable[Sequence[int]],
    block_len: int,
    invalid_prefix_policy: str = "nearest_feasible",
) -> List[Dict[str, Any]]:
    codewords = [tuple(int(bit) for bit in codeword) for codeword in feasible_codewords]
    prefix_to_allowed = build_prefix_to_allowed_bits(codewords)
    current_bits: List[int] = []
    steps: List[Dict[str, Any]] = []

    for step_index, observed_bucket in enumerate(generated_bucket_sequence):
        if len(current_bits) < block_len:
            allowed_bits, prefix_status, prefix_distance = resolve_adaptive_allowed_bits(
                current_bits,
                feasible_codewords=codewords,
                prefix_to_allowed=prefix_to_allowed,
                invalid_prefix_policy=invalid_prefix_policy,
            )
            decision_type = "forced" if len(allowed_bits) == 1 else "branching"
            if prefix_status == "exact":
                step_type = "payload_singleton" if decision_type == "forced" else "payload_flexible"
            elif prefix_status == "nearest_feasible":
                step_type = f"payload_recovery_{decision_type}"
            else:
                step_type = "payload_invalid_prefix"
            allowed_buckets = sorted(allowed_bits)
        else:
            allowed_bits = set()
            allowed_buckets = [2]
            prefix_status = "complete"
            prefix_distance = 0
            decision_type = "boundary"
            step_type = "boundary"

        observed_bucket = int(observed_bucket)
        steps.append(
            {
                "step_index": int(step_index),
                "step_type": step_type,
                "decision_type": decision_type,
                "prefix_status": prefix_status,
                "prefix_distance": int(prefix_distance),
                "prefix_bits": list(current_bits),
                "allowed_buckets": allowed_buckets,
                "used_fallback": prefix_status == "legacy_unconstrained",
                "used_recovery": prefix_status == "nearest_feasible",
                "observed_bucket": observed_bucket,
                "adheres_to_allowed_set": (
                    None
                    if prefix_status == "legacy_unconstrained"
                    else int(observed_bucket in allowed_buckets)
                ),
            }
        )

        if observed_bucket in (0, 1):
            if len(current_bits) < block_len:
                current_bits.append(observed_bucket)
        elif observed_bucket == 2:
            current_bits = []

    return steps


def soft_intervention_kl_nats(
    *,
    log_allowed_mass: float,
    log_disallowed_payload_mass: float,
    logit_bias: float,
) -> float:
    biased_allowed = float(logit_bias) + float(log_allowed_mass)
    if math.isinf(log_disallowed_payload_mass) and log_disallowed_payload_mass < 0:
        log_normalizer = biased_allowed
    else:
        largest = max(biased_allowed, float(log_disallowed_payload_mass))
        log_normalizer = largest + math.log(
            math.exp(biased_allowed - largest)
            + math.exp(float(log_disallowed_payload_mass) - largest)
        )
    q_allowed = math.exp(biased_allowed - log_normalizer)
    return float(logit_bias) * q_allowed - log_normalizer
