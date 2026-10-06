"""Draw the contribution calendar once, with a snake that crosses it a single time.

The resting frame is the full calendar. The snake is an overlay, so the
image still makes sense where SVG animation does not run.
"""

from __future__ import annotations

import json
from pathlib import Path

from svgutil import document, esc
from theme import THEMES

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contributions.json"
OUT_DIR = ROOT / "assets"

CELL = 10
GAP = 3
STEP = CELL + GAP
LABEL_W = 8
PAD = 18


def color_for(level: int, theme: dict) -> str:
    palette = theme["heatmap"]
    return palette[max(0, min(level, len(palette) - 1))]


def cell_center(week_index: int, day_index: int, offset_x: int) -> tuple[float, float]:
    x = offset_x + LABEL_W + week_index * STEP + CELL / 2
    y = PAD + day_index * STEP + CELL / 2
    return x, y


def render(data: dict, theme: dict) -> str:
    weeks = data["weeks"]
    width = 860
    grid_h = 7 * STEP
    height = PAD + grid_h + 28
    grid_w = LABEL_W + len(weeks) * STEP
    offset_x = max(PAD, (width - grid_w) // 2)
    parts = [f'<rect width="{width}" height="{height}" rx="12" fill="{theme["bg"]}"/>']

    points: list[tuple[float, float]] = []
    for day_index in range(7):
        week_indexes = range(len(weeks)) if day_index % 2 == 0 else range(len(weeks) - 1, -1, -1)
        for week_index in week_indexes:
            day = weeks[week_index][day_index] if week_index < len(weeks) else None
            if not day:
                continue
            x = offset_x + LABEL_W + week_index * STEP
            y = PAD + day_index * STEP
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{color_for(int(day["level"]), theme)}">'
                f"<title>{esc(day['date'])}</title></rect>"
            )
            points.append(cell_center(week_index, day_index, offset_x))

    if len(points) < 2:
        raise SystemExit("not enough contribution cells to draw a snake")

    path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points)
    # A short snake crosses the grid once and fades. The calendar itself is the
    # resting image, so the profile is not left with a line drawn over the year.
    for index in range(8):
        radius = 4.4 - index * 0.28
        begin = index * 0.06
        fill = theme["orange"] if index == 0 else theme["purple"]
        parts.append(
            f'<circle cx="0" cy="0" r="{radius:.2f}" fill="{fill}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.03;0.88;1" '
            f'dur="6.4s" begin="{begin:.2f}s" fill="freeze"/>'
            f'<animateMotion dur="6s" begin="{begin:.2f}s" fill="freeze" path="{path}"/>'
            "</circle>"
        )
    parts.append(
        f'<text x="{offset_x}" y="{height - 10}" fill="{theme["muted"]}" '
        f'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="12">'
        f"snake crosses the year once, then holds</text>"
    )
    total = int(data["total"])
    return document(
        width,
        height,
        "\n".join(parts),
        f"Contribution snake, {total:,} contributions in the last year",
        "The contribution calendar with a snake that travels the grid a single time and then stops.",
    )


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key, theme in THEMES.items():
        name = "snake.svg" if key == "dark" else "snake-light.svg"
        path = OUT_DIR / name
        path.write_text(render(data, theme), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
