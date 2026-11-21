"""Books -> one self-contained HTML file.

The page embeds its data as a *columnar-ish* JSON document (string tables for authors, categories, languages and
formats; one short array per book), gzip-compressed and base64-encoded when it is large. The browser decodes it
once, with ``DecompressionStream``.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import time
from importlib import resources

from . import __version__
from .fold import fold
from .grouping import assign_works
from .model import Book

PAYLOAD_VERSION = 1
LANGS = ("ar", "en", "fr")


def _asset(name: str) -> str:
    return resources.files("pocketshelf").joinpath("assets", name).read_text(encoding="utf-8")


def make_payload(books: list[Book], title: str = "Library", lang: str = "en", base: str = "") -> dict:
    """The JSON document the page reads. Books are sorted by folded title so the default order is alphabetical."""
    assign_works(books)
    books = sorted(books, key=lambda b: (fold(b.title), fold(b.author), b.year))
    cats: dict[str, int] = {}
    authors: dict[str, int] = {}
    alist: list[list] = []
    langs: dict[str, int] = {}
    fmts: dict[str, int] = {}
    works: dict[str, int] = {}
    rows: list[list] = []
    for b in books:
        ai = -1
        if b.author:
            key = fold(b.author)
            if key not in authors:
                authors[key] = len(alist)
                alist.append([b.author, b.author_death or 0, 1 if b.author_calendar == "ah" else 0])
            ai = authors[key]
            if b.author_death and not alist[ai][1]:
                alist[ai][1:] = [b.author_death, 1 if b.author_calendar == "ah" else 0]
        ci = cats.setdefault(b.category, len(cats)) if b.category else -1
        li = langs.setdefault(b.lang, len(langs)) if b.lang else -1
        fi = fmts.setdefault(b.fmt, len(fmts)) if b.fmt else -1
        wi = works.setdefault(b.work, len(works))
        if b.volumes:
            files: object = [[v.label, v.path, v.size] for v in b.volumes]
        else:
            files = b.path
        det: dict = {}
        for k, v in (
            ("e", b.editor),
            ("p", b.publisher),
            ("pl", b.place),
            ("ed", b.edition),
            ("s", b.series),
            ("i", b.isbn),
            ("n", b.note),
        ):
            if v:
                det[k] = v
        if b.alt_titles:
            det["at"] = b.alt_titles
        if b.tags:
            det["t"] = b.tags
        if b.ext_ids:
            det["x"] = b.ext_ids
        if b.pages:
            det["pg"] = b.pages
        rows.append([b.title, ai, ci, wi, b.year, b.size, li, fi, files, det or 0, b.mtime])
    return {
        "v": PAYLOAD_VERSION,
        "m": {"t": title, "lg": lang, "gen": time.strftime("%Y-%m-%d"), "base": base, "ver": __version__},
        "c": list(cats),
        "a": alist,
        "l": list(langs),
        "f": list(fmts),
        "b": rows,
    }


def encode_payload(payload: dict, compress: bool | None = None) -> tuple[str, str]:
    """Return ``(encoding, text)``: ``("gzip+base64", ...)`` or ``("json", ...)``."""
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if compress is None:
        compress = len(raw) > 200_000
    if compress:
        z = gzip.compress(raw, 9, mtime=0)
        return "gzip+base64", base64.b64encode(z).decode("ascii")
    return "json", raw.decode("utf-8").replace("</", "<\\/")


def build_html(
    books: list[Book], title: str = "Library", lang: str = "en", base: str = "", compress: bool | None = None
) -> str:
    if lang not in LANGS:
        raise ValueError(f"unknown UI language {lang!r}; available: {', '.join(LANGS)}")
    payload = make_payload(books, title, lang, base)
    enc, text = encode_payload(payload, compress)
    page = _asset("index.html")
    import html as _html

    parts = {
        "/*__CSS__*/": _asset("app.css"),
        "/*__FOLD__*/": _asset("fold.js"),
        "/*__JS__*/": _asset("app.js"),
        "__DATA_ENC__": enc,
        "__DATA__": text,
        "__TITLE__": _html.escape(title),
        "__LANG__": lang,
        "__DIR__": "rtl" if lang == "ar" else "ltr",
    }
    pat = re.compile("|".join(re.escape(k) for k in sorted(parts, key=len, reverse=True)))
    return pat.sub(lambda m: parts[m.group(0)], page)  # one pass: inserted text is never re-scanned
