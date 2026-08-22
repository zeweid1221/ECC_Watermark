"""Readable synchronization-string plus VT baseline used by the accepted work.

The implementation is intentionally independent from the ECC-IW generator and
detector. It reproduces the accepted construction's structural protocol:

* eight keyed vocabulary buckets encode a binary VT symbol and a four-ary
  synchronization symbol;
* each length-seven block draws a codeword from VT_a(7);
* a keyed permutation changes the effective bucket labels at every position;
* detection aligns the observed tokens to the expected synchronization string
  before checking the recovered VT blocks.

The surrounding LFQA runner supplies the current repository's prompt rendering,
sampling, perplexity, attack, and result-serialization conventions.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np

from watermark_project.config import GenerationProtocolConfig
from watermark_project.modeling import (
    BaseLanguageModel,
    apply_repetition_penalty,
    build_ascii_token_ban_mask,
    render_prompt_for_model,
    sample_token_from_logits,
    stable_hash_int,
)


MASK63 = 0x7FFFFFFFFFFFFFFF
SIGNED_GOLDEN_RATIO = -7046029254386353131


@dataclass(frozen=True)
class SyncEccConfig:
    block_len: int = 7
    sigma_size: int = 4
    vt_a: int = 4
    seed: int = 19920408
    seed_bucket: int | None = None
    seed_sync: int | None = None
    seed_message: int | None = None
    random_partition_each_step: bool = True

    @property
    def bucket_count(self) -> int:
        return 2 * int(self.sigma_size)

    @property
    def resolved_seed_bucket(self) -> int:
        return int(self.seed_bucket if self.seed_bucket is not None else self.seed ^ 0xA5A5A5A5)

    @property
    def resolved_seed_sync(self) -> int:
        return int(self.seed_sync if self.seed_sync is not None else self.seed ^ 0x3C3C3C3C)

    @property
    def resolved_seed_message(self) -> int:
        return int(self.seed_message if self.seed_message is not None else self.seed ^ 0x5A5A5A5A)

    def validate(self) -> None:
        if self.block_len != 7:
            raise ValueError("The accepted sync-ECC protocol uses block_len=7.")
        if self.sigma_size != 4:
            raise ValueError("The accepted sync-ECC protocol uses sigma_size=4.")
        if not 0 <= self.vt_a <= self.block_len:
            raise ValueError("vt_a must lie in [0, block_len].")


@dataclass
class SyncEccGenerationResult:
    prompt: str
    user_prompt: str
    rendered_prompt: str
    prompt_mode: str
    prompt_token_ids: List[int]
    generated_token_ids: List[int]
    suffix_text: str
    full_text: str
    target_codewords: List[List[int]]
    target_bits: List[int]
    target_sync_symbols: List[int]
    target_step_buckets: List[int]
    observed_bits: List[int]
    observed_sync_symbols: List[int]
    observed_step_buckets: List[int]
    block_tokens: List[List[int]]
    tag_adherence: float
    sync_adherence: float
    bit_adherence: float
    clean_vt_valid_rate: float


@dataclass(frozen=True)
class SyncEditEvent:
    op: str
    block_id: int
    local_position: int
    global_position: int


@dataclass
class SyncAttackResult:
    observed_token_ids: List[int]
    observed_blocks: List[List[int]]
    gt_events_per_block: List[List[SyncEditEvent]]
    gt_blocks: List[int]
    realized_edits: int


@dataclass
class SyncAlignmentResult:
    observed_to_expected: List[int]
    insertion_observed_indices: List[int]
    deletion_expected_positions: List[int]
    distance: int


@dataclass
class SyncDetectionResult:
    alignment: SyncAlignmentResult
    predicted_blocks: List[int]
    alignment_blocks: List[int]
    vt_inconsistent_blocks: List[int]
    block_bits: List[List[int]]
    block_distances: List[int]
    candidate_positions: List[int]
    candidate_events_by_block: Dict[int, List[Tuple[str, int]]]


def vt_syndrome(bits: Sequence[int]) -> int:
    return sum(index * int(bit) for index, bit in enumerate(bits, start=1))


def build_vt_codebook(block_len: int = 7, vt_a: int = 4) -> List[List[int]]:
    modulus = int(block_len) + 1
    syndrome = int(vt_a) % modulus
    codebook: List[List[int]] = []
    for value in range(1 << int(block_len)):
        bits = [
            (value >> (int(block_len) - 1 - index)) & 1
            for index in range(int(block_len))
        ]
        if vt_syndrome(bits) % modulus == syndrome:
            codebook.append(bits)
    if not codebook:
        raise RuntimeError("VT codebook construction returned no codewords.")
    return codebook


def levenshtein_distance(left: Sequence[int], right: Sequence[int]) -> int:
    previous = list(range(len(right) + 1))
    for i, left_value in enumerate(left, start=1):
        current = [i]
        for j, right_value in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + int(int(left_value) != int(right_value)),
                )
            )
        previous = current
    return int(previous[-1])


def levenshtein_ops(left: Sequence[int], right: Sequence[int]) -> List[str]:
    """Return the accepted evaluator's deterministic optimal edit script."""
    rows, cols = len(left) + 1, len(right) + 1
    dp = np.zeros((rows, cols), dtype=np.int32)
    back = np.full((rows, cols), "", dtype="<U1")
    for row in range(1, rows):
        dp[row, 0] = row
        back[row, 0] = "D"
    for col in range(1, cols):
        dp[0, col] = col
        back[0, col] = "I"
    for row in range(1, rows):
        for col in range(1, cols):
            best = int(dp[row - 1, col]) + 1
            move = "D"
            insertion = int(dp[row, col - 1]) + 1
            if insertion < best:
                best = insertion
                move = "I"
            substitution_cost = int(int(left[row - 1]) != int(right[col - 1]))
            diagonal = int(dp[row - 1, col - 1]) + substitution_cost
            if diagonal < best:
                best = diagonal
                move = "M" if substitution_cost == 0 else "S"
            dp[row, col] = best
            back[row, col] = move
    operations: List[str] = []
    row, col = len(left), len(right)
    while row > 0 or col > 0:
        move = str(back[row, col])
        operations.append(move)
        if move in {"M", "S"}:
            row -= 1
            col -= 1
        elif move == "D":
            row -= 1
        elif move == "I":
            col -= 1
        else:
            raise RuntimeError("Levenshtein backtracking failed.")
    operations.reverse()
    return operations


def nearest_codeword_candidates(
    observed_bits: Sequence[int],
    codebook: Sequence[Sequence[int]],
    block_len: int,
) -> Tuple[List[int], int, List[Tuple[str, int]]]:
    """Reproduce accepted nearest-codeword tie-breaking and candidate extraction."""
    best_codeword = list(codebook[0])
    best_operations = levenshtein_ops(best_codeword, observed_bits)
    best_distance = sum(operation != "M" for operation in best_operations)
    for codeword in codebook[1:]:
        operations = levenshtein_ops(codeword, observed_bits)
        distance = sum(operation != "M" for operation in operations)
        if distance < best_distance:
            best_codeword = list(codeword)
            best_operations = operations
            best_distance = distance

    if len(observed_bits) == int(block_len):
        return best_codeword, int(best_distance), []
    codeword_index = 0
    insertion_candidates: List[int] = []
    deletion_candidates: List[int] = []
    for operation in best_operations:
        if operation in {"M", "S"}:
            codeword_index += 1
        elif operation == "D":
            if 0 <= codeword_index < int(block_len):
                deletion_candidates.append(codeword_index)
            codeword_index += 1
        elif operation == "I" and 0 <= codeword_index <= int(block_len):
            insertion_candidates.append(codeword_index)
    if len(observed_bits) > int(block_len):
        candidates = [("insert", value) for value in sorted(set(insertion_candidates))]
    else:
        candidates = [("delete", value) for value in sorted(set(deletion_candidates))]
    return best_codeword, int(best_distance), candidates


class SyncEccSchedule:
    """Key schedule and exact accepted-work token-to-bucket mapping."""

    def __init__(self, vocab_size: int, config: SyncEccConfig):
        config.validate()
        self.config = config
        self.vocab_size = int(vocab_size)
        self.codebook = build_vt_codebook(config.block_len, config.vt_a)
        self.base_bucket_ids = np.asarray(
            [self._base_bucket(token_id) for token_id in range(self.vocab_size)],
            dtype=np.int16,
        )

    @staticmethod
    def _splitmix64(value: int) -> int:
        value = (int(value) + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        mixed = value
        mixed = (mixed ^ (mixed >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
        mixed = (mixed ^ (mixed >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
        return (mixed ^ (mixed >> 31)) & 0xFFFFFFFFFFFFFFFF

    def _prg_u64(self, seed: int, index: int) -> int:
        value = (int(seed) ^ (int(index) * 0x9E3779B97F4A7C15)) & 0xFFFFFFFFFFFFFFFF
        return self._splitmix64(value)

    def _prg_int(self, seed: int, index: int, modulus: int) -> int:
        return int(self._prg_u64(seed, index) % int(modulus))

    def _base_bucket(self, token_id: int) -> int:
        value = (int(token_id) ^ (self.config.resolved_seed_bucket & MASK63)) & MASK63
        value = (value * SIGNED_GOLDEN_RATIO) & MASK63
        value = (value ^ (value >> 33)) & MASK63
        return int(value % self.config.bucket_count)

    def sync_symbol(self, step: int) -> int:
        return self._prg_int(
            self.config.resolved_seed_sync,
            int(step),
            self.config.sigma_size,
        )

    def bucket_permutation(self, step: int) -> List[int]:
        values = list(range(self.config.bucket_count))
        if not self.config.random_partition_each_step:
            return values
        for index in range(self.config.bucket_count - 1, 0, -1):
            swap = self._prg_int(
                self.config.resolved_seed_bucket ^ 0xBADC0FFE,
                (int(step) << 8) + index,
                index + 1,
            )
            values[index], values[swap] = values[swap], values[index]
        return values

    def step_bucket(self, token_id: int, step: int) -> int:
        base = int(self.base_bucket_ids[int(token_id)])
        return int(self.bucket_permutation(step)[base])

    def decoded_tag(self, token_id: int, step: int) -> Tuple[int, int, int]:
        bucket = self.step_bucket(token_id, step)
        return bucket // self.config.sigma_size, bucket % self.config.sigma_size, bucket

    def base_bucket_for_target(self, target_step_bucket: int, step: int) -> int:
        permutation = self.bucket_permutation(step)
        inverse = [0] * self.config.bucket_count
        for base_bucket, step_bucket in enumerate(permutation):
            inverse[int(step_bucket)] = int(base_bucket)
        return int(inverse[int(target_step_bucket)])

    def sample_codewords(self, num_sequences: int, target_blocks: int) -> List[List[List[int]]]:
        """Match the accepted batched generator's block-major random stream."""
        rng = random.Random(self.config.resolved_seed_message)
        messages = [[0] * int(target_blocks) for _ in range(int(num_sequences))]
        for block_id in range(int(target_blocks)):
            for sequence_index in range(int(num_sequences)):
                messages[sequence_index][block_id] = rng.randrange(len(self.codebook))
        return [
            [list(self.codebook[message]) for message in row]
            for row in messages
        ]


def align_sync_tokens(
    schedule: SyncEccSchedule,
    observed_token_ids: Sequence[int],
    expected_length: int,
) -> SyncAlignmentResult:
    """Align edited tokens to the keyed synchronization sequence."""
    observed = [int(value) for value in observed_token_ids]
    expected_sync = [schedule.sync_symbol(step) for step in range(int(expected_length))]
    rows = len(observed) + 1
    cols = int(expected_length) + 1
    dp = np.full((rows, cols), 10**9, dtype=np.int32)
    back = np.full((rows, cols), -1, dtype=np.int8)  # 0=diag, 1=insert, 2=delete
    dp[0, 0] = 0
    for row in range(1, rows):
        dp[row, 0] = row
        back[row, 0] = 1
    for col in range(1, cols):
        dp[0, col] = col
        back[0, col] = 2
    for row in range(1, rows):
        token_id = observed[row - 1]
        for col in range(1, cols):
            best = int(dp[row - 1, col]) + 1
            move = 1
            deletion = int(dp[row, col - 1]) + 1
            if deletion < best:
                best = deletion
                move = 2
            _, implied_sync, _ = schedule.decoded_tag(token_id, col - 1)
            if implied_sync == expected_sync[col - 1]:
                diagonal = int(dp[row - 1, col - 1])
                if diagonal <= best:
                    best = diagonal
                    move = 0
            dp[row, col] = best
            back[row, col] = move

    mapping = [-1] * len(observed)
    insertions: List[int] = []
    deletions: List[int] = []
    row, col = len(observed), int(expected_length)
    while row > 0 or col > 0:
        move = int(back[row, col])
        if move == 0:
            mapping[row - 1] = col - 1
            row -= 1
            col -= 1
        elif move == 1:
            insertions.append(row - 1)
            row -= 1
        elif move == 2:
            deletions.append(col - 1)
            col -= 1
        else:
            raise RuntimeError("Synchronization alignment backtracking failed.")
    insertions.reverse()
    deletions.reverse()
    return SyncAlignmentResult(
        observed_to_expected=mapping,
        insertion_observed_indices=insertions,
        deletion_expected_positions=deletions,
        distance=int(dp[len(observed), int(expected_length)]),
    )


class SyncEccWatermark:
    def __init__(
        self,
        model: BaseLanguageModel,
        config: SyncEccConfig,
        protocol: GenerationProtocolConfig,
    ):
        self.model = model
        self.config = config
        self.protocol = protocol
        self.schedule = SyncEccSchedule(model.vocab_size, config)
        self.ban_mask = build_ascii_token_ban_mask(model, protocol.ascii_token_filter)
        for token_id in model.all_special_ids:
            if 0 <= int(token_id) < len(self.ban_mask):
                self.ban_mask[int(token_id)] = True

    def generate_one(
        self,
        prompt: str,
        *,
        codewords: Sequence[Sequence[int]],
        logit_bias: float,
        hard: bool,
        max_new_tokens: int,
        seed: int,
    ) -> SyncEccGenerationResult:
        target_bits = [int(bit) for codeword in codewords for bit in codeword]
        if len(target_bits) > int(max_new_tokens):
            raise ValueError("max_new_tokens is smaller than the requested sync-ECC sequence.")
        user_prompt, rendered_prompt, prompt_mode = render_prompt_for_model(
            self.model,
            prompt,
            self.protocol,
        )
        session = self.model.start_session(
            rendered_prompt,
            add_special_tokens=prompt_mode != "chat_template",
            clean=prompt_mode != "chat_template",
        )
        if not session.prompt_ids:
            raise RuntimeError("The rendered prompt produced no token ids.")
        rng = np.random.default_rng(
            (int(seed) + stable_hash_int(rendered_prompt)) % (2**32)
        )
        generated_ids: List[int] = []
        target_sync: List[int] = []
        target_buckets: List[int] = []
        observed_bits: List[int] = []
        observed_sync: List[int] = []
        observed_buckets: List[int] = []

        for step, target_bit in enumerate(target_bits):
            raw_logits = np.asarray(session.next_logits(), dtype=np.float64)
            adjusted = apply_repetition_penalty(
                raw_logits,
                generated_ids,
                self.protocol.repetition_penalty,
            )
            adjusted[self.ban_mask] = -1e9
            sync_symbol = self.schedule.sync_symbol(step)
            target_bucket = int(target_bit) * self.config.sigma_size + sync_symbol
            base_bucket = self.schedule.base_bucket_for_target(target_bucket, step)
            allowed = self.schedule.base_bucket_ids == base_bucket
            allowed &= ~self.ban_mask
            if not np.any(allowed):
                raise RuntimeError(f"No usable token remains in target bucket at step {step}.")
            if hard:
                adjusted[~allowed] = -1e9
            else:
                adjusted = adjusted + float(logit_bias) * allowed.astype(np.float64)
            next_id = sample_token_from_logits(adjusted, rng, self.protocol)
            bit, observed_sync_symbol, observed_bucket = self.schedule.decoded_tag(next_id, step)
            session.append(next_id)
            generated_ids.append(int(next_id))
            target_sync.append(int(sync_symbol))
            target_buckets.append(int(target_bucket))
            observed_bits.append(int(bit))
            observed_sync.append(int(observed_sync_symbol))
            observed_buckets.append(int(observed_bucket))

        block_len = self.config.block_len
        block_tokens = [
            generated_ids[start : start + block_len]
            for start in range(0, len(generated_ids), block_len)
        ]
        valid_blocks = [
            int(
                len(bits) == block_len
                and vt_syndrome(bits) % (block_len + 1) == self.config.vt_a
            )
            for bits in (
                observed_bits[start : start + block_len]
                for start in range(0, len(observed_bits), block_len)
            )
        ]
        target_array = np.asarray(target_buckets, dtype=np.int16)
        observed_array = np.asarray(observed_buckets, dtype=np.int16)
        return SyncEccGenerationResult(
            prompt=prompt,
            user_prompt=user_prompt,
            rendered_prompt=rendered_prompt,
            prompt_mode=prompt_mode,
            prompt_token_ids=[int(value) for value in session.prompt_ids],
            generated_token_ids=generated_ids,
            suffix_text=self.model.decode(generated_ids, skip_special_tokens=True),
            full_text=self.model.decode(
                list(session.prompt_ids) + generated_ids,
                skip_special_tokens=True,
            ),
            target_codewords=[list(map(int, codeword)) for codeword in codewords],
            target_bits=target_bits,
            target_sync_symbols=target_sync,
            target_step_buckets=target_buckets,
            observed_bits=observed_bits,
            observed_sync_symbols=observed_sync,
            observed_step_buckets=observed_buckets,
            block_tokens=block_tokens,
            tag_adherence=float(np.mean(target_array == observed_array)),
            sync_adherence=float(np.mean(np.asarray(target_sync) == np.asarray(observed_sync))),
            bit_adherence=float(np.mean(np.asarray(target_bits) == np.asarray(observed_bits))),
            clean_vt_valid_rate=float(np.mean(valid_blocks)),
        )

    def align(self, observed_token_ids: Sequence[int], expected_length: int) -> SyncAlignmentResult:
        return align_sync_tokens(self.schedule, observed_token_ids, expected_length)

    def detect(self, observed_token_ids: Sequence[int], expected_blocks: int) -> SyncDetectionResult:
        expected_length = int(expected_blocks) * self.config.block_len
        alignment = self.align(observed_token_ids, expected_length)
        mapping = alignment.observed_to_expected
        raw_block_ids = [
            -1 if int(position) < 0 else int(position) // self.config.block_len
            for position in mapping
        ]
        assigned_block_ids = assign_insertions_to_neighbor_block(raw_block_ids)
        block_bits: List[List[int]] = [[] for _ in range(int(expected_blocks))]
        alignment_blocks = {
            int(position // self.config.block_len)
            for position in alignment.deletion_expected_positions
            if 0 <= position < expected_length
        }
        candidate_positions = list(alignment.deletion_expected_positions)
        for observed_index, token_id in enumerate(observed_token_ids):
            block_id = int(assigned_block_ids[observed_index])
            if not 0 <= block_id < int(expected_blocks):
                continue
            expected_position = int(mapping[observed_index])
            if expected_position < 0:
                expected_position = min(
                    expected_length - 1,
                    block_id * self.config.block_len
                    + min(len(block_bits[block_id]), self.config.block_len - 1),
                )
            bit, _, _ = self.schedule.decoded_tag(int(token_id), expected_position)
            block_bits[block_id].append(int(bit))

        block_distances: List[int] = []
        candidate_events_by_block: Dict[int, List[Tuple[str, int]]] = {}
        for block_id, bits in enumerate(block_bits):
            _, distance, candidates = nearest_codeword_candidates(
                bits,
                self.schedule.codebook,
                self.config.block_len,
            )
            block_distances.append(distance)
            candidate_events_by_block[block_id] = candidates
        vt_inconsistent = {
            block_id
            for block_id, bits in enumerate(block_bits)
            if len(bits) != self.config.block_len
            or vt_syndrome(bits) % (self.config.block_len + 1) != self.config.vt_a
        }
        # The accepted paper flags a restored block when its recovered token
        # count differs from block_len. Alignment events remain diagnostics;
        # nearest-VT decoding is used only for candidate localization.
        predicted = [
            block_id
            for block_id, bits in enumerate(block_bits)
            if len(bits) != self.config.block_len
        ]
        candidate_positions = [
            block_id * self.config.block_len + local_position
            for block_id, candidates in candidate_events_by_block.items()
            for _, local_position in candidates
        ]
        return SyncDetectionResult(
            alignment=alignment,
            predicted_blocks=predicted,
            alignment_blocks=sorted(alignment_blocks),
            vt_inconsistent_blocks=sorted(vt_inconsistent),
            block_bits=block_bits,
            block_distances=block_distances,
            candidate_positions=sorted(set(int(value) for value in candidate_positions)),
            candidate_events_by_block=candidate_events_by_block,
        )


def assign_insertions_to_neighbor_block(block_ids: Sequence[int]) -> List[int]:
    """Assign alignment insertions using the accepted evaluator's convention.

    The previous matched block is preferred. An insertion before every matched
    token uses the next matched block; an entirely unmatched row remains -1.
    """
    assigned = [int(value) for value in block_ids]
    next_nonnegative = [-1] * len(assigned)
    next_value = -1
    for index in range(len(assigned) - 1, -1, -1):
        if assigned[index] >= 0:
            next_value = assigned[index]
        next_nonnegative[index] = next_value
    previous = -1
    for index, value in enumerate(assigned):
        if value >= 0:
            previous = value
        elif previous >= 0:
            assigned[index] = previous
        elif next_nonnegative[index] >= 0:
            assigned[index] = next_nonnegative[index]
    return assigned


def _sample_visible_substitute(
    token_id: int,
    global_position: int,
    vocab_ids: Sequence[int],
    schedule: SyncEccSchedule,
    rng: random.Random,
) -> int:
    original_bucket = schedule.step_bucket(int(token_id), int(global_position))
    for _ in range(256):
        candidate = int(vocab_ids[rng.randrange(len(vocab_ids))])
        if candidate != int(token_id) and schedule.step_bucket(candidate, global_position) != original_bucket:
            return candidate
    raise RuntimeError("Could not sample a structurally visible substitution.")


def apply_sync_attacks(
    token_blocks: Sequence[Sequence[int]],
    *,
    edit_rate: float,
    max_edits_per_block: int,
    edit_count_mode: str,
    attack_type: str,
    vocab_ids: Sequence[int],
    schedule: SyncEccSchedule,
    rng: random.Random,
    strict_interior_insertions: bool = True,
) -> SyncAttackResult:
    if attack_type not in {"insert", "delete", "substitute"}:
        raise ValueError(f"Unknown sync-ECC attack type: {attack_type!r}.")
    if edit_count_mode not in {"uniform_1_to_k", "fixed_k"}:
        raise ValueError(f"Unknown edit_count_mode: {edit_count_mode!r}.")
    if max_edits_per_block <= 0:
        raise ValueError("max_edits_per_block must be positive.")
    if not vocab_ids:
        raise ValueError("vocab_ids must not be empty.")

    observed_blocks: List[List[int]] = []
    events_per_block: List[List[SyncEditEvent]] = []
    for block_id, original_block in enumerate(token_blocks):
        original = [int(value) for value in original_block]
        current = list(original)
        origins: List[int | None] = list(range(len(original)))
        events: List[SyncEditEvent] = []
        if rng.random() < float(edit_rate):
            edit_count = (
                int(max_edits_per_block)
                if edit_count_mode == "fixed_k"
                else rng.randint(1, int(max_edits_per_block))
            )
            used_positions: set[int] = set()
            used_gaps: set[int] = set()
            for _ in range(edit_count):
                if attack_type == "insert":
                    gap_range = (
                        range(1, len(original))
                        if strict_interior_insertions
                        else range(len(original) + 1)
                    )
                    available = [gap for gap in gap_range if gap not in used_gaps]
                    if not available:
                        break
                    original_gap = int(rng.choice(available))
                    used_gaps.add(original_gap)
                    insertion_index = next(
                        (
                            index
                            for index, origin in enumerate(origins)
                            if origin is not None and int(origin) >= original_gap
                        ),
                        len(current),
                    )
                    token_id = int(vocab_ids[rng.randrange(len(vocab_ids))])
                    current.insert(insertion_index, token_id)
                    origins.insert(insertion_index, None)
                    events.append(
                        SyncEditEvent(
                            op="insert",
                            block_id=block_id,
                            local_position=original_gap,
                            global_position=block_id * schedule.config.block_len + original_gap,
                        )
                    )
                    continue

                available_positions = [
                    position
                    for position in range(len(original))
                    if position not in used_positions and position in origins
                ]
                if not available_positions:
                    break
                original_position = int(rng.choice(available_positions))
                used_positions.add(original_position)
                current_index = origins.index(original_position)
                global_position = block_id * schedule.config.block_len + original_position
                if attack_type == "delete":
                    del current[current_index]
                    del origins[current_index]
                else:
                    current[current_index] = _sample_visible_substitute(
                        current[current_index],
                        global_position,
                        vocab_ids,
                        schedule,
                        rng,
                    )
                events.append(
                    SyncEditEvent(
                        op=attack_type,
                        block_id=block_id,
                        local_position=original_position,
                        global_position=global_position,
                    )
                )
        observed_blocks.append(current)
        events_per_block.append(events)

    return SyncAttackResult(
        observed_token_ids=[token for block in observed_blocks for token in block],
        observed_blocks=observed_blocks,
        gt_events_per_block=events_per_block,
        gt_blocks=[index for index, events in enumerate(events_per_block) if events],
        realized_edits=sum(len(events) for events in events_per_block),
    )


def evaluate_sync_blocks(
    detection: SyncDetectionResult,
    gt_events_per_block: Sequence[Sequence[SyncEditEvent]],
    expected_blocks: int,
    candidate_tolerance: int = 1,
) -> Dict[str, Any]:
    gt_blocks = {index for index, events in enumerate(gt_events_per_block) if events}
    predicted_blocks = {
        int(value)
        for value in detection.predicted_blocks
        if 0 <= int(value) < int(expected_blocks)
    }
    universe = set(range(int(expected_blocks)))
    tp = len(gt_blocks & predicted_blocks)
    fp = len(predicted_blocks - gt_blocks)
    fn = len(gt_blocks - predicted_blocks)
    tn = len(universe - gt_blocks - predicted_blocks)
    true_events = [
        event
        for events in gt_events_per_block
        for event in events
    ]
    covered = sum(
        int(
            any(
                candidate_type == event.op
                and abs(int(candidate_position) - int(event.local_position))
                <= int(candidate_tolerance)
                for candidate_type, candidate_position in detection.candidate_events_by_block.get(
                    int(event.block_id), []
                )
            )
        )
        for event in true_events
    )
    candidate_sizes = [
        len(detection.candidate_events_by_block.get(block_id, []))
        for block_id in sorted(gt_blocks)
        if detection.candidate_events_by_block.get(block_id, [])
    ]
    return {
        "TP": int(tp),
        "FP": int(fp),
        "FN": int(fn),
        "TN": int(tn),
        "block_tpr": float(tp / (tp + fn)) if tp + fn else 0.0,
        "block_far": float(fp / (fp + tn)) if fp + tn else 0.0,
        "gt_blocks": sorted(gt_blocks),
        "pred_blocks": sorted(predicted_blocks),
        "candidate_events": len(true_events),
        "candidate_events_covered": int(covered),
        "candidate_coverage": float(covered / len(true_events)) if true_events else 0.0,
        "candidate_nonempty_sets": len(candidate_sizes),
        "candidate_total_size": int(sum(candidate_sizes)),
        "mean_candidate_set_size": float(np.mean(candidate_sizes)) if candidate_sizes else 0.0,
    }


def aggregate_sync_rows(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(rows)
    totals = {
        key: int(sum(int(row[key]) for row in rows))
        for key in (
            "TP",
            "FP",
            "FN",
            "TN",
            "candidate_events",
            "candidate_events_covered",
            "candidate_nonempty_sets",
            "candidate_total_size",
        )
    }
    return {
        **totals,
        "block_tpr": float(totals["TP"] / (totals["TP"] + totals["FN"]))
        if totals["TP"] + totals["FN"]
        else 0.0,
        "block_far": float(totals["FP"] / (totals["FP"] + totals["TN"]))
        if totals["FP"] + totals["TN"]
        else 0.0,
        "candidate_coverage": float(
            totals["candidate_events_covered"] / totals["candidate_events"]
        )
        if totals["candidate_events"]
        else 0.0,
        "mean_candidate_set_size": float(
            totals["candidate_total_size"] / totals["candidate_nonempty_sets"]
        )
        if totals["candidate_nonempty_sets"]
        else 0.0,
    }
