from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SAMPLE_INDICES = (10, 188, 180, 114, 190)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export matched, verbatim Qwen3 LFQA watermark examples to LaTeX."
    )
    parser.add_argument("--soft-results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def normalize_whitespace(text: str) -> str:
    return " ".join(str(text).split())


def sentence_prefix(text: str, min_chars: int = 80, max_chars: int = 420) -> str:
    normalized = normalize_whitespace(text)
    candidates = [
        match.end()
        for match in re.finditer(r"[.!?](?=\s|[A-Z]|$)", normalized)
        if match.end() >= min_chars
    ]
    within_limit = [end for end in candidates if end <= max_chars]
    if within_limit:
        return normalized[: within_limit[0]]
    if candidates:
        return normalized[: candidates[0]]
    return normalized


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def adaptive_settings(path: Path) -> dict[int, list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        int(float(setting["logit_bias"])): setting["generated"]
        for setting in payload["settings"]
        if bool(setting.get("adaptive"))
    }


def main() -> None:
    args = parse_args()
    settings = adaptive_settings(args.soft_results)
    expected_biases = (2, 5, 20)
    missing = set(expected_biases).difference(settings)
    if missing:
        raise ValueError(f"Missing adaptive settings: {sorted(missing)}")

    output = [
        "% Auto-generated from saved experiment artifacts; do not edit by hand.",
        "% Whitespace is normalized and each response is truncated only at its first", 
        "% sentence boundary after 80 characters.",
    ]
    for bias in expected_biases:
        output.append(rf"\subsubsection{{$\delta={bias}$}}")
        output.append("")
        for display_index, sample_index in enumerate(SAMPLE_INDICES, start=1):
            generated = settings[bias][sample_index]
            prompt = latex_escape(normalize_whitespace(generated["prompt"]))
            response = latex_escape(sentence_prefix(generated["suffix_text"]))
            output.extend(
                [
                    r"\noindent\fcolorbox{black!18}{black!2}{%",
                    r"\parbox{\dimexpr\linewidth-2\fboxsep-2\fboxrule\relax}{%",
                    rf"\textbf{{Example {display_index} (sample {sample_index}).}}\\[-1pt]",
                    rf"\textbf{{Prompt:}} {prompt}\\[2pt]",
                    rf"\textbf{{Watermarked response:}} {response}%",
                    r"}}",
                    r"\par\vspace{6pt}",
                    "",
                ]
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
