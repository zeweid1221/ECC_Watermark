from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, Sequence

import pandas as pd


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def to_jsonable(obj: Any) -> Any:
    if is_dataclass(obj):
        return {k: to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if hasattr(obj, "tolist"):
        return obj.tolist()
    return obj


def write_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(to_jsonable(payload), handle, ensure_ascii=False, indent=2)


def save_dataframe(df: pd.DataFrame, out_stem: str, save_parquet: bool = True) -> None:
    df.to_csv(out_stem + ".csv", index=False)
    write_json(out_stem + ".json", df.to_dict(orient="records"))
    if save_parquet:
        try:
            df.to_parquet(out_stem + ".parquet", index=False)
        except Exception:
            pass


def save_prompts(path: str, prompts: Sequence[str]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for prompt in prompts:
            handle.write(prompt.strip() + "\n")
