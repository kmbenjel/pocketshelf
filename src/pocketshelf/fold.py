"""Search folding. The browser has a twin of this function (``assets/fold.js``); the two must agree.

Rules, applied in order:

1. Unicode NFKD, then drop every combining mark: Latin accents, Arabic harakat, Hebrew points.
2. Remove the tatweel (kashida) and the transliteration marks ayn/hamza/apostrophes.
3. Fold letter variants: Arabic alef forms, alef maqsura, teh marbuta, waw/yeh with hamza, Persian yeh/kaf;
   Latin ligatures and barred letters (ae, oe, ss, o, d, l).
4. Arabic-Indic and extended digits become ASCII digits; lower-case; every other non letter/digit becomes a space.
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
    "ة": "ه",
    "ۀ": "ه",
    "ھ": "ه",
    "ہ": "ه",
    "ؤ": "و",
    "ک": "ك",
    "گ": "ك",
    "æ": "ae",
    "œ": "oe",
    "ß": "ss",
    "ø": "o",
    "đ": "d",
    "ð": "d",
    "ł": "l",
    "þ": "th",
    "ı": "i",
}
_DROP = {"ـ", "ء", "ʿ", "ʾ", "ʻ", "ʼ", "ʽ", "'", "’", "‘", "`", "´", "ʹ", "ʺ"}
_DIGITS = {ord(c): str(i % 10) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹")}
_NONWORD = re.compile(r"[^\w]+", re.UNICODE)


def fold(s: str | None) -> str:
    """Return the search key of ``s``: accent-, diacritic- and variant-insensitive, lower-case."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s)).lower()
    out = []
    for ch in s:
        if unicodedata.category(ch).startswith("M") or ch in _DROP:
            continue
        out.append(_MAP.get(ch, ch))
    s = "".join(out).translate(_DIGITS)
    s = s.replace("_", " ")
    return _NONWORD.sub(" ", s).strip()
