"""Build a static public portrait from already-published aggregate output."""
import argparse
import json
import re
import shutil
from datetime import datetime
from html import escape
from pathlib import Path


def build(source: Path, destination: Path):
    stats = json.loads((source / "stats.json").read_text())
    if stats.get("version") != 1:
        raise ValueError("Unsupported public stats schema.")
    stage, total = stats["stage"], stats["total_commits"]
    next_stage = stage["next"]
    if next_stage:
        remaining = f'{next_stage["remaining"]:,} more commits to {next_stage["name"]}'
        progress = f'<progress value="{next_stage["progress"]}" max="1" aria-label="Progress from {escape(stage["name"])} to {escape(next_stage["name"])}">{next_stage["progress"]:.0%}</progress>'
    else:
        remaining, progress = "Elder reached. Every growth form is unlocked.", ""
    buttons = "".join(f'<button type="button" data-feature="language-{i}" aria-pressed="false"><span class="swatch" style="--swatch:{escape(item["color"], quote=True)}" aria-hidden="true"></span>{escape(item["name"])}</button>' for i, item in enumerate(stats["palette"]))
    svg = (source / "dragon.svg").read_text().replace('role="img"', 'role="group"')
    updated = datetime.fromisoformat(stats["updated_at"])
    replacements = {
        "DRAGON": svg, "STATS": json.dumps(stats).replace("<", "\\u003c"),
        "UPDATED": escape(stats["updated_at"], quote=True),
        "UPDATED_LABEL": updated.strftime("%b %d, %Y · %H:%M UTC"),
        "STAGE_NUMBER": f'{stage["index"] + 1:02}', "STAGE": escape(stage["name"]),
        "TOTAL": f'{total:,}', "RECENT": f'{stats["recent_commits"]:,}',
        "CURRENT": str(stats["current_weeks"]), "CURRENT_UNIT": "week" if stats["current_weeks"] == 1 else "weeks",
        "RECORD_UNIT": "week" if stats["record_weeks"] == 1 else "weeks", "RECORD": str(stats["record_weeks"]),
        "NEXT_LABEL": f'Next form · {escape(next_stage["name"])}' if next_stage else "Final form",
        "PROGRESS_LABEL": f'{next_stage["progress"]:.0%}' if next_stage else "Complete",
        "PROGRESS": progress, "REMAINING": escape(remaining), "LANGUAGE_BUTTONS": buttons,
        "LANGUAGE_SUMMARY": escape(", ".join(f'{item["name"]} {item["share"]:.1%}' for item in stats["palette"]) or "No language metadata available")}
    template = Path(__file__).resolve().parents[1] / "web"
    # One pass prevents placeholder-like text in API language names being expanded.
    html = re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: replacements[match[1]], (template / "index.html").read_text())
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "index.html").write_text(html)
    for name in ("style.css", "app.js"):
        shutil.copyfile(template / name, destination / name)
    (destination / ".nojekyll").touch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("dragon"))
    parser.add_argument("--output", type=Path, default=Path("_site"))
    args = parser.parse_args()
    build(args.source, args.output)
