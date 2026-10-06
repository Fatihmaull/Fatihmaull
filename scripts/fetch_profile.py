"""Scrape public profile counts and GitHub achievements.

Used by the self-hosted trophy card. Exits with an error if the followers
count or repository counter cannot be read, so a layout change cannot
replace the committed SVG with blanks.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "profile.json"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


def _number(text: str) -> int | None:
    match = re.search(r"[\d,]+", text)
    if not match:
        return None
    return int(match.group(0).replace(",", ""))


def parse_profile(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    followers = None
    following = None
    for span in soup.select("span.text-bold"):
        blob = " ".join(span.parent.get_text(" ", strip=True).split()).lower()
        number = _number(span.get_text(" ", strip=True))
        if number is None:
            continue
        if "follower" in blob and followers is None:
            followers = number
        elif "following" in blob and following is None:
            following = number

    public_repos = None
    for span in soup.select("span.Counter"):
        blob = " ".join(span.parent.get_text(" ", strip=True).split()).lower()
        if blob.startswith("repositories"):
            public_repos = _number(span.get_text(" ", strip=True))
            break

    name_node = soup.select_one("span.p-name")
    location_node = soup.select_one('[itemprop="homeLocation"]')
    achievements = []
    seen = set()
    for anchor in soup.select('a[href*="achievement="]'):
        match = re.search(r"achievement=([^&]+)", anchor.get("href", ""))
        if not match:
            continue
        slug = match.group(1)
        if slug in seen:
            continue
        seen.add(slug)
        image = anchor.find("img")
        alt = image.get("alt", "") if image else ""
        name = alt.split(":", 1)[1].strip() if ":" in alt else slug
        tier = "default"
        count = None
        badge = anchor.select_one("[class*='achievement-tier-label--']")
        if badge is not None:
            for cls in badge.get("class") or []:
                if cls.startswith("achievement-tier-label--"):
                    tier = cls.split("--", 1)[1]
            count_match = re.search(r"x\s*(\d+)", badge.get_text(" ", strip=True))
            if count_match:
                count = int(count_match.group(1))
        achievements.append({"slug": slug, "name": name, "tier": tier, "count": count})

    if followers is None or public_repos is None:
        raise SystemExit("profile page did not include followers and repository counts")

    return {
        "name": name_node.get_text(" ", strip=True) if name_node else "",
        "location": location_node.get_text(" ", strip=True) if location_node else "",
        "followers": followers,
        "following": following,
        "public_repos": public_repos,
        "achievements": achievements,
    }


def fetch(user: str) -> str:
    response = requests.get(
        f"https://github.com/{user}",
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def main() -> None:
    user = os.environ.get("GH_PROFILE_USER", "Fatihmaull")
    parsed = parse_profile(fetch(user))
    payload = {
        "user": user,
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        **parsed,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT} followers={payload['followers']} repos={payload['public_repos']} "
        f"achievements={len(payload['achievements'])}"
    )


if __name__ == "__main__":
    main()
