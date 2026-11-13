"""Write N synthetic books as a CSV catalog and as N one-page PDFs (shared by bench/compare.sh)."""

import sys
from pathlib import Path

from pocketshelf.catalog_io import write_catalog
from pocketshelf.synth import synthetic_books

n, out = int(sys.argv[1]), Path(sys.argv[2])
lib = out / "library"
books = synthetic_books(n)
PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\ntrailer<</Root 1 0 R/Size 4>>\n%%EOF\n"
for i, b in enumerate(books):
    stem = f"{b.title[:50]} - {b.author.split(',')[0]} {i}"
    path = f"{b.category}/{stem}.pdf"
    f = lib / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(PDF)
    b.path, b.volumes, b.size = path, [], len(PDF)
write_catalog(books, out / "catalog.csv")
print(f"{n} books -> {out}")
