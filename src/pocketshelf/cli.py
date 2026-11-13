"""Command line: ``pocketshelf build|scan|inspect|demo|bench``."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from importlib import resources
from pathlib import Path

from . import __version__
from .build import LANGS, build_html
from .catalog_io import apply_sidecar, parse_mapping, read_catalog, write_catalog
from .meta.filename import FilenameParser
from .scan import ScanOptions, read_embedded, scan

DESCRIPTION = """\
Turn a folder of PDFs/EPUBs/DJVUs, or a CSV/JSON catalog, into ONE self-contained offline HTML file:
instant accent-insensitive search (Arabic folding included), categories, authors by century, edition grouping,
dark mode and RTL/LTR. No server, no links between local files: open it straight from a phone's storage.
"""

EPILOG = """\
examples:
  pocketshelf build ~/Books                       writes ~/Books/pocketshelf.html (links are relative)
  pocketshelf build ~/Books -o index.html --lang ar --profile warraq
  pocketshelf build ~/Books --template '{author} - {title} ({year})'
  pocketshelf build catalog.csv -o catalog.html   a catalog without files (see docs/catalog-schema.md)
  pocketshelf scan ~/Books -o books.csv           edit the metadata in a spreadsheet, then:
  pocketshelf build ~/Books --sidecar books.csv
  pocketshelf demo --open                         a live sample in under a minute
"""


def _log(*a: object, **kw: object) -> None:
    print(*a, file=sys.stderr, **kw)  # type: ignore[call-overload]


def _add_scan_args(p: argparse.ArgumentParser) -> None:
    g = p.add_argument_group("how filenames and files are read")
    g.add_argument(
        "--profile",
        help="filename profile: warraq, dashes, author-title, or an installed plugin (entry point group pocketshelf.profiles)",
    )
    g.add_argument(
        "--template",
        action="append",
        default=[],
        metavar="T",
        help="filename template, repeatable, first match wins; fields: {title} {author} {editor} {publisher} {place} {year} {series} {edition} {volume} {lang} {skip}",
    )
    g.add_argument(
        "--order",
        choices=["title-author", "author-title"],
        default="title-author",
        help="which part of 'A - B' is the title when no template/profile is given (default: title-author)",
    )
    g.add_argument(
        "--prefer",
        choices=["embedded", "filename"],
        default="embedded",
        help="which source wins when both give a title or author (default: embedded)",
    )
    g.add_argument(
        "--no-embedded",
        action="store_true",
        help="do not read PDF info/XMP or EPUB OPF (fastest; filenames only)",
    )
    g.add_argument(
        "--ext", default="pdf,epub,djvu", help="comma-separated extensions to index (default: pdf,epub,djvu)"
    )
    g.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="skip matching files or folders, repeatable",
    )
    g.add_argument(
        "--no-volume-groups",
        action="store_true",
        help="never merge numbered files of one folder into a multi-volume book",
    )
    g.add_argument("--jobs", type=int, default=8, help="threads reading file metadata (default 8)")
    g.add_argument(
        "--no-cache", action="store_true", help="do not keep a metadata cache in ~/.cache/pocketshelf"
    )


def _scan_opts(a: argparse.Namespace) -> ScanOptions:
    return ScanOptions(
        exts=tuple("." + e.strip().lstrip(".").lower() for e in a.ext.split(",") if e.strip()),
        profile=a.profile, templates=a.template, order=a.order, embedded=not a.no_embedded, prefer=a.prefer,
        exclude=a.exclude, jobs=a.jobs, cache=not a.no_cache, group_volumes=not a.no_volume_groups,
    )  # fmt: skip


def _relative_base(root: Path, out: Path) -> str:
    """Prefix that turns a library-relative path into a link valid from where ``out`` sits ('' when beside the books)."""
    rel = os.path.relpath(root.resolve(), out.resolve().parent).replace(os.sep, "/")
    return "" if rel == "." else rel + "/"


def cmd_build(a: argparse.Namespace) -> int:
    src = Path(a.source)
    if not src.exists():
        _log(f"error: {src} does not exist")
        return 2
    t0 = time.time()
    meta: dict = {}
    if src.is_dir():
        books = scan(
            src,
            _scan_opts(a),
            progress=lambda i, n: _log(f"\r  reading metadata {i}/{n}", end="") if n > 400 else None,
        )
        if len(books) > 400:
            _log()
        out = Path(a.output) if a.output else src / "pocketshelf.html"
        base = a.base if a.base is not None else _relative_base(src, out)
        title = a.title or src.resolve().name
        if not books:
            _log(f"error: no {a.ext} files found under {src}")
            return 1
    else:
        books, meta = read_catalog(src, parse_mapping(a.map))
        out = Path(a.output) if a.output else src.with_suffix(".html")
        base = a.base or ""
        title = a.title or meta.get("title") or src.stem
        if not books:
            _log(f"error: no rows read from {src}")
            return 1
    if a.sidecar:
        side, _ = read_catalog(a.sidecar, parse_mapping(a.map))
        n = apply_sidecar(books, side)
        _log(f"  sidecar: {n} of {len(side)} rows matched a file by path")
    lang = a.lang or meta.get("lang") or "en"
    if lang not in LANGS:
        _log(f"error: --lang must be one of {', '.join(LANGS)}")
        return 2
    page = build_html(
        books,
        title=title,
        lang=lang,
        base=base,
        compress=False if a.no_compress else (True if a.compress else None),
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    _log(f"{len(books):,} entries -> {out} ({len(page.encode()) / 1e6:.2f} MB) in {time.time() - t0:.1f}s")
    if base:
        _log(f"  links are resolved from {out.resolve().parent} as '{base}<path>'")
    return 0


def cmd_scan(a: argparse.Namespace) -> int:
    books = scan(a.source, _scan_opts(a))
    out = a.output or "pocketshelf-catalog.csv"
    write_catalog(books, out)
    _log(f"{len(books):,} entries -> {out} (edit it, then: pocketshelf build {a.source} --sidecar {out})")
    return 0


def cmd_inspect(a: argparse.Namespace) -> int:
    p = Path(a.file)
    parser = FilenameParser(a.template, a.profile, a.order)
    res = {
        "file": str(p),
        "filename_parse": parser(p.stem),
        "embedded": read_embedded(str(p)),
    }
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


def _demo_books(kind: str):
    out = []
    for name in {
        "arabic": ["arabic-classics.csv"],
        "gutenberg": ["gutenberg-sample.csv"],
        "all": ["gutenberg-sample.csv", "arabic-classics.csv"],
    }[kind]:
        with resources.as_file(resources.files("pocketshelf").joinpath("data", name)) as f:
            books, _ = read_catalog(f)
            out += books
    return out


def cmd_demo(a: argparse.Namespace) -> int:
    kind = "arabic" if a.arabic else "all"
    books = _demo_books(kind)
    lang = "ar" if a.arabic else (a.lang or "en")
    title = "مكتبة العربية الكلاسيكية" if a.arabic else "Public-domain shelf"
    out = Path(a.output or "pocketshelf-demo.html")
    page = build_html(books, title=title, lang=lang)
    out.write_text(page, encoding="utf-8")
    _log(f"{len(books):,} sample entries -> {out.resolve()} ({len(page.encode()) / 1e6:.2f} MB)")
    if a.open:
        import webbrowser

        webbrowser.open(out.resolve().as_uri())
    return 0


def cmd_bench(a: argparse.Namespace) -> int:
    from .synth import synthetic_books

    t0 = time.time()
    books = synthetic_books(a.n, seed=a.seed)
    t1 = time.time()
    page = build_html(books, title=f"Synthetic library {a.n:,}", lang=a.lang)
    t2 = time.time()
    out = Path(a.output or f"bench-{a.n}.html")
    out.write_text(page, encoding="utf-8")
    import gzip

    res = {"books": a.n, "html_bytes": len(page.encode()), "html_gzip_bytes": len(gzip.compress(page.encode(), 6)),
           "generate_s": round(t1 - t0, 2), "build_s": round(t2 - t1, 2), "file": str(out)}  # fmt: skip
    print(json.dumps(res))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="pocketshelf",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--version", action="version", version=f"pocketshelf {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="{build,scan,inspect,demo,bench}")

    b = sub.add_parser(
        "build",
        help="build the HTML catalog from a folder or a catalog file",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    b.add_argument("source", help="a folder of ebooks, or a catalog .csv/.json")
    b.add_argument(
        "-o",
        "--output",
        help="output file (folder default: <folder>/pocketshelf.html; catalog default: next to it)",
    )
    b.add_argument("--title", help="page title (default: the folder name)")
    b.add_argument(
        "--lang", choices=LANGS, help="default UI language; the reader can switch it in Settings (default en)"
    )
    b.add_argument(
        "--base",
        help="prefix put before every file path (default: computed from where --output sits relative to the library)",
    )
    b.add_argument(
        "--sidecar",
        metavar="CSV",
        help="CSV (same columns as a catalog) whose rows, matched by path, override scanned metadata",
    )
    b.add_argument(
        "--map", metavar="A=col,B=col", help="map catalog columns, e.g. author=author_name,work=work_id"
    )
    comp = b.add_mutually_exclusive_group()
    comp.add_argument(
        "--no-compress",
        action="store_true",
        help="embed the data as plain JSON (largest, readable in the HTML)",
    )
    comp.add_argument(
        "--compress", action="store_true", help="always gzip+base64 the data (default: only above 200 KB)"
    )
    _add_scan_args(b)
    b.set_defaults(fn=cmd_build)

    s = sub.add_parser(
        "scan",
        help="write the scanned metadata as an editable CSV",
        description="Scan a folder and write a catalog CSV you can correct in a spreadsheet, then pass back with --sidecar.",
    )
    s.add_argument("source")
    s.add_argument("-o", "--output", help="CSV to write (default: pocketshelf-catalog.csv)")
    _add_scan_args(s)
    s.set_defaults(fn=cmd_scan)

    i = sub.add_parser(
        "inspect", help="show what pocketshelf reads from one file (filename parse + embedded metadata)"
    )
    i.add_argument("file")
    i.add_argument("--profile")
    i.add_argument("--template", action="append", default=[])
    i.add_argument("--order", choices=["title-author", "author-title"], default="title-author")
    i.set_defaults(fn=cmd_inspect)

    d = sub.add_parser("demo", help="build a sample catalog from public-domain metadata")
    d.add_argument("-o", "--output")
    d.add_argument(
        "--arabic", action="store_true", help="the Arabic classics sample with an Arabic interface"
    )
    d.add_argument("--lang", choices=LANGS)
    d.add_argument("--open", action="store_true", help="open the result in the default browser")
    d.set_defaults(fn=cmd_demo)

    be = sub.add_parser(
        "bench", help="build a synthetic catalog of N books and report the size and build time"
    )
    be.add_argument("-n", type=int, default=20000)
    be.add_argument("--seed", type=int, default=7)
    be.add_argument("--lang", choices=LANGS, default="en")
    be.add_argument("-o", "--output")
    be.set_defaults(fn=cmd_bench)

    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except (ValueError, OSError) as e:
        _log(f"error: {e}")
        return 2
