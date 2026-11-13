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
    strings = [c[0] or "" for c in CASES] + ["Les Misérables", "حدّثنا أبو هريرة", "Ǆ ǅ ǆ", "ﬁnance ﬂuide", "x²", "①②", "Ⅷ", "日本語 テスト", "a–b—c", "ſ"]
    (tmp_path / "in.json").write_text(json.dumps(strings), encoding="utf-8")
    runner = tmp_path / "r.js"
    runner.write_text(
        f"const {{fold}}=require({json.dumps(str(js))});const s=JSON.parse(require('fs').readFileSync({json.dumps(str(tmp_path / 'in.json'))},'utf8'));"
        "console.log(JSON.stringify(s.map(fold)));",
        encoding="utf-8",
    )
    out = json.loads(subprocess.run(["node", str(runner)], capture_output=True, text=True, check=True).stdout)
    assert out == [fold(s) for s in strings]
