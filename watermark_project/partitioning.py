from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

from .config import ECCConfig
from .modeling import BaseLanguageModel, clean_text

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
            key = abs(hash((token_id, token_id % 17))) % max(1, 2**min(8, lsh_bits))
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


def build_payload_buckets(
    model: BaseLanguageModel,
    freq: np.ndarray,
    boundary_ids: Sequence[int],
    config: ECCConfig,
) -> Tuple[List[int], List[int]]:
    boundary_set = set(int(x) for x in boundary_ids)
    special_ids = set(model.all_special_ids)
    candidate_ids = [
        token_id
        for token_id in range(model.vocab_size)
        if token_id not in boundary_set and token_id not in special_ids
    ]
    groups = assign_semantic_groups(model.embedding_matrix(), candidate_ids, config.lsh_bits)
    bucket0: List[int] = []
    bucket1: List[int] = []
    count0 = count1 = 0
    mass0 = mass1 = 0.0
    for _, members in sorted(groups.items(), key=lambda kv: kv[0]):
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


def build_vocabulary_partition(
    model: BaseLanguageModel,
    texts_for_frequency: Sequence[str],
    config: ECCConfig,
) -> VocabularyPartition:
    freq = build_token_frequency(model, texts_for_frequency)
    usable_vocab = max(0, model.vocab_size - len(set(model.all_special_ids)))
    effective_boundary_pool = min(config.target_boundary_pool, max(4, usable_vocab // 6))
    boundary_ids, boundary_report = build_boundary_pool(
        model=model,
        freq=freq,
        target_size=effective_boundary_pool,
    )
    bucket0_ids, bucket1_ids = build_payload_buckets(
        model=model,
        freq=freq,
        boundary_ids=boundary_ids,
        config=config,
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
    )
