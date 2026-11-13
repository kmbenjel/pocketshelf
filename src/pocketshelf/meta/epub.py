"""EPUB metadata from the OPF package document (Dublin Core), with the standard library."""

from __future__ import annotations

import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

_NS = {
    "c": "urn:oasis:names:tc:opendocument:xmlns:container",
    "o": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def read_epub(path: str) -> dict[str, str | int]:
    try:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            if "META-INF/container.xml" not in names:
                return {}
            c = ET.fromstring(z.read("META-INF/container.xml"))
            rf = c.find(".//c:rootfile", _NS)
            if rf is None:
                return {}
            opf_path = posixpath.normpath(rf.get("full-path", ""))
            if opf_path not in names:
                return {}
            root = ET.fromstring(z.read(opf_path))
    except (OSError, zipfile.BadZipFile, ET.ParseError, KeyError, ValueError, RuntimeError):
        return {}
    md = root.find("o:metadata", _NS)
    if md is None:
        md = root.find("{*}metadata")
    if md is None:
        return {}

    def texts(tag: str) -> list[str]:
        return [(e.text or "").strip() for e in md.findall(f"dc:{tag}", _NS) if (e.text or "").strip()]

    out: dict[str, str | int] = {}
    if t := texts("title"):
        out["title"] = t[0]
    if a := texts("creator"):
        out["author"] = " & ".join(a[:3])
    if p := texts("publisher"):
        out["publisher"] = p[0]
    if lg := texts("language"):
        out["lang"] = lg[0][:2].lower()
    if d := texts("date"):
        m = re.match(r"-?(\d{4})", d[0])
        if m:
            out["year"] = int(m.group(1))
    if s := texts("subject"):
        out["tags"] = "; ".join(s[:8])
    if i := texts("identifier"):
        for v in i:
            m = re.search(r"(97[89][\d-]{10,14})", v)
            if m:
                out["isbn"] = m.group(1)
                break
    for meta in md.findall("o:meta", _NS) + md.findall("{*}meta"):  # calibre / EPUB 3 series
        n = meta.get("name") or meta.get("property")
        if n in ("calibre:series", "belongs-to-collection"):
            val = meta.get("content") or (meta.text or "").strip()
            if val:
                out["series"] = val
    return out
