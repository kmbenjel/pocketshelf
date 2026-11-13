from pocketshelf.grouping import assign_works, author_key, title_key
from pocketshelf.model import Book


def test_title_key():
    assert title_key("The Count of Monte Cristo: A Tale") == "count of monte cristo"
    assert title_key("Les Misérables vol 2") == "miserables"
    assert title_key("Les Misérables, Tome 2") == title_key("Les Misérables")
    assert title_key("الكتاب ج 3") == "كتاب"
    assert title_key("") == ""


def test_author_key():
    assert author_key("Austen, Jane") == "austen"
    assert author_key("Jane Austen") == "austen"
    assert author_key("ابن خلدون") == "خلدون"
    assert author_key("") == ""


def test_assign_groups_editions():
    bs = [Book(title="Emma", author="Austen, Jane"), Book(title="EMMA", author="Jane Austen"), Book(title="Emma", author="Someone Else"),
          Book(title="Dune", author="Herbert"), Book(title="Dune", author="")]  # fmt: skip
    n = assign_works(bs)
    assert n == 1
    assert bs[0].work == bs[1].work and len({b.work for b in bs}) == 4


def test_explicit_work_wins():
    bs = [
        Book(title="A", author="x", work="w1"),
        Book(title="B", author="y", work="w1"),
        Book(title="A", author="x"),
    ]
    assign_works(bs)
    assert bs[0].work == bs[1].work and bs[2].work != "w1"


def test_untitled_never_grouped():
    bs = [Book(title="", author="a"), Book(title="", author="a")]
    assert assign_works(bs) == 0
