"""Structure-aware parsing of the AI Act text.

Legal text is not chunked by a fixed token window. Every chunk is exactly one
numbered paragraph of one article, so a citation like "Art. 14(4)" maps to one
chunk and never cuts a list of points in half.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from complyrag.schemas import Chunk

csv.field_size_limit(10**9)

# Paragraph numbers appear inline ("... lifecycle. 2. The risk management ...").
# A number only counts if it follows the end of a sentence and is followed by a
# capital letter, which keeps references like "Article 72." from matching.
_PARAGRAPH_START = r"(?:^|(?<=[.;:]\s)|(?<=[.;:])){n}\.\s(?=[A-Z‘'(])"


@dataclass(frozen=True)
class Article:
    number: int
    title: str
    chapter: str
    section: str
    text: str


def load_articles(csv_path: Path) -> dict[int, Article]:
    articles: dict[int, Article] = {}
    with csv_path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            num = row["article_number"].strip()
            if not num.isdigit():
                continue
            articles[int(num)] = Article(
                number=int(num),
                title=row["article_title"].strip(),
                chapter=row.get("chapter_number", "").strip(),
                section=row.get("section_number", "").strip(),
                text=row["article_text"].strip(),
            )
    return articles


def split_paragraphs(text: str) -> list[tuple[int, str]]:
    """Return [(paragraph_number, paragraph_text), ...] for one article.

    Paragraphs are numbered 1..n in order, so the search looks for the next
    expected number only. Articles without numbered paragraphs come back as a
    single paragraph 1.
    """
    starts: list[tuple[int, int, int]] = []
    pos, n = 0, 1
    while True:
        match = re.compile(_PARAGRAPH_START.format(n=n)).search(text, pos)
        if not match:
            break
        starts.append((n, match.start(), match.end()))
        pos, n = match.end(), n + 1

    if not starts:
        return [(1, text.strip())]

    out = []
    for i, (num, _, body_start) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(text)
        out.append((num, text[body_start:end].strip()))
    return out


def paragraph_text(articles: dict[int, Article], article: int, paragraph: int) -> str:
    for num, body in split_paragraphs(articles[article].text):
        if num == paragraph:
            return body
    raise KeyError(f"Article {article} has no paragraph {paragraph}")


def regulation_chunks(articles: dict[int, Article], only: set[int] | None = None) -> list[Chunk]:
    chunks = []
    for art in articles.values():
        if only and art.number not in only:
            continue
        for num, body in split_paragraphs(art.text):
            chunks.append(
                Chunk(
                    id=f"AIA-Art{art.number}#p{num}",
                    doc_id=f"AIA-Art{art.number}",
                    title=f"AI Act Article {art.number}: {art.title}",
                    section=f"{art.number}({num})",
                    text=body,
                    system="regulation",
                    source="regulation",
                    metadata={"chapter": art.chapter, "section": art.section},
                )
            )
    return chunks
