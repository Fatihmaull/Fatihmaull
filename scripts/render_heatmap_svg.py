"""Render data/contributions.json as a 53-week calendar that reveals once."""

from __future__ import annotations

import json
from pathlib import Path

from svgutil import document, esc, motion_style
from theme import THEMES

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contributions.json"
OUT_DIR = ROOT / "assets"

CELL = 11
GAP = 3
STEP = CELL + GAP
LABEL_W = 36
PAD_X = 16
PAD_TOP = 28
FOOTER = 36


def color_for(level: int, theme: dict) -> str:
    palette = theme["heatmap"]
    return palette[max(0, min(level, len(palette) - 1))]


def render(data: dict, theme: dict) -> str:
    weeks = data["weeks"]
    width = 860
    grid_width = LABEL_W + len(weeks) * STEP
    offset_x = PAD_X + max(0, (width - PAD_X * 2 - grid_width) // 2)
    height = PAD_TOP + 7 * STEP + FOOTER
    parts = [
        motion_style(
            "\n".join(
                [
                    "@keyframes cell-in {",
                    "  from { opacity: 0; transform: translateY(-3px); }",
                    "  to { opacity: 1; transform: translateY(0); }",
                    "}",
                    ".cell { animation-name: cell-in; animation-duration: 0.35s; "
                    "animation-timing-function: ease; animation-fill-mode: both; }",
                ]
            ),
            False,
        ),
        f'<rect width="{width}" height="{height}" rx="12" fill="{theme["bg"]}"/>',
    ]

    cursor = 0
    for month in data["months"]:
        span = int(month["colspan"])
        x = offset_x + LABEL_W + cursor * STEP
        parts.append(
            f'<text x="{x}" y="18" fill="{theme["muted"]}" '
            f'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="12">'
            f'{esc(month["label"])}</text>'
        )
        cursor += span

    weekday_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for weekday, label in weekday_labels.items():
        y = PAD_TOP + weekday * STEP + CELL - 1
        parts.append(
            f'<text x="{offset_x}" y="{y}" fill="{theme["muted"]}" '
            f'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="11">{label}</text>'
        )

    for week_index, week in enumerate(weeks):
        for day_index, day in enumerate(week):
            if not day:
                continue
            x = offset_x + LABEL_W + week_index * STEP
            y = PAD_TOP + day_index * STEP
            delay = (week_index + day_index) * 0.012
            fill = color_for(int(day["level"]), theme)
            count = int(day["count"])
            noun = "contribution" if count == 1 else "contributions"
            tip = f'{count} {noun} on {day["date"]}' if count else f'No contributions on {day["date"]}'
            parts.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{fill}" style="animation-delay:{delay:.3f}s">'
                f"<title>{esc(tip)}</title></rect>"
            )

    legend_y = height - 16
    legend_colors = theme["heatmap"]
    legend_x = width - PAD_X - (len(legend_colors) * STEP) - 78
    parts.append(
        f'<text x="{legend_x}" y="{legend_y}" fill="{theme["muted"]}" '
        f'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="12">Less</text>'
    )
    for index, fill in enumerate(legend_colors):
        x = legend_x + 36 + index * STEP
        parts.append(
            f'<rect x="{x}" y="{legend_y - 10}" width="{CELL}" height="{CELL}" rx="2" fill="{fill}"/>'
        )
    more_x = legend_x + 36 + len(legend_colors) * STEP + 4
    parts.append(
        f'<text x="{more_x}" y="{legend_y}" fill="{theme["muted"]}" '
        f'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="12">More</text>'
    )
    total = int(data["total"])
    parts.append(
        f'<text x="{offset_x}" y="{legend_y}" fill="{theme["fg"]}" '
        f'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="13">'
        f"{total:,} contributions in the last year</text>"
    )
    return document(
        width,
        height,
        "\n".join(parts),
        f"{total:,} contributions in the last year",
        "GitHub contribution calendar for Fatihmaull. Cells reveal once on a diagonal, then hold.",
    )


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if not data.get("weeks"):
        raise SystemExit("contributions.json has no weeks")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key, theme in THEMES.items():
        name = "contrib-heatmap.svg" if key == "dark" else "contrib-heatmap-light.svg"
        path = OUT_DIR / name
        path.write_text(render(data, theme), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
