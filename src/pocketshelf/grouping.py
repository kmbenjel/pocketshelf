"""Group editions of one work: explicit ``work`` ids first, then a title+author key."""

from __future__ import annotations

import re

from .fold import fold
from .model import Book

_NOISE = re.compile(
    r"\b(vol(ume)?|v|part|pt|ed(ition)?|tome|book|livre|ج|جزء|المجلد|مجلد)\s*\d+\b|\b\d+\s*(vols?|volumes|أجزاء)\b"
)
_SUB = re.compile(r"[:;،].*$")
_ARTICLES = ("the ", "a ", "an ", "le ", "la ", "les ", "l ", "der ", "die ", "das ", "el ", "al ", "ال")


def title_key(title: str) -> str:
    t = fold(_SUB.sub("", title or ""))
    t = _NOISE.sub(" ", t)
    for art in _ARTICLES:
        if t.startswith(art) and len(t) > len(art) + 2:
            t = t[len(art) :]
            break
    return " ".join(t.split())


def author_key(author: str) -> str:
    """The author's main name: the part before a comma (``Austen, Jane``), else the last word."""
    a = (author or "").strip()
    if not a:
        return ""
    if "," in a and not re.search(r"[؀-ۿ]", a):
        a = a.split(",", 1)[0]
        return fold(a).split()[-1] if fold(a) else ""
    toks = fold(a).split()
    return toks[-1] if toks else ""


def assign_works(books: list[Book]) -> int:
    """Give every book a ``work`` id; returns the number of works with more than one edition."""
    ids: dict[str, str] = {}
    for b in books:
        if b.work:
            continue
        tk = title_key(b.title)
        key = f"{tk}|{author_key(b.author)}" if tk else f"~{id(b)}"
        b.work = ids.setdefault(key, f"k{len(ids)}")
    count: dict[str, int] = {}
    for b in books:
        count[b.work] = count.get(b.work, 0) + 1
    return sum(1 for n in count.values() if n > 1)
