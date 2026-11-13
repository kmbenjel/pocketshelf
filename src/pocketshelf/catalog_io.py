"""Read and write catalogs: CSV or JSON in the schema of docs/catalog-schema.md."""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import date, timedelta
from pathlib import Path

from .lives import split_life_dates
from .model import Book, Volume

COLUMNS = [
    "title", "author", "author_death", "author_calendar", "category", "path", "volumes", "size", "pages", "lang",
    "work", "edition", "editor", "publisher", "place", "year", "series", "isbn", "tags", "note", "ext_ids", "added",
]  # fmt: skip
INT_FIELDS = {"author_death", "size", "pages", "year", "mtime"}
ALIASES = {  # tolerated spellings -> canonical column
    "file": "path", "filename": "path", "url": "path", "authors": "author", "creator": "author", "name": "title",
    "section": "category", "categories": "category", "folder": "category", "language": "lang", "publisher_name": "publisher",
    "researcher": "editor", "editors": "editor", "date": "year", "published": "year", "bytes": "size", "filesize": "size",
    "work_id": "work", "workid": "work", "death": "author_death", "death_year": "author_death", "calendar": "author_calendar",
    "keywords": "tags", "subjects": "tags", "comment": "note", "notes": "note", "ids": "ext_ids", "isbn13": "isbn",
}  # fmt: skip


_NUM = re.compile(r"-?\d+")


def _int(v: object) -> int:
    """First integer in ``v`` (Arabic-Indic digits accepted); 0 when there is none. ``"1923-1924"`` -> 1923."""
    s = str(v if v is not None else "").translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    m = _NUM.search(s.replace(",", ""))
    return int(m.group()) if m else 0


def parse_volumes(v: object) -> list[Volume]:
    """JSON list of ``{n|label, path, size}``, or CSV text ``label|path|size;label|path|size``."""
    if not v:
        return []
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("["):
            try:
                v = json.loads(s)
            except ValueError:
                v = []
        else:
            out = []
            for chunk in s.split(";"):
                bits = [x.strip() for x in chunk.split("|")]
                if not bits or not any(bits):
                    continue
                label = bits[0]
                path = bits[1] if len(bits) > 1 else ""
                size = _int(bits[2]) if len(bits) > 2 else 0
                out.append(Volume(label, path, size))
            return out
    out = []
    for x in v if isinstance(v, list) else []:
        if isinstance(x, dict):
            out.append(Volume(str(x.get("label", x.get("n", ""))), str(x.get("path", "")), _int(x.get("size", 0))))
        elif isinstance(x, (list, tuple)) and x:
            out.append(Volume(str(x[0]), str(x[1]) if len(x) > 1 else "", _int(x[2]) if len(x) > 2 else 0))
    return out


def _split(v: object, sep: str = ";") -> list[str]:
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in str(v or "").split(sep) if x.strip()]


def row_to_book(row: dict, mapping: dict[str, str] | None = None) -> Book:
    mapping = mapping or {}
    r: dict[str, object] = {}
    for k, v in row.items():
        if k is None:
            continue
        key = mapping.get(k.strip(), mapping.get(k.strip().lower()))
        key = key or ALIASES.get(k.strip().lower(), k.strip().lower())
        if key not in r or not r[key]:
            r[key] = v
    b = Book()
    for f in ("title", "author", "category", "path", "lang", "work", "edition", "editor", "publisher", "place", "series", "isbn", "note"):
        val = r.get(f, "")
        setattr(b, f, ("; ".join(map(str, val)) if isinstance(val, list) else str(val or "")).strip())
    b.path = b.path.replace("\\", "/")
    for f in INT_FIELDS:
        if f in r:
            setattr(b, f, _int(r[f]))
    cal = str(r.get("author_calendar", "") or "").strip().lower()
    b.author_calendar = "ah" if cal in ("ah", "h", "hijri", "هـ") else "ce"
    added = str(r.get("added", "") or "").strip()
    if added and not b.mtime:
        try:
            b.mtime = (date.fromisoformat(added[:10]) - date(1970, 1, 1)).days
        except ValueError:
            pass
    if not b.author_death and b.author:
        name, death, cal = split_life_dates(b.author)
        if death:
            b.author, b.author_death, b.author_calendar = name, death, cal
    b.volumes = parse_volumes(r.get("volumes"))
    if b.volumes and not b.size:
        b.size = sum(v.size for v in b.volumes)
    b.tags = _split(r.get("tags"))
    ids = r.get("ext_ids")
    if isinstance(ids, dict):
        b.ext_ids = {str(k): str(v) for k, v in ids.items()}
    else:
        b.ext_ids = dict(p.split(":", 1) for p in _split(ids) if ":" in p)
    return b


def parse_mapping(spec: str | None) -> dict[str, str]:
    """``"author=author_name,work=work_id"`` -> {source column: canonical column}."""
    m: dict[str, str] = {}
    for item in (spec or "").split(","):
        if "=" in item:
            canon, src = item.split("=", 1)
            m[src.strip()] = canon.strip()
    return m


def read_catalog(path: str | Path, mapping: dict[str, str] | None = None) -> tuple[list[Book], dict]:
    """Read a CSV or JSON catalog; returns ``(books, meta)`` where meta is the optional dataset-level block."""
    p = Path(path)
    text = p.read_text(encoding="utf-8-sig")
    meta: dict = {}
    if p.suffix.lower() == ".json" or text.lstrip().startswith(("[", "{")):
        data = json.loads(text)
        if isinstance(data, dict):
            meta = data.get("meta", {}) or {}
            data = data.get("books", data.get("items", []))
        rows = data
    else:
        dialect = csv.excel_tab if "\t" in text.split("\n", 1)[0] else csv.excel
        rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    books = [row_to_book(r, mapping) for r in rows]
    books = [b for b in books if b.title or b.path]
    for b in books:
        if not b.title:
            b.title = b.path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return books, meta


def write_catalog(books: list[Book], path: str | Path) -> None:
    """Write books as a CSV that ``read_catalog`` (and ``--sidecar``) reads back."""
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for b in books:
            vols = ";".join(f"{v.label}|{v.path}|{v.size}" for v in b.volumes)
            w.writerow([
                b.title, b.author, b.author_death or "", b.author_calendar if b.author_death else "", b.category, b.path,
                vols, b.size or "", b.pages or "", b.lang, b.work, b.edition, b.editor, b.publisher, b.place,
                b.year or "", b.series, b.isbn, ";".join(b.tags), b.note, ";".join(f"{k}:{v}" for k, v in b.ext_ids.items()),
                (date(1970, 1, 1) + timedelta(days=b.mtime)).isoformat() if b.mtime else "",
            ])  # fmt: skip


def apply_sidecar(books: list[Book], sidecar: list[Book], by_path: bool = True) -> int:
    """Overlay sidecar rows (matched by ``path``) on scanned books: non-empty sidecar fields win. Returns matches."""
    index = {b.path: b for b in books if b.path}
    for b in books:
        for v in b.volumes:
            index.setdefault(v.path, b)
    n = 0
    for s in sidecar:
        target = index.get(s.path) if s.path else None
        if target is None:
            continue
        n += 1
        for f in ("title", "author", "category", "lang", "work", "edition", "editor", "publisher", "place", "series", "isbn", "note"):
            if getattr(s, f):
                setattr(target, f, getattr(s, f))
        for f in ("author_death", "pages", "year"):
            if getattr(s, f):
                setattr(target, f, getattr(s, f))
        if s.author_death:
            target.author_calendar = s.author_calendar
        if s.tags:
            target.tags = s.tags
        if s.ext_ids:
            target.ext_ids = {**target.ext_ids, **s.ext_ids}
    return n
