"""Progression rules; receives aggregates, never private repository identities."""
from datetime import timedelta

STAGE_THRESHOLDS = (0, 50, 150, 500, 1500)
GOLD_THRESHOLDS = (25, 100, 300, 750, 2000)
STAGE_NAMES = ("Hatchling", "Young", "Growing", "Mature", "Elder")


def monday(day):
    return day - timedelta(days=day.weekday())


def streaks(active_days, today):
    weeks = sorted({monday(day) for day in active_days if day <= today})
    longest, run, previous = 0, 0, None
    for week in weeks:
        run = run + 1 if previous and week - previous == timedelta(weeks=1) else 1
        longest, previous = max(longest, run), week
    cursor = monday(today)
    if cursor not in weeks:
        cursor -= timedelta(weeks=1)
    current = 0
    while cursor in weeks:
        current += 1
        cursor -= timedelta(weeks=1)
    return current, longest, weeks


def develop(snapshot, calendar, previous, today):
    if previous:
        if (previous.get("version") not in (1, 2)
                or type(previous.get("stage")) is not int or not 0 <= previous["stage"] <= 4
                or type(previous.get("gold")) is not int or not 0 <= previous["gold"] <= 5
                or type(previous.get("record_weeks", 0)) is not int
                or not 0 <= previous.get("record_weeks", 0) <= 10000):
            raise ValueError("Invalid retained development state.")
    active = {day for day, count in calendar.items() if count > 0}
    current, longest, weeks = streaks(active, today)
    record = max(longest, previous.get("record_weeks", 0))
    # Current streak fills an accent over 13 active weeks. When broken, the last
    # run's accent decays over six quiet weeks; a new streak builds it again.
    accent = min(1, current / 13)
    if not current and weeks:
        end, count = weeks[-1], 0
        cursor = end
        while cursor in weeks:
            count += 1
            cursor -= timedelta(weeks=1)
        quiet = (monday(today) - end).days / 7 - 1
        accent = min(1, count / 13) * max(0, 1 - quiet / 6) ** 2
    total = sum(calendar.values())
    recent = sum(count for day, count in calendar.items() if today - timedelta(days=6) <= day <= today)
    stage = max(previous.get("stage", 0), sum(total >= n for n in STAGE_THRESHOLDS[1:]))
    gold = max(previous.get("gold", 0), sum(total >= n for n in GOLD_THRESHOLDS))
    weights = sum(item["weight"] for item in snapshot["palette"])
    palette = [dict(name=item["name"], color=item["color"], share=item["weight"] / weights)
               for item in snapshot["palette"]] if weights else []
    return {
        "state": {"version": 2, "stage": stage, "gold": gold, "record_weeks": record},
        "total_contributions": total, "recent_contributions": recent,
        "current_weeks": current, "accent": round(accent, 4),
        "vividness": .65 + .55 * min(1, record / 52),
        "metallic": min(1, record / 208), "palette": palette,
        "mood": "rest" if recent == 0 else "active" if recent < 10 else "busy",
        "milestone": stage > previous.get("stage", stage) or gold > previous.get("gold", gold),
    }


def public_stats(model, now):
    """Explicit allowlist: never serialize the raw collector or private identities."""
    stage, gold = model["state"]["stage"], model["state"]["gold"]
    total = model["total_contributions"]
    next_stage = None
    if stage < len(STAGE_THRESHOLDS) - 1:
        floor, goal = STAGE_THRESHOLDS[stage:stage + 2]
        next_stage = {"name": STAGE_NAMES[stage + 1], "threshold": goal,
                      "remaining": max(0, goal - total),
                      "progress": max(0, min(1, (total - floor) / (goal - floor)))}
    return {"version": 2, "updated_at": now.isoformat(),
            "total_contributions": total, "recent_contributions": model["recent_contributions"],
            "stage": {"index": stage, "name": STAGE_NAMES[stage], "next": next_stage},
            "gold": {"count": gold, "remaining": max(0, GOLD_THRESHOLDS[gold] - total)
                     if gold < len(GOLD_THRESHOLDS) else None},
            "current_weeks": model["current_weeks"],
            "record_weeks": model["state"]["record_weeks"],
            "accent": model["accent"], "mood": model["mood"],
            "palette": [{key: item[key] for key in ("name", "color", "share")}
                        for item in model["palette"]]}
