"""Headless-Chrome checks of the real page. Skipped when node or Chrome are missing."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from pocketshelf.build import build_html
from pocketshelf.model import Book, Volume

ROOT = Path(__file__).parents[1]
CHROME = any(shutil.which(c) or os.path.exists(c) for c in ("/opt/google/chrome/chrome", "google-chrome", "chromium", "chromium-browser"))
pytestmark = pytest.mark.skipif(not (shutil.which("node") and CHROME), reason="node and Chrome are needed")


def fixture_books():
    return [
        Book(title="Emma", author="Austen, Jane", author_death=1817, category="Fiction", path="Fiction/Emma - Austen.pdf", size=1_200_000, year=1815, lang="en"),
        Book(title="Emma", author="Jane Austen", category="Fiction", path="Fiction/Emma 2.epub", size=300_000, edition="2nd"),
        Book(title="Les Misérables", author="Hugo, Victor", author_death=1885, category="Fiction", volumes=[Volume("01", "Fiction/Hugo/01.pdf", 5), Volume("02", "Fiction/Hugo/02.pdf", 6)], lang="fr"),
        Book(title="إحياء علوم الدين", author="الغزالي", author_death=505, author_calendar="ah", category="التصوف", lang="ar"),
        Book(title="المقدمة", author="ʿAbd al-Raḥmān ibn Khaldūn", author_death=808, author_calendar="ah", category="التاريخ/فلسفة", lang="ar"),
        Book(title='<img src=x onerror="window.__injected=1"> img', author="<script>window.__injected=1</script>", category="Other"),
    ]


@pytest.mark.parametrize("compress", [True, False])
def test_page_in_chrome(tmp_path, compress):
    out = tmp_path / "web" / "catalog.html"
    out.parent.mkdir()
    (tmp_path / "lib").mkdir()
    out.write_text(build_html(fixture_books(), "Fixture", "en", base="../lib/", compress=compress), encoding="utf-8")
    env = {**os.environ, "PS_DIRECT_CHROME": "1"} if os.environ.get("CI") else os.environ
    r = subprocess.run(["node", str(ROOT / "scripts/e2e.mjs"), str(out)], capture_output=True, text=True, timeout=180, env=env)
    last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "{}"
    res = json.loads(last)
    assert res.get("ok"), res.get("failures") or r.stderr
