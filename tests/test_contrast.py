"""WCAG contrast of the page's four colour sets, computed from the CSS itself.

Text must reach 4.5:1 on every background it is drawn on, and the edge of a form control 3:1 against both the
control and the page (WCAG 2.1 AA, criteria 1.4.3 and 1.4.11).
"""

import re
from pathlib import Path

import pytest

CSS = (Path(__file__).parents[1] / "src/pocketshelf/assets/app.css").read_text(encoding="utf-8")


def palette(selector: str, base: dict[str, str] | None = None) -> dict[str, str]:
    """The colour variables of the first rule with this selector, over those of ``base``."""
    body = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", CSS)
    assert body, selector
    found = re.findall(r"--([a-z-]+):#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-fA-F])", body.group(1))
    return {**(base or {}), **{k: "#" + (v if len(v) == 6 else "".join(c * 2 for c in v)) for k, v in found}}


LIGHT = palette(":root")
DARK = palette(":root[data-theme=dark]", LIGHT)
PALETTES = {
    "lapis light": LIGHT,
    "paper light": palette(":root[data-palette=paper]", LIGHT),
    "lapis dark": DARK,
    "paper dark": palette(":root[data-theme=dark][data-palette=paper]", DARK),
}


def luminance(colour: str) -> float:
    def channel(v: int) -> float:
        c = v / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (int(colour[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


TEXT = [  # (text colour, background): every pairing the page draws
    ("ink", "bg"),
    ("ink", "surface"),
    ("ink", "mark"),  # a highlighted match
    ("ink", "line"),  # the remove button of a filter pill, a hovered icon
    ("muted", "bg"),
    ("muted", "surface"),
    ("accent", "bg"),
    ("accent", "surface"),
    ("accent", "line"),  # the current tab on wide screens
    ("accent-ink", "accent"),  # filled buttons
]


@pytest.mark.parametrize("name", PALETTES)
def test_text_contrast(name):
    p = PALETTES[name]
    low = {
        f"{fg} on {bg}": round(contrast(p[fg], p[bg]), 2) for fg, bg in TEXT if contrast(p[fg], p[bg]) < 4.5
    }
    assert not low, low


@pytest.mark.parametrize("name", PALETTES)
def test_control_edges(name):
    p = PALETTES[name]
    assert contrast(p["edge"], p["surface"]) >= 3 and contrast(p["edge"], p["bg"]) >= 3


def test_dark_palettes_are_the_same_in_auto_and_forced_mode():
    """The dark colours are written twice (system preference, and the Settings switch): they must not drift."""
    auto = re.search(r"@media \(prefers-color-scheme:dark\)\{(.*?)\}\}", CSS, re.S).group(1)
    for forced in (":root[data-theme=dark]", ":root[data-theme=dark][data-palette=paper]"):
        body = re.search(re.escape(forced) + r"\s*\{([^}]*)\}", CSS).group(1).strip()
        assert body in auto, forced
