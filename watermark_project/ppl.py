from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from .modeling import BaseLanguageModel

try:
    import torch
except Exception:  # pragma: no cover
    torch = None


def compute_text_perplexity(model: BaseLanguageModel, texts: Sequence[str], max_length: int | None = None) -> float:
    return model.compute_perplexity(texts, max_length=max_length)


def _mock_continuation_nll(
    model: BaseLanguageModel,
    context_ids: Sequence[int],
    continuation_ids: Sequence[int],
) -> tuple[float, int]:
    context = [int(x) for x in context_ids]
    if not context and hasattr(model, "token_to_id") and "<bos>" in model.token_to_id:
        context = [int(model.token_to_id["<bos>"])]
    total_nll = 0.0
    count = 0
    for token_id in continuation_ids:
        if not context:
            context.append(int(token_id))
            continue
        logits = np.asarray(model.next_token_logits(context), dtype=np.float64)
        maximum = float(np.max(logits))
        log_norm = maximum + float(np.log(np.exp(logits - maximum).sum()))
        total_nll += log_norm - float(logits[int(token_id)])
        count += 1
        context.append(int(token_id))
    return total_nll, count


def _hf_continuation_nll(
    model: BaseLanguageModel,
    context_ids: Sequence[int],
    continuation_ids: Sequence[int],
) -> tuple[float, int]:
    if torch is None:
        raise RuntimeError("torch is required for HF token-id perplexity.")
    context = [int(x) for x in context_ids]
    continuation = [int(x) for x in continuation_ids]
    if not continuation:
        return 0.0, 0
    if not context:
        bos_token_id = getattr(model.tokenizer, "bos_token_id", None)
        if bos_token_id is not None:
            context = [int(bos_token_id)]
        elif len(continuation) > 1:
            context = [continuation[0]]
            continuation = continuation[1:]
        else:
            return 0.0, 0
    combined = context + continuation
    input_ids = torch.tensor([combined], dtype=torch.long, device=model.device)
    with torch.no_grad():
        logits = model.model(input_ids=input_ids).logits
    start = len(context) - 1
    prediction_logits = logits[:, start : start + len(continuation), :]
    labels = torch.tensor(continuation, dtype=torch.long, device=prediction_logits.device)
    losses = torch.nn.functional.cross_entropy(
        prediction_logits.reshape(-1, prediction_logits.size(-1)),
        labels.reshape(-1),
        reduction="sum",
    )
    return float(losses.item()), len(continuation)


def compute_token_id_perplexity(
    model: BaseLanguageModel,
    continuation_token_ids: Sequence[Sequence[int]],
    prompt_token_ids: Sequence[Sequence[int]] | None = None,
) -> float:
    if prompt_token_ids is None:
        prompt_token_ids = [[] for _ in continuation_token_ids]
    if len(prompt_token_ids) != len(continuation_token_ids):
        raise ValueError("prompt_token_ids and continuation_token_ids must have equal length.")
    total_nll = 0.0
    total_tokens = 0
    is_hf = hasattr(model, "model") and hasattr(model, "tokenizer")
    for prompt_ids, continuation_ids in zip(prompt_token_ids, continuation_token_ids):
        if is_hf:
            nll, count = _hf_continuation_nll(model, prompt_ids, continuation_ids)
        else:
            nll, count = _mock_continuation_nll(model, prompt_ids, continuation_ids)
        total_nll += nll
        total_tokens += count
    if total_tokens == 0:
        return float("nan")
    return float(math.exp(total_nll / total_tokens))


def compute_generation_perplexities(
    model: BaseLanguageModel,
    prompt_token_ids: Sequence[Sequence[int]],
    generated_token_ids: Sequence[Sequence[int]],
) -> dict[str, float]:
    return {
        "ppl_unconditional_token_ids": compute_token_id_perplexity(
            model,
            continuation_token_ids=generated_token_ids,
        ),
        "ppl_conditional_token_ids": compute_token_id_perplexity(
            model,
            continuation_token_ids=generated_token_ids,
            prompt_token_ids=prompt_token_ids,
        ),
    }
