from __future__ import annotations

import json
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

from .config import ECCConfig
from .modeling import BaseLanguageModel, clean_text, stable_hash_int

import re

WORDISH_RE = re.compile(r"[A-Za-z]")


MANUAL_BOUNDARY_WORDS = [
    "also", "rather", "quite", "maybe", "perhaps", "indeed", "still", "though", "while", "meanwhile",
    "besides", "instead", "otherwise", "therefore", "however", "moreover", "furthermore", "nonetheless",
    "anyway", "anyhow", "somehow", "somewhat", "altogether", "together", "simply", "mostly", "largely",
    "roughly", "nearly", "barely", "hardly", "clearly", "plainly", "surely", "truly", "really", "actually",
    "basically", "generally", "usually", "normally", "mainly", "partly", "fairly", "softly", "gently",
    "briefly", "quietly", "slowly", "quickly", "openly", "closely", "widely", "deeply", "firmly", "easily",
    "likely", "possibly", "probably", "certainly", "apparently", "naturally", "similarly", "likewise",
    "currently", "presently", "recently", "suddenly", "eventually", "gradually", "finally", "earlier",
    "later", "soon", "today", "tonight", "yesterday", "tomorrow", "already", "yet", "again", "once",
    "twice", "often", "sometimes", "always", "never", "seldom", "rarely", "frequently", "occasionally",
    "simple", "basic", "general", "normal", "common", "usual", "clear", "plain", "direct", "brief",
    "short", "long", "small", "large", "major", "minor", "main", "full", "local", "global",
    "early", "late", "final", "fresh", "quiet", "gentle", "soft", "light", "steady", "stable",
    "equal", "close", "near", "ready", "proper", "formal", "casual", "neutral", "modest", "fair",
    "seem", "seems", "seemed", "appear", "appears", "appeared", "remain", "remains", "remained",
    "become", "becomes", "became", "follow", "follows", "followed", "continue", "continues", "continued",
    "begin", "begins", "began", "started", "start", "starts", "finish", "finished",
    "move", "moves", "moved", "turn", "turns", "turned", "stay", "stays", "stayed",
    "keep", "keeps", "kept", "hold", "holds", "held", "pass", "passes", "passed",
    "separate", "separates", "separated", "connect", "connects", "connected",
    "above", "below", "across", "along", "around", "behind", "beneath", "beside", "between", "beyond",
    "inside", "outside", "within", "without", "toward", "towards", "under", "over", "through",
    "despite", "during", "before", "after", "until", "since", "among", "amongst",
    "detail", "details", "point", "points", "part", "parts", "case", "cases",
    "view", "views", "form", "forms", "style", "styles", "level", "levels",
    "phase", "phases", "period", "periods", "result", "results", "effect", "effects",
    "reason", "reasons", "matter", "matters", "issue", "issues", "change", "changes",
    "state", "states", "value", "values", "note", "notes",
]


@dataclass
class VocabularyPartition:
    token_to_bucket: np.ndarray
    bucket0_ids: List[int]
    bucket1_ids: List[int]
    boundary_ids: List[int]
    banned_ids: List[int]
    boundary_report: List[Dict[str, object]]
    metadata: Dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


def normalize_surface(text: str) -> str:
    text = text.replace("▁", " ").replace("Ġ", " ")
    return re.sub(r"\s+", " ", text).strip()


def build_token_frequency(model: BaseLanguageModel, texts: Sequence[str]) -> np.ndarray:
    freq = np.zeros(model.vocab_size, dtype=np.int64)
    for text in texts:
        for token_id in model.encode(clean_text(text), add_special_tokens=False):
            freq[int(token_id)] += 1
    return freq


def word_to_single_token_id(model: BaseLanguageModel, word: str) -> Optional[int]:
    ids = model.encode(word, add_special_tokens=False)
    if len(ids) == 1:
        return int(ids[0])
    ids2 = model.encode(" " + word, add_special_tokens=False)
    if len(ids2) == 1:
        return int(ids2[0])
    return None


def build_boundary_pool(
    model: BaseLanguageModel,
    freq: np.ndarray,
    target_size: int,
) -> Tuple[List[int], List[Dict[str, object]]]:
    rows: List[Dict[str, object]] = []
    chosen: List[int] = []
    chosen_set: Set[int] = set()
    special_ids = set(model.all_special_ids)
    for word in MANUAL_BOUNDARY_WORDS:
        tok_id = word_to_single_token_id(model, word)
        if tok_id is None:
            rows.append({"word": word, "accepted": False, "reason": "not_single_token", "token_id": None})
            continue
        if tok_id in special_ids:
            rows.append({"word": word, "accepted": False, "reason": "special_token", "token_id": tok_id})
            continue
        if tok_id in chosen_set:
            rows.append({"word": word, "accepted": False, "reason": "duplicate_token_id", "token_id": tok_id})
            continue
        chosen.append(tok_id)
        chosen_set.add(tok_id)
        rows.append(
            {
                "word": word,
                "accepted": True,
                "reason": "manual",
                "token_id": tok_id,
                "decoded": model.decode([tok_id], skip_special_tokens=False),
                "freq": int(freq[tok_id]),
            }
        )
        if len(chosen) >= target_size:
            return chosen[:target_size], rows

    fallback_candidates: List[int] = []
    for token_id in range(model.vocab_size):
        if token_id in chosen_set or token_id in special_ids:
            continue
        surf = normalize_surface(model.token_surface(token_id))
        if not surf or not WORDISH_RE.search(surf):
            continue
        if len(model.encode(surf, add_special_tokens=False)) != 1:
            continue
        fallback_candidates.append(token_id)
    fallback_candidates.sort(key=lambda tid: (freq[tid] == 0, abs(int(freq[tid]) - 8), normalize_surface(model.token_surface(tid)).lower()))
    for token_id in fallback_candidates:
        if len(chosen) >= target_size:
            break
        chosen.append(token_id)
        chosen_set.add(token_id)
        rows.append(
            {
                "word": normalize_surface(model.token_surface(token_id)),
                "accepted": True,
                "reason": "fallback",
                "token_id": token_id,
                "decoded": model.decode([token_id], skip_special_tokens=False),
                "freq": int(freq[token_id]),
            }
        )
    return chosen[:target_size], rows


def assign_semantic_groups(embedding_matrix: Optional[np.ndarray], candidate_ids: List[int], lsh_bits: int) -> Dict[int, List[int]]:
    groups: Dict[int, List[int]] = {}
    if embedding_matrix is None or len(candidate_ids) == 0:
        for token_id in candidate_ids:
            key = stable_hash_int((token_id, token_id % 17), modulo=max(1, 2**min(8, lsh_bits)))
            groups.setdefault(key, []).append(int(token_id))
        return groups

    emb = embedding_matrix[np.array(candidate_ids, dtype=np.int64)]
    rng = np.random.default_rng(20250322)
    projection = rng.standard_normal((emb.shape[1], lsh_bits))
    sign = (emb @ projection > 0).astype(np.int64)
    powers = (1 << np.arange(lsh_bits, dtype=np.int64)).reshape(1, -1)
    gids = (sign * powers).sum(axis=1)
    for token_id, gid in zip(candidate_ids, gids.tolist()):
        groups.setdefault(int(gid), []).append(int(token_id))
    return groups


def resolve_boundary_pool_size(
    model: BaseLanguageModel,
    config: ECCConfig,
) -> Tuple[int, int, str]:
    special_ids = set(int(x) for x in model.all_special_ids)
    eligible_vocab = int(model.vocab_size) - len(special_ids)
    if eligible_vocab < 3:
        raise ValueError("At least three eligible tokens are required for the ECC partition.")

    if config.target_boundary_pool is not None:
        target_size = int(config.target_boundary_pool)
        strategy = "fixed_count"
    else:
        target_size = int(round(float(config.boundary_vocab_fraction) * eligible_vocab))
        strategy = "eligible_vocab_fraction"
    if target_size <= 0 or target_size > eligible_vocab - 2:
        raise ValueError(
            "Boundary allocation must leave at least two eligible payload tokens: "
            f"target={target_size}, eligible={eligible_vocab}."
        )
    return target_size, eligible_vocab, strategy


def build_fractional_boundary_pool(
    model: BaseLanguageModel,
    freq: np.ndarray,
    target_size: int,
    config: ECCConfig,
    embedding_matrix: Optional[np.ndarray] = None,
    semantic_groups: Optional[Dict[int, List[int]]] = None,
) -> Tuple[List[int], List[Dict[str, object]]]:
    """Select an exact-size boundary pool across embedding-based semantic groups."""
    special_ids = set(int(x) for x in model.all_special_ids)
    candidate_ids = [
        token_id for token_id in range(model.vocab_size) if token_id not in special_ids
    ]
    if target_size > len(candidate_ids):
        raise ValueError(
            f"Boundary target {target_size} exceeds {len(candidate_ids)} eligible tokens."
        )
    groups = semantic_groups or assign_semantic_groups(
        embedding_matrix, candidate_ids, config.lsh_bits
    )
    group_items = sorted(groups.items(), key=lambda item: item[0])

    exact_quotas = [target_size * len(members) / len(candidate_ids) for _, members in group_items]
    quotas = [int(np.floor(value)) for value in exact_quotas]
    remainder = target_size - sum(quotas)
    quota_order = sorted(
        range(len(group_items)),
        key=lambda index: (-(exact_quotas[index] - quotas[index]), group_items[index][0]),
    )
    for index in quota_order[:remainder]:
        quotas[index] += 1

    chosen: List[int] = []
    report: List[Dict[str, object]] = []
    for (group_id, members), quota in zip(group_items, quotas):
        if quota == 0:
            continue
        ranked = sorted(members, key=lambda token_id: (-int(freq[token_id]), token_id))
        # Midpoint quantiles spread boundary choices across each group's frequency ranks.
        positions = [int(np.floor((index + 0.5) * len(ranked) / quota)) for index in range(quota)]
        for rank in positions:
            token_id = int(ranked[min(rank, len(ranked) - 1)])
            chosen.append(token_id)
            report.append(
                {
                    "token_id": token_id,
                    "decoded": model.decode([token_id], skip_special_tokens=False),
                    "surface": normalize_surface(model.token_surface(token_id)),
                    "freq": int(freq[token_id]),
                    "semantic_group": int(group_id),
                    "reason": "semantic_group_frequency_quantile",
                }
            )
    if len(chosen) != target_size or len(set(chosen)) != target_size:
        raise RuntimeError(
            "Fractional boundary construction did not produce the requested unique token count: "
            f"requested={target_size}, produced={len(chosen)}, unique={len(set(chosen))}."
        )
    return chosen, report


def _payload_candidates_and_groups(
    model: BaseLanguageModel,
    boundary_ids: Sequence[int],
    config: ECCConfig,
    embedding_matrix: Optional[np.ndarray] = None,
    semantic_groups: Optional[Dict[int, List[int]]] = None,
) -> Dict[int, List[int]]:
    boundary_set = set(int(x) for x in boundary_ids)
    special_ids = set(model.all_special_ids)
    candidate_ids = [
        token_id
        for token_id in range(model.vocab_size)
        if token_id not in boundary_set and token_id not in special_ids
    ]
    if semantic_groups is None:
        groups = assign_semantic_groups(embedding_matrix, candidate_ids, config.lsh_bits)
    else:
        groups = {
            int(group_id): [int(token_id) for token_id in members if token_id not in boundary_set]
            for group_id, members in semantic_groups.items()
        }
        groups = {group_id: members for group_id, members in groups.items() if members}
    return groups


def _split_semantic_group(
    members: Sequence[int],
    freq: np.ndarray,
) -> Tuple[List[int], List[int], float, float]:
    members_sorted = sorted(members, key=lambda tid: (-int(freq[tid]), tid))
    local0: List[int] = []
    local1: List[int] = []
    local_mass0 = local_mass1 = 0.0
    for token_id in members_sorted:
        weight = float(max(int(freq[token_id]), 1))
        if len(local0) < len(local1):
            local0.append(token_id)
            local_mass0 += weight
        elif len(local1) < len(local0):
            local1.append(token_id)
            local_mass1 += weight
        elif local_mass0 <= local_mass1:
            local0.append(token_id)
            local_mass0 += weight
        else:
            local1.append(token_id)
            local_mass1 += weight
    return local0, local1, local_mass0, local_mass1


def build_payload_buckets_paper_main(
    model: BaseLanguageModel,
    freq: np.ndarray,
    boundary_ids: Sequence[int],
    config: ECCConfig,
    embedding_matrix: Optional[np.ndarray] = None,
    semantic_groups: Optional[Dict[int, List[int]]] = None,
) -> Tuple[List[int], List[int]]:
    """Implement the group-local payload split used by the paper's main runs."""
    groups = _payload_candidates_and_groups(
        model=model,
        boundary_ids=boundary_ids,
        config=config,
        embedding_matrix=embedding_matrix,
        semantic_groups=semantic_groups,
    )
    bucket0: List[int] = []
    bucket1: List[int] = []
    count0 = count1 = 0
    mass0 = mass1 = 0.0
    for _, members in sorted(groups.items(), key=lambda kv: kv[0]):
        local0, local1, local_mass0, local_mass1 = _split_semantic_group(members, freq)
        # This is the original paper implementation: orientation changes only
        # when the larger local half would worsen the accumulated count gap.
        if count0 > count1 and len(local0) > len(local1):
            local0, local1 = local1, local0
            local_mass0, local_mass1 = local_mass1, local_mass0
        bucket0.extend(local0)
        bucket1.extend(local1)
        count0 += len(local0)
        count1 += len(local1)
        mass0 += local_mass0
        mass1 += local_mass1
    return bucket0, bucket1


def build_payload_buckets_quality_variant_lsh(
    model: BaseLanguageModel,
    freq: np.ndarray,
    boundary_ids: Sequence[int],
    config: ECCConfig,
    embedding_matrix: Optional[np.ndarray] = None,
    semantic_groups: Optional[Dict[int, List[int]]] = None,
) -> Tuple[List[int], List[int]]:
    """Globally balance LSH groups for the quality-oriented boundary variant."""
    groups = _payload_candidates_and_groups(
        model=model,
        boundary_ids=boundary_ids,
        config=config,
        embedding_matrix=embedding_matrix,
        semantic_groups=semantic_groups,
    )
    bucket0: List[int] = []
    bucket1: List[int] = []
    count0 = count1 = 0
    mass0 = mass1 = 0.0
    for _, members in sorted(groups.items(), key=lambda kv: kv[0]):
        local0, local1, local_mass0, local_mass1 = _split_semantic_group(members, freq)
        keep_count_gap = abs((count0 + len(local0)) - (count1 + len(local1)))
        swap_count_gap = abs((count0 + len(local1)) - (count1 + len(local0)))
        keep_mass_gap = abs((mass0 + local_mass0) - (mass1 + local_mass1))
        swap_mass_gap = abs((mass0 + local_mass1) - (mass1 + local_mass0))
        if swap_count_gap < keep_count_gap or (
            swap_count_gap == keep_count_gap and swap_mass_gap < keep_mass_gap
        ):
            local0, local1 = local1, local0
            local_mass0, local_mass1 = local_mass1, local_mass0
        bucket0.extend(local0)
        bucket1.extend(local1)
        count0 += len(local0)
        count1 += len(local1)
        mass0 += local_mass0
        mass1 += local_mass1
    return bucket0, bucket1


def build_payload_buckets(
    model: BaseLanguageModel,
    freq: np.ndarray,
    boundary_ids: Sequence[int],
    config: ECCConfig,
    embedding_matrix: Optional[np.ndarray] = None,
    semantic_groups: Optional[Dict[int, List[int]]] = None,
) -> Tuple[List[int], List[int]]:
    builders = {
        "paper_main": build_payload_buckets_paper_main,
        "quality_variant_lsh": build_payload_buckets_quality_variant_lsh,
    }
    return builders[config.payload_split_strategy](
        model=model,
        freq=freq,
        boundary_ids=boundary_ids,
        config=config,
        embedding_matrix=embedding_matrix,
        semantic_groups=semantic_groups,
    )


def build_vocabulary_partition(
    model: BaseLanguageModel,
    texts_for_frequency: Sequence[str],
    config: ECCConfig,
) -> VocabularyPartition:
    freq = build_token_frequency(model, texts_for_frequency)
    embedding_matrix = model.embedding_matrix()
    target_size, eligible_vocab, boundary_strategy = resolve_boundary_pool_size(model, config)
    semantic_groups: Optional[Dict[int, List[int]]] = None
    if config.target_boundary_pool is None:
        eligible_ids = [
            token_id
            for token_id in range(model.vocab_size)
            if token_id not in set(int(x) for x in model.all_special_ids)
        ]
        semantic_groups = assign_semantic_groups(
            embedding_matrix, eligible_ids, config.lsh_bits
        )
        boundary_ids, boundary_report = build_fractional_boundary_pool(
            model=model,
            freq=freq,
            target_size=target_size,
            config=config,
            embedding_matrix=embedding_matrix,
            semantic_groups=semantic_groups,
        )
    else:
        boundary_ids, boundary_report = build_boundary_pool(
            model=model,
            freq=freq,
            target_size=target_size,
        )
    bucket0_ids, bucket1_ids = build_payload_buckets(
        model=model,
        freq=freq,
        boundary_ids=boundary_ids,
        config=config,
        embedding_matrix=embedding_matrix,
        semantic_groups=semantic_groups,
    )
    token_to_bucket = np.full(model.vocab_size, fill_value=-1, dtype=np.int16)
    token_to_bucket[np.array(bucket0_ids, dtype=np.int64)] = 0
    token_to_bucket[np.array(bucket1_ids, dtype=np.int64)] = 1
    token_to_bucket[np.array(boundary_ids, dtype=np.int64)] = 2
    banned_ids = sorted(set(int(x) for x in model.all_special_ids))
    return VocabularyPartition(
        token_to_bucket=token_to_bucket,
        bucket0_ids=bucket0_ids,
        bucket1_ids=bucket1_ids,
        boundary_ids=boundary_ids,
        banned_ids=banned_ids,
        boundary_report=boundary_report,
        metadata={
            **model_partition_identity(model),
            "payload_split_source": (
                "embedding_lsh" if embedding_matrix is not None else "deterministic_hash_fallback_no_lm_weights"
            ),
            "lsh_bits": int(config.lsh_bits),
            "payload_split_strategy": config.payload_split_strategy,
            "boundary_selection_source": (
                "embedding_lsh_stratified_fraction"
                if config.target_boundary_pool is None and embedding_matrix is not None
                else "deterministic_hash_stratified_fraction"
                if config.target_boundary_pool is None
                else "curated_fixed_count"
            ),
            "boundary_allocation_strategy": boundary_strategy,
            "target_boundary_size": int(target_size),
            "eligible_vocab_size": int(eligible_vocab),
            "boundary_vocab_fraction_requested": (
                float(config.boundary_vocab_fraction)
                if config.target_boundary_pool is None
                else None
            ),
            "boundary_vocab_fraction_realized": float(len(boundary_ids) / eligible_vocab),
        },
    )


def build_vocabulary_partition_from_boundary_ids(
    model: BaseLanguageModel,
    texts_for_frequency: Sequence[str],
    config: ECCConfig,
    boundary_ids: Sequence[int],
    boundary_report: Optional[List[Dict[str, object]]] = None,
) -> VocabularyPartition:
    """Build bucket0/1 around an externally fixed bucket2 boundary set."""
    freq = build_token_frequency(model, texts_for_frequency)
    boundary_ids = [int(x) for x in boundary_ids]
    embedding_matrix = model.embedding_matrix()
    bucket0_ids, bucket1_ids = build_payload_buckets(
        model=model,
        freq=freq,
        boundary_ids=boundary_ids,
        config=config,
        embedding_matrix=embedding_matrix,
    )
    token_to_bucket = np.full(model.vocab_size, fill_value=-1, dtype=np.int16)
    token_to_bucket[np.array(bucket0_ids, dtype=np.int64)] = 0
    token_to_bucket[np.array(bucket1_ids, dtype=np.int64)] = 1
    token_to_bucket[np.array(boundary_ids, dtype=np.int64)] = 2
    banned_ids = sorted(set(int(x) for x in model.all_special_ids))
    return VocabularyPartition(
        token_to_bucket=token_to_bucket,
        bucket0_ids=bucket0_ids,
        bucket1_ids=bucket1_ids,
        boundary_ids=boundary_ids,
        banned_ids=banned_ids,
        boundary_report=boundary_report or [],
        metadata={
            **model_partition_identity(model),
            "payload_split_source": (
                "embedding_lsh" if embedding_matrix is not None else "deterministic_hash_fallback_no_lm_weights"
            ),
            "lsh_bits": int(config.lsh_bits),
            "payload_split_strategy": config.payload_split_strategy,
            "boundary_selection_source": "externally_fixed",
            "boundary_allocation_strategy": "fixed_count",
            "target_boundary_size": int(len(boundary_ids)),
            "eligible_vocab_size": int(model.vocab_size - len(set(model.all_special_ids))),
            "boundary_vocab_fraction_realized": float(
                len(boundary_ids) / max(1, model.vocab_size - len(set(model.all_special_ids)))
            ),
        },
    )


def model_partition_identity(model: BaseLanguageModel) -> Dict[str, Any]:
    tokenizer = getattr(model, "tokenizer", None)
    config = getattr(model, "config", None)
    model_name = getattr(config, "model_name", None) or getattr(tokenizer, "name_or_path", model.__class__.__name__)
    tokenizer_digest = hashlib.sha256()
    if tokenizer is not None and hasattr(tokenizer, "get_vocab"):
        vocab_items = sorted(
            ((int(token_id), str(token)) for token, token_id in tokenizer.get_vocab().items()),
            key=lambda item: (item[0], item[1]),
        )
    elif hasattr(model, "id_to_token"):
        vocab_items = [(index, str(token)) for index, token in enumerate(model.id_to_token)]
    else:
        vocab_items = [
            (token_id, str(model.token_surface(token_id)))
            for token_id in range(int(model.vocab_size))
        ]
    for token_id, token in vocab_items:
        tokenizer_digest.update(int(token_id).to_bytes(8, byteorder="little", signed=False))
        tokenizer_digest.update(token.encode("utf-8", errors="surrogatepass"))
        tokenizer_digest.update(b"\0")
    return {
        "model_name": str(model_name),
        "tokenizer_name_or_path": str(getattr(tokenizer, "name_or_path", model_name)),
        "tokenizer_class": tokenizer.__class__.__name__ if tokenizer is not None else model.__class__.__name__,
        "tokenizer_vocab_size": int(model.vocab_size),
        "tokenizer_vocab_sha256": tokenizer_digest.hexdigest(),
    }


def partition_checksum(partition: VocabularyPartition) -> str:
    digest = hashlib.sha256()
    for values in (
        np.asarray(partition.token_to_bucket, dtype=np.int16),
        np.asarray(partition.bucket0_ids, dtype=np.int32),
        np.asarray(partition.bucket1_ids, dtype=np.int32),
        np.asarray(partition.boundary_ids, dtype=np.int32),
        np.asarray(partition.banned_ids, dtype=np.int32),
    ):
        digest.update(values.tobytes(order="C"))
    return digest.hexdigest()


def validate_vocabulary_partition(
    partition: VocabularyPartition,
    model: BaseLanguageModel,
    *,
    require_semantic_split: bool = False,
) -> None:
    model_vocab_size = int(model.vocab_size)
    if len(partition.token_to_bucket) != model_vocab_size:
        raise ValueError(
            "Loaded vocabulary partition does not match the model vocabulary size: "
            f"partition={len(partition.token_to_bucket)} model={model_vocab_size}."
        )
    active_identity = model_partition_identity(model)
    expected_name = str(active_identity["model_name"])
    saved_name = partition.metadata.get("model_name")
    if saved_name and str(saved_name) != expected_name:
        raise ValueError(
            "Loaded vocabulary partition was built for a different model: "
            f"partition={saved_name!r} requested={expected_name!r}."
        )
    saved_vocab_size = partition.metadata.get("tokenizer_vocab_size")
    if saved_vocab_size is not None and int(saved_vocab_size) != model_vocab_size:
        raise ValueError(
            "Loaded vocabulary partition tokenizer size does not match the active tokenizer: "
            f"partition={saved_vocab_size} tokenizer={model_vocab_size}."
        )
    saved_vocab_hash = partition.metadata.get("tokenizer_vocab_sha256")
    active_vocab_hash = active_identity["tokenizer_vocab_sha256"]
    if saved_vocab_hash and str(saved_vocab_hash) != active_vocab_hash:
        raise ValueError(
            "Loaded vocabulary partition tokenizer vocabulary/order does not match the active tokenizer."
        )
    split_source = partition.metadata.get("payload_split_source")
    if require_semantic_split and split_source != "embedding_lsh":
        raise ValueError(
            "This run requires an embedding-based semantic partition, but the loaded artifact "
            f"records payload_split_source={split_source!r}."
        )

    bucket_sets = [
        set(int(x) for x in partition.bucket0_ids),
        set(int(x) for x in partition.bucket1_ids),
        set(int(x) for x in partition.boundary_ids),
    ]
    if bucket_sets[0] & bucket_sets[1] or bucket_sets[0] & bucket_sets[2] or bucket_sets[1] & bucket_sets[2]:
        raise ValueError("Vocabulary partition buckets overlap.")
    for bucket_id, token_ids in enumerate(bucket_sets):
        for token_id in token_ids:
            if token_id < 0 or token_id >= model_vocab_size:
                raise ValueError(f"Vocabulary partition contains out-of-range token id {token_id}.")
            if int(partition.token_to_bucket[token_id]) != bucket_id:
                raise ValueError(
                    f"token_to_bucket disagrees with bucket{bucket_id}_ids for token {token_id}."
                )


def save_vocabulary_partition(
    partition: VocabularyPartition,
    output_dir: str | Path,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    np.save(output_path / "token_to_bucket.npy", partition.token_to_bucket.astype(np.int16))
    np.save(output_path / "bucket0_ids.npy", np.array(partition.bucket0_ids, dtype=np.int32))
    np.save(output_path / "bucket1_ids.npy", np.array(partition.bucket1_ids, dtype=np.int32))
    np.save(output_path / "bucket2_ids.npy", np.array(partition.boundary_ids, dtype=np.int32))
    np.save(output_path / "banned_ids.npy", np.array(partition.banned_ids, dtype=np.int32))
    with open(output_path / "boundary_report.json", "w", encoding="utf-8") as handle:
        json.dump(partition.boundary_report, handle, ensure_ascii=False, indent=2)
    combined_metadata = {**partition.metadata, **(metadata or {})}
    combined_metadata["partition_checksum_sha256"] = partition_checksum(partition)
    config_payload = {
        "num_bucket0": len(partition.bucket0_ids),
        "num_bucket1": len(partition.bucket1_ids),
        "num_bucket2": len(partition.boundary_ids),
        "num_banned": len(partition.banned_ids),
        "metadata": combined_metadata,
    }
    with open(output_path / "partition_config.json", "w", encoding="utf-8") as handle:
        json.dump(config_payload, handle, ensure_ascii=False, indent=2)


def load_vocabulary_partition(partition_dir: str | Path) -> VocabularyPartition:
    partition_path = Path(partition_dir)
    token_to_bucket = np.load(partition_path / "token_to_bucket.npy", allow_pickle=False).astype(np.int16)
    bucket0_ids = np.load(partition_path / "bucket0_ids.npy", allow_pickle=False).astype(np.int64).tolist()
    bucket1_ids = np.load(partition_path / "bucket1_ids.npy", allow_pickle=False).astype(np.int64).tolist()
    boundary_ids = np.load(partition_path / "bucket2_ids.npy", allow_pickle=False).astype(np.int64).tolist()
    banned_path = partition_path / "banned_ids.npy"
    banned_ids = np.load(banned_path, allow_pickle=False).astype(np.int64).tolist() if banned_path.exists() else []
    report_path = partition_path / "boundary_report.json"
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as handle:
            boundary_report = json.load(handle)
    else:
        boundary_report = []
    config_path = partition_path / "partition_config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as handle:
            metadata = dict(json.load(handle).get("metadata") or {})
    else:
        metadata = {}
    partition = VocabularyPartition(
        token_to_bucket=token_to_bucket,
        bucket0_ids=[int(x) for x in bucket0_ids],
        bucket1_ids=[int(x) for x in bucket1_ids],
        boundary_ids=[int(x) for x in boundary_ids],
        banned_ids=[int(x) for x in banned_ids],
        boundary_report=boundary_report,
        metadata=metadata,
    )
    expected_checksum = metadata.get("partition_checksum_sha256")
    if expected_checksum and str(expected_checksum) != partition_checksum(partition):
        raise ValueError(f"Vocabulary partition checksum mismatch in {partition_path}.")
    return partition
