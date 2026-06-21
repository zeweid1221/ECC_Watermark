from __future__ import annotations

from typing import Sequence

from .modeling import BaseLanguageModel


def compute_text_perplexity(model: BaseLanguageModel, texts: Sequence[str], max_length: int | None = None) -> float:
    return model.compute_perplexity(texts, max_length=max_length)
