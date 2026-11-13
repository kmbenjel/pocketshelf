"""Build src/pocketshelf/data/gutenberg-sample.csv from the Project Gutenberg catalog (pg_catalog.csv).

Source: https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv  (bibliographic facts only; no book text).
The sample keeps the authors with at least 20 texts in Project Gutenberg (up to 6 titles each, curated shelves first),
plus every Gutenberg edition of the titles on the "Best Books Ever Listings" shelf.

    python scripts/make_gutenberg_sample.py pg_catalog.csv
"""

import csv
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pocketshelf.fold import fold  # noqa: E402
from pocketshelf.lives import split_life_dates  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "src/pocketshelf/data/gutenberg-sample.csv"
GENRE = {"Novels", "Poetry", "Short Stories", "Plays/Films/Dramas", "Humour", "Romance", "Science-Fiction & Fantasy", "Adventure",
         "Historical Novels", "Crime, Thrillers and Mystery", "Children & Young Adult Reading", "Mythology, Legends & Folklore", "Classics of Literature"}  # fmt: skip


def category(shelves: list[str], freq: Counter) -> str:
    cats = [s[len("Category: ") :] for s in shelves if s.startswith("Category: ")]
    if not cats:
        return "Other"
    lit = [c for c in cats if c.endswith(" Literature") and c not in GENRE]
    pick = lit[0] if lit else min(cats, key=lambda c: freq[c])
    if pick.startswith("History - "):
        return "History/" + re.sub(r"\s*\(.*\)", "", pick[10:])
    if pick.startswith("Science - "):
        return "Science/" + pick[10:]
    if pick in GENRE:
        return "Literature/" + pick
    if pick.endswith(" Literature"):
        return "Literature/" + pick[:-11]
    if pick in ("Biographies", "Essays, Letters & Speeches", "Journals", "Travel Writing"):
        return "Non-fiction/" + pick
    return "Other/" + pick


def main(src: str) -> None:
    with open(src, encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["Type"] == "Text"]
    freq: Counter = Counter()
    for r in rows:
        for s in r["Bookshelves"].split("; "):
            if s.startswith("Category: "):
                freq[s[len("Category: ") :]] += 1
    first = lambda r: r["Authors"].split(";")[0].strip()  # noqa: E731
    life = re.compile(r"\d{4}\s*-\s*\d{4}")
    per_author: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if life.search(first(r)):
            per_author[first(r)].append(r)
    best = {
        (fold(r["Title"].split("\n")[0]), fold(first(r)))
        for r in rows
        if "Best Books Ever" in r["Bookshelves"]
    }
    keep: dict[str, dict] = {}
    for _a, lst in per_author.items():
        if len(lst) < 20:
            continue
        lst.sort(
            key=lambda r: (
                "Best Books Ever" not in r["Bookshelves"],
                "Classics of Literature" not in r["Bookshelves"],
                int(r["Text#"]),
            )
        )
        for r in lst[:6]:
            keep[r["Text#"]] = r
    for r in rows:
        if (fold(r["Title"].split("\n")[0]), fold(first(r))) in best:
            keep[r["Text#"]] = r
    out = []
    for r in sorted(keep.values(), key=lambda r: int(r["Text#"])):
        name, death, cal = split_life_dates(re.sub(r"\s*\[[^\]]*\]", "", first(r)))
        title = " — ".join(x.strip() for x in r["Title"].split("\n") if x.strip())[:140]
        shelves = r["Bookshelves"].split("; ")
        added = r["Issued"][:10]
        try:
            date.fromisoformat(added)
        except ValueError:
            added = ""
        out.append({
            "title": title, "author": name, "author_death": death or "", "author_calendar": "ce" if death else "",
            "category": category(shelves, freq), "path": f"https://www.gutenberg.org/ebooks/{r['Text#']}.epub3.images",
            "lang": r["Language"].split(";")[0].strip(), "edition": f"Project Gutenberg #{r['Text#']}",
            "ext_ids": f"gutenberg:{r['Text#']}", "added": added,
        })  # fmt: skip
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(
        len(out),
        "rows ->",
        OUT,
        round(OUT.stat().st_size / 1e3),
        "KB;",
        len(Counter(o["author"] for o in out)),
        "authors",
    )


if __name__ == "__main__":
    main(sys.argv[1])
