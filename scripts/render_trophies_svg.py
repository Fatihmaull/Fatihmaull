"""Self-hosted trophy row.

Replaces github-profile-trophy, which returns HTTP 402. Numbers come from
data/profile.json and data/contributions.json. Career cards are the public
awards on https://fatihmaull.github.io and the Porto Tracker brief. GitHub
achievement names and tiers are scraped, not invented.
"""

from __future__ import annotations

import json
from pathlib import Path

from svgutil import document, esc, motion_style
from theme import THEMES

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data" / "profile.json"
CONTRIB = ROOT / "data" / "contributions.json"
OUT_DIR = ROOT / "assets"

# Facts stated on the portfolio and in the profile brief. Not ranks.
CAREER = [
    {"title": "Gold medal", "value": "ICYMS 2026", "note": "HalalChain"},
    {"title": "SCF Instaward", "value": "Sep 2026", "note": "Evergreen"},
    {"title": "Ambassador", "value": "Stellar", "note": "Aug 2026–now"},
    {"title": "First author", "value": "PQC", "note": "Blockchain Kaigi 2026"},
]


def tier_color(tier: str, theme: dict) -> str:
    return {
        "gold": theme["gold"],
        "silver": theme["silver"],
        "bronze": theme["bronze"],
    }.get(tier, theme["blue"])


def trophy_icon(x: int, y: int, fill: str) -> str:
    return (
        f'<g transform="translate({x} {y})" fill="{fill}">'
        '<path d="M6 1h12v6.2c0 3.6-2.4 6.2-6 6.6-3.6-.4-6-3-6-6.6V1z"/>'
        f'<path d="M6 3H2.2C1.2 3 1.2 8 3.4 8H6" fill="none" stroke="{fill}" stroke-width="1.4"/>'
        f'<path d="M18 3h3.8c1 0 1 5-1.2 5H18" fill="none" stroke="{fill}" stroke-width="1.4"/>'
        '<rect x="10.2" y="14" width="3.6" height="4"/>'
        '<rect x="7" y="18" width="10" height="2.2" rx="0.4"/>'
        "</g>"
    )


def cards_for(profile: dict, contrib: dict, theme: dict) -> list[dict]:
    cards = [
        {
            "title": "Contributions",
            "value": f"{int(contrib['total']):,}",
            "note": "last year",
            "accent": theme["cyan"],
        },
        {
            "title": "Current streak",
            "value": str(int(contrib["current_streak"])),
            "note": "days",
            "accent": theme["green"],
        },
        {
            "title": "Longest streak",
            "value": str(int(contrib["longest_streak"])),
            "note": "days",
            "accent": theme["purple"],
        },
        {
            "title": "Followers",
            "value": str(int(profile["followers"])),
            "note": "GitHub",
            "accent": theme["blue"],
        },
        {
            "title": "Repositories",
            "value": str(int(profile["public_repos"])),
            "note": "public",
            "accent": theme["orange"],
        },
    ]
    for item in CAREER:
        cards.append({**item, "accent": theme["gold"]})
    for achievement in profile.get("achievements", []):
        count = achievement.get("count")
        cards.append(
            {
                "title": achievement["name"],
                "value": f"x{count}" if count else achievement["tier"].title(),
                "note": achievement["tier"],
                "accent": tier_color(achievement.get("tier", "default"), theme),
            }
        )
    return cards


def render(profile: dict, contrib: dict, theme: dict) -> str:
    cards = cards_for(profile, contrib, theme)
    columns = 4
    card_w = 196
    card_h = 92
    gap = 12
    pad = 18
    rows = (len(cards) + columns - 1) // columns
    width = 860
    height = 46 + rows * (card_h + gap) + 8
    parts = [
        motion_style(
            "\n".join(
                [
                    "@keyframes trophy-in {",
                    "  from { opacity: 0; transform: translateY(6px); }",
                    "  to { opacity: 1; transform: translateY(0); }",
                    "}",
                    ".trophy { animation-name: trophy-in; animation-duration: 0.4s; "
                    "animation-timing-function: ease; animation-fill-mode: both; }",
                ]
            ),
            False,
        ),
        f'<rect width="{width}" height="{height}" rx="12" fill="{theme["bg"]}"/>',
        f'<text x="{pad}" y="28" fill="{theme["yellow"]}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="13">'
        f"fatih@github ~ $ cat achievements.txt</text>",
    ]
    for index, card in enumerate(cards):
        col = index % columns
        row = index // columns
        x = pad + col * (card_w + gap)
        y = 42 + row * (card_h + gap)
        delay = 0.08 + index * 0.06
        parts.append(
            f'<g class="trophy" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="10" '
            f'fill="{theme["bg_elevated"]}" stroke="{card["accent"]}"/>'
            f"{trophy_icon(x + 12, y + 14, card['accent'])}"
            f'<text x="{x + 44}" y="{y + 28}" fill="{theme["muted"]}" '
            f'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="12">'
            f"{esc(card['title'])}</text>"
            f'<text x="{x + 14}" y="{y + 58}" fill="{theme["fg"]}" '
            f'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="18" font-weight="700">'
            f"{esc(card['value'])}</text>"
            f'<text x="{x + 14}" y="{y + 78}" fill="{card["accent"]}" '
            f'font-family="ui-sans-serif, Segoe UI, sans-serif" font-size="12">'
            f"{esc(card['note'])}</text>"
            f"</g>"
        )
    summary = ", ".join(f"{card['title']} {card['value']}" for card in cards)
    return document(
        width,
        height,
        "\n".join(parts),
        "Achievements",
        summary,
    )


def main() -> None:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    contrib = json.loads(CONTRIB.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key, theme in THEMES.items():
        name = "trophies.svg" if key == "dark" else "trophies-light.svg"
        path = OUT_DIR / name
        path.write_text(render(profile, contrib, theme), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
