from pocketshelf.meta.epub import read_epub
from pocketshelf.meta.pdf import decode_pdf_string, parse_info_dict, read_pdf


def test_pdf_info_literal(tmp_path, pdf_factory):
    p = pdf_factory(tmp_path / "a.pdf", {"Title": "Pride and Prejudice", "Author": "Jane Austen"})
    assert read_pdf(str(p)) == {"title": "Pride and Prejudice", "author": "Jane Austen"}


def test_pdf_info_utf16_hex_arabic(tmp_path, pdf_factory):
    p = pdf_factory(tmp_path / "a.pdf", {"Title": "مقدمة ابن خلدون", "Author": "ابن خلدون"})
    d = read_pdf(str(p))
    assert d["title"] == "مقدمة ابن خلدون" and d["author"] == "ابن خلدون"


def test_pdf_escapes_and_parentheses(tmp_path, pdf_factory):
    p = pdf_factory(tmp_path / "a.pdf", {"Title": "Algebra (2nd ed.) \\ notes"})
    assert read_pdf(str(p))["title"] == "Algebra (2nd ed.) \\ notes"


def test_pdf_junk_title_dropped(tmp_path, pdf_factory):
    for junk in ("Microsoft Word - doc1.docx", "untitled", "scan0001", "report.indd", ""):
        p = pdf_factory(tmp_path / "j.pdf", {"Title": junk, "Author": "admin"})
        assert read_pdf(str(p)) == {}, junk


def test_pdf_xmp_only(tmp_path, pdf_factory):
    xmp = (
        '<?xpacket begin="" id="x"?><x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/"><rdf:Description><dc:title><rdf:Alt><rdf:li xml:lang="x-default">Les Misérables</rdf:li></rdf:Alt></dc:title>'
        "<dc:creator><rdf:Seq><rdf:li>Victor Hugo</rdf:li></rdf:Seq></dc:creator><dc:language><rdf:Bag><rdf:li>fr-FR</rdf:li></rdf:Bag></dc:language>"
        "</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end='w'?>"
    )
    p = pdf_factory(tmp_path / "x.pdf", None, xmp=xmp)
    d = read_pdf(str(p))
    assert d == {"title": "Les Misérables", "author": "Victor Hugo", "lang": "fr"}


def test_pdf_info_beats_xmp(tmp_path, pdf_factory):
    xmp = '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dc="http://purl.org/dc/elements/1.1/"><rdf:Description><dc:title>XMP title</dc:title></rdf:Description></rdf:RDF></x:xmpmeta>'
    p = pdf_factory(tmp_path / "x.pdf", {"Title": "Info title"}, xmp=xmp)
    assert read_pdf(str(p))["title"] == "Info title"


def test_pdf_large_file_tail_is_read(tmp_path, pdf_factory):
    p = pdf_factory(tmp_path / "big.pdf", {"Title": "Tail Title"}, pad=600_000)
    assert read_pdf(str(p))["title"] == "Tail Title"


def test_not_a_pdf_and_missing(tmp_path):
    f = tmp_path / "x.pdf"
    f.write_bytes(b"hello world")
    assert read_pdf(str(f)) == {}
    assert read_pdf(str(tmp_path / "missing.pdf")) == {}


def test_decode_pdf_string_variants():
    assert decode_pdf_string(b"\xfe\xff\x00H\x00i") == "Hi"
    assert decode_pdf_string(b"\xff\xfeH\x00i\x00") == "Hi"
    assert decode_pdf_string(b"caf\xe9") == "café"
    assert decode_pdf_string("café".encode()) == "café"


def test_parse_info_dict_octal_and_newline_escapes():
    assert parse_info_dict(rb"/Title (A\101B\nC)") == {"title": "AAB\nC"}


def test_epub(tmp_path, epub_factory):
    p = epub_factory(tmp_path / "a.epub", title="Emma", author="Jane Austen", lang="en-GB", date="1815-12-23", publisher="John Murray", series="Austen Novels", subjects=["Fiction", "Romance"])
    d = read_epub(str(p))
    assert d["title"] == "Emma" and d["author"] == "Jane Austen" and d["lang"] == "en" and d["year"] == 1815
    assert d["publisher"] == "John Murray" and d["series"] == "Austen Novels" and d["tags"] == "Fiction; Romance" and d["isbn"] == "9780141439518"


def test_epub_broken(tmp_path):
    f = tmp_path / "bad.epub"
    f.write_bytes(b"not a zip")
    assert read_epub(str(f)) == {}
