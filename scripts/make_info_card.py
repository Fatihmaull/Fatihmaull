"""Neofetch-style identity card.

The lines are the story the contribution graph cannot tell. Facts come from
the portfolio site and the Porto Tracker brief. Set STATIC=1 to emit a
frozen frame with no animation, for local previews.
"""

from __future__ import annotations

import os
from pathlib import Path

from svgutil import document, esc, motion_style
from theme import THEMES

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets"

WIDTH = 490
# Monospace 13px is about 8px per glyph. The value column starts at x=122
# and must end before the 16px right padding: (490 - 122 - 16) / 8 = 44.
WRAP = 40
VALUE_X = 122

LINES = [
    (
        "Role",
        "Forward Deployed Engineer & Researcher",
        "cyan",
    ),
    (
        "Now",
        "FDE & PO @ Daemon Protocol · PM Intern @ Ibunda.id · Stellar Ambassador · Lead, Superteam Campus Club · Founder, FOCU Studio",
        "green",
    ),
    (
        "Prev",
        "City Builders Lead @ BlockDev.ID · GRC Member @ Wo-Men in Tech Security · Technical Writer & Analyst @ Ibunda.id",
        "purple",
    ),
    (
        "Edu",
        "Informatics Engineering @ UIN Sunan Gunung Djati Bandung (Summa Cum Laude track) · B.CS exchange @ Universiti Utara Malaysia",
        "blue",
    ),
    (
        "Focus",
        "Cybersecurity · Blockchain · Quantum Computing · Quant Finance",
        "yellow",
    ),
    (
        "Stack",
        "Rust · Solidity · Python · TypeScript · Next.js · Soroban · Solana · Base",
        "orange",
    ),
    (
        "Highlights",
        "SCF Instaward (Evergreen, Sep 2026) · Gold Medal ICYMS 2026 (HalalChain) · First-author post-quantum cryptography research",
        "red",
    ),
    (
        "Based",
        "Bandung, Indonesia",
        "cyan",
    ),
]


def wrap(text: str, limit: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if len(trial) <= limit:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def render(theme: dict, static: bool) -> str:
    wrapped = [(label, wrap(value, WRAP), color) for label, value, color in LINES]
    line_h = 20
    body_lines = sum(len(lines) for _, lines, _ in wrapped)
    height = 48 + body_lines * line_h + 18
    parts = [
        motion_style(
            "\n".join(
                [
                    "@keyframes row-in {",
                    "  from { opacity: 0; transform: translateX(-8px); }",
                    "  to { opacity: 1; transform: translateX(0); }",
                    "}",
                    ".row { animation-name: row-in; animation-duration: 0.45s; "
                    "animation-timing-function: ease; animation-fill-mode: both; }",
                ]
            ),
            static,
        ),
        f'<rect width="{WIDTH}" height="{height}" rx="12" fill="{theme["bg"]}" stroke="{theme["border"]}"/>',
        f'<rect width="{WIDTH}" height="36" rx="12" fill="{theme["bg_elevated"]}"/>',
        f'<rect y="24" width="{WIDTH}" height="12" fill="{theme["bg_elevated"]}"/>',
        f'<circle cx="18" cy="18" r="5" fill="{theme["red"]}"/>',
        f'<circle cx="34" cy="18" r="5" fill="{theme["yellow"]}"/>',
        f'<circle cx="50" cy="18" r="5" fill="{theme["green"]}"/>',
        f'<text x="68" y="23" fill="{theme["fg"]}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="13">'
        f"fatih@github ~ $ neofetch</text>",
    ]
    y = 58
    font = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    for index, (label, lines, color_name) in enumerate(wrapped):
        color = theme[color_name]
        delay = "" if static else f' style="animation-delay:{0.15 + index * 0.12:.2f}s"'
        row = [f'<g class="row"{delay}>']
        for line_index, line in enumerate(lines):
            if line_index == 0:
                row.append(
                    f'<text x="16" y="{y}" fill="{color}" font-family="{font}" '
                    f'font-size="13" font-weight="700">{esc(label)}</text>'
                )
            row.append(
                f'<text x="{VALUE_X}" y="{y}" fill="{theme["fg"]}" font-family="{font}" '
                f'font-size="13">{esc(line)}</text>'
            )
            y += line_h
        row.append("</g>")
        parts.append("".join(row))
        y += 4
    height = y + 8
    # The header rects were drawn with the previous height estimate. Rebuild
    # the background now that wrapping is known by rewriting the opening rect.
    parts[1] = (
        f'<rect width="{WIDTH}" height="{height}" rx="12" fill="{theme["bg"]}" stroke="{theme["border"]}"/>'
    )
    return document(
        WIDTH,
        height,
        "\n".join(parts),
        "Fatih Maulana",
        "Forward Deployed Engineer and Researcher in Bandung. "
        "Role, current work, previous roles, education, focus, stack, and highlights.",
    )


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key, theme in THEMES.items():
        name = "info-card.svg" if key == "dark" else "info-card-light.svg"
        path = OUT_DIR / name
        path.write_text(render(theme, static), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
