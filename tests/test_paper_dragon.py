import copy
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from paper_dragon import api, collect, calendar_days, derive_state, require_owner, require_scope, windows, render


class ActivityTests(unittest.TestCase):
    def test_creation_utc_date_does_not_drop_previous_calendar_day(self):
        from datetime import timedelta
        from unittest.mock import patch
        viewer = {"login": "dusk9998-max", "createdAt": "2026-08-10T02:10:35Z"}
        first, last = date(2026, 1, 1), date(2026, 8, 10)
        days = [{"date": (first + timedelta(days=i)).isoformat(),
                 "contributionCount": 8 if first + timedelta(days=i) == date(2026, 8, 9) else 0}
                for i in range((last - first).days + 1)]
        payload = {"data": {"viewer": dict(viewer, contributionsCollection={
            "contributionCalendar": {"totalContributions": 8,
                                     "weeks": [{"contributionDays": days}]}})}}
        with patch("paper_dragon.api", side_effect=[{"data": {"viewer": viewer}}, payload]):
            result = collect("dusk9998-max", "test-only", date(2026, 8, 11))
        self.assertEqual(sum(result.values()), 8)
        self.assertEqual(result[date(2026, 8, 9)], 8)

    def setUp(self):
        self.payload = {"data": {"viewer": {"login": "dusk9998-max",
            "contributionsCollection": {"restrictedContributionsCount": 3,
                "contributionCalendar": {"totalContributions": 5, "weeks": [
                    {"contributionDays": [{"date": "2026-01-01", "contributionCount": 5},
                                         {"date": "2026-01-02", "contributionCount": 0}]}]}}}}}

    def test_no_double_counting(self):
        days = calendar_days(self.payload, "dusk9998-max", date(2026, 1, 1), date(2026, 1, 2))
        self.assertEqual(sum(days.values()), 5)

    def test_rejects_missing_duplicate_and_mismatched_days(self):
        for change in ("missing", "duplicate", "total"):
            p = copy.deepcopy(self.payload)
            cal = p["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]
            if change == "missing":
                cal["weeks"][0]["contributionDays"].pop()
            elif change == "duplicate":
                cal["weeks"][0]["contributionDays"].append(cal["weeks"][0]["contributionDays"][0])
            else:
                cal["totalContributions"] = 10
            with self.assertRaises(ValueError):
                calendar_days(p, "dusk9998-max", date(2026, 1, 1), date(2026, 1, 2))

    def test_partial_errors_and_identity(self):
        self.payload["errors"] = [{"message": "partial failure"}]
        with self.assertRaises(ValueError):
            calendar_days(self.payload, "dusk9998-max", date(2026, 1, 1), date(2026, 1, 2))
        with self.assertRaises(ValueError):
            require_owner({"login": "someone-else"}, "dusk9998-max")

    def test_scope_required(self):
        for scopes in ("", "repo", "public_repo"):
            with self.assertRaises(ValueError):
                require_scope(scopes)
        require_scope("read:user")
        require_scope("repo, user")

    def test_missing_token_fails_before_network(self):
        with self.assertRaisesRegex(ValueError, "secret"):
            api("query { viewer { login } }", {}, "")

    def test_invalid_state_is_rejected(self):
        with self.assertRaises(ValueError):
            derive_state({}, {"version": 1, "stage": 999, "gold": 0}, date(2026, 1, 2))

    def test_failed_collection_retains_existing_image(self):
        import os
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "dragon.svg"
            image.write_text("previous successful image")
            environment = dict(os.environ, DRAGON_ACTIVITY_TOKEN="")
            run = subprocess.run([sys.executable, "scripts/paper_dragon.py",
                                  "--login", "dusk9998-max", "--output-dir", directory],
                                 env=environment, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(image.read_text(), "previous successful image")
            self.assertFalse((Path(directory) / "state.json").exists())

    def test_year_windows_include_leap_day_without_overlap(self):
        self.assertEqual(list(windows(date(2024, 2, 28), date(2025, 1, 2))),
                         [(date(2024, 2, 28), date(2024, 12, 31)),
                          (date(2025, 1, 1), date(2025, 1, 2))])

    def test_growth_is_bounded_and_retained(self):
        self.assertEqual(derive_state({}, {}, date(2026, 1, 2))["stage"], 0)
        self.assertEqual(derive_state({date(2026, 1, 1): 1000000}, {}, date(2026, 1, 2))["stage"], 4)
        prior = {"version": 1, "stage": 3, "gold": 4}
        self.assertEqual(derive_state({}, prior, date(2026, 1, 2)), prior)

    def test_svg_is_self_contained_and_valid(self):
        import xml.etree.ElementTree as ET
        svg = render({"version": 1, "stage": 2, "gold": 2}, 0)
        ET.fromstring(svg)
        for forbidden in ("<script", "http://", "https://", "contributionCount", "restricted"):
            # The XML namespace URI is the sole non-resource URI.
            self.assertNotIn(forbidden, svg.replace("http://www.w3.org/2000/svg", ""))
        self.assertIn("<animateTransform", svg)
        self.assertIn("<title", svg)


if __name__ == "__main__":
    unittest.main()
