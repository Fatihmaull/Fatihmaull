"""Prepare a portrait for ASCII conversion.

Steps, matching the profile-readme technique:
1. Cut the subject out of the background.
2. Lift local contrast so a flat photo still has highlights and shadows.
3. Composite onto white so the empty background maps to the blank end of the
   ASCII ramp.

The raw photo is not committed. Pass an input path and an output path.

    python scripts/prep_photo.py source.jpg assets/source-prepped.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def remove_background(image: Image.Image) -> Image.Image:
    # u2net keeps a person in front of a busy wall. The library default
    # (bria-rmbg) treated this avatar's concrete background as the subject.
    from rembg import new_session, remove

    session = new_session("u2net")
    cut = remove(image.convert("RGBA"), session=session)
    if not isinstance(cut, Image.Image):
        cut = Image.open(cut)
    return cut.convert("RGBA")


def crop_to_subject(image: Image.Image, pad_ratio: float = 0.04) -> Image.Image:
    alpha = np.array(image.split()[-1])
    ys, xs = np.where(alpha > 24)
    if len(xs) == 0:
        return image
    pad_x = max(4, int((xs.max() - xs.min()) * pad_ratio))
    pad_y = max(4, int((ys.max() - ys.min()) * pad_ratio))
    left = max(0, int(xs.min()) - pad_x)
    top = max(0, int(ys.min()) - pad_y)
    right = min(image.width, int(xs.max()) + pad_x + 1)
    bottom = min(image.height, int(ys.max()) + pad_y + 1)
    return image.crop((left, top, right, bottom))


def composite_on_white(image: Image.Image) -> Image.Image:
    rgba = np.array(image.convert("RGBA"))
    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3]
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    lightness, green_red, yellow_blue = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    boosted = clahe.apply(lightness)
    # Keep the boost on the subject only; the cleared background stays neutral.
    mask = alpha > 24
    lightness = np.where(mask, boosted, lightness)
    merged = cv2.merge((lightness, green_red, yellow_blue))
    rgb = cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)
    alpha_f = (alpha.astype(np.float32) / 255.0)[..., None]
    white = np.full_like(rgb, 255, dtype=np.float32)
    composed = rgb.astype(np.float32) * alpha_f + white * (1.0 - alpha_f)
    gray = cv2.cvtColor(composed.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    edge = np.concatenate([gray[:6, :].ravel(), gray[-6:, :].ravel()])
    if float(edge.mean()) < 200:
        raise SystemExit("background was not cleared; refusing to write the portrait")
    return Image.fromarray(gray, mode="L")


def prep(src: Path, dst: Path) -> None:
    image = Image.open(src)
    cut = remove_background(image)
    cut = crop_to_subject(cut)
    gray = composite_on_white(cut)
    dst.parent.mkdir(parents=True, exist_ok=True)
    gray.save(dst)
    print(f"wrote {dst} ({gray.width}x{gray.height})")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: prep_photo.py INPUT OUTPUT.png")
    prep(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()
