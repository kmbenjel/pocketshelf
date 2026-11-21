# Catalog schema

`pocketshelf build catalog.csv` (or `.json`) builds the page from a catalog instead of a folder, and `--sidecar` overlays the same
columns on a scanned folder. One row is one book: a single file, or a multi-volume work.

Only `title` is required. Unknown columns are ignored. Column names are matched case-insensitively and a few aliases are accepted
(`file`/`filename`/`url` for `path`, `authors` for `author`, `section` for `category`, `language` for `lang`, `researcher`/`editors` for
`editor`, `work_id` for `work`, `death` for `author_death`, `keywords` for `tags`, `bytes` for `size`, `ids` for `ext_ids`,
`aka`/`other_titles` for `alt_titles`). A CSV is read as UTF-8, or as UTF-16 when it starts with a byte-order mark (a spreadsheet's «Unicode text»).
A file with neither a `title` nor a `path` column is refused with the list of the columns it has.
Other names can be mapped on the command line: `--map author=author_name,work=work_id`.

| Column | Type | Meaning |
|--------|------|---------|
| `title` | text | **Required.** |
| `alt_titles` | text | Other titles the same book is known by, `;`-separated (a JSON list in JSON): `تفسير القرطبي` for «الجامع لأحكام القرآن». Searchable, listed in the book's panel. |
| `author` | text | Display name. A trailing death-date is understood and removed: `Jefferson, Thomas, 1743-1826`, `ابن تيمية (ت 728 هـ)`. |
| `author_death` | integer | Death year. Negative for BCE. Drives "authors by century". |
| `author_calendar` | `ce` or `ah` | Calendar of `author_death` (default `ce`). Hijri centuries are shown as their own centuries, ordered by their Gregorian equivalent. |
| `category` | path | `/` separates levels: `History/Medieval`. Builds the category tree. |
| `path` | text | File path relative to the library root, `/` separators. A full URL (`https://…`) is used as is. Empty: the book is listed without a link. |
| `volumes` | list | JSON `[{"label":"01","path":"…","size":123}]`, or in a CSV `label\|path\|size;label\|path\|size`. An empty path is allowed (the volume is counted, not linked). |
| `size` | integer | Bytes. Defaults to the sum of the volumes. |
| `pages` | integer | |
| `lang` | text | ISO 639-1 (`ar`, `en`, `fr`). Guessed as `ar` from the title's script when a folder is scanned. |
| `work` | text | A stable id of the work. Rows sharing it are grouped as editions of one work. Without it, books are grouped when title and author's main name agree after folding. |
| `edition` | text | Free text: `ed. Dar al-Fikr, Damascus 1988`. |
| `editor` | text | Editor, investigator (`;` between several). |
| `publisher`, `place` | text | |
| `year` | integer | Publication year (CE). |
| `series`, `isbn` | text | |
| `tags` | text | `;`-separated. Searchable. |
| `note` | text | Shown in the book's panel. |
| `ext_ids` | text | `shamela:123;openiti:0676Nawawi.AdabFatwa;wikidata:Q123`. Searchable, shown in the panel. |
| `added` | date | `YYYY-MM-DD`; feeds the "Recently added" sort (a scan uses the file's modification date). |

`century` columns, if present, are ignored: centuries are computed from `author_death` and `author_calendar`.

## JSON form

```json
{
  "meta": {"title": "My library", "lang": "ar"},
  "books": [
    {"title": "آداب الفتوى والمفتي والمستفتي", "author": "النووي", "author_death": 676, "author_calendar": "ah",
     "category": "أصول الفقه", "work": "w_ab12cd34ef", "editor": "بسام عبد الوهاب الجابي", "publisher": "دار الفكر", "place": "دمشق",
     "year": 1988, "path": "usul/adab-al-fatwa.pdf"}
  ]
}
```

A bare array of objects works too.

## Filename profiles

A folder scan fills the same fields from file names. Give a template, or a profile:

```bash
pocketshelf build ~/Books --template '{author} - {title} ({year})'   # fields: title author editor publisher place year series edition volume lang skip
pocketshelf build ~/Books --profile warraq                         # <title> - <author> - ت <editor> - <publisher> <city>
pocketshelf inspect ~/Books/some-file.pdf --template '{author} - {title}'   # check what is read from one file
```

Profiles installed by other packages are found through the `pocketshelf.profiles` entry point group; see `CONTRIBUTING.md`.
