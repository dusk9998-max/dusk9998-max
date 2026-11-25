"""Owner-authenticated aggregate activity -> an original folded-paper dragon."""
import argparse
import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

QUERY = """query($from: DateTime!, $to: DateTime!) {
  viewer { login createdAt contributionsCollection(from:$from, to:$to) {
    contributionCalendar { totalContributions weeks {
      contributionDays { date contributionCount }
    } }
  } }
}"""


def require_scope(scopes: str):
    if not {"read:user", "user"} & {s.strip() for s in scopes.split(",")}:
        raise ValueError("DRAGON_ACTIVITY_TOKEN requires read:user (classic PAT); no public-only fallback.")


def require_owner(viewer: dict, login: str):
    if viewer["login"].lower() != login.lower():
        raise ValueError("Activity credential must belong to the profile owner.")


def api(query: str, variables: dict, token: str) -> dict:
    if not token:
        raise ValueError("Add the DRAGON_ACTIVITY_TOKEN Actions secret first.")
    request = Request("https://api.github.com/graphql",
                      data=json.dumps({"query": query, "variables": variables}).encode(),
                      headers={"Authorization": "Bearer " + token,
                               "Content-Type": "application/json", "User-Agent": "paper-dragon"})
    with urlopen(request, timeout=45) as response:
        require_scope(response.headers.get("X-OAuth-Scopes", ""))
        payload = json.load(response)
    if payload.get("errors") or not payload.get("data"):
        raise ValueError("GitHub returned an incomplete query; previous art is retained.")
    return payload


def windows(first: date, last: date):
    while first <= last:
        end = min(date(first.year, 12, 31), last)
        yield first, end
        first = end + timedelta(days=1)


def calendar_days(payload: dict, login: str, first: date, last: date) -> dict:
    if payload.get("errors"):
        raise ValueError("Partial GraphQL response.")
    viewer = payload["data"]["viewer"]
    require_owner(viewer, login)
    calendar = viewer["contributionsCollection"]["contributionCalendar"]
    days = {}
    for week in calendar["weeks"]:
        for item in week["contributionDays"]:
            day = date.fromisoformat(item["date"])
            count = item["contributionCount"]
            if day in days or not first <= day <= last or type(count) is not int or count < 0:
                raise ValueError("Invalid or duplicate calendar day.")
            days[day] = count
    expected = (last - first).days + 1
    if len(days) != expected or sum(days.values()) != calendar["totalContributions"]:
        raise ValueError("Incomplete or inconsistent contribution calendar.")
    return days


def collect(login: str, token: str, today: date, include_today: bool = False) -> dict:
    viewer = api("query { viewer { login createdAt } }", {}, token)["data"]["viewer"]
    require_owner(viewer, login)
    # Calendar attribution can precede the UTC creation date. Query the entire
    # creation year rather than clipping legitimate early contribution days.
    first = date(int(viewer["createdAt"][:4]), 1, 1)
    days = {}
    for start, end in windows(first, today if include_today else today - timedelta(days=1)):
        payload = api(QUERY, {"from": start.isoformat() + "T00:00:00Z",
                              "to": end.isoformat() + "T23:59:59Z"}, token)
        days.update(calendar_days(payload, login, start, end))
    return days


def collect_profile_calendar(login, token, today):
    # Let GitHub choose its default contribution-graph window.
    query = QUERY.replace(
        "query($from: DateTime!, $to: DateTime!)", "query"
    ).replace("contributionsCollection(from:$from, to:$to)", "contributionsCollection")
    payload = api(query, {}, token)
    calendar = payload["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]
    dates = [date.fromisoformat(day["date"])
             for week in calendar["weeks"] for day in week["contributionDays"]]
    if not dates or max(dates) != today or (today - min(dates)).days not in (364, 365, 366):
        raise ValueError("Unexpected GitHub profile calendar window.")
    return calendar_days(payload, login, min(dates), today)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("dragon"))
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    today = now.date()
    phase = "setup"
    try:
        from living_activity import collect_repositories
        from living_model import develop, public_stats
        from living_renderer import render_living
        credentials = os.environ.get("DRAGON_REPO_TOKENS", "")
        if not credentials:
            raise ValueError("Repository credentials missing.")
        phase = "repository language collection"
        snapshot = collect_repositories(args.login, credentials, now)
        phase = "GitHub contribution calendar"
        days = collect_profile_calendar(args.login, os.environ.get("DRAGON_ACTIVITY_TOKEN", ""), today)
        phase = "rendering and output validation"
        state_path = args.output_dir / "state.json"
        previous = json.loads(state_path.read_text()) if state_path.exists() else {}
        model = develop(snapshot, days, previous, today)
        outputs = {"dragon.svg": render_living(model),
                   "still.svg": render_living(model, animated=False),
                   "state.json": json.dumps(model["state"], indent=2) + "\n",
                   "stats.json": json.dumps(public_stats(model, now), indent=2) + "\n"}
        import xml.etree.ElementTree as ET
        ET.fromstring(outputs["dragon.svg"])
        ET.fromstring(outputs["still.svg"])
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, content in outputs.items():
            temporary = args.output_dir / (name + ".tmp")
            temporary.write_text(content)
            temporary.replace(args.output_dir / name)
    except Exception as error:
        # Never echo API response bodies, headers, credentials, or private data.
        detail = f"HTTP {error.code}" if isinstance(error, HTTPError) else type(error).__name__
        if str(error) == "Unexpected GitHub profile calendar window.":
            detail = "unexpected calendar date range"
        if re.fullmatch(r"GitHub repository API returned HTTP [1-5][0-9]{2}\.", str(error)):
            detail = str(error)
        parser.exit(1, f"Collector failed during {phase} ({detail}).\nPaper Dragon failed: verify DRAGON_REPO_TOKENS read-only private access, owner activity token, API limits and complete calendar. Previous artwork retained.\n")


if __name__ == "__main__":
    main()
