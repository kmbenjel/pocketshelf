from __future__ import annotations

import zipfile
from pathlib import Path

import pytest


def pdf_string(s: str) -> bytes:
    """A PDF text string: PDFDocEncoding if it fits cp1252, else UTF-16BE hex."""
    try:
        raw = s.encode("cp1252")
        return b"(" + raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b")"
    except UnicodeEncodeError:
        return b"<" + (b"\xfe\xff" + s.encode("utf-16-be")).hex().upper().encode() + b">"


def make_pdf(path: Path, info: dict[str, str] | None = None, xmp: str | None = None, pad: int = 0) -> Path:
    """Write a tiny valid PDF (one blank page) with an Info dictionary and/or an XMP packet."""
    objs: list[bytes] = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R" + (b" /Metadata 5 0 R" if xmp else b"") + b" >>")
    objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>")
    parts = b"".join(b"/" + k.encode() + b" " + pdf_string(v) + b" " for k, v in (info or {}).items())
    objs.append(b"<< " + parts + b">>")
    if xmp:
        x = xmp.encode("utf-8")
        objs.append(b"<< /Type /Metadata /Subtype /XML /Length %d >>\nstream\n" % len(x) + x + b"\nendstream")
    out = bytearray(b"%PDF-1.4\n")
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    if pad:
        out += b"%" + b"x" * pad + b"\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R /Info 4 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))
    return path


def make_epub(path: Path, title="T", author="A", lang="en", date="1999-01-01", publisher=None, series=None, subjects=()) -> Path:
    opf = f"""<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
<dc:title>{title}</dc:title><dc:creator>{author}</dc:creator><dc:language>{lang}</dc:language><dc:date>{date}</dc:date>
{f'<dc:publisher>{publisher}</dc:publisher>' if publisher else ''}
{''.join(f'<dc:subject>{s}</dc:subject>' for s in subjects)}
<dc:identifier>urn:isbn:9780141439518</dc:identifier>
{f'<meta name="calibre:series" content="{series}"/>' if series else ''}
</metadata></package>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr("META-INF/container.xml", '<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr("OEBPS/content.opf", opf)
    return path


@pytest.fixture
def pdf_factory():
    return make_pdf


@pytest.fixture
def epub_factory():
    return make_epub
