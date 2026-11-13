"""Run with calibre-debug: create a Calibre library from the benchmark CSV (metadata only, no book files)."""

import csv
import sys

from calibre.ebooks.metadata.book.base import Metadata
from calibre.library import db

src, dest = sys.argv[1], sys.argv[2]
with open(src, encoding="utf-8-sig") as fh:
    rows = list(csv.DictReader(fh))
d = db(dest).new_api
books = []
for r in rows:
    m = Metadata(r["title"], [r["author"]] if r["author"] else None)
    if r.get("publisher"):
        m.publisher = r["publisher"]
    if r.get("lang"):
        m.languages = [r["lang"]]
    books.append((m, {}))
d.add_books(books, add_duplicates=True)
print(len(d.all_book_ids()), "records")
