import json
import shutil
import subprocess
from pathlib import Path

import pytest

from pocketshelf.fold import fold

CASES = [
    ("Misérables", "miserables"),
    ("Œuvres ÆSOP Straße", "oeuvres aesop strasse"),
    ("الإِمَامُ الغَزَالِيّ", "الامام الغزالي"),
    ("إحياء علوم الدين", "احيا علوم الدين"),  # hamza ء is dropped, on both sides of a search,
    ("المنقذ من الضلال", "المنقذ من الضلال"),
    ("مَقَامَات", "مقامات"),
    ("مدرسة", "مدرسه"),
    ("مكتبة", "مكتبه"),
    ("على / علي", "علي علي"),
    ("مؤمن", "مومن"),
    ("ئ", "ي"),
    ("ʿAbd al-Raḥmān ibn Khaldūn", "abd al rahman ibn khaldun"),
    ("القرن ٧ هـ ۱۲۳", "القرن 7 ه 123"),
    ("كــــتاب", "كتاب"),
    ("Ibn Taymiyya's fatwas", "ibn taymiyyas fatwas"),
    ("  many   spaces\tand_tabs ", "many spaces and tabs"),
    ("Ωmega Ελληνικά", "ωmega ελληνικα"),
    ("", ""),
    (None, ""),
    ("ﷲ", "الله"),  # presentation form
    ("ﻟﻠﻪ", "لله"),
    ("Ça va? Ñandú", "ca va nandu"),
    ("İstanbul", "istanbul"),
    ("ک گ ی", "ك ك ي"),
    ("ڪتاب ڭ ے ۃ ە", "كتاب ك ي ه ه"),  # swash kaf, Maghrebi gaf, yeh barree, teh marbuta goal, ae
    ("عبد\u200fالله", "عبدالله"),  # a direction mark inside a word leaves no trace
    ("\ufeffبسم \u202bالله\u202c", "بسم الله"),  # byte-order mark, embedding controls
    ("می\u200cخواهم", "ميخواهم"),  # zero-width non-joiner
    ("co\u00adoperate", "cooperate"),  # soft hyphen
    ("ΟΔΟΣ όσος", "οδοσ οσοσ"),  # the final sigma is the same letter
    ("x…y ½ ⒜", "x y 1 2 a"),  # compatibility characters that unfold to several words
    ("ﷺ", "صلي الله عليه وسلم"),
]


@pytest.mark.parametrize(("raw", "expected"), CASES)
def test_fold(raw, expected):
    assert fold(raw) == expected


def test_fold_is_idempotent():
    for raw, _ in CASES:
        assert fold(fold(raw)) == fold(raw)


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_python_and_js_fold_agree(tmp_path: Path):
    """The page's fold.js must produce exactly what fold.py produces."""
    js = Path(__file__).parents[1] / "src/pocketshelf/assets/fold.js"
    strings = [c[0] or "" for c in CASES] + [
        "Les Misérables",
        "حدّثنا أبو هريرة",
        "Ǆ ǅ ǆ",
        "ﬁnance ﬂuide",
        "x²",
        "①②",
        "Ⅷ",
        "日本語 テスト",
        "a–b—c",
        "ſ",
    ]
    (tmp_path / "in.json").write_text(json.dumps(strings), encoding="utf-8")
    runner = tmp_path / "r.js"
    runner.write_text(
        f"const {{fold}}=require({json.dumps(str(js))});const s=JSON.parse(require('fs').readFileSync({json.dumps(str(tmp_path / 'in.json'))},'utf8'));"
        "console.log(JSON.stringify(s.map(fold)));",
        encoding="utf-8",
    )
    out = json.loads(subprocess.run(["node", str(runner)], capture_output=True, text=True, check=True).stdout)
    assert out == [fold(s) for s in strings]


# Blocks whose characters have had the same properties for many Unicode versions, so that the Python and the
# Node of any supported pair agree on them: Latin, Greek, Cyrillic, Hebrew, Arabic and its presentation forms,
# general punctuation (where the invisible format characters live), letter-like symbols.
STABLE_BLOCKS = [
    (0x20, 0x250),
    (0x370, 0x500),
    (0x5D0, 0x5EB),
    (0x600, 0x700),
    (0x750, 0x780),
    (0x2000, 0x2070),
    (0x2100, 0x2190),
    (0xFB50, 0xFE00),
    (0xFE70, 0xFF00),
    (0x1D400, 0x1D420),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_twins_agree_on_every_character(tmp_path: Path):
    """Each character alone, inside a Latin word, inside an Arabic word and doubled: about 9,600 strings."""
    js = Path(__file__).parents[1] / "src/pocketshelf/assets/fold.js"
    chars = [chr(c) for a, b in STABLE_BLOCKS for c in range(a, b)]
    strings = chars + [f"a{c}b" for c in chars] + [f"كت{c}اب" for c in chars] + [c + c for c in chars]
    (tmp_path / "in.json").write_text(json.dumps(strings), encoding="utf-8")
    code = (
        f"const {{fold}}=require({json.dumps(str(js))});"
        f"const s=JSON.parse(require('fs').readFileSync({json.dumps(str(tmp_path / 'in.json'))},'utf8'));"
        "console.log(JSON.stringify(s.map(fold)));"
    )
    out = json.loads(subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True).stdout)
    differ = [(s, fold(s), j) for s, j in zip(strings, out, strict=True) if fold(s) != j]
    assert not differ, differ[:10]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_highlight_marks_whole_runs(tmp_path: Path):
    """A match is one <mark>, vowel marks and the final hamza included; hostile text stays text."""
    js = Path(__file__).parents[1] / "src/pocketshelf/assets/fold.js"
    cases = [
        ["إِحْيَاءُ علوم الدين", ["احيا"]],
        ["Les Misérables", ["miserables"]],
        ["Les Misérables", ["les", "mis"]],
        ["عبد الله بن المبارك", ["عبد الله"]],
        ["<b>bold</b> & co", ["bold"]],
        ["كــــتاب", ["كتاب"]],
        ["𝐀bc abc", ["abc"]],
        ["nothing here", ["zzz"]],
    ]
    code = (
        f"const {{highlight}}=require({json.dumps(str(js))});"
        "const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));"
        f"console.log(JSON.stringify({json.dumps(cases)}.map(([s,t])=>highlight(s,t,esc))));"
    )
    out = json.loads(subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True).stdout)
    assert out == [
        "<mark>إِحْيَاءُ</mark> علوم الدين",
        "Les <mark>Misérables</mark>",
        "<mark>Les</mark> <mark>Mis</mark>érab<mark>les</mark>",  # a word matches anywhere, as in the search
        "<mark>عبد الله</mark> بن المبارك",
        "&lt;b&gt;<mark>bold</mark>&lt;/b&gt; &amp; co",
        "<mark>كــــتاب</mark>",
        "<mark>𝐀bc</mark> <mark>abc</mark>",
        "nothing here",
    ]
