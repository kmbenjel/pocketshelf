"""PDF metadata with the standard library only: the Info dictionary and the XMP packet.

It reads the first and last 192 KB of the file, so it is fast on USB sticks and phones' storage, and it
does not open compressed object streams. A PDF whose Info dictionary lives inside one just yields no
metadata, and the filename parser takes over.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

CHUNK = 192 * 1024

_INFO_REF = re.compile(rb"/Info\s+(\d+)\s+(\d+)\s+R")
_KEYS = {
    "Title": "title",
    "Author": "author",
    "Subject": "subject",
    "Keywords": "keywords",
    "Creator": "creator",
    "Producer": "producer",
    "CreationDate": "date",
}
# generic titles that tools write when the author did not
JUNK_TITLE = re.compile(
    r"^(untitled|unnamed|document\d*|doc\d*|microsoft word.*|scan(ned)?.*|new document.*|slide \d+|"
    r".*\.(docx?|pdf|indd|qxd|tex|rtf|odt|txt|pmd|ps|dvi|html?|pub)|\s*)$",
    re.I,
)
JUNK_AUTHOR = re.compile(r"^(unknown|admin(istrator)?|user|owner|author|windows user|\s*)$", re.I)


def _read_ends(path: str) -> tuple[bytes, bytes, int]:
    with open(path, "rb") as f:
        head = f.read(CHUNK)
        f.seek(0, 2)
        size = f.tell()
        tail = b""
        if size > CHUNK:
            f.seek(max(CHUNK, size - CHUNK))
            tail = f.read()
        return head, tail, size


def decode_pdf_string(raw: bytes) -> str:
    """Decode a PDF text string: UTF-16 with BOM, UTF-8 with BOM, else PDFDocEncoding (~ cp1252)."""
    if raw.startswith(b"\xfe\xff"):
        return raw[2:].decode("utf-16-be", "replace")
    if raw.startswith(b"\xff\xfe"):
        return raw[2:].decode("utf-16-le", "replace")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", "replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", "replace")


_ESC = {ord("n"): b"\n", ord("r"): b"\r", ord("t"): b"\t", ord("b"): b"\b", ord("f"): b"\f"}


def _literal(buf: bytes, i: int) -> tuple[bytes, int]:
    """Parse ``( ... )`` starting at ``buf[i] == '('``; returns the bytes and the index after the string."""
    depth, out, i = 1, bytearray(), i + 1
    n = len(buf)
    while i < n and depth:
        c = buf[i]
        if c == 0x5C and i + 1 < n:  # backslash
            d = buf[i + 1]
            if d in _ESC:
                out += _ESC[d]
                i += 2
            elif 0x30 <= d <= 0x37:
                j = i + 1
                while j < n and j < i + 4 and 0x30 <= buf[j] <= 0x37:
                    j += 1
                out.append(int(buf[i + 1 : j], 8) & 0xFF)
                i = j
            elif d in (0x0D, 0x0A):
                i += 2 + (1 if d == 0x0D and i + 2 < n and buf[i + 2] == 0x0A else 0)
            else:
                out.append(d)
                i += 2
            continue
        if c == 0x28:
            depth += 1
        elif c == 0x29:
            depth -= 1
            if depth == 0:
                i += 1
                break
        out.append(c)
        i += 1
    return bytes(out), i


def _hex(buf: bytes, i: int) -> tuple[bytes, int]:
    j = buf.find(b">", i)
    j = len(buf) if j < 0 else j
    h = re.sub(rb"[^0-9A-Fa-f]", b"", buf[i + 1 : j])
    if len(h) % 2:
        h += b"0"
    return bytes.fromhex(h.decode()), j + 1


def parse_info_dict(buf: bytes) -> dict[str, str]:
    """Pull ``/Key (value)`` and ``/Key <hex>`` pairs for the keys we know out of a dictionary body."""
    out: dict[str, str] = {}
    for m in re.finditer(rb"/(Title|Author|Subject|Keywords|Creator|Producer|CreationDate)\s*([(<])", buf):
        key = m.group(1).decode()
        i = m.end() - 1
        raw, _ = _literal(buf, i) if buf[i] == 0x28 else _hex(buf, i)
        out.setdefault(_KEYS[key], decode_pdf_string(raw).replace("\x00", "").strip())
    return out


def _info_from(refs_in: bytes, search_in: bytes) -> dict[str, str]:
    """Follow the last ``/Info N G R`` found in ``refs_in`` to its object, searched in ``search_in``."""
    refs = _INFO_REF.findall(refs_in)
    for num, gen in reversed(refs):  # the last trailer wins (incremental updates)
        pat = re.compile(rb"(?<![\d])" + num + rb"\s+" + gen + rb"\s+obj\s*<<(.*?)>>\s*endobj", re.S)
        for m in reversed(list(pat.finditer(search_in))):
            info = parse_info_dict(m.group(1))
            if info:
                return info
    return {}


def _xmp(buf: bytes) -> dict[str, str]:
    a = buf.find(b"<x:xmpmeta")
    if a < 0:
        a = buf.find(b"<?xpacket begin")
    b = buf.find(b"</x:xmpmeta>", a) if a >= 0 else -1
    if a < 0 or b < 0:
        return {}
    xml = buf[a : b + len(b"</x:xmpmeta>")]
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return {}
    ns = {"dc": "http://purl.org/dc/elements/1.1/", "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"}

    def first(tag: str) -> str:
        el = root.find(f".//dc:{tag}", ns)
        if el is None:
            return ""
        li = el.find(".//rdf:li", ns)
        return ((li.text if li is not None else el.text) or "").strip()

    out = {"title": first("title"), "author": first("creator"), "lang": first("language"), "subject": first("description")}
    pub = first("publisher")
    if pub:
        out["publisher"] = pub
    return {k: v for k, v in out.items() if v}


def read_pdf(path: str) -> dict[str, str | int]:
    """Return ``title``, ``author``, ``publisher``, ``lang``, ``year`` when present (junk values dropped)."""
    try:
        head, tail, _ = _read_ends(path)
    except OSError:
        return {}
    if not head.startswith(b"%PDF") and b"%PDF" not in head[:1024]:
        return {}
    both = head + tail
    info = _info_from(tail, both) or _info_from(head, both)
    info = {**_xmp(head + tail), **{k: v for k, v in info.items() if v}} if info else _xmp(head + tail)
    out: dict[str, str | int] = {}
    if info.get("title") and not JUNK_TITLE.match(info["title"]):
        out["title"] = info["title"]
    if info.get("author") and not JUNK_AUTHOR.match(info["author"]):
        out["author"] = info["author"]
    for k in ("publisher", "lang"):
        if info.get(k):
            out[k] = info[k][:2].lower() if k == "lang" else info[k]
    m = re.search(r"(\d{4})", info.get("date", ""))
    if m and 1000 < int(m.group(1)) < 2200 and "producer" not in out:
        # the creation date of the PDF file is rarely the publication year: kept under its own key
        out["created"] = int(m.group(1))
    return out
