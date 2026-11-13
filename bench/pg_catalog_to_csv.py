"""First N texts of the Project Gutenberg catalog as a pocketshelf CSV: a benchmark on real titles and authors.

curl -L -o pg_catalog.csv https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv
python bench/pg_catalog_to_csv.py pg_catalog.csv 20000 pg20k.csv
pocketshelf build pg20k.csv -o pg20k.html && node bench/load_time.mjs "$PWD/pg20k.html" 4
"""

import csv
import re
import sys

src, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
with open(src, encoding="utf-8") as fh:
    rows = [r for r in csv.DictReader(fh) if r["Type"] == "Text"][:n]
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["title", "author", "lang", "category", "path", "ext_ids"])
    for r in rows:
        cats = [s[10:] for s in r["Bookshelves"].split("; ") if s.startswith("Category: ")]
        w.writerow(
            [
                " — ".join(x.strip() for x in r["Title"].split("\n") if x.strip()),
                r["Authors"].split(";")[0].strip(),
                r["Language"].split(";")[0],
                re.sub(r" - ", "/", cats[0]) if cats else "",
                f"https://www.gutenberg.org/ebooks/{r['Text#']}.epub3.images",
                f"gutenberg:{r['Text#']}",
            ]
        )
print(len(rows), "rows ->", out)
