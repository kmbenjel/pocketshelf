# Changelog

All notable changes are listed here. The project follows [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-13

First public version.

- `pocketshelf build` turns a folder of PDF, EPUB and DJVU files, or a CSV/JSON catalog, into one self-contained offline HTML file.
- Metadata from PDF Info and XMP, EPUB OPF, filename templates and profiles (`warraq`, `dashes`, `author-title`, plugins), and a sidecar CSV.
- Page: instant accent- and Arabic-folding search, virtualised list, category tree, authors by century (Hijri and Gregorian), edition grouping, statistics, dark mode, Arabic, English and French interface with RTL/LTR.
- Search folding shared by Python and the page, one character at a time: Arabic letter variants, harakat, tatweel, invisible direction marks and joiners, Latin accents and ligatures; «عبدالله» also finds «عبد الله» and «ابن» finds «بن»; a match is highlighted as one run.
- Other titles of a book (`alt_titles`) are searchable and shown in its panel.
- Phone use: the Back button closes any panel, Enter puts the on-screen keyboard away, layouts hold from 320 px wide upright and sideways, a note explains what to do when a file manager opens the page through a `content://` address.
- Keyboard and screen readers: arrows walk the list and the category tree, Enter and Escape open and close, the focus survives every redraw, the result count is announced, panels are modal dialogs, colours meet WCAG AA.
- A bookmark made before a rebuild opens the catalog even when its filter no longer fits the data.
- Clear messages for a catalog that cannot be read (not UTF-8, invalid JSON, no `title` column); UTF-16 spreadsheet exports are read; `-o` accepts a folder.
- Gzip + base64 embedded data; 20,000 books are ready in about 0.3 s on a 4x-throttled CPU (bench/RESULTS.md).
- `scan`, `inspect`, `demo` and `bench` commands.
