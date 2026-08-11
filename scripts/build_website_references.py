"""Build the website reference list from citations in the current paper draft."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TITLE_CORRECTIONS = {
    "lcvenshtcin1966binary": "Binary codes capable of correcting deletions, insertions, and reversals",
}


def cited_keys(tex: str) -> list[str]:
    # LaTeX ignores unescaped percent signs and everything following them.
    tex = "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in tex.splitlines())
    keys: list[str] = []
    pattern = re.compile(r"\\cite\w*\s*(?:\[[^\]]*\]\s*)*\{([^}]*)\}")
    for match in pattern.finditer(tex):
        for key in match.group(1).split(","):
            key = key.strip()
            if key and key not in keys:
                keys.append(key)
    return keys


def parse_braced_value(text: str, start: int) -> tuple[str, int]:
    opener = text[start]
    closer = "}" if opener == "{" else '"'
    depth = 0
    escaped = False
    chars: list[str] = []
    index = start + 1
    while index < len(text):
        char = text[index]
        if escaped:
            chars.append(char)
            escaped = False
        elif char == "\\":
            chars.append(char)
            escaped = True
        elif opener == "{" and char == "{":
            depth += 1
            chars.append(char)
        elif char == closer:
            if opener == "{" and depth:
                depth -= 1
                chars.append(char)
            else:
                return "".join(chars), index + 1
        else:
            chars.append(char)
        index += 1
    raise ValueError("Unterminated BibTeX field value")


def parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    index = 0
    while index < len(body):
        while index < len(body) and (body[index].isspace() or body[index] == ","):
            index += 1
        name_match = re.match(r"([A-Za-z][\w-]*)\s*=\s*", body[index:])
        if not name_match:
            break
        name = name_match.group(1).lower()
        index += name_match.end()
        if index >= len(body):
            break
        if body[index] in '{"':
            value, index = parse_braced_value(body, index)
        else:
            end = body.find(",", index)
            if end < 0:
                end = len(body)
            value = body[index:end].strip()
            index = end
        fields[name] = value.strip()
    return fields


def parse_bibliography(text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    entry_start = re.compile(r"@(\w+)\s*\{\s*([^,]+),")
    for match in entry_start.finditer(text):
        depth = 1
        index = match.end()
        while index < len(text) and depth:
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
            index += 1
        entries[match.group(2).strip()] = parse_fields(text[match.end() : index - 1])
    return entries


def clean_latex(value: str) -> str:
    value = re.sub(r"\\(?:textit|emph|textbf|url)\s*\{([^{}]*)\}", r"\1", value)
    value = re.sub(r"\\['\"`^~=.uvHckbdtr]\s*\{?([A-Za-z])\}?", r"\1", value)
    value = value.replace(r"\&", "&").replace("~", " ")
    value = value.replace("{", "").replace("}", "")
    value = value.replace("--", "–")
    return re.sub(r"\s+", " ", value).strip().rstrip(".")


def short_authors(value: str) -> str:
    authors = [clean_latex(author) for author in re.split(r"\s+and\s+", value) if author.strip()]
    if not authors:
        return "Unknown authors"

    def surname(author: str) -> str:
        if "," in author:
            return author.split(",", 1)[0].strip()
        return author.split()[-1]

    if len(authors) == 1:
        return surname(authors[0])
    if len(authors) == 2:
        return f"{surname(authors[0])} and {surname(authors[1])}"
    return f"{surname(authors[0])} et al."


def build_records(keys: list[str], entries: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    missing = [key for key in keys if key not in entries]
    if missing:
        raise RuntimeError(f"Missing cited BibTeX entries: {missing}")

    records = []
    for key in keys:
        fields = entries[key]
        venue = fields.get("booktitle") or fields.get("journal") or fields.get("publisher") or ""
        records.append(
            {
                "key": key,
                "authors": short_authors(fields.get("author", "")),
                "title": TITLE_CORRECTIONS.get(key, clean_latex(fields.get("title", key))),
                "venue": clean_latex(venue),
                "year": clean_latex(fields.get("year", "n.d.")),
            }
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tex", type=Path, default=Path("arr_draft/main.tex"))
    parser.add_argument("--bib", type=Path, default=Path("arr_draft/myreferences.bib"))
    parser.add_argument("--output", type=Path, default=Path("website/src/referencesData.js"))
    args = parser.parse_args()

    keys = cited_keys(args.tex.read_text(encoding="utf-8"))
    entries = parse_bibliography(args.bib.read_text(encoding="utf-8"))
    records = build_records(keys, entries)
    payload = json.dumps(records, ensure_ascii=False, indent=2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "// Generated from the cited references in arr_draft/main.tex.\n"
        f"export const paperReferences = {payload};\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} cited references to {args.output}")


if __name__ == "__main__":
    main()
