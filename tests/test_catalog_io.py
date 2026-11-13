import json

from pocketshelf.catalog_io import apply_sidecar, parse_mapping, parse_volumes, read_catalog, write_catalog
from pocketshelf.model import Book, Volume


def test_read_csv_minimal(tmp_path):
    f = tmp_path / "c.csv"
    f.write_text("title,author\nEmma,Austen\n,\nDune,Herbert\n", encoding="utf-8")
    books, meta = read_catalog(f)
    assert [b.title for b in books] == ["Emma", "Dune"] and meta == {}


def test_read_csv_turath_style_row(tmp_path):
    f = tmp_path / "c.csv"
    f.write_text(
        "title,author,author_death,author_calendar,category,path,size,pages,lang,work,edition,editor,publisher,place,year,tags,ext_ids,century,volumes\n"
        'آداب الفتوى,النووي,676,ah,أصول الفقه,,1263747,120,ar,w_ab12cd34ef,"ط 1",بسام الجابي,دار الفكر,دمشق,1988,تحقيق;رسالة,'
        '"shamela:123;openiti:0676Nawawi.AdabFatwa",7,"1||600000;2||663747"\n',
        encoding="utf-8",
    )
    (b,), _ = read_catalog(f)
    assert b.author_death == 676 and b.author_calendar == "ah" and b.work == "w_ab12cd34ef" and b.year == 1988
    assert b.tags == ["تحقيق", "رسالة"] and b.ext_ids == {"shamela": "123", "openiti": "0676Nawawi.AdabFatwa"}
    assert [(v.label, v.path, v.size) for v in b.volumes] == [("1", "", 600000), ("2", "", 663747)]
    assert b.size == 1263747 and b.files[0].path == ""


def test_read_json_forms(tmp_path):
    f = tmp_path / "c.json"
    f.write_text(json.dumps({"meta": {"title": "My shelf", "lang": "fr"}, "books": [{"title": "X", "author_death": "1,350", "volumes": [{"n": 1, "path": "a/1.pdf", "size": 5}]}]}))
    (b,), meta = read_catalog(f)
    assert meta["title"] == "My shelf" and b.author_death == 1350 and b.volumes[0].label == "1" and b.size == 5
    g = tmp_path / "d.json"
    g.write_text(json.dumps([{"title": "Y", "ext_ids": {"k": "v"}, "tags": ["a", "b"]}]))
    (c,), _ = read_catalog(g)
    assert c.ext_ids == {"k": "v"} and c.tags == ["a", "b"]


def test_aliases_and_mapping(tmp_path):
    f = tmp_path / "c.csv"
    f.write_text("Name,Authors,File,Section,Researcher,ISBN13,Date\nEmma,Austen,a/b.pdf,Fiction,Ed,9780141439518,1815\n", encoding="utf-8")
    (b,), _ = read_catalog(f)
    assert (b.title, b.author, b.path, b.category, b.editor, b.isbn, b.year) == ("Emma", "Austen", "a/b.pdf", "Fiction", "Ed", "9780141439518", 1815)
    g = tmp_path / "d.csv"
    g.write_text("t,who,id\nEmma,Austen,w1\n", encoding="utf-8")
    (c,), _ = read_catalog(g, parse_mapping("title=t,author=who,work=id"))
    assert (c.title, c.author, c.work) == ("Emma", "Austen", "w1")


def test_tab_separated_and_bom(tmp_path):
    f = tmp_path / "c.tsv"
    f.write_text("﻿title\tauthor\nEmma\tAusten\n", encoding="utf-8")
    (b,), _ = read_catalog(f)
    assert b.title == "Emma"


def test_author_life_dates_in_name_and_added(tmp_path):
    f = tmp_path / "c.csv"
    f.write_text("title,author,added\nHamlet,\"Shakespeare, William, 1564-1616\",1970-01-11\n", encoding="utf-8")
    (b,), _ = read_catalog(f)
    assert b.author == "Shakespeare, William" and b.author_death == 1616 and b.mtime == 10


def test_title_from_path_when_missing(tmp_path):
    f = tmp_path / "c.csv"
    f.write_text("path\nsome/dir/Dune.pdf\n", encoding="utf-8")
    (b,), _ = read_catalog(f)
    assert b.title == "Dune"


def test_backslash_paths_normalised(tmp_path):
    f = tmp_path / "c.csv"
    f.write_text("title,path\nX,a\\b\\c.pdf\n", encoding="utf-8")
    assert read_catalog(f)[0][0].path == "a/b/c.pdf"


def test_roundtrip(tmp_path):
    b = Book(title="T, with comma", author="A", author_death=808, author_calendar="ah", category="C/D", volumes=[Volume("01", "x/01.pdf", 10), Volume("02", "x/02.pdf", 20)],
             lang="ar", edition="e", tags=["a", "b"], ext_ids={"k": "v"}, year=1999, mtime=100)  # fmt: skip
    f = tmp_path / "o.csv"
    write_catalog([b], f)
    (r,), _ = read_catalog(f)
    for field in ("title", "author", "author_death", "author_calendar", "category", "lang", "edition", "tags", "ext_ids", "year", "mtime", "size"):
        assert getattr(r, field) == getattr(b, field) or field == "size", field
    assert r.size == 30 and [(v.label, v.path, v.size) for v in r.volumes] == [("01", "x/01.pdf", 10), ("02", "x/02.pdf", 20)]


def test_parse_volumes_forms():
    assert parse_volumes("") == [] and parse_volumes(None) == []
    assert parse_volumes('[{"label":"a","path":"p","size":1}]')[0].label == "a"
    assert parse_volumes("[bad json")[0:0] == []
    assert parse_volumes([["1", "p", 2]])[0].size == 2
    assert parse_volumes("a|p|3;b")[1].path == ""


def test_apply_sidecar():
    scanned = [Book(title="old", path="a/1.pdf"), Book(title="vol", volumes=[Volume("1", "v/1.pdf")]), Book(title="keep", path="k.pdf", author="X")]
    side = [Book(title="New", author="Au", author_death=100, author_calendar="ah", path="a/1.pdf", tags=["t"]), Book(title="V2", path="v/1.pdf"), Book(title="ghost", path="zz.pdf"), Book(title="nopath")]
    n = apply_sidecar(scanned, side)
    assert n == 2 and scanned[0].title == "New" and scanned[0].author_calendar == "ah" and scanned[0].tags == ["t"]
    assert scanned[1].title == "V2" and scanned[2].author == "X"
