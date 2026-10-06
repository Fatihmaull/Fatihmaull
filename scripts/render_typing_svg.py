"""One-line terminal that types the headline once, then holds.

The same headline is also plain text in the README, so it can be copied
and still shows up when animation is disabled.
"""

from __future__ import annotations

import os
from pathlib import Path

from svgutil import document, motion_style
from theme import THEMES

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets"

PROMPT = "fatih@github ~ $ whoami"
ANSWER = "Forward Deployed Engineer & Researcher"
WIDTH = 860
HEIGHT = 86


def render(theme: dict, static: bool) -> str:
    body = "\n".join(
        [
            motion_style(
                "\n".join(
                    [
                        "@keyframes type-line {",
                        "  from { clip-path: inset(0 100% 0 0); }",
                        "  to { clip-path: inset(0 0 0 0); }",
                        "}",
                        f".typed {{ animation: type-line 1.8s steps({len(ANSWER)}, end) 0.2s both; }}",
                    ]
                ),
                static,
            ),
            f'<rect width="{WIDTH}" height="{HEIGHT}" rx="10" fill="{theme["bg"]}" stroke="{theme["border"]}"/>',
            f'<text x="16" y="34" fill="{theme["green"]}" '
            'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="16">'
            f"{PROMPT}</text>",
            '<g class="typed">',
            f'<text x="16" y="64" fill="{theme["fg"]}" '
            'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="16">'
            f"{ANSWER.replace('&', '&amp;')}"
            f'<tspan fill="{theme["cursor"]}"> ▌</tspan></text>',
            "</g>",
        ]
    )
    return document(
        WIDTH,
        HEIGHT,
        body,
        "whoami",
        "Types 'Forward Deployed Engineer & Researcher' once.",
    )


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key, theme in THEMES.items():
        name = "typing.svg" if key == "dark" else "typing-light.svg"
        path = OUT_DIR / name
        path.write_text(render(theme, static), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
