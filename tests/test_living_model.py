import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from living_model import develop


class DevelopmentTests(unittest.TestCase):
    def snapshot(self, total=20, recent=1, daily=None):
        return {"total": total, "recent": recent, "daily": daily or {},
                "palette": [{"name": "Python", "color": "#3572A5", "weight": 3},
                            {"name": "TypeScript", "color": "#3178C6", "weight": 1}]}

    def test_migration_never_removes_earned_growth(self):
        model = develop(self.snapshot(), {}, {"version": 1, "stage": 3, "gold": 4}, date(2026, 11, 16))
        self.assertEqual((model["state"]["stage"], model["state"]["gold"]), (3, 4))

    def test_weekly_streak_spans_year_and_current_empty_week_does_not_break_it(self):
        days = {date(2025, 12, 29): 1, date(2026, 1, 5): 1}
        model = develop(self.snapshot(), days, {}, date(2026, 1, 12))
        self.assertEqual(model["current_weeks"], 2)
        self.assertEqual(model["state"]["record_weeks"], 2)

    def test_record_is_permanent_and_accents_fade_after_break(self):
        today = date(2026, 11, 16)
        old = {today - timedelta(weeks=i): 1 for i in range(2, 15)}
        model = develop(self.snapshot(), old, {"version": 2, "stage": 2, "gold": 2, "record_weeks": 40}, today)
        self.assertEqual(model["current_weeks"], 0)
        self.assertEqual(model["state"]["record_weeks"], 40)
        self.assertLess(model["accent"], 1)
        self.assertGreater(model["accent"], 0)
        self.assertEqual(model["mood"], "rest")

    def test_palette_tracks_real_language_mix_and_calendar_is_not_double_counted(self):
        model = develop(self.snapshot(total=149, recent=12), {date(2026, 11, 16): 99}, {}, date(2026, 11, 16))
        self.assertEqual(model["total_contributions"], 99)
        self.assertEqual(model["recent_contributions"], 99)
        self.assertEqual(model["mood"], "busy")
        self.assertEqual(model["palette"][0]["share"], .75)

    def test_recent_activity_uses_seven_calendar_days_including_today(self):
        today = date(2026, 11, 16)
        calendar = {today: 3, today - timedelta(days=6): 7,
                    today - timedelta(days=7): 90}
        model = develop(self.snapshot(total=999, recent=999), calendar, {}, today)
        self.assertEqual(model["total_contributions"], 100)
        self.assertEqual(model["recent_contributions"], 10)
        self.assertEqual(model["state"]["stage"], 1)



if __name__ == "__main__":
    unittest.main()
