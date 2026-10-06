"""Turn a prepped grayscale portrait into a one-shot typing ASCII SVG.

The image is resampled to a character grid. Bright pixels become spaces
(the background) and dark pixels become denser glyphs. One gray is used
for every glyph so the portrait reads as a face instead of colored noise.

Each row wipes left to right once, with a block cursor on the leading edge,
then freezes. The SVG's resting state is the finished portrait.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from svgutil import document, esc, motion_style
from theme import THEMES

RAMP = " .`:-=+*cs#%@"
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets"

# Characters are roughly twice as tall as they are wide, so a square photo
# needs about half as many rows as columns to stay square on screen.
COLS = 72
CHAR_W = 8
CHAR_H = 16


def resample(gray: Image.Image, cols: int) -> np.ndarray:
    width, height = gray.size
    rows = max(16, round(cols * (height / width) * (CHAR_W / CHAR_H)))
    small = gray.resize((cols, rows), Image.Resampling.LANCZOS)
    return np.asarray(small, dtype=np.float32)


def to_glyphs(pixels: np.ndarray) -> list[str]:
    flat = pixels.reshape(-1)
    low, high = np.percentile(flat, [4, 96])
    if high <= low:
        high = low + 1
    stretched = np.clip((pixels - low) / (high - low), 0, 1)
    # Gamma > 1 pushes midtones toward the sparse end so the background
    # stays empty and the face keeps its darker marks.
    stretched = stretched ** 1.15
    indexes = np.clip((1.0 - stretched) * (len(RAMP) - 1), 0, len(RAMP) - 1).astype(int)
    rows = []
    for row in indexes:
        rows.append("".join(RAMP[i] for i in row))
    return rows


def render(rows: list[str], theme: dict, static: bool) -> str:
    cols = max(len(row) for row in rows)
    width = cols * CHAR_W + 16
    height = len(rows) * CHAR_H + 16
    delay_step = 0.045
    wipe = 0.42
    parts = [
        motion_style(
            "\n".join(
                [
                    "@keyframes ascii-wipe {",
                    "  from { clip-path: inset(0 100% 0 0); }",
                    "  to { clip-path: inset(0 0 0 0); }",
                    "}",
                    ".ascii-line {",
                    "  animation-name: ascii-wipe;",
                    f"  animation-duration: {wipe}s;",
                    "  animation-timing-function: linear;",
                    "  animation-fill-mode: both;",
                    "}",
                ]
            ),
            static,
        ),
        f'<rect width="{width}" height="{height}" fill="{theme["bg"]}"/>',
    ]
    travel = cols * CHAR_W
    for index, row in enumerate(rows):
        y = 16 + index * CHAR_H
        delay = index * delay_step
        style = "" if static else f' style="animation-delay:{delay:.3f}s"'
        cursor = ""
        if not static:
            cursor = (
                f'<rect x="0" y="1" width="{CHAR_W - 1}" height="{CHAR_H - 2}" '
                f'fill="{theme["cursor"]}" opacity="0">'
                f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.86;1" '
                f'dur="{wipe}s" begin="{delay:.3f}s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="0 0" to="{travel} 0" dur="{wipe}s" begin="{delay:.3f}s" fill="freeze"/>'
                f"</rect>"
            )
        parts.append(
            f'<g transform="translate(8 {y})">'
            f'<g class="ascii-line"{style}>'
            f'<text x="0" y="{CHAR_H - 3}" fill="{theme["ascii"]}" '
            f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
            f'font-size="14">{esc(row)}</text></g>'
            f"{cursor}"
            f"</g>"
        )
    filled = sum(1 for row in rows for ch in row if ch != " ")
    return document(
        width,
        height,
        "\n".join(parts),
        "ASCII portrait of Fatih Maulana",
        f"Monochrome ASCII portrait, {cols} by {len(rows)}, {filled} marks. Types once, then holds.",
    )


def build(prepped: Path, static: bool) -> None:
    gray = Image.open(prepped).convert("L")
    rows = to_glyphs(resample(gray, COLS))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key, theme in THEMES.items():
        name = "fatih-ascii.svg" if key == "dark" else "fatih-ascii-light.svg"
        path = OUT_DIR / name
        path.write_text(render(rows, theme, static), encoding="utf-8")
        print(f"wrote {path} rows={len(rows)} cols={len(rows[0])}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: make_ascii_svg.py PREPPED.png")
    static = os.environ.get("STATIC") == "1"
    build(Path(sys.argv[1]), static)


if __name__ == "__main__":
    main()
