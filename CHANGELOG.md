# Changelog

All notable changes are listed here. The project follows [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-13

First public version.

- `pocketshelf build` turns a folder of PDF, EPUB and DJVU files, or a CSV/JSON catalog, into one self-contained offline HTML file.
- Metadata from PDF Info and XMP, EPUB OPF, filename templates and profiles (`warraq`, `dashes`, `author-title`, plugins), and a sidecar CSV.
- Page: instant accent- and Arabic-folding search, virtualised list, category tree, authors by century (Hijri and Gregorian), edition grouping, statistics, dark mode, Arabic, English and French interface with RTL/LTR.
- Gzip + base64 embedded data; 20,000 books are ready in about 0.3 s on a 4x-throttled CPU (bench/RESULTS.md).
- `scan`, `inspect`, `demo` and `bench` commands.
