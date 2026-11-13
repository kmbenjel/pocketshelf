import pytest

from pocketshelf.lives import ah_to_ce, century, split_life_dates


@pytest.mark.parametrize(
    ("raw", "name", "year", "cal"),
    [
        ("Jefferson, Thomas, 1743-1826", "Jefferson, Thomas", 1826, "ce"),
        ("Austen, Jane (1775–1817)", "Austen, Jane", 1817, "ce"),
        ("ابن تيمية (ت 728 هـ)", "ابن تيمية", 728, "ah"),
        ("الغزالي ت 505", "الغزالي", 505, "ah"),
        ("النووي المتوفى سنة ٦٧٦ هـ", "النووي", 676, "ah"),
        ("ابن خلدون (732-808 هـ)", "ابن خلدون", 808, "ah"),
        ("Smith, John (d. 1350)", "Smith, John", 1350, "ce"),
        ("Doe, J., b. 1950", "Doe, J.", 0, "ce"),
        ("Homer", "Homer", 0, "ce"),
        ("", "", 0, "ce"),
        ("بيت 123", "بيت 123", 0, "ce"),  # a word ending in ت is not the death marker
    ],
)
def test_split_life_dates(raw, name, year, cal):
    assert split_life_dates(raw) == (name, year, cal)


@pytest.mark.parametrize(
    ("y", "c"),
    [(1, 1), (100, 1), (101, 2), (728, 8), (1826, 19), (2000, 20), (-44, -1), (-100, -1), (-101, -2), (0, 0)],
)
def test_century(y, c):
    assert century(y) == c


def test_ah_to_ce():
    assert abs(ah_to_ce(728) - 1328) <= 1
    assert abs(ah_to_ce(1) - 622) <= 1
