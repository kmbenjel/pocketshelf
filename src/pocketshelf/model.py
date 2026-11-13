"""The data model shared by every input (scan, sidecar CSV, catalog) and the builder."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_EXT = re.compile(r"\.(pdf|epub|djvu|djv|mobi|azw3|txt|html?|cbz|fb2)\d?(?=[./?#]|$)")

BOOK_EXTS = (".pdf", ".epub", ".djvu", ".djv", ".mobi", ".azw3", ".cbz", ".txt", ".fb2")


@dataclass
class Volume:
    """One file of a multi-file book."""

    label: str
    path: str
    size: int = 0


@dataclass
class Book:
    """One catalog entry: a single file, or a multi-volume work kept in one folder.

    ``path`` is relative to the library root with ``/`` separators (or an absolute URL, or empty
    when the entry is listed without a file).
    """

    title: str = ""
    author: str = ""
    author_death: int = 0  # 0 = unknown; negative = before the common era
    author_calendar: str = "ce"  # "ce" or "ah"
    category: str = ""  # "/"-separated path, e.g. "History/Medieval"
    path: str = ""
    volumes: list[Volume] = field(default_factory=list)
    size: int = 0
    pages: int = 0
    lang: str = ""
    work: str = ""  # explicit work id; rows sharing it are editions of one work
    edition: str = ""
    editor: str = ""
    publisher: str = ""
    place: str = ""
    year: int = 0
    series: str = ""
    isbn: str = ""
    tags: list[str] = field(default_factory=list)
    note: str = ""
    ext_ids: dict[str, str] = field(default_factory=dict)
    mtime: int = 0  # days since the Unix epoch

    @property
    def files(self) -> list[Volume]:
        if self.volumes:
            return self.volumes
        return [Volume("", self.path, self.size)] if self.path else []

    @property
    def fmt(self) -> str:
        files = self.files
        if not files:
            return ""
        m = _EXT.search(files[0].path.lower())
        return m.group(1) if m else ""
