"""Headless-Chrome checks of the real page. Skipped when Node 22+ or Chrome are missing."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from pocketshelf.build import build_html
from pocketshelf.model import Book, Volume
from pocketshelf.synth import synthetic_books

ROOT = Path(__file__).parents[1]
CHROME = any(
    shutil.which(c) or os.path.exists(c)
    for c in ("/opt/google/chrome/chrome", "google-chrome", "chromium", "chromium-browser")
)


def node_major() -> int:
    if not shutil.which("node"):
        return 0
    v = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout
    m = re.match(r"v(\d+)", v.strip())
    return int(m.group(1)) if m else 0


# scripts/chrome.mjs talks to Chrome with Node's built-in WebSocket (Node 22+)
pytestmark = pytest.mark.skipif(not (node_major() >= 22 and CHROME), reason="Node 22+ and Chrome are needed")


def fixture_books():
    return [
        Book(
            title="Emma",
            author="Austen, Jane",
            author_death=1817,
            category="Fiction",
            path="Fiction/Emma - Austen.pdf",
            size=1_200_000,
            year=1815,
            lang="en",
        ),
        Book(
            title="Emma",
            author="Jane Austen",
            category="Fiction",
            path="Fiction/Emma 2.epub",
            size=300_000,
            edition="2nd",
        ),
        Book(
            title="Les Misérables",
            author="Hugo, Victor",
            author_death=1885,
            category="Fiction",
            volumes=[Volume("01", "Fiction/Hugo/01.pdf", 5), Volume("02", "Fiction/Hugo/02.pdf", 6)],
            lang="fr",
        ),
        Book(
            title="إحياء علوم الدين",
            author="الغزالي",
            author_death=505,
            author_calendar="ah",
            category="التصوف",
            lang="ar",
        ),
        Book(
            title="المقدمة",
            author="ʿAbd al-Raḥmān ibn Khaldūn",
            author_death=808,
            author_calendar="ah",
            category="التاريخ/فلسفة",
            lang="ar",
        ),
        Book(title="الزهد", author="عبد الله بن المبارك", author_death=181, author_calendar="ah", lang="ar"),
        Book(
            title="الجامع لأحكام القرآن",
            alt_titles=["تفسير القرطبي"],
            author="القرطبي",
            author_death=671,
            author_calendar="ah",
            category="التفسير",
            lang="ar",
        ),
        Book(title="Dune Messiah", author="Herbert, Frank", path="Dune: Messiah.epub", lang="en"),
        Book(
            title='<img src=x onerror="window.__injected=1"> img',
            author="<script>window.__injected=1</script>",
            category="Other",
        ),
    ]


def run_e2e(page: Path, *flags: str) -> None:
    direct = os.environ.get("CI") or not shutil.which("systemd-run")
    env = {**os.environ, "PS_DIRECT_CHROME": "1"} if direct else os.environ
    r = subprocess.run(
        ["node", str(ROOT / "scripts/e2e.mjs"), str(page), *flags],
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )
    last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "{}"
    res = json.loads(last)
    assert res.get("ok"), res.get("failures") or r.stderr


@pytest.mark.parametrize("compress", [True, False])
def test_page_in_chrome(tmp_path, compress):
    out = tmp_path / "web" / "catalog.html"
    out.parent.mkdir()
    (tmp_path / "lib").mkdir()
    out.write_text(
        build_html(fixture_books(), "Fixture", "en", base="../lib/", compress=compress), encoding="utf-8"
    )
    run_e2e(out)


def test_large_catalog_keyboard_and_phone_widths(tmp_path):
    """3,000 synthetic books: the virtual list under the keyboard, and layouts down to a 320 px phone."""
    out = tmp_path / "big.html"
    out.write_text(build_html(synthetic_books(3000), "Big", "en"), encoding="utf-8")
    run_e2e(out, "--big")
