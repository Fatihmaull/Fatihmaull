"""Capsule-style terminal banner.

Drawn locally and committed, so the profile does not depend on a live
capsule-render server. The wave eases in once and then holds.
"""

from __future__ import annotations

import os
from pathlib import Path

from svgutil import document, motion_style
from theme import THEMES

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets"
WIDTH = 900
HEIGHT = 220


def waves(theme: dict) -> str:
    # Waves stay in the bottom band so the name never sits on top of them.
    return "\n".join(
        [
            (
                f'<path fill="{theme["purple"]}" opacity="0.55" '
                'd="M0 168 C 140 148, 240 196, 380 170 S 640 146, 900 178 L 900 220 L 0 220 Z"/>'
            ),
            (
                f'<path fill="{theme["blue"]}" opacity="0.7" '
                'd="M0 184 C 160 166, 300 208, 460 186 S 720 160, 900 192 L 900 220 L 0 220 Z"/>'
            ),
            (
                f'<path fill="{theme["cyan"]}" opacity="0.9" '
                'd="M0 198 C 180 186, 340 214, 520 198 S 760 184, 900 206 L 900 220 L 0 220 Z"/>'
            ),
        ]
    )


def render(theme: dict, static: bool) -> str:
    body = "\n".join(
        [
            motion_style(
                "\n".join(
                    [
                        "@keyframes banner-in {",
                        "  from { opacity: 0; transform: translateY(8px); }",
                        "  to { opacity: 1; transform: translateY(0); }",
                        "}",
                        "@keyframes wave-in {",
                        "  from { opacity: 0; transform: translateY(16px); }",
                        "  to { opacity: 1; transform: translateY(0); }",
                        "}",
                        ".banner-copy { animation: banner-in 0.7s ease both; }",
                        ".banner-wave { animation: wave-in 0.9s ease 0.15s both; }",
                    ]
                ),
                static,
            ),
            "<defs>",
            '<linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">',
            f'<stop offset="0" stop-color="{theme["bg"]}"/>',
            f'<stop offset="0.55" stop-color="{theme["bg_elevated"]}"/>',
            f'<stop offset="1" stop-color="{theme["bg"]}"/>',
            "</linearGradient>",
            '<clipPath id="capsule"><rect width="900" height="220" rx="28"/></clipPath>',
            "</defs>",
            '<g clip-path="url(#capsule)">',
            f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sky)"/>',
            f'<g class="banner-wave">{waves(theme)}</g>',
            '<g class="banner-copy">',
            f'<circle cx="28" cy="28" r="6" fill="{theme["red"]}"/>',
            f'<circle cx="48" cy="28" r="6" fill="{theme["yellow"]}"/>',
            f'<circle cx="68" cy="28" r="6" fill="{theme["green"]}"/>',
            f'<text x="88" y="33" fill="{theme["muted"]}" '
            'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14">'
            "fatih@github ~ $</text>",
            f'<rect x="150" y="52" width="600" height="86" rx="14" fill="{theme["bg"]}" opacity="0.82"/>',
            f'<text x="450" y="90" text-anchor="middle" fill="{theme["fg"]}" '
            'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="36" font-weight="700">'
            "Fatih Maulana</text>",
            f'<text x="450" y="120" text-anchor="middle" fill="{theme["cyan"]}" '
            'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="16">'
            "Forward Deployed Engineer &amp; Researcher</text>",
            "</g>",
            "</g>",
        ]
    )
    return document(
        WIDTH,
        HEIGHT,
        body,
        "Fatih Maulana",
        "Terminal banner. Forward Deployed Engineer and Researcher.",
    )


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key, theme in THEMES.items():
        name = "header.svg" if key == "dark" else "header-light.svg"
        path = OUT_DIR / name
        path.write_text(render(theme, static), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
