import json
import re

import pytest

from pocketshelf.cli import _relative_base, main


def lib(tmp_path, pdf_factory):
    pdf_factory(tmp_path / "Books/Fiction/Emma - Austen.pdf")
    pdf_factory(tmp_path / "Books/Fiction/Dune - Herbert.pdf")
    return tmp_path / "Books"


def test_build_folder_default_output(tmp_path, pdf_factory, capsys):
    root = lib(tmp_path, pdf_factory)
    assert main(["build", str(root), "--no-cache"]) == 0
    out = root / "pocketshelf.html"
    assert out.exists() and "Emma" in out.read_text(encoding="utf-8")
    assert '"base":""' in out.read_text(encoding="utf-8")
    assert "2 entries" in capsys.readouterr().err


def test_build_output_elsewhere_gets_relative_base(tmp_path, pdf_factory):
    root = lib(tmp_path, pdf_factory)
    out = tmp_path / "Books/index/web/catalog.html"
    assert main(["build", str(root), "-o", str(out), "--no-cache", "--lang", "fr"]) == 0
    text = out.read_text(encoding="utf-8")
    assert '"base":"../../"' in text and 'lang="fr"' in text


def test_relative_base_helper(tmp_path):
    assert _relative_base(tmp_path, tmp_path / "x.html") == ""
    assert _relative_base(tmp_path, tmp_path / "a" / "x.html") == "../"


def test_explicit_base(tmp_path, pdf_factory):
    root = lib(tmp_path, pdf_factory)
    assert (
        main(["build", str(root), "--base", "/sdcard/Books/", "-o", str(tmp_path / "o.html"), "--no-cache"])
        == 0
    )
    assert '"base":"/sdcard/Books/"' in (tmp_path / "o.html").read_text(encoding="utf-8")


def test_build_catalog_and_sidecar_and_template(tmp_path, pdf_factory, capsys):
    root = lib(tmp_path, pdf_factory)
    side = tmp_path / "side.csv"
    side.write_text(
        "path,title,author_death,author_calendar\nFiction/Emma - Austen.pdf,Emma (corrected),1817,ce\n",
        encoding="utf-8",
    )
    assert (
        main(["build", str(root), "--sidecar", str(side), "--template", "{title} - {author}", "--no-cache"])
        == 0
    )
    assert "Emma (corrected)" in (root / "pocketshelf.html").read_text(encoding="utf-8")
    assert "1 of 1 rows matched" in capsys.readouterr().err
    cat = tmp_path / "cat.csv"
    cat.write_text("title,author\nX,Y\n", encoding="utf-8")
    assert main(["build", str(cat)]) == 0 and (tmp_path / "cat.html").exists()


def test_build_errors(tmp_path, capsys):
    assert main(["build", str(tmp_path / "missing")]) == 2
    assert main(["build", str(tmp_path)]) == 1  # empty folder
    empty = tmp_path / "e.csv"
    empty.write_text("title\n", encoding="utf-8")
    assert main(["build", str(empty)]) == 1
    bad = tmp_path / "t.csv"
    bad.write_text("title\nx\n", encoding="utf-8")
    assert main(["build", str(bad), "--template", "{nope}"]) in (0, 2)
    err = capsys.readouterr().err
    assert "error" in err


def test_bad_template_is_a_clean_error(tmp_path, pdf_factory, capsys):
    root = lib(tmp_path, pdf_factory)
    assert main(["build", str(root), "--template", "{nope} - {title}", "--no-cache"]) == 2
    assert "unknown field" in capsys.readouterr().err


def test_scan_then_sidecar_roundtrip(tmp_path, pdf_factory):
    root = lib(tmp_path, pdf_factory)
    csv_path = tmp_path / "c.csv"
    assert main(["scan", str(root), "-o", str(csv_path), "--no-cache"]) == 0
    assert "Fiction/Emma - Austen.pdf" in csv_path.read_text(encoding="utf-8-sig")
    assert main(["build", str(root), "--sidecar", str(csv_path), "--no-cache"]) == 0


def test_inspect(tmp_path, pdf_factory, capsys):
    p = pdf_factory(tmp_path / "Emma - Austen.pdf", {"Title": "Emma", "Author": "J. Austen"})
    assert main(["inspect", str(p)]) == 0
    d = json.loads(capsys.readouterr().out)
    assert d["filename_parse"]["author"] == "Austen" and d["embedded"]["author"] == "J. Austen"


def test_demo_and_bench(tmp_path, capsys):
    out = tmp_path / "d.html"
    assert main(["demo", "-o", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert len(text) > 100_000 and "Tolstoy" in text or 'data-enc="gzip+base64"' in text
    ar = tmp_path / "ar.html"
    assert main(["demo", "--arabic", "-o", str(ar)]) == 0 and 'dir="rtl"' in ar.read_text(encoding="utf-8")
    capsys.readouterr()
    assert main(["bench", "-n", "300", "-o", str(tmp_path / "b.html")]) == 0
    res = json.loads(capsys.readouterr().out)
    assert res["books"] == 300 and res["html_bytes"] > 10_000


def test_help_teaches(capsys):
    with pytest.raises(SystemExit) as e:
        main(["build", "--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "--template" in out and "--profile" in out and "examples:" in out and re.search(r"--sidecar", out)


def test_version(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
    assert "pocketshelf 0.1.0" in capsys.readouterr().out


def test_progress_line_for_big_folders(tmp_path, capsys):
    pdf = b"%PDF-1.4\n%%EOF\n"
    for i in range(450):
        f = tmp_path / "lib" / f"Book {i} - Author.pdf"
        f.parent.mkdir(exist_ok=True)
        f.write_bytes(pdf)
    assert main(["build", str(tmp_path / "lib"), "--no-cache"]) == 0
    assert "450 entries" in capsys.readouterr().err
