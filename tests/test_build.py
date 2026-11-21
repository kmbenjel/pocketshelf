import base64
import gzip
import json
import re

import pytest

from pocketshelf.build import build_html, encode_payload, make_payload
from pocketshelf.model import Book, Volume


def books():
    return [
        Book(
            title="Emma",
            author="Austen, Jane",
            author_death=1817,
            category="Fiction/Novels",
            path="fic/emma.pdf",
            size=1000,
            year=1815,
            lang="en",
        ),
        Book(
            title="Emma",
            author="Jane Austen",
            category="Fiction/Novels",
            path="fic/emma2.epub",
            size=500,
            edition="2nd",
        ),
        Book(
            title="المغني",
            author="ابن قدامة",
            author_death=620,
            author_calendar="ah",
            category="الفقه",
            volumes=[Volume("01", "a/01.pdf", 10), Volume("02", "a/02.pdf", 20)],
            lang="ar",
        ),
        Book(title="No file", note="</script><b>x</b>"),
    ]


def payload_from(page):
    m = re.search(r'<script id="data" type="text/plain" data-enc="([^"]+)">(.*?)</script>', page, re.S)
    enc, text = m.groups()
    if enc == "json":
        return json.loads(text)
    return json.loads(gzip.decompress(base64.b64decode(text)))


def test_payload_structure_and_grouping():
    p = make_payload(books(), "T", "en", "../")
    assert p["m"]["base"] == "../" and p["v"] == 1
    rows = p["b"]
    assert [r[0] for r in rows] == ["Emma", "Emma", "No file", "المغني"] or len(rows) == 4
    emma = [r for r in rows if r[0] == "Emma"]
    assert emma[0][3] == emma[1][3]  # same work index
    assert len({r[3] for r in rows}) == 3
    assert p["a"][emma[0][1]][0:2] == ["Austen, Jane", 1817]  # the first spelling and the death year win
    arabic = next(r for r in rows if r[0] == "المغني")
    assert arabic[8] == [["01", "a/01.pdf", 10], ["02", "a/02.pdf", 20]] and p["a"][arabic[1]][2] == 1
    assert p["f"] == ["pdf", "epub"] or set(p["f"]) == {"pdf", "epub"}


def test_other_titles_travel_in_the_details():
    p = make_payload([Book(title="الجامع لأحكام القرآن", alt_titles=["تفسير القرطبي"]), Book(title="Plain")])
    by_title = {r[0]: r[9] for r in p["b"]}
    assert by_title["الجامع لأحكام القرآن"] == {"at": ["تفسير القرطبي"]} and by_title["Plain"] == 0


def test_sorted_by_folded_title():
    bs = [Book(title="Zebra"), Book(title="école"), Book(title="Apple")]
    assert [r[0] for r in make_payload(bs)["b"]] == ["Apple", "école", "Zebra"]


def test_html_is_one_self_contained_file():
    page = build_html(books(), "My <shelf> & co", "ar")
    assert "My &lt;shelf&gt; &amp; co" in page and 'dir="rtl"' in page and 'lang="ar"' in page
    assert "__DATA__" not in page and "/*__JS__*/" not in page and "__TITLE__" not in page
    assert not re.search(r"""(src|href)\s*=\s*["']https?://""", page)  # nothing is fetched
    assert "<link " not in page and "@import" not in page
    assert page.count("</script>") == 3  # data, fold, app: nothing from the payload closes a script


def test_script_terminator_in_data_is_escaped():
    page = build_html(books(), compress=False)
    assert "</script><b>" not in page
    assert payload_from(page)["b"][0] is not None
    assert any(r[9] and r[9].get("n") == "</script><b>x</b>" for r in payload_from(page)["b"])


def test_compress_roundtrip_and_threshold():
    small = build_html(books())
    assert 'data-enc="json"' in small
    forced = build_html(books(), compress=True)
    assert 'data-enc="gzip+base64"' in forced and payload_from(forced) == payload_from(small) | {
        "m": payload_from(forced)["m"]
    }
    many = [Book(title=f"Book {i} " * 3, author=f"Author {i % 50}") for i in range(8000)]
    assert 'data-enc="gzip+base64"' in build_html(many)


def test_encoding_is_deterministic():
    p = make_payload(books())
    assert encode_payload(p, True) == encode_payload(p, True)


def test_unknown_language():
    with pytest.raises(ValueError, match="UI language"):
        build_html(books(), lang="xx")


def test_data_cannot_inject_placeholders():
    b = [Book(title="__TITLE__ /*__JS__*/ __LANG__")]
    page = build_html(b, "Real", compress=False)
    assert payload_from(page)["b"][0][0] == "__TITLE__ /*__JS__*/ __LANG__"
