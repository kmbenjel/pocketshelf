"""Filename parsing: templates like ``{author} - {title} ({year})`` and pluggable profiles."""

from __future__ import annotations

import re
from collections.abc import Callable
from importlib import metadata

from ..lives import split_life_dates

Parsed = dict[str, "str | int"]
Profile = Callable[..., "Parsed | None"]

FIELDS = ("title", "author", "editor", "publisher", "place", "year", "series", "edition", "volume", "lang", "skip")
_TOKEN = re.compile(r"\{(\w+)\}")


def compile_template(template: str) -> re.Pattern[str]:
    """``"{author} - {title} ({year})"`` -> an anchored regex with one named group per field.

    ``{skip}`` matches anything and is discarded; a field used twice must match the same text twice.
    ``{year}`` and ``{volume}`` match digits only, so ``Title - 1998`` does not swallow the title.
    """
    parts, pos, seen = [], 0, set()
    for m in _TOKEN.finditer(template):
        name = m.group(1)
        if name not in FIELDS:
            raise ValueError(f"unknown field {{{name}}} in template {template!r}; known: {', '.join(FIELDS)}")
        parts.append(re.escape(template[pos : m.start()]).replace(r"\ ", r"\s+"))
        if name == "skip":
            parts.append(r".*?")
        elif name in seen:
            parts.append(f"(?P={name})")
        else:
            seen.add(name)
            body = {"year": r"\d{4}", "volume": r"\d{1,3}"}.get(name, r".+?")
            parts.append(f"(?P<{name}>{body})")
        pos = m.end()
    parts.append(re.escape(template[pos:]).replace(r"\ ", r"\s+"))
    return re.compile("^" + "".join(parts) + "$", re.S)


def parse_template(patterns: list[re.Pattern[str]], stem: str) -> Parsed | None:
    for pat in patterns:
        m = pat.match(stem.strip())
        if m:
            d: Parsed = {k: v.strip() for k, v in m.groupdict().items() if v and v.strip()}
            for k in ("year", "volume"):
                if k in d:
                    d[k] = int(d[k])
            return d
    return None


_SEP = re.compile(r"\s+[-–—_]\s+|\s+--\s+")
_YEAR = re.compile(r"[\(\[]\s*(1[0-9]{3}|20[0-9]{2})\s*[\)\]]\s*$|\s+[-,]\s*(1[0-9]{3}|20[0-9]{2})\s*$")


def parse_dashes(stem: str, order: str = "title-author") -> Parsed | None:
    """The common ``Title - Author - ...`` shape; ``order="author-title"`` flips the first two parts.

    A trailing ``(1998)`` becomes the year; ``Author (1743-1826)`` yields a death year.
    """
    stem = stem.strip()
    out: Parsed = {}
    m = _YEAR.search(stem)
    if m:
        out["year"] = int(m.group(1) or m.group(2))
        stem = stem[: m.start()].rstrip()
    parts = [p.strip() for p in _SEP.split(stem) if p.strip()]
    if not parts:
        return None
    if len(parts) == 1:
        out["title"] = parts[0]
        return out
    a, b = (1, 0) if order == "author-title" else (0, 1)
    out["title"], out["author"] = parts[a], parts[b]
    return out


# --- the `warraq` profile ---------------------------------------------------------------------------------------

_EDITOR = re.compile(r"^(?:ت|تحقيق|تحقيق وتعليق|تح)\s+(.+)$")
_PUB_PLACE = re.compile(r"^(.+?)\s+(بيروت|القاهرة|دمشق|الرياض|عمان|الدار البيضاء|الرباط|تونس|بغداد|الكويت|جدة|مكة|المدينة|الإسكندرية|حلب|الجزائر|الدوحة|مصر|لبنان)$")
_VOL = re.compile(r"^(\d{1,3})\s*[-–]\s*(.+)$")


def parse_warraq(stem: str, is_folder: bool = False) -> Parsed | None:
    """``<title> - <author> - ت <editor> - <publisher> <city>``, volumes ``NN - <shared name>``.

    Used when the ``arabic_bib`` plugin is not installed; it covers the shape but none of arabic-bib's
    normalisation. Returns None if there are not at least a title and an author.
    """
    out: Parsed = {}
    stem = stem.strip()
    vm = _VOL.match(stem)
    if vm and not is_folder:
        out["volume"] = int(vm.group(1))
        stem = vm.group(2)
    parts = [p.strip() for p in _SEP.split(stem) if p.strip()]
    if len(parts) < 2:
        return None
    out["title"] = parts[0]
    name, death, cal = split_life_dates(parts[1])
    out["author"] = name
    if death:
        out["author_death"], out["author_calendar"] = death, cal
    for p in parts[2:]:
        m = _EDITOR.match(p)
        if m:
            out["editor"] = m.group(1)
            continue
        if re.fullmatch(r"\d{4}", p):
            out["year"] = int(p)
            continue
        m = _PUB_PLACE.match(p)
        if m:
            out["publisher"], out["place"] = m.group(1), m.group(2)
        elif "publisher" not in out:
            out["publisher"] = p
        else:
            out["edition"] = (out.get("edition", "") + " " + p).strip()
    return out


def get_profile(name: str) -> Profile:
    """Resolve a profile by name: installed plugins first (entry point group ``pocketshelf.profiles``), then built-ins."""
    try:
        for ep in metadata.entry_points(group="pocketshelf.profiles"):
            if ep.name == name:
                return ep.load()
    except Exception:  # a broken third-party plugin must not break the build
        pass
    builtin: dict[str, Profile] = {
        "warraq": parse_warraq,
        "dashes": lambda stem, is_folder=False: parse_dashes(stem),
        "author-title": lambda stem, is_folder=False: parse_dashes(stem, "author-title"),
    }
    if name not in builtin:
        raise ValueError(f"unknown profile {name!r}; built-in: {', '.join(sorted(builtin))}")
    return builtin[name]


class FilenameParser:
    """Tries the user's templates in order, then a profile, then the generic dash split."""

    def __init__(self, templates: list[str] | None = None, profile: str | None = None, order: str = "title-author"):
        self.patterns = [compile_template(t) for t in templates or []]
        self.profile = get_profile(profile) if profile else None
        self.order = order

    def __call__(self, stem: str, is_folder: bool = False) -> Parsed:
        d = parse_template(self.patterns, stem) if self.patterns else None
        if d is None and self.profile:
            d = self.profile(stem, is_folder=is_folder)
        if d is None and not self.patterns and not self.profile:
            d = parse_dashes(stem, self.order)
        if d is None:
            d = {"title": stem.strip()}
        if "author" in d:
            name, death, cal = split_life_dates(str(d["author"]))
            d["author"] = name
            if death and "author_death" not in d:
                d["author_death"], d["author_calendar"] = death, cal
        if "title" not in d or not str(d["title"]).strip():
            d["title"] = stem.strip()
        return d
