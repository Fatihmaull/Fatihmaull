"""Render a self-hosted streak card from data/contributions.json.

This sits beside the github-readme-stats images. It only shows numbers
computed from the public calendar, so it keeps working when that service
is down.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from svgutil import document, esc, motion_style
from theme import THEMES

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contributions.json"
OUT_DIR = ROOT / "assets"


def pretty_day(iso: str) -> str:
    return date.fromisoformat(iso).strftime("%d %b %Y").lstrip("0")


def render(data: dict, theme: dict) -> str:
    width, height = 860, 168
    cards = [
        ("Contributions", f"{int(data['total']):,}", "last year"),
        ("Current streak", str(int(data["current_streak"])), "days"),
        ("Longest streak", str(int(data["longest_streak"])), "days"),
        ("Best day", f"{int(data['best_day']['count']):,}", pretty_day(data["best_day"]["date"])),
    ]
    gap = 14
    card_w = (width - 32 - gap * (len(cards) - 1)) // len(cards)
    parts = [
        motion_style(
            "\n".join(
                [
                    "@keyframes stat-in {",
                    "  from { opacity: 0; transform: translateY(8px); }",
                    "  to { opacity: 1; transform: translateY(0); }",
                    "}",
                    ".stat { animation-name: stat-in; animation-duration: 0.45s; "
                    "animation-timing-function: ease; animation-fill-mode: both; }",
                ]
            ),
            False,
        ),
        f'<rect width="{width}" height="{height}" rx="12" fill="{theme["bg"]}"/>',
        f'<text x="24" y="28" fill="{theme["green"]}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="13">'
        f"fatih@github ~ $ ./streak.sh</text>",
    ]
    accents = [theme["cyan"], theme["green"], theme["purple"], theme["orange"]]
    for index, (label, value, note) in enumerate(cards):
        x = 16 + index * (card_w + gap)
        delay = 0.12 + index * 0.1
        parts.append(
            f'<g class="stat" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x}" y="44" width="{card_w}" height="104" rx="10" fill="{theme["bg_elevated"]}" '
            f'stroke="{theme["border"]}"/>'
            f'<rect x="{x}" y="44" width="4" height="104" rx="2" fill="{accents[index]}"/>'
            f'<text x="{x + 16}" y="72" fill="{theme["muted"]}" '
            f'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="13">{esc(label)}</text>'
            f'<text x="{x + 16}" y="108" fill="{theme["fg"]}" '
            f'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="32" font-weight="700">'
            f"{esc(value)}</text>"
            f'<text x="{x + 16}" y="130" fill="{accents[index]}" '
            f'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="13">{esc(note)}</text>'
            f"</g>"
        )
    return document(
        width,
        height,
        "\n".join(parts),
        "Contribution streaks",
        "Current streak, longest streak, best day, and last-year total from the public contribution calendar.",
    )


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    for key in ("total", "current_streak", "longest_streak", "best_day"):
        if key not in data:
            raise SystemExit(f"contributions.json missing {key}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key, theme in THEMES.items():
        name = "stats.svg" if key == "dark" else "stats-light.svg"
        path = OUT_DIR / name
        path.write_text(render(data, theme), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
