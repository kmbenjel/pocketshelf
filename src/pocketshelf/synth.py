"""Deterministic synthetic libraries for benchmarks and tests (no real titles, no real files)."""

from __future__ import annotations

import random

from .model import Book, Volume

_EN = [
    "river",
    "garden",
    "winter",
    "stone",
    "lantern",
    "mirror",
    "harbour",
    "orchard",
    "compass",
    "thunder",
    "velvet",
    "meadow",
    "cipher",
    "voyage",
    "almanac",
    "ember",
    "glacier",
    "quarry",
    "saffron",
    "tapestry",
]
_FR = [
    "jardin",
    "hiver",
    "pierre",
    "miroir",
    "verger",
    "tonnerre",
    "prairie",
    "voyage",
    "braise",
    "glacier",
    "carrière",
    "safran",
    "tapisserie",
    "souvenir",
    "horizon",
]
_AR = [
    "الحديقة",
    "الشتاء",
    "الحجر",
    "المرآة",
    "البستان",
    "الرعد",
    "المرج",
    "الرحلة",
    "الجمر",
    "الجليد",
    "الزعفران",
    "النسيج",
    "الأفق",
    "الميزان",
    "الكتاب",
    "الشرح",
    "المختصر",
]
_FIRST = [
    "Anna",
    "Boris",
    "Clara",
    "Dmitri",
    "Elena",
    "Farid",
    "Greta",
    "Hugo",
    "Ingrid",
    "Jamal",
    "Karim",
    "Lena",
    "Mateo",
    "Nadia",
    "Omar",
    "Pavel",
    "Rosa",
    "Samir",
    "Tariq",
    "Ursula",
]
_LAST = [
    "Alder",
    "Brandt",
    "Castell",
    "Duval",
    "Esposito",
    "Farouk",
    "Gallo",
    "Haddad",
    "Ivanov",
    "Jansen",
    "Kovacs",
    "Laurent",
    "Mansour",
    "Novak",
    "Okafor",
    "Petrov",
    "Quint",
    "Rahman",
    "Santos",
    "Vidal",
]
_AR_AUTH = [
    "الفارس",
    "الحداد",
    "المنصور",
    "القاسم",
    "الرحمن",
    "الأنصاري",
    "البغدادي",
    "الدمشقي",
    "الأندلسي",
    "المغربي",
]
_CATS = ["History/Ancient", "History/Modern", "Science/Physics", "Science/Biology", "Literature/Poetry", "Literature/Novels",
         "Philosophy", "Religion", "Law", "Medicine", "Travel", "Mathematics/Algebra", "Mathematics/Geometry", "Art", "Music"]  # fmt: skip


def synthetic_books(n: int, seed: int = 7) -> list[Book]:
    rnd = random.Random(seed)
    books: list[Book] = []
    authors = [
        (f"{rnd.choice(_LAST)}, {rnd.choice(_FIRST)}", rnd.randint(1500, 1990), "ce")
        for _ in range(max(50, n // 8))
    ]
    authors += [
        (f"{rnd.choice(_AR_AUTH)} {rnd.choice(_AR_AUTH)}", rnd.randint(150, 1000), "ah")
        for _ in range(max(20, n // 20))
    ]
    for _i in range(n):
        lang = rnd.choices(["en", "fr", "ar"], [6, 2, 2])[0]
        words = {"en": _EN, "fr": _FR, "ar": _AR}[lang]
        title = " ".join(rnd.choice(words) for _ in range(rnd.randint(2, 6))).capitalize()
        name, death, cal = (
            rnd.choice([a for a in authors[:: rnd.randint(1, 3)]] or authors)
            if lang != "ar"
            else rnd.choice(authors[-max(20, n // 20) :])
        )
        cat = rnd.choice(_CATS)
        ext = rnd.choice(["pdf", "pdf", "pdf", "epub", "djvu"])
        folder = f"{cat}/{title[:40]}"
        if rnd.random() < 0.08:
            vols = [
                Volume(f"{k:02d}", f"{folder}/{k:02d} - {title[:30]}.pdf", rnd.randint(2_000_000, 40_000_000))
                for k in range(1, rnd.randint(2, 6))
            ]
            b = Book(
                title=title,
                author=name,
                author_death=death,
                author_calendar=cal,
                category=cat,
                volumes=vols,
                size=sum(v.size for v in vols),
                lang=lang,
            )
        else:
            b = Book(
                title=title,
                author=name,
                author_death=death,
                author_calendar=cal,
                category=cat,
                path=f"{folder}.{ext}",
                size=rnd.randint(200_000, 90_000_000),
                lang=lang,
            )
        b.year = rnd.choice([0, rnd.randint(1850, 2020)])
        b.mtime = rnd.randint(17000, 20400)
        if rnd.random() < 0.3:
            b.publisher = f"{rnd.choice(_LAST)} Press"
        if rnd.random() < 0.15:
            b.editor = f"{rnd.choice(_FIRST)} {rnd.choice(_LAST)}"
        books.append(b)
        if rnd.random() < 0.06:  # a second edition of the same work
            e = Book(
                **{
                    **b.__dict__,
                    "path": b.path.replace(".", "-2.", 1) if b.path else "",
                    "edition": "2nd ed.",
                    "year": (b.year or 1950) + 20,
                    "publisher": f"{rnd.choice(_LAST)} House",
                }
            )
            books.append(e)
    return books[:n]
