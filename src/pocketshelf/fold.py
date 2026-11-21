"""Search folding. The browser has a twin of this function (``assets/fold.js``); the two must agree.

Rules, applied in order:

1. Unicode NFKD, then drop every combining mark: Latin accents, Arabic harakat, Hebrew points.
2. Remove the tatweel (kashida), the transliteration marks ayn/hamza/apostrophes, and the invisible format
   characters (direction marks, zero-width joiners, soft hyphen, byte-order mark).
3. Fold letter variants: Arabic alef forms, alef maqsura, teh marbuta, waw/yeh with hamza, Persian and Urdu
   yeh/kaf/heh; Latin ligatures and barred letters (ae, oe, ss, o, d, l); the Greek final sigma.
4. Arabic-Indic and extended digits become ASCII digits; lower-case; every other non letter/digit becomes a space.

Every rule looks at one character at a time, so folding a string is folding its characters: both twins keep a
table of the characters they have met.
"""

from __future__ import annotations

import re
import unicodedata

_MAP = {
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ٱ": "ا",
    "ٲ": "ا",
    "ٳ": "ا",
    "ى": "ي",
    "ی": "ي",
    "ې": "ي",
    "ئ": "ي",
    "ے": "ي",
    "ة": "ه",
    "ۀ": "ه",
    "ھ": "ه",
    "ہ": "ه",
    "ۃ": "ه",
    "ە": "ه",
    "ؤ": "و",
    "ک": "ك",
    "گ": "ك",
    "ڪ": "ك",
    "ڭ": "ك",
    "æ": "ae",
    "œ": "oe",
    "ß": "ss",
    "ø": "o",
    "đ": "d",
    "ð": "d",
    "ł": "l",
    "þ": "th",
    "ı": "i",
    "ς": "σ",
}
_DROP = {"ـ", "ء", "ʿ", "ʾ", "ʻ", "ʼ", "ʽ", "'", "’", "‘", "`", "´", "ʹ", "ʺ"}
_DIGITS = {c: str(i % 10) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹")}
_NONWORD = re.compile(r"[^\w]+", re.UNICODE)
_ASCII_NONWORD = re.compile(r"[^a-z0-9]+")


class _Table(dict):
    """``str.translate`` table filled as characters are met: code point -> folded text (``None`` drops it)."""

    def __missing__(self, code: int) -> str | None:
        ch = chr(code)
        out: str | None
        if ch in _DROP or unicodedata.category(ch) in ("Mn", "Mc", "Me", "Cf"):
            out = None
        elif ch == "_":
            out = " "
        else:
            out = _MAP.get(ch) or _DIGITS.get(ch) or ch
        self[code] = out
        return out


_TABLE = _Table()


def fold(s: str | None) -> str:
    """Return the search key of ``s``: accent-, diacritic- and variant-insensitive, lower-case."""
    if not s:
        return ""
    s = str(s)
    if s.isascii():
        return _ASCII_NONWORD.sub(" ", s.lower().replace("'", "").replace("`", "")).strip()
    s = unicodedata.normalize("NFKD", s).lower().translate(_TABLE)
    return _NONWORD.sub(" ", s).strip()
