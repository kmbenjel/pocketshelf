"""Walk a folder of ebooks and turn it into ``Book`` entries."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import unicodedata
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from .lives import split_life_dates
from .meta.epub import read_epub
from .meta.filename import FilenameParser
from .meta.pdf import read_pdf
from .model import BOOK_EXTS, Book, Volume

_VOL_PREFIX = re.compile(r"^\s*(\d{1,3})\s*[-–._)\s]\s*\S")
_VOL_WORDS = re.compile(
    r"(?i)(?:\b(?:vol(?:ume)?s?\.?|v\.?|part|pt\.?|tome|t\.?|book|livre|band|bd\.?)\s*[-_.]?\s*\d+\b|"
    r"\b\d+\s*(?:of|de|von|sur)\s*\d+\b|(?:ج|جـ|جزء|المجلد|مجلد)\s*\d+|\(\s*\d+\s*\)|[-_ ]\d{1,3}$)"
)


@dataclass
class ScanOptions:
    exts: tuple[str, ...] = (".pdf", ".epub", ".djvu", ".djv")
    profile: str | None = None
    templates: list[str] = field(default_factory=list)
    order: str = "title-author"
    embedded: bool = True
    prefer: str = "embedded"  # "embedded" | "filename": which wins when both give a title/author
    exclude: list[str] = field(default_factory=list)
    jobs: int = 8
    cache: bool = True
    cache_dir: str | None = None
    group_volumes: bool = True


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def is_volume_set(names: list[str]) -> bool:
    """True if the files of one folder are volumes of one book: all start with a number, or differ only by one."""
    if len(names) < 2:
        return False
    stems = [os.path.splitext(n)[0] for n in names]
    if all(_VOL_PREFIX.match(s) for s in stems):
        return True
    stripped = {" ".join(_VOL_WORDS.sub(" ", s).split()).lower() for s in stems}
    return len(stripped) == 1 and bool(next(iter(stripped)))


def volume_label(stem: str, folder: str = "") -> str:
    """Short label of a volume file: its leading number (``01``), else the stem minus the folder's words."""
    m = _VOL_PREFIX.match(stem)
    if m:
        return m.group(1).zfill(2)
    m = _VOL_WORDS.search(stem)
    if m:
        d = re.search(r"\d+", m.group())
        if d:
            return d.group().zfill(2)
    return stem


def detect_lang(*texts: str) -> str:
    s = " ".join(texts)
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return ""
    ar = sum(1 for c in letters if "؀" <= c <= "ۿ" or "ݐ" <= c <= "ݿ")
    return "ar" if ar * 2 >= len(letters) else ""


class Cache:
    """Embedded-metadata cache keyed by path+size+mtime, kept outside the library (``~/.cache/pocketshelf``)."""

    def __init__(self, root: Path, directory: str | None, enabled: bool):
        self.data: dict[str, dict] = {}
        self.dirty = False
        self.file: Path | None = None
        if enabled:
            base = Path(directory) if directory else Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "pocketshelf"
            self.file = base / (hashlib.sha1(str(root.resolve()).encode()).hexdigest()[:16] + ".json")
            try:
                self.data = json.loads(self.file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self.data = {}

    def key(self, rel: str, st: os.stat_result) -> str:
        return f"{rel}|{st.st_size}|{int(st.st_mtime)}"

    def save(self) -> None:
        if self.file and self.dirty:
            try:
                self.file.parent.mkdir(parents=True, exist_ok=True)
                self.file.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
            except OSError:
                pass


def read_embedded(path: str) -> dict:
    low = path.lower()
    if low.endswith(".pdf"):
        return read_pdf(path)
    if low.endswith(".epub"):
        return read_epub(path)
    return {}


def _excluded(rel: str, patterns: list[str]) -> bool:
    parts = rel.split("/")
    return any(fnmatch.fnmatch(rel, p) or any(fnmatch.fnmatch(x, p) for x in parts) for p in patterns)


def walk_dirs(root: Path, opts: ScanOptions) -> list[tuple[str, list[os.DirEntry]]]:
    """All directories under ``root`` that hold ebooks: ``(relative dir with '/', [entries])``."""
    out: list[tuple[str, list[os.DirEntry]]] = []
    stack = [(root, "")]
    while stack:
        d, rel = stack.pop()
        try:
            with os.scandir(d) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError:
            continue
        files = []
        for e in entries:
            if e.name.startswith((".", "~$")):
                continue
            erel = f"{rel}/{e.name}" if rel else e.name
            if _excluded(erel, opts.exclude):
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    stack.append((Path(e.path), erel))
                elif e.is_file() and e.name.lower().endswith(opts.exts):
                    files.append(e)
            except OSError:
                continue
        if files:
            out.append((rel, files))
    out.sort(key=lambda t: t[0])
    return out


def scan(root: str | Path, opts: ScanOptions | None = None, progress: Callable[[int, int], None] | None = None) -> list[Book]:
    opts = opts or ScanOptions()
    root = Path(root)
    parser = FilenameParser(opts.templates, opts.profile, opts.order)
    cache = Cache(root, opts.cache_dir, opts.cache and opts.embedded)
    dirs = walk_dirs(root, opts)
    total = sum(len(f) for _, f in dirs)
    done = 0

    # 1. embedded metadata for the files we need (first file of a volume set, every single file)
    wanted: list[tuple[str, os.DirEntry]] = []
    plans: list[tuple[str, list[os.DirEntry], bool]] = []
    for rel, files in dirs:
        vol = opts.group_volumes and rel != "" and is_volume_set([f.name for f in files])
        plans.append((rel, files, vol))
        for f in (files[:1] if vol else files):
            wanted.append((f"{rel}/{f.name}" if rel else f.name, f))
    embedded: dict[str, dict] = {}
    if opts.embedded and wanted:

        def work(item: tuple[str, os.DirEntry]) -> tuple[str, dict]:
            rel, e = item
            st = e.stat()
            k = cache.key(rel, st)
            if k in cache.data:
                return rel, cache.data[k]
            r = read_embedded(e.path)
            cache.data[k] = r
            cache.dirty = True
            return rel, r

        with ThreadPoolExecutor(max_workers=max(1, opts.jobs)) as ex:
            for i, (rel, r) in enumerate(ex.map(work, wanted)):
                embedded[rel] = r
                if progress and i % 200 == 0:
                    progress(i, len(wanted))
        cache.save()

    # 2. build the books
    books: list[Book] = []
    for rel, files, vol in plans:
        if vol:
            parent, _, leaf = rel.rpartition("/")
            first_rel = f"{rel}/{files[0].name}"
            parsed = parser(_nfc(leaf), is_folder=True)
            vols = []
            for f in files:
                st = f.stat()
                vols.append(Volume(volume_label(os.path.splitext(_nfc(f.name))[0]), f"{rel}/{_nfc(f.name)}", st.st_size))
            b = _make_book(parsed, embedded.get(first_rel, {}), opts)
            b.category = _nfc(parent)
            b.volumes = vols
            b.size = sum(v.size for v in vols)
            b.mtime = int(max(f.stat().st_mtime for f in files) // 86400)
            books.append(b)
            done += len(files)
        else:
            for f in files:
                st = f.stat()
                frel = f"{rel}/{f.name}" if rel else f.name
                parsed = parser(_nfc(os.path.splitext(f.name)[0]))
                b = _make_book(parsed, embedded.get(frel, {}), opts)
                b.category = _nfc(rel)
                b.path = _nfc(frel)
                b.size = st.st_size
                b.mtime = int(st.st_mtime // 86400)
                books.append(b)
                done += 1
    if progress:
        progress(total, total)
    return books


def _make_book(parsed: dict, emb: dict, opts: ScanOptions) -> Book:
    """Merge a filename parse and embedded metadata according to ``opts.prefer``."""
    b = Book()
    first, second = (emb, parsed) if opts.prefer == "embedded" else (parsed, emb)
    for f in ("title", "author", "publisher", "lang", "series", "isbn", "editor", "place", "edition"):
        val = first.get(f) or second.get(f) or ""
        setattr(b, f, str(val).strip())
    b.year = int(parsed.get("year") or emb.get("year") or 0)
    if parsed.get("author_death") and (not emb.get("author") or opts.prefer != "embedded" or b.author == parsed.get("author")):
        b.author_death = int(parsed["author_death"])
        b.author_calendar = str(parsed.get("author_calendar", "ce"))
    if b.author and not b.author_death:
        name, death, cal = split_life_dates(b.author)
        if death:
            b.author, b.author_death, b.author_calendar = name, death, cal
    if emb.get("tags"):
        b.tags = [t.strip() for t in str(emb["tags"]).split(";") if t.strip()]
    if not b.lang:
        b.lang = detect_lang(b.title, b.author)
    return b
