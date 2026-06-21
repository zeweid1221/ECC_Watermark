from __future__ import annotations

import math
import random
import re
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np

from .config import ModelConfig

try:
    import torch
    import torch.nn.functional as F
except Exception:  # pragma: no cover
    torch = None
    F = None

try:
    from datasets import load_dataset
except Exception:  # pragma: no cover
    load_dataset = None

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except Exception:  # pragma: no cover
    AutoModelForCausalLM = None
    AutoTokenizer = None

try:
    from transformers import BitsAndBytesConfig
except Exception:  # pragma: no cover
    BitsAndBytesConfig = None

try:
    import bitsandbytes  # noqa: F401
except Exception:  # pragma: no cover
    bitsandbytes = None


TOKEN_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+|[^\w\s]")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\n", " ").replace("\r", " ")).strip()


def sample_prompts_from_config(prompt_config, rng: random.Random) -> List[str]:
    if prompt_config.inline_prompts:
        return [clean_text(x) for x in list(prompt_config.inline_prompts)[: prompt_config.prompt_count]]

    if prompt_config.prompt_text_file:
        with open(prompt_config.prompt_text_file, "r", encoding="utf-8") as handle:
            lines = [clean_text(line) for line in handle.readlines()]
        lines = [line for line in lines if len(line) >= prompt_config.min_prompt_chars]
        rng.shuffle(lines)
        return lines[: prompt_config.prompt_count]

    if prompt_config.dataset_path:
        if load_dataset is None:
            raise RuntimeError("datasets is not installed; cannot sample prompts from dataset.")
        ds = load_dataset(
            prompt_config.dataset_path,
            prompt_config.dataset_name,
            split=prompt_config.dataset_split,
        )
        texts = [clean_text(str(t)) for t in ds["text"]]
        texts = [t for t in texts if len(t) >= prompt_config.min_prompt_chars]
        rng.shuffle(texts)
        return texts[: prompt_config.prompt_count]

    return []


@dataclass
class GenerationSession(ABC):
    @abstractmethod
    def next_logits(self) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def append(self, token_id: int) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def prompt_ids(self) -> List[int]:
        raise NotImplementedError

    @property
    @abstractmethod
    def generated_ids(self) -> List[int]:
        raise NotImplementedError


class BaseLanguageModel(ABC):
    def __init__(self, config: ModelConfig):
        self.config = config

    @property
    @abstractmethod
    def vocab_size(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def pad_token_id(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def eos_token_id(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def all_special_ids(self) -> Sequence[int]:
        raise NotImplementedError

    @abstractmethod
    def encode(self, text: str, add_special_tokens: bool = True, max_length: Optional[int] = None) -> List[int]:
        raise NotImplementedError

    @abstractmethod
    def decode(self, token_ids: Sequence[int], skip_special_tokens: bool = True) -> str:
        raise NotImplementedError

    @abstractmethod
    def token_surface(self, token_id: int) -> str:
        raise NotImplementedError

    @abstractmethod
    def start_session(self, prompt: str) -> GenerationSession:
        raise NotImplementedError

    @abstractmethod
    def compute_perplexity(self, texts: Sequence[str], max_length: Optional[int] = None) -> float:
        raise NotImplementedError

    def embedding_matrix(self):
        return None

    @property
    def resolved_device(self) -> str:
        return getattr(self, "device", self.config.device)

    @property
    def quantization_mode(self) -> str:
        return getattr(self, "_quantization_mode", "none")

    @property
    def used_4bit(self) -> bool:
        return self.quantization_mode == "4bit"


class MockGenerationSession(GenerationSession):
    def __init__(self, model: "MockLanguageModel", prompt_ids: List[int]):
        self.model = model
        self._prompt_ids = list(prompt_ids)
        self._generated_ids: List[int] = []

    @property
    def prompt_ids(self) -> List[int]:
        return self._prompt_ids

    @property
    def generated_ids(self) -> List[int]:
        return self._generated_ids

    def next_logits(self) -> np.ndarray:
        return self.model.next_token_logits(self._prompt_ids + self._generated_ids)

    def append(self, token_id: int) -> None:
        self._generated_ids.append(int(token_id))


class MockLanguageModel(BaseLanguageModel):
    def __init__(self, config: ModelConfig, corpus_texts: Optional[Sequence[str]] = None):
        super().__init__(config)
        self.device = resolve_requested_device(config.device)
        self._quantization_mode = "none"
        self._special_tokens = ["<pad>", "<eos>", "<bos>"]
        base_corpus = list(corpus_texts or [])
        if not base_corpus:
            base_corpus = [
                "Watermarking balances robustness and fluency in generated text.",
                "Adaptive generation keeps each prefix compatible with feasible continuations.",
                "Boundary anchors help recover blocks after insertions deletions and substitutions.",
                "KGW provides a strong green list baseline for comparison.",
                "Perplexity helps quantify generation quality and distortion.",
            ]
        vocab = Counter()
        for text in base_corpus:
            vocab.update(TOKEN_PATTERN.findall(clean_text(text).lower()))
        filler = [
            "the", "a", "an", "model", "text", "token", "boundary", "soft", "hard", "adaptive",
            "nonadaptive", "edit", "insert", "delete", "substitute", "robust", "clean", "block",
            "anchor", "bucket", "sequence", "prompt", "quality", "language", "data", "score",
        ]
        vocab.update(filler)
        ordered = [tok for tok, _ in vocab.most_common(max(8, config.mock_vocab_size - len(self._special_tokens)))]
        vocab_tokens = self._special_tokens + ordered[: max(0, config.mock_vocab_size - len(self._special_tokens))]
        self.id_to_token = vocab_tokens
        self.token_to_id = {tok: idx for idx, tok in enumerate(vocab_tokens)}
        self._unigram = np.ones(len(vocab_tokens), dtype=np.float64)
        self._bigram = defaultdict(lambda: np.ones(len(vocab_tokens), dtype=np.float64))
        self._embedding = self._build_embedding_matrix()
        self._fit_language_model(base_corpus)

    def _build_embedding_matrix(self) -> np.ndarray:
        emb = np.zeros((len(self.id_to_token), 12), dtype=np.float32)
        for idx, tok in enumerate(self.id_to_token):
            seed = abs(hash(tok)) % (2**32)
            rng = np.random.default_rng(seed)
            emb[idx] = rng.standard_normal(12)
        norm = np.linalg.norm(emb, axis=1, keepdims=True)
        norm[norm == 0] = 1.0
        return emb / norm

    def _fit_language_model(self, texts: Sequence[str]) -> None:
        bos = self.token_to_id["<bos>"]
        for text in texts:
            ids = self.encode(text, add_special_tokens=True)
            prev = bos
            for token_id in ids:
                self._unigram[token_id] += 1.0
                self._bigram[prev][token_id] += 1.0
                prev = token_id

    @property
    def vocab_size(self) -> int:
        return len(self.id_to_token)

    @property
    def pad_token_id(self) -> int:
        return self.token_to_id["<pad>"]

    @property
    def eos_token_id(self) -> int:
        return self.token_to_id["<eos>"]

    @property
    def all_special_ids(self) -> Sequence[int]:
        return [self.token_to_id[tok] for tok in self._special_tokens]

    def encode(self, text: str, add_special_tokens: bool = True, max_length: Optional[int] = None) -> List[int]:
        toks = TOKEN_PATTERN.findall(clean_text(text).lower())
        ids = [self.token_to_id.get(tok, self.token_to_id["the"]) for tok in toks]
        if add_special_tokens:
            ids = [self.token_to_id["<bos>"]] + ids + [self.eos_token_id]
        if max_length is not None:
            ids = ids[:max_length]
        return ids

    def decode(self, token_ids: Sequence[int], skip_special_tokens: bool = True) -> str:
        toks: List[str] = []
        for tid in token_ids:
            tok = self.id_to_token[int(tid)]
            if skip_special_tokens and tok in self._special_tokens:
                continue
            toks.append(tok)
        pieces: List[str] = []
        for tok in toks:
            if not pieces:
                pieces.append(tok)
            elif re.fullmatch(r"[^\w\s]", tok):
                pieces[-1] = pieces[-1] + tok
            else:
                pieces.append(tok)
        return " ".join(pieces)

    def token_surface(self, token_id: int) -> str:
        return self.id_to_token[int(token_id)]

    def embedding_matrix(self):
        return self._embedding

    def next_token_logits(self, context_ids: Sequence[int]) -> np.ndarray:
        prev = int(context_ids[-1]) if context_ids else self.token_to_id["<bos>"]
        probs = self._bigram[prev] + 0.25 * self._unigram
        logits = np.log(probs)
        if context_ids:
            theme_counts = Counter(int(x) for x in context_ids[-12:] if int(x) not in self.all_special_ids)
            for token_id, count in theme_counts.items():
                logits[token_id] += 0.15 * count
        for token_id, token in enumerate(self.id_to_token):
            if re.fullmatch(r"[^\w\s]+", token or ""):
                logits[token_id] -= 2.5
        logits[self.pad_token_id] = -1e9
        return logits.astype(np.float64)

    def start_session(self, prompt: str) -> GenerationSession:
        prompt_ids = self.encode(prompt, add_special_tokens=True, max_length=self.config.max_prompt_tokens)
        return MockGenerationSession(self, prompt_ids)

    def compute_perplexity(self, texts: Sequence[str], max_length: Optional[int] = None) -> float:
        total_nll = 0.0
        total_tokens = 0
        bos = self.token_to_id["<bos>"]
        for text in texts:
            ids = self.encode(text, add_special_tokens=True, max_length=max_length)
            prev = bos
            for token_id in ids:
                logits = self.next_token_logits([prev])
                log_probs = logits - np.log(np.exp(logits - logits.max()).sum()) - logits.max()
                total_nll -= float(log_probs[int(token_id)])
                total_tokens += 1
                prev = int(token_id)
        if total_tokens == 0:
            return float("nan")
        return float(math.exp(total_nll / total_tokens))


class HfGenerationSession(GenerationSession):
    def __init__(self, model: "HfLanguageModel", prompt_ids: List[int], attention_mask: List[int]):
        self.model = model
        self._prompt_ids = list(prompt_ids)
        self._generated_ids: List[int] = []
        with torch.no_grad():
            input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=model.device)
            attn = torch.tensor([attention_mask], dtype=torch.long, device=model.device)
            out = model.model(input_ids=input_ids, attention_mask=attn, use_cache=True)
            self.past = out.past_key_values
            self.cached_logits = out.logits[:, -1, :].detach().float().cpu().numpy()[0]

    @property
    def prompt_ids(self) -> List[int]:
        return self._prompt_ids

    @property
    def generated_ids(self) -> List[int]:
        return self._generated_ids

    def next_logits(self) -> np.ndarray:
        return self.cached_logits.astype(np.float64)

    def append(self, token_id: int) -> None:
        self._generated_ids.append(int(token_id))
        with torch.no_grad():
            nxt = torch.tensor([[int(token_id)]], dtype=torch.long, device=self.model.device)
            out = self.model.model(input_ids=nxt, past_key_values=self.past, use_cache=True)
            self.past = out.past_key_values
            self.cached_logits = out.logits[:, -1, :].detach().float().cpu().numpy()[0]


class HfLanguageModel(BaseLanguageModel):
    def __init__(self, config: ModelConfig):
        if AutoTokenizer is None or AutoModelForCausalLM is None or torch is None:
            raise RuntimeError("transformers/torch are required for backend='hf'.")
        super().__init__(config)
        requested_device = config.device
        self.device = resolve_requested_device(requested_device)
        self._quantization_mode = "none"
        self.tokenizer = AutoTokenizer.from_pretrained(
            config.model_name,
            use_fast=True,
            trust_remote_code=config.trust_remote_code,
        )
        if self.tokenizer.pad_token_id is None:
            if self.tokenizer.eos_token_id is not None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            else:
                self.tokenizer.add_special_tokens({"pad_token": "<|pad|>"})
        model_kwargs: Dict[str, object] = {
            "trust_remote_code": config.trust_remote_code,
            "low_cpu_mem_usage": config.low_cpu_mem_usage,
        }
        compute_dtype = preferred_torch_dtype(self.device, config.prefer_bfloat16)
        if self.device.startswith("cuda"):
            model_kwargs["torch_dtype"] = compute_dtype
        else:
            model_kwargs["torch_dtype"] = "auto"
        self.model = self._load_model(config, model_kwargs, compute_dtype)
        if self.quantization_mode == "none":
            self.model.to(self.device)
        self.model.eval()
        if self.model.get_input_embeddings().num_embeddings != len(self.tokenizer):
            self.model.resize_token_embeddings(len(self.tokenizer))
        self.device = infer_model_device(self.model, fallback_device=self.device)

    def _load_model(self, config: ModelConfig, model_kwargs: Dict[str, object], compute_dtype) -> object:
        if (
            config.use_4bit
            and self.device.startswith("cuda")
            and BitsAndBytesConfig is not None
            and bitsandbytes is not None
        ):
            try:
                quant_kwargs = dict(model_kwargs)
                quant_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_compute_dtype=compute_dtype,
                )
                quant_kwargs["device_map"] = "auto"
                model = AutoModelForCausalLM.from_pretrained(config.model_name, **quant_kwargs)
                self._quantization_mode = "4bit"
                print(f"[info] Loaded {config.model_name} with 4-bit quantization on {self.device}.")
                return model
            except Exception as exc:
                print(f"[warning] 4-bit loading failed for {config.model_name}: {exc}. Falling back to standard loading.")
        if (
            config.use_8bit
            and not config.use_4bit
            and self.device.startswith("cuda")
            and BitsAndBytesConfig is not None
            and bitsandbytes is not None
        ):
            try:
                quant_kwargs = dict(model_kwargs)
                quant_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
                quant_kwargs["device_map"] = "auto"
                model = AutoModelForCausalLM.from_pretrained(config.model_name, **quant_kwargs)
                self._quantization_mode = "8bit"
                print(f"[info] Loaded {config.model_name} with 8-bit quantization on {self.device}.")
                return model
            except Exception as exc:
                print(f"[warning] 8-bit loading failed for {config.model_name}: {exc}. Falling back to standard loading.")
        elif config.use_4bit:
            if not self.device.startswith("cuda"):
                print("[warning] 4-bit loading was requested but CUDA is unavailable or not selected. Falling back to standard loading.")
            elif BitsAndBytesConfig is None or bitsandbytes is None:
                print("[warning] 4-bit loading was requested but bitsandbytes/transformers 4-bit support is unavailable. Falling back to standard loading.")
        elif config.use_8bit:
            if not self.device.startswith("cuda"):
                print("[warning] 8-bit loading was requested but CUDA is unavailable or not selected. Falling back to standard loading.")
            elif BitsAndBytesConfig is None or bitsandbytes is None:
                print("[warning] 8-bit loading was requested but bitsandbytes/transformers quantization support is unavailable. Falling back to standard loading.")
        return AutoModelForCausalLM.from_pretrained(config.model_name, **model_kwargs)

    @property
    def vocab_size(self) -> int:
        return len(self.tokenizer)

    @property
    def pad_token_id(self) -> int:
        return int(self.tokenizer.pad_token_id)

    @property
    def eos_token_id(self) -> int:
        return int(self.tokenizer.eos_token_id)

    @property
    def all_special_ids(self) -> Sequence[int]:
        return [int(x) for x in self.tokenizer.all_special_ids]

    def encode(self, text: str, add_special_tokens: bool = True, max_length: Optional[int] = None) -> List[int]:
        enc = self.tokenizer(
            clean_text(text),
            add_special_tokens=add_special_tokens,
            truncation=max_length is not None,
            max_length=max_length,
        )
        return [int(x) for x in enc["input_ids"]]

    def decode(self, token_ids: Sequence[int], skip_special_tokens: bool = True) -> str:
        return self.tokenizer.decode(list(token_ids), skip_special_tokens=skip_special_tokens)

    def token_surface(self, token_id: int) -> str:
        return self.tokenizer.decode([int(token_id)], skip_special_tokens=False)

    def embedding_matrix(self):
        emb = self.model.get_input_embeddings().weight.detach().float().cpu().numpy()
        norm = np.linalg.norm(emb, axis=1, keepdims=True)
        norm[norm == 0] = 1.0
        return emb / norm

    def start_session(self, prompt: str) -> GenerationSession:
        enc = self.tokenizer(
            clean_text(prompt),
            return_tensors="pt",
            truncation=True,
            max_length=self.config.max_prompt_tokens,
            add_special_tokens=True,
        )
        prompt_ids = enc["input_ids"][0].tolist()
        attn = enc["attention_mask"][0].tolist()
        return HfGenerationSession(self, prompt_ids, attn)

    def compute_perplexity(self, texts: Sequence[str], max_length: Optional[int] = None) -> float:
        if not texts:
            return float("nan")
        total_nll = 0.0
        total_tokens = 0
        loss_fct = torch.nn.CrossEntropyLoss(reduction="none")
        for text in texts:
            enc = self.tokenizer(
                clean_text(text),
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
                add_special_tokens=True,
            )
            input_ids = enc["input_ids"].to(self.device)
            with torch.no_grad():
                logits = self.model(input_ids=input_ids).logits[:, :-1, :]
            labels = input_ids[:, 1:]
            losses = loss_fct(logits.reshape(-1, logits.size(-1)), labels.reshape(-1))
            total_nll += float(losses.sum().item())
            total_tokens += int(labels.numel())
        if total_tokens == 0:
            return float("nan")
        return float(math.exp(total_nll / total_tokens))


def build_language_model(config: ModelConfig, corpus_texts: Optional[Sequence[str]] = None) -> BaseLanguageModel:
    if config.backend == "mock":
        return MockLanguageModel(config, corpus_texts=corpus_texts)
    if config.backend == "hf":
        return HfLanguageModel(config)
    raise ValueError(f"Unknown model backend: {config.backend}")


def resolve_requested_device(requested_device: str) -> str:
    requested = (requested_device or "cpu").lower()
    if requested.startswith("cuda"):
        if torch is not None and torch.cuda.is_available():
            return requested if ":" in requested else "cuda"
        print(f"[warning] CUDA was requested ({requested_device}) but is unavailable. Falling back to cpu.")
        return "cpu"
    return requested


def preferred_torch_dtype(device: str, prefer_bfloat16: bool):
    if torch is None:
        return None
    if device.startswith("cuda"):
        if prefer_bfloat16 and torch.cuda.is_bf16_supported():
            return torch.bfloat16
        return torch.float16
    return torch.float32


def infer_model_device(model, fallback_device: str) -> str:
    try:
        return str(next(model.parameters()).device)
    except StopIteration:
        return fallback_device
    except Exception:
        hf_map = getattr(model, "hf_device_map", None)
        if isinstance(hf_map, dict) and hf_map:
            first_device = next(iter(hf_map.values()))
            return str(first_device)
        return fallback_device
