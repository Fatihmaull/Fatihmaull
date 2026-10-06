"""Download the public contribution calendar and write data/contributions.json.

GitHub serves the same markup the profile page uses at
https://github.com/users/<user>/contributions. No token and no GraphQL.
The script exits with an error when the calendar is missing so a later
render step cannot replace a good SVG with an empty one.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "contributions.json"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


def parse_count(tooltip: str) -> int:
    text = " ".join(tooltip.split())
    if text.lower().startswith("no contribution"):
        return 0
    match = re.search(r"([\d,]+)\s+contribution", text, flags=re.IGNORECASE)
    if not match:
        return 0
    return int(match.group(1).replace(",", ""))


def parse_header_total(soup: BeautifulSoup) -> int | None:
    heading = soup.select_one("h2#js-contribution-activity-description") or soup.find("h2")
    if heading is None:
        return None
    text = " ".join(heading.get_text(" ", strip=True).split())
    match = re.search(r"([\d,]+)\s+contributions?\s+in the last year", text, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def parse_calendar(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.ContributionCalendar-grid")
    if table is None:
        raise SystemExit("contribution calendar table not found")

    months = []
    for cell in table.select("thead td.ContributionCalendar-label"):
        short = cell.select_one("span[aria-hidden='true']")
        label = short.get_text(strip=True) if short else cell.get_text(" ", strip=True)
        months.append({"label": label, "colspan": int(cell.get("colspan") or 1)})

    weekday_rows = []
    for tr in table.select("tbody tr"):
        days = [
            td
            for td in tr.find_all("td")
            if "ContributionCalendar-day" in (td.get("class") or [])
        ]
        if days:
            weekday_rows.append(days)
    if len(weekday_rows) != 7:
        raise SystemExit(f"expected 7 weekday rows, found {len(weekday_rows)}")

    week_count = max(len(row) for row in weekday_rows)
    weeks = []
    flat = []
    for week_index in range(week_count):
        column = []
        for weekday in range(7):
            row = weekday_rows[weekday]
            if week_index >= len(row):
                column.append(None)
                continue
            cell = row[week_index]
            day = cell.get("data-date")
            if not day:
                column.append(None)
                continue
            tooltip = soup.select_one(f'tool-tip[for="{cell.get("id")}"]')
            count = parse_count(tooltip.get_text(" ", strip=True) if tooltip else "")
            entry = {
                "date": day,
                "count": count,
                "level": int(cell.get("data-level") or 0),
            }
            column.append(entry)
            flat.append(entry)
        weeks.append(column)

    if not flat:
        raise SystemExit("contribution calendar contained 0 days")

    # GitHub sometimes omits the label for the current partial month.
    labeled = sum(month["colspan"] for month in months)
    if labeled < len(weeks):
        label = ""
        for day in weeks[labeled]:
            if day:
                label = date.fromisoformat(day["date"]).strftime("%b")
                break
        if label:
            months.append({"label": label, "colspan": len(weeks) - labeled})

    header_total = parse_header_total(soup)
    summed = sum(day["count"] for day in flat)
    return {
        "weeks": weeks,
        "months": months,
        "days": flat,
        "header_total": header_total,
        "summed_total": summed,
    }


def streaks(days: list[dict]) -> dict:
    by_date = {date.fromisoformat(day["date"]): day["count"] for day in days}
    ordered = sorted(by_date)
    longest = 0
    run = 0
    previous = None
    for current in ordered:
        if by_date[current] > 0 and previous is not None and current - previous == timedelta(days=1):
            run += 1
        elif by_date[current] > 0:
            run = 1
        else:
            run = 0
        longest = max(longest, run)
        previous = current

    today = datetime.now(timezone.utc).date()
    cursor = today if by_date.get(today, 0) > 0 else today - timedelta(days=1)
    current_streak = 0
    while by_date.get(cursor, 0) > 0:
        current_streak += 1
        cursor -= timedelta(days=1)

    best = max(days, key=lambda day: (day["count"], day["date"]))
    monthly: dict[str, int] = {}
    for day in days:
        monthly[day["date"][:7]] = monthly.get(day["date"][:7], 0) + day["count"]
    best_month = max(monthly.items(), key=lambda item: item[1])
    return {
        "current_streak": current_streak,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "best_month": {"month": best_month[0], "count": best_month[1]},
        "monthly": [{"month": key, "count": monthly[key]} for key in sorted(monthly)],
    }


def fetch(user: str) -> str:
    url = f"https://github.com/users/{user}/contributions"
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def main() -> None:
    user = os.environ.get("GH_PROFILE_USER", "Fatihmaull")
    parsed = parse_calendar(fetch(user))
    if len(parsed["days"]) < 300:
        raise SystemExit(f"calendar too short ({len(parsed['days'])} days); refusing to overwrite")
    summary = streaks(parsed["days"])
    total = parsed["header_total"] if parsed["header_total"] is not None else parsed["summed_total"]
    payload = {
        "user": user,
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "total": total,
        "total_source": "header" if parsed["header_total"] is not None else "sum",
        "summed_total": parsed["summed_total"],
        "current_streak": summary["current_streak"],
        "longest_streak": summary["longest_streak"],
        "best_day": summary["best_day"],
        "best_month": summary["best_month"],
        "monthly": summary["monthly"],
        "months": parsed["months"],
        "weeks": parsed["weeks"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT} days={len(parsed['days'])} total={total} "
        f"streak={summary['current_streak']}/{summary['longest_streak']} "
        f"best={summary['best_day']}"
    )


if __name__ == "__main__":
    main()
