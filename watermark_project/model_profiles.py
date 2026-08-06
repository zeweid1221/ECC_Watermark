from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ModelProfile:
    key: str
    model_name: str
    use_chat_template: bool
    prompt_style: str = "qa"
    enable_thinking: bool = False


MODEL_PROFILES: Dict[str, ModelProfile] = {
    "qwen3-8b": ModelProfile(
        key="qwen3-8b",
        model_name="Qwen/Qwen3-8B",
        use_chat_template=True,
    ),
    "mistral-7b-instruct-v0.3": ModelProfile(
        key="mistral-7b-instruct-v0.3",
        model_name="mistralai/Mistral-7B-Instruct-v0.3",
        use_chat_template=True,
    ),
    "opt-125m": ModelProfile(
        key="opt-125m",
        model_name="facebook/opt-125m",
        use_chat_template=False,
    ),
}


def get_model_profile(name: str) -> ModelProfile:
    try:
        return MODEL_PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown model profile {name!r}.") from exc
