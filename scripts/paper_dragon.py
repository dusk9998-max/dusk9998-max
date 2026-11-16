"""Owner-authenticated aggregate activity -> an original folded-paper dragon."""
import argparse
import json
import math
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


def collect(login: str, token: str, today: date) -> dict:
    viewer = api("query { viewer { login createdAt } }", {}, token)["data"]["viewer"]
    require_owner(viewer, login)
    # Calendar attribution can precede the UTC creation date. Query the entire
    # creation year rather than clipping legitimate early contribution days.
    first = date(int(viewer["createdAt"][:4]), 1, 1)
    days = {}
    for start, end in windows(first, today - timedelta(days=1)):
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
    stage, gold = state["stage"], state["gold"]
    speed = 8 if recent == 0 else 6 if recent < 10 else 4.5
    motion = f"""<style>
@keyframes float {{
  0%, 100% {{ transform: translate(-8px, 14px) rotate(-4deg); }}
  50% {{ transform: translate(8px, -22px) rotate(4deg); }}
}}
@media (prefers-reduced-motion: no-preference) {{
  .dragon-motion {{
    transform-origin: 390px 267px;
    animation: float {speed}s ease-in-out infinite;
  }}
}}
</style>""" if animated else ""
    pieces = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 540" role="img" aria-labelledby="title desc">
<title id="title">Paper Dragon</title>
<desc id="desc">An ivory and vermilion origami dragon with golden seams, growing with combined public and private GitHub activity. Quiet days bring rest.</desc>
{motion}
<defs>
  <radialGradient id="paper"><stop stop-color="#fff9eb"/><stop offset="1" stop-color="#ead9ba"/></radialGradient>
  <linearGradient id="sun" x2="0" y2="1"><stop stop-color="#d45036"/><stop offset="1" stop-color="#c93b2b" stop-opacity=".55"/></linearGradient>
  <pattern id="grain" width="13" height="17" patternUnits="userSpaceOnUse"><path d="M1 2l2 1m5 8l1 2m-5 1h1" stroke="#a98454" stroke-opacity=".1" stroke-width=".6"/></pattern>
</defs>
<rect width="800" height="540" rx="8" fill="url(#paper)"/>
<rect width="800" height="540" rx="8" fill="url(#grain)"/>
<circle cx="386" cy="246" r="163" fill="url(#sun)" opacity=".9"/>
<circle cx="386" cy="246" r="178" fill="none" stroke="#aa8547" stroke-opacity=".28" stroke-width="1"/>
<g fill="none" stroke="#8d806e" stroke-width="1.3" opacity=".32">
 <path d="M60 360h153c28 0 29-16 8-16h-52c-24 0-26-18-3-18h36"/>
 <path d="M566 141h155c19 0 22-13 5-13h-53c-28 0-27-17-6-17h28"/>
 <path d="M563 412h119c23 0 23-14 4-14h-37"/>
</g>
<g transform="translate(390 267) scale({.68 + stage * .08:.2f}) translate(-390 -267)">
<g class="dragon-motion">
''']
    # A tapered open coil, made of hand-folded triangular facets.
    count = 27 + stage * 4
    points = []
    for i in range(count + 1):
        t = i / count
        angle = math.radians(30 + 292 * t)
        radius = 142 + 28 * t
        points.append((390 + radius * math.cos(angle), 267 + radius * .91 * math.sin(angle)))
    edges = []
    for i, (x, y) in enumerate(points):
        before, after = points[max(0, i - 1)], points[min(count, i + 1)]
        dx, dy = after[0] - before[0], after[1] - before[1]
        length = math.hypot(dx, dy)
        width = 2 + 30 * (i / count) ** .65
        ox, oy = -dy / length * width, dx / length * width
        edges.append(((x + ox, y + oy), (x - ox, y - oy)))
    for i in range(count):
        x, y = points[i]
        nx, ny = points[i + 1]
        dx, dy = nx - x, ny - y
        length = math.hypot(dx, dy)
        width = 4 + 30 * (i / count) ** .65
        ox, oy = -dy / length * width, dx / length * width
        a, b = edges[i]
        c, d = edges[i + 1]
        def polygon(vertices, color):
            return '<polygon points="' + " ".join(f"{px:.1f},{py:.1f}" for px, py in vertices) + f'" fill="{color}" stroke="#7f3528" stroke-width=".65" stroke-linejoin="round"/>'
        pieces.extend([polygon([a, b, c], "#d34e32" if i % 3 else "#e16c45"),
                       polygon([b, c, d], "#f5e7cb" if i % 4 < 2 else "#ae3025")])
        if i % 3 == 0:
            pieces.append(polygon([a, (a[0] + ox * .55 - dx * .8, a[1] + oy * .55 - dy * .8), c], "#e8d4aa"))
        if gold and i % max(2, 8 - gold) == 0:
            pieces.append(f'<path d="M{b[0]:.1f},{b[1]:.1f}L{c[0]:.1f},{c[1]:.1f}" stroke="#c4a25c" stroke-width="2"/>')
    # Head faces right. Horns, jaw, whiskers, and angular mane preserve the dragon silhouette.
    hx, hy = points[-1]
    pieces.append(f'''<g transform="translate({hx-30:.1f} {hy-18:.1f}) rotate(18)">
<path d="M-24 22L-46-7-13 2-35-35 5-9-4-54 28-25 53-33 73-7 113 9 92 26 112 38 63 42 44 64 23 35Z" fill="#f8ead0" stroke="#873e2d" stroke-width="1.2"/>
<path d="M-24 22L5-9 28-25 33 8 73-7 113 9 65 19 44 64 23 35Z" fill="#cc402c"/>
<path d="M5-9L33 8 23 35M33 8L65 19 73-7M65 19L63 42 92 26" fill="none" stroke="#c8a15a" stroke-width="1.7"/>
<path d="M-4-54L12-18 28-25M-35-35L5-9-13 2" fill="#dfc895" stroke="#b68b48"/>
<path d="M47 5l19-2-12 10Z" fill="#322d29"/>
<circle cx="57" cy="5" r="1.5" fill="#fff9e9"/>
<path d="M92 26l-22 6M92 26Q137 34 145 12M89 32Q133 57 146 42" fill="none" stroke="#9c6b3d" stroke-width="1.4"/>
<path d="M-21 25L-45 39-31 10M19 37L6 63 34 49" fill="#a72c23"/>
</g>
</g>
</g>
<g fill="#b38c4b" opacity=".8"><path d="M125 170l3 7 7 3-7 3-3 7-3-7-7-3 7-3Z"/><path d="M662 328l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z"/></g>
<path d="M328 473h144" stroke="#ad8a50" stroke-width=".8"/>
<text x="400" y="498" text-anchor="middle" fill="#784f37" font-family="Georgia,serif" font-size="17" letter-spacing="5">PAPER DRAGON</text>
</svg>''')
    return "".join(pieces)


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
    today = datetime.now(timezone.utc).date()
    try:
        days = collect(args.login, os.environ.get("DRAGON_ACTIVITY_TOKEN", ""), today)
        publish(days, args.output_dir, today)
    except Exception:
        # Never echo API response bodies, headers, credentials, or private data.
        parser.exit(1, "Paper Dragon failed: verify owner token, read:user scope, API access and complete calendar. Previous artwork retained.\n")


if __name__ == "__main__":
    main()
