# Contributing

Thanks for helping. pocketshelf is small on purpose: Python standard library only, one HTML file out.

```bash
git clone https://github.com/kmbenjel/pocketshelf && cd pocketshelf
uv venv && uv pip install -e ".[dev]"      # or: python -m venv .venv && pip install -e ".[dev]"
pytest                                       # unit tests, and the real page in headless Chrome when Chrome and Node exist
ruff check . && ruff format --check .
pocketshelf demo --open                      # look at your change
```

## Where things are

| Path | What |
|------|------|
| `src/pocketshelf/scan.py`, `meta/` | Reading folders, PDF/EPUB metadata, filename templates and profiles |
| `src/pocketshelf/catalog_io.py` | CSV/JSON catalogs and the sidecar overlay (`docs/catalog-schema.md`) |
| `src/pocketshelf/build.py` | Books to the embedded JSON and the final HTML |
| `src/pocketshelf/assets/` | The page: `index.html`, `app.css`, `app.js`, `fold.js` (no build step, no dependencies) |
| `scripts/e2e.mjs`, `tests/test_e2e.py` | Headless-Chrome checks of the real page |
| `bench/` | Benchmarks you can rerun |

## Rules of thumb

- `fold.py` and `assets/fold.js` are twins: change both, `tests/test_fold.py` checks they agree.
- The page must stay one file with no network access: no CDN, no web fonts, no `fetch` of anything but the embedded data.
- Every new filename profile or metadata reader comes with tests using generated files (`tests/conftest.py`).
- Sample data must be public domain or openly licensed, with its source cited.
- Add a line to `CHANGELOG.md`.

## Adding a filename profile

A profile is a function `profile(stem: str, is_folder: bool = False) -> dict | None` returning any of `title, author, author_death, author_calendar, editor, publisher, place, year, edition, volume, lang`.
Register it in your package as an entry point:

```toml
[project.entry-points."pocketshelf.profiles"]
myprofile = "mypackage.module:profile"
```

then `pocketshelf build ~/Books --profile myprofile`.
