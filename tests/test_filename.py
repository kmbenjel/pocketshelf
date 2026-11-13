import pytest

from pocketshelf.meta import filename as fn
from pocketshelf.meta.filename import (
    FilenameParser,
    compile_template,
    parse_dashes,
    parse_template,
    parse_warraq,
)


def test_template_basic():
    pat = [compile_template("{author} - {title} ({year})")]
    assert parse_template(pat, "Austen, Jane - Emma (1815)") == {
        "author": "Austen, Jane",
        "title": "Emma",
        "year": 1815,
    }


def test_template_non_greedy_and_extra_dashes():
    pat = [compile_template("{author} - {title}")]
    assert parse_template(pat, "Hugo - Les Misérables - Tome 1") == {
        "author": "Hugo",
        "title": "Les Misérables - Tome 1",
    }


def test_template_year_only_digits():
    pat = [compile_template("{title} - {year}")]
    assert parse_template(pat, "War and Peace - Tolstoy") is None
    assert parse_template(pat, "War and Peace - 1869")["year"] == 1869


def test_template_first_match_wins_and_skip():
    pats = [compile_template("{title} [{skip}]"), compile_template("{title} - {author}")]
    assert parse_template(pats, "Dune [retail]")["title"] == "Dune"
    assert parse_template(pats, "Dune - Herbert") == {"title": "Dune", "author": "Herbert"}


def test_template_unknown_field():
    with pytest.raises(ValueError, match="unknown field"):
        compile_template("{nope} - {title}")


def test_template_volume_int():
    pat = [compile_template("{volume} - {title}")]
    assert parse_template(pat, "03 - Al-Kitab") == {"volume": 3, "title": "Al-Kitab"}


def test_dashes_default_and_order():
    assert parse_dashes("Emma - Austen") == {"title": "Emma", "author": "Austen"}
    assert parse_dashes("Austen - Emma", "author-title") == {"title": "Emma", "author": "Austen"}
    assert parse_dashes("Just a title") == {"title": "Just a title"}
    assert parse_dashes("Emma - Austen (1815)")["year"] == 1815
    assert parse_dashes("") is None


def test_dashes_does_not_split_hyphenated_words():
    assert parse_dashes("Jean-Jacques Rousseau - Émile") == {
        "title": "Jean-Jacques Rousseau",
        "author": "Émile",
    }


def test_warraq_full():
    d = parse_warraq("آداب الفتوى والمفتي - النووي - ت بسام الجابي - دار الفكر دمشق")
    assert d == {
        "title": "آداب الفتوى والمفتي",
        "author": "النووي",
        "editor": "بسام الجابي",
        "publisher": "دار الفكر",
        "place": "دمشق",
    }


def test_warraq_volume_and_death():
    d = parse_warraq("03 - المغني - ابن قدامة ت 620 - ت التركي - هجر")
    assert (
        d["volume"] == 3
        and d["author_death"] == 620
        and d["author_calendar"] == "ah"
        and d["editor"] == "التركي"
        and d["publisher"] == "هجر"
    )


def test_warraq_needs_title_and_author():
    assert parse_warraq("فقط عنوان") is None


def test_parser_chain():
    p = FilenameParser(["{author} - {title}"], "warraq")
    assert p("Austen - Emma")["title"] == "Emma"
    assert p("one - two - three")["title"] == "two - three"  # the template matches first


def test_parser_uses_life_dates_in_author():
    p = FilenameParser()
    d = p("Dune - Herbert, Frank, 1920-1986")
    assert d["author"] == "Herbert, Frank" and d["author_death"] == 1986


def test_unknown_profile():
    with pytest.raises(ValueError, match="unknown profile"):
        fn.get_profile("nope")


def test_plugin_profile_wins(monkeypatch):
    class EP:
        name = "warraq"

        def load(self):
            return lambda stem, is_folder=False: {"title": "from-plugin"}

    monkeypatch.setattr(fn.metadata, "entry_points", lambda group=None: [EP()])
    assert FilenameParser(profile="warraq")("x - y")["title"] == "from-plugin"


def test_plugin_failure_falls_back(monkeypatch):
    def boom(group=None):
        raise RuntimeError("broken plugin")

    monkeypatch.setattr(fn.metadata, "entry_points", boom)
    assert FilenameParser(profile="warraq")("A - B")["title"] == "A"
