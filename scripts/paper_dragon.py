"""Owner-authenticated aggregate activity -> an original folded-paper dragon."""
import argparse
import json
from dragon_art import embedded_art
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
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


def derive_state(days: dict, previous: dict, today: date) -> dict:
    if previous:
        if (set(previous) != {"version", "stage", "gold"} or previous["version"] != 1
                or type(previous["stage"]) is not int or not 0 <= previous["stage"] <= 4
                or type(previous["gold"]) is not int or not 0 <= previous["gold"] <= 5):
            raise ValueError("Invalid retained growth state.")
    total = sum(days.values())
    stage = sum(total >= threshold for threshold in (50, 150, 500, 1500))
    gold = sum(total >= threshold for threshold in (25, 100, 300, 750, 2000))
    return {"version": 1, "stage": max(stage, previous.get("stage", 0)),
            "gold": max(gold, previous.get("gold", 0))}


def render(state: dict, recent: int, animated: bool = True) -> str:
    # The detailed reference artwork is present at every growth stage. Activity
    # changes scale, earned gold ornaments, and motion, never the art's identity.
    stage, gold = state["stage"], state["gold"]
    speed = 8 if recent == 0 else 6 if recent < 10 else 4.5
    scale = .84 + stage * .035
    motion = f"""<style>
@keyframes float {{
  0%, 100% {{ transform: translate(-8px, 14px) rotate(-3deg); }}
  50% {{ transform: translate(8px, -22px) rotate(3deg); }}
}}
@media (prefers-reduced-motion: no-preference) {{
  .dragon-motion {{
    transform-origin: 400px 320px;
    animation: float {speed}s ease-in-out infinite;
  }}
}}
</style>""" if animated else ""
    # Milestones add small permanent gold floral seals along the lower edge.
    ornaments = []
    for i in range(gold):
        petals = "".join(f'<ellipse cx="0" cy="-5" rx="2.7" ry="4.5" transform="rotate({j * 72})"/>'
                         for j in range(5))
        ornaments.append(f'<g transform="translate({650 + i * 23} 609)" fill="#c49a51" opacity=".8">{petals}<circle r="2" fill="#98652e"/></g>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="640" viewBox="0 0 800 640" role="img" aria-labelledby="title desc">
<title id="title">Paper Dragon</title>
<desc id="desc">A textured vermilion and ivory origami dragon with a flowing body, sculpted head, folded mane, golden flowers and whiskers, floating over parchment, a red sun and ink clouds. Growth reflects combined public and private GitHub activity.</desc>
{motion}
<image width="800" height="640" preserveAspectRatio="xMidYMid slice" href="{embedded_art('background.jpg')}"/>
<g transform="translate(400 320) scale({scale:.3f}) translate(-400 -320)">
  <g class="dragon-motion">
    <image x="26" y="20" width="748" height="600" preserveAspectRatio="xMidYMid meet" href="{embedded_art('dragon.png')}"/>
  </g>
</g>
{''.join(ornaments)}
</svg>'''


def publish(days: dict, output: Path, today: date):
    state_path = output / "state.json"
    previous = json.loads(state_path.read_text()) if state_path.exists() else {}
    state = derive_state(days, previous, today)
    recent = sum(count for day, count in days.items() if today - timedelta(days=7) <= day < today)
    svg = render(state, recent)
    import xml.etree.ElementTree as ET
    ET.fromstring(svg)
    output.mkdir(parents=True, exist_ok=True)
    # All fetching and validation finish before either output is replaced.
    for name, content in (("dragon.svg", svg), ("still.svg", render(state, recent, animated=False)),
                          ("state.json", json.dumps(state, indent=2) + "\n")):
        temporary = output / (name + ".tmp")
        temporary.write_text(content)
        temporary.replace(output / name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("dragon"))
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    today = now.date()
    try:
        from living_activity import collect_repositories
        from living_model import develop, public_stats
        from living_renderer import render_living
        credentials = os.environ.get("DRAGON_REPO_TOKENS", "")
        if not credentials:
            raise ValueError("Repository credentials missing.")
        snapshot = collect_repositories(args.login, credentials, now)
        days = collect(args.login, os.environ.get("DRAGON_ACTIVITY_TOKEN", ""), today, include_today=True)
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
    except Exception:
        # Never echo API response bodies, headers, credentials, or private data.
        parser.exit(1, "Paper Dragon failed: verify DRAGON_REPO_TOKENS read-only private access, owner activity token, API limits and complete calendar. Previous artwork retained.\n")


if __name__ == "__main__":
    main()
