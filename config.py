from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple


HARD_LOGIT_BIAS = 1000.0
SOFT_LOGIT_BIAS = 2.0


def resolve_logit_bias(watermark_mode: str, logit_bias: Optional[float]) -> float:
    if logit_bias is not None:
        return float(logit_bias)
    if watermark_mode == "hard":
        return HARD_LOGIT_BIAS
    if watermark_mode == "soft":
        return SOFT_LOGIT_BIAS
    raise ValueError(f"Unknown watermark_mode: {watermark_mode}")


@dataclass
class ModelConfig:
    backend: str = "mock"
    model_name: str = "mock-lm"
    device: str = "cpu"
    trust_remote_code: bool = True
    max_prompt_tokens: int = 96
    mock_vocab_size: int = 256
    use_4bit: bool = False
    use_8bit: bool = False
    prefer_bfloat16: bool = True
    low_cpu_mem_usage: bool = True


@dataclass
class PromptConfig:
    inline_prompts: Sequence[str] = field(default_factory=tuple)
    prompt_text_file: Optional[str] = None
    dataset_path: Optional[str] = None
    dataset_name: Optional[str] = None
    dataset_split: str = "train"
    prompt_count: int = 8
    min_prompt_chars: int = 64
    prompt_seed: int = 1234


@dataclass
class ECCConfig:
    block_len: int = 7
    vt_a: int = 6
    target_boundary_pool: int = 150
    boundary_bonus: float = 3.5
    lsh_bits: int = 12
    lsh_chunk: int = 2048


@dataclass
class KGWConfig:
    block_len: int = 7
    seed_count: int = 1
    seed_offset: int = 3779


@dataclass
class GenerationSetting:
    scheme: str
    watermark_mode: str
    adaptive: Optional[bool]
    target_blocks: int
    max_new_tokens: int
    seed: int
    logit_bias: Optional[float] = None

    def resolved_logit_bias(self) -> float:
        return resolve_logit_bias(self.watermark_mode, self.logit_bias)


@dataclass
class AttackConfig:
    edit_rate: float
    allow_boundary_edit: bool = True
    boundary_edit_modes: Tuple[str, ...] = ("delete", "sub")
    attack_max_edits_per_block: int = 1
    edit_count_mode: str = "uniform_1_to_k"


@dataclass
class DecoderConfig:
    decoder_max_edits_per_block: int = 1
    boundary_edit_modes: Tuple[str, ...] = ("delete", "sub")


@dataclass
class RunConfig:
    output_dir: str
    model: ModelConfig = field(default_factory=ModelConfig)
    prompts: PromptConfig = field(default_factory=PromptConfig)
    ecc: ECCConfig = field(default_factory=ECCConfig)
    kgw: KGWConfig = field(default_factory=KGWConfig)
    schemes: List[str] = field(default_factory=lambda: ["ecc", "kgw"])
    watermark_modes: List[str] = field(default_factory=lambda: ["hard", "soft"])
    ecc_adaptive_modes: List[bool] = field(default_factory=lambda: [True, False])
    edit_rates: List[float] = field(default_factory=lambda: [0.2, 0.4, 0.6, 0.8])
    prompt_seed: int = 1234
    generation_seed: int = 2026
    generation_count: int = 256
    target_blocks: int = 18
    max_new_tokens: int = 512
    attack_max_edits_per_block: Optional[int] = 1
    attack_max_edits_per_blocks: List[int] = field(default_factory=list)
    decoder_max_edits_per_block: int = 3
    edit_count_mode: str = "uniform_1_to_k"
    allow_boundary_edit: bool = True
    boundary_edit_modes: Tuple[str, ...] = ("delete", "sub")
    save_parquet: bool = True
    run_name: str = "experiment"
    save_detailed_json: bool = True

    def __post_init__(self) -> None:
        if self.attack_max_edits_per_blocks:
            normalized = [int(x) for x in self.attack_max_edits_per_blocks]
        elif self.attack_max_edits_per_block is not None:
            normalized = [int(self.attack_max_edits_per_block)]
        else:
            normalized = [1]
        if any(x <= 0 for x in normalized):
            raise ValueError("attack_max_edits_per_block values must be positive integers.")
        self.attack_max_edits_per_blocks = normalized
        self.attack_max_edits_per_block = int(normalized[0])
