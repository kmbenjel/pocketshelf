<div align="center">

# pocketshelf

**Your PDFs, EPUBs and DJVUs as one offline HTML file you open from your phone's storage.**<br>
Instant search that ignores accents and Arabic spelling variants, categories, authors by century, editions grouped. No server, no app, no cloud.

[![CI](https://github.com/kmbenjel/pocketshelf/actions/workflows/ci.yml/badge.svg)](https://github.com/kmbenjel/pocketshelf/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pocketshelf.svg)](https://pypi.org/project/pocketshelf/)
[![Python](https://img.shields.io/pypi/pyversions/pocketshelf.svg)](https://pypi.org/project/pocketshelf/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](pyproject.toml)

<img src="docs/media/hero.webp" alt="pocketshelf catalog on a desktop and three phones: search with highlights, editions of one work, authors by century in dark mode, and an Arabic right-to-left view" width="900">

</div>

```bash
uvx pocketshelf build ~/Books        # writes ~/Books/pocketshelf.html  (or: pipx install pocketshelf)
pocketshelf demo --open              # a live sample from public-domain metadata, in under a minute
```

**[Live demo](https://kmbenjel.github.io/pocketshelf/)** · [Arabic demo](https://kmbenjel.github.io/pocketshelf/arabic.html) · [Catalog schema](docs/catalog-schema.md) · [Arabic docs](docs/ar/index.md)

<p align="center"><img src="docs/media/search.gif" alt="Typing three searches on a phone: a prefix, an accent-free French title, and an Arabic query that ignores alef and hamza variants" width="300"></p>

## Why it exists

A personal library of thousands of PDFs lives on a phone or a USB stick. Browsing it means scrolling a file manager, or running Calibre
on a computer and a server for the phone. Mobile browsers will not follow links between local HTML files, so the usual "static site
of pages" idea breaks on exactly the device where you read.

pocketshelf makes **one file**: the data, the search engine and the interface are all inside it. Put it beside the books, open it from
the phone's storage, and every title is a plain relative link to its PDF. It was built for a 16,700-volume Arabic library on an Android
phone, and rebuilt as a general tool: any language, any folder layout, any catalog.

## Why pocketshelf? How it compares

Checked against each project's documentation on 2026-11-13 and, where marked **measured**, by running it (script: [`bench/compare.sh`](bench/compare.sh)).
"–" means I did not check it, so I make no claim.

| | pocketshelf | Calibre content server | Calibre catalog export | Calibre-Web | Kavita | Komga | Ubooquity | Kiwix |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Needs a server running to browse | **no** | yes [^cs] | no | yes [^cw] | yes | yes | yes | no (reads ZIM files) |
| One offline file, opened from phone storage | **yes** | no | partial [^cat] | no | no | no | no | no (ZIM files + app) |
| Indexes your existing folder without importing or converting | **yes** | no (imports into its library) | no | no (needs a Calibre `metadata.db`) | – | yes (**measured**) | – | no (needs ZIM) |
| Search ignores accents and Arabic hamza/ta marbuta variants | **yes** (tested) | Latin accents yes, Arabic hamza/alef no (**measured**) | – | – | – | Latin accents yes, Arabic hamza/alef no (**measured**) | – | – |
| Right-to-left interface | **yes**, per-language setting | – | – | – | – | – | – | – |
| Authors grouped by Hijri or Gregorian century | **yes** | no built-in | no built-in | – | – | – | – | – |
| Editions of one work grouped | **yes** | no built-in | no built-in | – | – | – | – | – |
| Install size | **167 KB wheel**, no dependencies | **measured:** 229 MB download, 910 MB installed (9.18.0) | same | pip + Calibre library | 112 MB (v0.9.1.4) | 121 MB jar + Java (1.30.1) | – | 67 MB APK (3.14.1, arm64) |

[^cs]: "A calibre process must be running" ([manual](https://manual.calibre-ebook.com/server.html)); full offline mode needs HTTPS.
[^cw]: Python web app (`cps`, port 8083) over a Calibre library ([README](https://github.com/janeczku/calibre-web)).
[^cat]: `calibredb catalog` writes static files (CSV measured: 2.4 s for 20,000 books); it is a list, not a searchable page.

### What is different, with evidence

1. **Nothing to run.** The output is one HTML file. `pocketshelf demo` produces a working catalog of 3,018 books in 0.2 s and 0.22 MB; open it with
   no network and no process.
2. **It stays quick at 20,000 books.** Measured on a [public Project Gutenberg title list](bench/pg_catalog_to_csv.py) and on synthetic data (see
   [Benchmarks](#benchmarks)): about 1 MB of HTML, ready in 299 ms on a CPU throttled 4x to resemble a phone, searches in tens of milliseconds, and only the rows on screen exist in the DOM.
3. **Search that knows Arabic.** `احياء علوم` finds «إحياء علوم الدين»; `miserables` finds *Les Misérables*; harakat, tatweel, alef/hamza forms, ta marbuta and ya are
   folded on both sides, with the same rules in Python and in the page (a test runs both against each other).
4. **Built for scholarly libraries.** Authors are grouped by century in the author's own calendar (7th c. AH next to 19th c. CE), editions of one work
   share a card, and a catalog can come from a CSV, so a bibliography with no files at all gets the same interface. The CSV schema is shared with the
   [turath-catalog](https://warraq.benjelloun.dev/turath-catalog/) dataset.
5. **The reader owns the language.** Arabic, English and French interfaces, switched in Settings, with right-to-left layout following the language, not the browser.

### When to use something else

If you want to read inside the app, track reading progress, sync across devices, serve many users, convert formats or edit metadata in place,
use Calibre (with Calibre-Web or its content server), Kavita or Komga: they are libraries with servers, and pocketshelf is deliberately only an index.
Kiwix is the right tool for packaged web content such as Wikipedia, not for your own PDFs. If your phone cannot run a modern browser (the compressed
data needs `DecompressionStream`), build with `--no-compress`.

## Features

- **One file.** Data, search, UI, styles: inline. No network access, no fonts, no CDN.
- **Instant search** across title, author, editor, publisher, category, tags and identifiers; accent- and diacritic-insensitive; Arabic folding; matches highlighted; ranked (exact title, word start, anywhere).
- **Virtualised list**: only visible rows are rendered, and the search index is built after the first paint.
- **Categories as a tree** (from folders or the `category` column), **authors by century** (Hijri and Gregorian), **editions grouped**, statistics, six sort orders, filters.
- **Metadata from everywhere**: PDF Info and XMP, EPUB OPF (Dublin Core, calibre series), filename templates and profiles (pluggable, `warraq` for Arabic naming), and a sidecar CSV you can edit in a spreadsheet.
- **Multi-volume books** from numbered files in one folder (`01 - …`, `vol 2`, `ج3`).
- **Dark mode**, two palettes, RTL/LTR, Arabic/English/French UI, keyboard `/` to search, back button closes panels, state in the URL hash.
- **Zero dependencies**, Python 3.10+, a 167 KB wheel.

## Usage

```bash
pocketshelf build ~/Books                                   # folder -> ~/Books/pocketshelf.html
pocketshelf build ~/Books -o index.html --lang ar           # elsewhere; links stay valid (computed relative base)
pocketshelf build ~/Books --template '{author} - {title} ({year})'
pocketshelf build ~/Books --profile warraq                  # <title> - <author> - ت <editor> - <publisher> <city>
pocketshelf scan ~/Books -o books.csv                       # edit the metadata in a spreadsheet ...
pocketshelf build ~/Books --sidecar books.csv               # ... and feed it back
pocketshelf build catalog.csv -o catalog.html               # a catalog without files (docs/catalog-schema.md)
pocketshelf inspect ~/Books/some.pdf                        # what is read from one file
```

Copy the folder (books and `pocketshelf.html`) to the phone and open the HTML from the file manager with Chrome or Brave. Details: [catalog schema](docs/catalog-schema.md), `pocketshelf build --help`.

## How it works

```mermaid
flowchart LR
  A[Folder of PDF / EPUB / DJVU] --> S[scan: walk, volume sets,<br/>PDF Info/XMP, EPUB OPF,<br/>filename templates and profiles]
  C[CSV / JSON catalog] --> M[merge: sidecar over embedded over filename]
  S --> M
  M --> G[group editions,<br/>compute centuries]
  G --> P[payload: string tables + one array per book]
  P --> Z[gzip + base64]
  Z --> H[(one HTML file:<br/>data + fold.js + app.js + css)]
  H --> B[browser: decode, virtual list,<br/>lazy search index]
```

Design decisions:

- **One file, no links between files.** Mobile browsers do not follow local file links; so the page never navigates, it switches views in place and uses the URL hash for state.
- **Compact data.** Authors, categories, languages and formats are string tables; each book is one short array; the whole payload is gzip-compressed and base64-embedded. 20,000 books cost about 0.6 MB.
- **Fold twice, the same way.** `fold.py` (build side, grouping) and `fold.js` (page) implement one rule set and are tested against each other.
- **Lazy index.** The page paints first, then folds titles and authors in the background; the first query waits only if it comes before that.
- **Fixed-height rows** make the virtual list a pair of binary searches; details open in a panel instead of expanding rows.
- **Plugins, not options.** Naming conventions are filename *profiles*, found through the `pocketshelf.profiles` entry point (`warraq` is shipped; `arabic-bib` provides a fuller one when installed).

## Benchmarks

Headless Chrome 157 on a 32-vCPU cloud VM; "4x" means `Emulation.setCPUThrottlingRate(4)`, which resembles a mid-range phone but is not a real phone (on an older laptop CPU the 4x run takes 0.7-0.8 s).
Real titles are the first 20,000 texts of the Project Gutenberg catalog; synthetic is `pocketshelf bench -n 20000`.
Reproduce: `make bench`, or `bench/load_time.mjs` (see [`bench/RESULTS.md`](bench/RESULTS.md) for the run and the machine).

| 20,000 books | HTML file | Build | Ready at 1x | Ready at 4x | Search "river" at 4x |
|---|---|---|---|---|---|
| Real titles (Project Gutenberg) | 1.01 MB | 1.8 s | 77 ms | 299 ms | 21 ms |
| Synthetic (`pocketshelf bench`) | 0.86 MB | 1.1 s | 76 ms | 288 ms | 28 ms |

The first query after start-up also builds the search index when it comes before the background timer (88 ms at 1x, 356 ms at 4x for a 17,000-hit query); every later query takes 1-30 ms.
Building from a folder of 20,000 one-page PDFs takes 5.0 s.

Head to head on the same 20,000 synthetic books, same VM:

| | Calibre 9.18.0 | Komga 1.30.1 | pocketshelf |
|---|---|---|---|
| Download / installed | 229 MB / 910 MB | 121 MB jar + Java | 167 KB wheel |
| Make 20,000 books searchable | 581 s (records via the Python API) | 44.8 s (scan of 20,000 PDFs) | 1.1 s (CSV), 5.0 s (folder of PDFs) |
| Running cost while you browse | server: 191 MB resident | server: 1,036 MB resident | none: a browser tab and one file |
| Static catalog export | CSV, 2.4 s, no search UI | none | the page itself |

Arabic probe (`احياء علوم` against a title written «إحياء علوم الدين»): Calibre 0 hits, Komga 0 hits, pocketshelf 1 hit; all three find `miserables` in *Les Misérables*.
Everything, with the raw lines: [`bench/RESULTS.md`](bench/RESULTS.md); scripts: [`bench/compare.sh`](bench/compare.sh), [`bench/browser_bench.sh`](bench/browser_bench.sh).

## Roadmap

- Optional cover thumbnails for EPUBs (a separate, lazy-loaded file so the main page stays small).
- Per-book reading-status marks stored in the browser.
- More interface languages (contributions welcome: one dictionary in `app.js`).
- Reading metadata from DJVU text layers and MOBI headers.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Sample data is public domain or openly licensed:
the demo's English entries are bibliographic facts from the [Project Gutenberg catalog](https://www.gutenberg.org/ebooks/offline_catalogs.html),
the Arabic ones are classical works with their authors' death years. Code is MIT.

## Cite

See [`CITATION.cff`](CITATION.cff).
