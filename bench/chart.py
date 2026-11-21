"""Draw docs/media/scale.svg from the lines of bench/scale.sh: time until the list is on screen, by catalog size.

python bench/chart.py bench/scale-results.jsonl docs/media/scale.svg
"""

import json
import sys
from pathlib import Path

SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0"
SERIES = {4: ("#2a78d6", "CPU slowed 4x, like a phone"), 1: ("#eb6834", "desktop CPU")}
W, H, LEFT, RIGHT, TOP, BOTTOM = 760, 400, 64, 96, 104, 52


def nice_step(top: float) -> float:
    """A round tick step that gives four to six ticks up to ``top``."""
    for step in (50, 100, 200, 250, 500, 1000, 2000, 5000):
        if top / step <= 6:
            return step
    return 10000


def table(rows: list[dict]) -> str:
    """The Markdown table of the README: one line per catalog, from the same result lines."""
    size = {r["file"]: r["html_bytes"] for r in rows if "html_bytes" in r and "file" in r}
    size.update({r["build"] + ".html": r["html_bytes"] for r in rows if "build" in r})
    runs = {(r["file"], r["cpuSlowdown"]): r for r in rows if "readyMs" in r}
    out = [
        '| Books | HTML file | Ready, 1x | Ready, 4x | Longest block after the first paint, 4x | Search "river", 4x | Sort by author, 4x | JS heap |',
        "|---|---|---|---|---|---|---|---|",
    ]
    for name in sorted({f for f, _ in runs}, key=lambda f: runs[f, 4]["books"]):
        a, b = runs[name, 1], runs[name, 4]
        kind = "real titles (Project Gutenberg)" if name.startswith("pg") else "synthetic"
        # Chrome reports a block only from 50 ms up
        block = f"{b['blockedMs']:.0f} ms" if b["blockedMs"] else "under 50 ms"
        out.append(
            f"| {b['books']:,} {kind} | {size[name] / 1e6:.2f} MB | {a['readyMs']:.0f} ms | {b['readyMs']:.0f} ms | "
            f"{block} | {b['wordMs']:.0f} ms | {b['sortAuthorMs']:.0f} ms | {b['heapMB']:.0f} MB |"
        )
    return "\n".join(out)


def main(src: str, out: str) -> None:
    rows = [json.loads(ln) for ln in Path(src).read_text(encoding="utf-8").splitlines() if ln.startswith("{")]
    points: dict[int, list[tuple[int, float]]] = {1: [], 4: []}
    for r in rows:
        if "readyMs" in r and r["file"].startswith("synth-"):
            points[r["cpuSlowdown"]].append((r["books"], r["readyMs"]))
    for p in points.values():
        p.sort()
    xmax = max(x for p in points.values() for x, _ in p)
    step = nice_step(max(y for p in points.values() for _, y in p))
    ymax = step * -(-max(y for p in points.values() for _, y in p) // step)

    def px(x: float) -> float:
        return LEFT + (W - LEFT - RIGHT) * x / xmax

    def py(y: float) -> float:
        return H - BOTTOM - (H - TOP - BOTTOM) * y / ymax

    def secs(ms: float) -> str:
        return f"{ms / 1000:.1f} s" if ms >= 1000 else f"{ms:.0f} ms"

    def key(
        k: int, x: float
    ) -> str:  # a legend entry: a short piece of the line, its marker, its name in ink
        colour, name = SERIES[k]
        return (
            f'<line x1="{x}" x2="{x + 26}" y1="76" y2="76" stroke="{colour}" stroke-width="2"/>'
            f'<circle cx="{x + 13}" cy="76" r="4.5" fill="{colour}" stroke="{SURFACE}" stroke-width="2"/>'
            f'<text x="{x + 34}" y="80" fill="{INK}">{name}</text>'
        )

    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'font-family="system-ui,-apple-system,Segoe UI,Roboto,sans-serif" font-size="13">',
        "<title>Time until the list is on screen, by catalog size</title>",
        "<desc>"
        + "; ".join(
            f"{SERIES[k][1]}: " + ", ".join(f"{x:,} books {secs(y)}" for x, y in points[k]) for k in (4, 1)
        )
        + "</desc>",
        f'<rect width="{W}" height="{H}" rx="12" fill="{SURFACE}"/>',
        f'<text x="{LEFT - 40}" y="32" font-size="17" font-weight="600" fill="{INK}">Time until the list is on screen</text>',
        f'<text x="{LEFT - 40}" y="52" fill="{MUTED}">one HTML file, opened from disk in headless Chrome; median of the runs</text>',
        key(4, LEFT - 40),
        key(1, LEFT + 190),
    ]
    y = 0.0
    while y <= ymax:
        s.append(
            f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{py(y):.1f}" y2="{py(y):.1f}" stroke="{GRID}" stroke-width="1"/>'
        )
        s.append(
            f'<text x="{LEFT - 10}" y="{py(y) + 4:.1f}" text-anchor="end" fill="{MUTED}">{f"{y / 1000:g} s" if y else "0"}</text>'
        )
        y += step
    for x in range(0, xmax + 1, 20000):
        s.append(
            f'<text x="{px(x):.1f}" y="{H - BOTTOM + 20}" text-anchor="middle" fill="{MUTED}">{x:,}</text>'
        )
    s.append(
        f'<text x="{(LEFT + W - RIGHT) / 2:.1f}" y="{H - 10}" text-anchor="middle" fill="{MUTED}">books in the catalog</text>'
    )
    for k in (1, 4):
        colour, name = SERIES[k]
        path = " ".join(
            f"{'M' if i == 0 else 'L'}{px(x):.1f},{py(y):.1f}" for i, (x, y) in enumerate(points[k])
        )
        s.append(f'<path d="{path}" fill="none" stroke="{colour}" stroke-width="2" stroke-linejoin="round"/>')
        for x, y in points[k]:
            s.append(
                f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="4.5" fill="{colour}" stroke="{SURFACE}" stroke-width="2"/>'
            )
        x, y = points[k][-1]  # the value at the line's end; the legend names the line
        s.append(
            f'<text x="{px(x) + 12:.1f}" y="{py(y) + 4:.1f}" font-weight="600" fill="{INK}">{secs(y)}</text>'
        )
    s.append("</svg>")
    Path(out).write_text("\n".join(s) + "\n", encoding="utf-8")
    print(table(rows))
    print(f"{out}: " + "; ".join(f"{SERIES[k][1]} {points[k]}" for k in (4, 1)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
