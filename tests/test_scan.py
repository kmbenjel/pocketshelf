import os
import time

from pocketshelf.scan import ScanOptions, detect_lang, is_volume_set, scan, volume_label


def tree(tmp_path, pdf_factory, epub_factory):
    pdf_factory(tmp_path / "History/Rome/The Republic - Cicero.pdf", {"Title": "De Re Publica", "Author": "Marcus Tullius Cicero"})
    pdf_factory(tmp_path / "History/Rome/SPQR - Beard.pdf")
    epub_factory(tmp_path / "Fiction/emma.epub", title="Emma", author="Jane Austen", lang="en")
    for i in (1, 2, 3):
        pdf_factory(tmp_path / f"Law/المغني - ابن قدامة/{i:02d} - المغني.pdf")
    (tmp_path / "Law/المغني - ابن قدامة/notes.txt").write_text("x")
    pdf_factory(tmp_path / ".hidden/secret.pdf")
    pdf_factory(tmp_path / "top.pdf")
    return tmp_path


def by_title(books):
    return {b.title: b for b in books}


def test_scan_basic(tmp_path, pdf_factory, epub_factory):
    tree(tmp_path, pdf_factory, epub_factory)
    books = scan(tmp_path, ScanOptions(cache=False))
    t = by_title(books)
    assert len(books) == 5  # hidden folder skipped, volumes merged
    assert t["De Re Publica"].author == "Marcus Tullius Cicero" and t["De Re Publica"].category == "History/Rome"
    assert t["De Re Publica"].path == "History/Rome/The Republic - Cicero.pdf"
    assert t["SPQR"].author == "Beard"  # filename fallback when the PDF has no info
    assert t["Emma"].fmt == "epub" and t["Emma"].lang == "en" and t["Emma"].category == "Fiction"
    assert t["top"].category == "" and t["top"].path == "top.pdf"


def test_scan_volume_set(tmp_path, pdf_factory, epub_factory):
    tree(tmp_path, pdf_factory, epub_factory)
    books = scan(tmp_path, ScanOptions(cache=False, profile="warraq"))
    m = next(b for b in books if b.volumes)
    assert m.title == "المغني" and m.author == "ابن قدامة" and m.category == "Law" and m.lang == "ar"
    assert [v.label for v in m.volumes] == ["01", "02", "03"] and m.size == sum(v.size for v in m.volumes) > 0
    assert m.volumes[0].path == "Law/المغني - ابن قدامة/01 - المغني.pdf" and m.fmt == "pdf"


def test_no_volume_groups(tmp_path, pdf_factory, epub_factory):
    tree(tmp_path, pdf_factory, epub_factory)
    books = scan(tmp_path, ScanOptions(cache=False, group_volumes=False))
    assert len(books) == 7


def test_prefer_filename_and_no_embedded(tmp_path, pdf_factory):
    pdf_factory(tmp_path / "Emma - Austen.pdf", {"Title": "Something Else", "Author": "Someone"})
    a = scan(tmp_path, ScanOptions(cache=False))[0]
    assert (a.title, a.author) == ("Something Else", "Someone")
    b = scan(tmp_path, ScanOptions(cache=False, prefer="filename"))[0]
    assert (b.title, b.author) == ("Emma", "Austen")
    c = scan(tmp_path, ScanOptions(cache=False, embedded=False))[0]
    assert (c.title, c.author) == ("Emma", "Austen")


def test_template_and_death_year(tmp_path, pdf_factory):
    pdf_factory(tmp_path / "Austen, Jane (1775-1817) - Emma [1815].pdf")
    b = scan(tmp_path, ScanOptions(cache=False, embedded=False, templates=["{author} - {title} [{year}]"]))[0]
    assert b.title == "Emma" and b.author == "Austen, Jane" and b.author_death == 1817 and b.year == 1815


def test_exclude_and_ext(tmp_path, pdf_factory, epub_factory):
    tree(tmp_path, pdf_factory, epub_factory)
    assert all(b.fmt != "epub" for b in scan(tmp_path, ScanOptions(cache=False, exts=(".pdf",))))
    got = scan(tmp_path, ScanOptions(cache=False, exclude=["Law", "History"]))
    assert {b.title for b in got} == {"Emma", "top"}


def test_cache_used_and_invalidated(tmp_path, pdf_factory):
    lib = tmp_path / "lib"
    p = pdf_factory(lib / "a.pdf", {"Title": "First"})
    cache = tmp_path / "cache"
    opts = ScanOptions(cache_dir=str(cache))
    assert scan(lib, opts)[0].title == "First"
    assert list(cache.glob("*.json"))
    # same size and mtime: the cached value is returned even though the content changed
    st = p.stat()
    data = p.read_bytes().replace(b"(First)", b"(Other)")
    p.write_bytes(data)
    os.utime(p, (st.st_atime, st.st_mtime))
    assert scan(lib, opts)[0].title == "First"
    os.utime(p, (st.st_atime, st.st_mtime + 10))
    assert scan(lib, opts)[0].title == "Other"


def test_empty_and_unreadable(tmp_path):
    assert scan(tmp_path, ScanOptions(cache=False)) == []
    assert scan(tmp_path / "nope", ScanOptions(cache=False)) == []


def test_mtime_days(tmp_path, pdf_factory):
    p = pdf_factory(tmp_path / "a.pdf")
    t = time.time() - 86400 * 30
    os.utime(p, (t, t))
    assert abs(scan(tmp_path, ScanOptions(cache=False))[0].mtime - int(t // 86400)) <= 1


def test_volume_heuristics():
    assert is_volume_set(["01 - A.pdf", "02 - A.pdf"])
    assert is_volume_set(["Foo vol 1.pdf", "Foo vol 2.pdf"])
    assert is_volume_set(["الكتاب ج1.pdf", "الكتاب ج2.pdf"])
    assert not is_volume_set(["Foo.pdf"])
    assert not is_volume_set(["Moby Dick - Melville.pdf", "Dracula - Stoker.pdf"])
    assert volume_label("03 - Foo") == "03" and volume_label("Foo vol 12") == "12" and volume_label("Standalone") == "Standalone"


def test_detect_lang():
    assert detect_lang("مقدمة ابن خلدون", "") == "ar"
    assert detect_lang("Emma", "Austen") == ""
    assert detect_lang("", "") == ""
