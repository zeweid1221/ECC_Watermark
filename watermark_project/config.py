from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Union


HARD_LOGIT_BIAS = 1000.0
SOFT_LOGIT_BIAS = 2.0
DEFAULT_SYSTEM_PROMPT = (
    "You are a careful explanatory writing assistant. Answer directly without showing reasoning. "
    "Write fluent, self-contained English prose in a neutral factual tone."
)


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
    model_profile: Optional[str] = None
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
    target_boundary_pool: Optional[int] = None
    boundary_vocab_fraction: float = 1.0 / 8.0
    boundary_bonus: float = 3.5
    lsh_bits: int = 12
    lsh_chunk: int = 2048
    payload_split_strategy: str = "quality_variant_lsh"

    def __post_init__(self) -> None:
        if self.target_boundary_pool is not None and self.target_boundary_pool <= 0:
            raise ValueError("target_boundary_pool must be positive when specified.")
        if not 0.0 < self.boundary_vocab_fraction < 1.0:
            raise ValueError("boundary_vocab_fraction must be in (0, 1).")
        if self.payload_split_strategy not in {"paper_main", "quality_variant_lsh"}:
            raise ValueError(
                "payload_split_strategy must be 'paper_main' or 'quality_variant_lsh'."
            )


@dataclass
class GenerationProtocolConfig:
    stop_after: str = "closed_blocks"
    sampling: str = "sample"
    temperature: float = 0.75
    top_k: int = 40
    top_p: float = 0.9
    repetition_penalty: float = 1.2
    prompt_style: str = "qa"
    use_chat_template: bool = True
    enable_thinking: bool = False
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    ascii_token_filter: bool = True
    adaptive_invalid_prefix_policy: str = "nearest_feasible"

    def __post_init__(self) -> None:
        if self.stop_after not in {"closed_blocks", "feasible_blocks"}:
            raise ValueError("stop_after must be 'closed_blocks' or 'feasible_blocks'.")
        if self.sampling not in {"sample", "greedy"}:
            raise ValueError("sampling must be 'sample' or 'greedy'.")
        if self.prompt_style not in {"qa", "plain"}:
            raise ValueError("prompt_style must be 'qa' or 'plain'.")
        if self.temperature <= 0:
            raise ValueError("temperature must be positive.")
        if self.top_k < 0:
            raise ValueError("top_k must be non-negative.")
        if not 0 < self.top_p <= 1:
            raise ValueError("top_p must be in (0, 1].")
        if self.repetition_penalty < 1:
            raise ValueError("repetition_penalty must be at least 1.")
        if self.adaptive_invalid_prefix_policy not in {
            "nearest_feasible",
            "legacy_unconstrained",
        }:
            raise ValueError(
                "adaptive_invalid_prefix_policy must be 'nearest_feasible' "
                "or 'legacy_unconstrained'."
            )


@dataclass
class KGWConfig:
    block_len: int = 7
    seed_count: int = 1
    seed_offset: int = 3779


@dataclass
class SegmentBaselineConfig:
    enabled: bool = True
    methods: Tuple[str, ...] = ("zhao_aol", "waterseeker")
    block_len: int = 8
    approx_hard_logit_bias: float = 20.0
    use_same_prompt_list: bool = True
    target_blocks: Optional[int] = None
    total_tokens: Optional[int] = None
    generation_seed_offset: int = 700000
    score_type: str = "watermark_deficit"
    aol_iterations: int = 10
    aol_backend: str = "simple"
    aol_aligator_source: Optional[str] = "llm-watermark-location-main"
    aol_top_mean_fraction: float = 0.20
    aol_token_threshold: Optional[float] = None
    aol_block_threshold: Optional[float] = None
    waterseeker_window: Optional[int] = None
    waterseeker_top_k: int = 20
    waterseeker_connect_tolerance: Optional[int] = None
    waterseeker_min_fragment_len: int = 1
    waterseeker_block_overlap_tokens: int = 1


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
    partition_dir: Optional[str] = None
    require_semantic_partition: bool = False
    model: ModelConfig = field(default_factory=ModelConfig)
    prompts: PromptConfig = field(default_factory=PromptConfig)
    ecc: ECCConfig = field(default_factory=ECCConfig)
    generation_protocol: GenerationProtocolConfig = field(default_factory=GenerationProtocolConfig)
    kgw: KGWConfig = field(default_factory=KGWConfig)
    segment_baselines: SegmentBaselineConfig = field(default_factory=SegmentBaselineConfig)
    schemes: List[str] = field(default_factory=lambda: ["ecc", "kgw"])
    watermark_modes: List[str] = field(default_factory=lambda: ["hard", "soft"])
    ecc_adaptive_modes: List[bool] = field(default_factory=lambda: [True])
    ecc_logit_bias_values: List[float] = field(default_factory=list)
    kgw_logit_bias: Optional[float] = None
    kgw_logit_bias_values: List[float] = field(default_factory=list)
    edit_rates: List[float] = field(default_factory=lambda: [0.2, 0.4, 0.6, 0.8])
    prompt_seed: int = 1234
    generation_seed: int = 2026
    generation_count: int = 256
    target_blocks: int = 18
    max_new_tokens: int = 512
    attack_max_edits_per_block: Optional[int] = 1
    attack_max_edits_per_blocks: List[int] = field(default_factory=list)
    decoder_max_edits_per_block: int = 3
    ecc_tolerance_by_logit_bias: Dict[float, Union[int, Sequence[int]]] = field(default_factory=dict)
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
