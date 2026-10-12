"""Loading and chunking of the company's own documents.

Policies and runbooks are written in sections, and assessors cite sections, so
the chunk boundary is the section heading. Long sections are split on
paragraph breaks, never in the middle of a sentence.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from complyrag.schemas import Chunk

_FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_SECTION = re.compile(r"^##\s+(?:(\d+)\.\s*)?(.+)$", re.MULTILINE)


def parse_markdown(raw: str) -> tuple[dict, str]:
    match = _FRONT_MATTER.match(raw)
    if not match:
        return {}, raw
    meta = yaml.safe_load(match.group(1)) or {}
    return meta, raw[match.end() :]


def _split_long(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts, current = [], ""
    for para in re.split(r"\n\s*\n", text):
        if current and len(current) + len(para) + 2 > max_chars:
            parts.append(current.strip())
            current = ""
        current += para + "\n\n"
    if current.strip():
        parts.append(current.strip())
    return parts


def chunk_document(path: Path, max_chars: int = 1200) -> list[Chunk]:
    meta, body = parse_markdown(path.read_text(encoding="utf-8"))
    doc_id = str(meta.get("doc_id") or path.stem)
    title = str(meta.get("title") or path.stem.replace("_", " "))
    system = str(meta.get("system") or "enterprise")
    base_meta = {
        "path": str(path),
        "owner": meta.get("owner"),
        "version": str(meta.get("version", "")),
        "last_reviewed": str(meta.get("last_reviewed", "")),
        "classification": meta.get("classification"),
    }

    headings = list(_SECTION.finditer(body))
    chunks: list[Chunk] = []
    for i, head in enumerate(headings):
        number = head.group(1) or str(i + 1)
        heading = head.group(2).strip()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        section_body = body[head.end() : end].strip()
        if not section_body:
            continue
        for part_no, part in enumerate(_split_long(section_body, max_chars), start=1):
            suffix = "" if part_no == 1 else f"-{part_no}"
            chunks.append(
                Chunk(
                    id=f"{doc_id}#s{number}{suffix}",
                    doc_id=doc_id,
                    title=title,
                    section=f"{number}. {heading}",
                    # The heading is kept in the chunk text: "3. Oversight measures"
                    # carries a lot of meaning for both BM25 and the embedder.
                    text=f"{heading}\n{part}",
                    system=system,
                    source="company",
                    metadata=dict(base_meta),
                )
            )
    return chunks


def load_corpus(data_dir: Path, folders: list[str], max_chars: int = 1200) -> list[Chunk]:
    chunks: list[Chunk] = []
    for folder in folders:
        for path in sorted((data_dir / folder).glob("*.md")):
            if path.name.lower() == "readme.md":
                continue
            chunks.extend(chunk_document(path, max_chars))
    return chunks
