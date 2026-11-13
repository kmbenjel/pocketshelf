"""Find an author's death year inside a name string, and map years to centuries."""

from __future__ import annotations

import re

_AR_DIG = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

# "(ت 728 هـ)", "ت 728", "المتوفى سنة 728 هـ", "(d. 1350)", "(1743-1826)", ", 1743-1826", "(1809–1865 CE)", "(1850?-1926)"
_AH = re.compile(r"[\(\[]?\s*(?<![\u0600-\u06FF])(?:ت|المتوفى|توفي|المتوفي)\s*(?:سنة\s*)?(\d{2,4})\s*(?:هـ|ه|هجرية)?\s*[\)\]]?")
_DIED = re.compile(r"[\(\[]\s*(?:d\.?|died|mort)\s*(\d{3,4})\s*(?:(ah|h)|(ce|ad))?\s*[\)\]]", re.I)
_RANGE = re.compile(
    r"[\(\[,]?\s*(?:ca?\.?\s*)?(-?\d{3,4})\??\s*[-–—/]\s*(-?\d{3,4})\??\s*(?:(ah|h|هـ)|(ce|ad|م))?\s*[\)\]]?\s*$", re.I
)
_BORN = re.compile(r"[\(\[,]?\s*(?:b\.?|born|né)\s*(\d{4})\s*[\)\]]?\s*$", re.I)


def split_life_dates(name: str) -> tuple[str, int, str]:
    """``"Jefferson, Thomas, 1743-1826"`` -> ``("Jefferson, Thomas", 1826, "ce")``.

    Returns the cleaned name, the death year (0 if none found) and the calendar (``"ce"`` or ``"ah"``).
    A name with only a birth year gives no death year.
    """
    if not name:
        return "", 0, "ce"
    s = name.translate(_AR_DIG).strip()
    m = _AH.search(s)
    if m:
        year = int(m.group(1))
        if 1 <= year <= 1500:
            return _clean(s[: m.start()] + " " + s[m.end() :]), year, "ah"
    m = _DIED.search(s)
    if m:
        cal = "ah" if m.group(2) else "ce"
        return _clean(s[: m.start()]), int(m.group(1)), cal
    m = _RANGE.search(s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        cal = "ah" if m.group(3) else "ce"
        death = max(abs(a), abs(b)) if a >= 0 else b
        if a < 0 and b < 0:
            death = b  # both BCE: the later year is the larger (closer to zero) number
        if b < a and a > 0:
            death = a  # swapped
        return _clean(s[: m.start()]), death, cal
    m = _BORN.search(s)
    if m:
        return _clean(s[: m.start()]), 0, "ce"
    return _clean(s), 0, "ce"


def _clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip(" ,;-–—([")
    return s.rstrip(" ,;-–—")


def century(year: int) -> int:
    """Century number of a year: 1..100 -> 1, 101..200 -> 2; negative years are before the era (-1 = 1st c. BCE)."""
    if year > 0:
        return -(-year // 100)
    if year < 0:
        return -(-abs(year) // 100) * -1
    return 0


def ah_to_ce(year: int) -> int:
    """Approximate Gregorian year of a Hijri year (good to a year; used to sort centuries, not to date things)."""
    return round(year * 0.970229 + 621.5740)
