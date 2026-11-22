import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from living_model import develop, public_stats
from living_renderer import render_living
from build_site import build


class PublicStatsTests(unittest.TestCase):
    def model(self, total, previous=None):
        return develop({"total": total, "recent": 3, "daily": {},
                        "private_repository": "must-not-publish",
                        "palette": [{"name": "Python", "color": "#3572A5", "weight": 1}]},
                       {}, previous or {}, date(2026, 11, 16))

    def stats(self, model):
        return public_stats(model, datetime(2026, 11, 16, tzinfo=timezone.utc))

    def test_threshold_boundaries_and_final_form(self):
        for total, name, remaining in [(0, "Young", 50), (49, "Young", 1),
                                        (50, "Growing", 100), (149, "Growing", 1),
                                        (150, "Mature", 350), (499, "Mature", 1),
                                        (500, "Elder", 1000), (1499, "Elder", 1)]:
            stats = self.stats(self.model(total))
            self.assertEqual(stats["stage"]["next"]["name"], name)
            self.assertEqual(stats["stage"]["next"]["remaining"], remaining)
            self.assertTrue(0 <= stats["stage"]["next"]["progress"] <= 1)
        self.assertIsNone(self.stats(self.model(1500))["stage"]["next"])
        self.assertIsNone(self.stats(self.model(2000))["gold"]["remaining"])

    def test_retained_stage_uses_next_absolute_threshold(self):
        stats = self.stats(self.model(20, {"version": 2, "stage": 2, "gold": 2}))
        self.assertEqual(stats["stage"]["name"], "Growing")
        self.assertEqual(stats["stage"]["next"]["remaining"], 480)
        self.assertEqual(stats["stage"]["next"]["progress"], 0)

    def test_public_allowlist_and_no_language_footer(self):
        model = self.model(180)
        model["private_repository"] = "must-not-publish"
        self.assertNotIn("must-not-publish", json.dumps(self.stats(model)))
        svg = render_living(model)
        self.assertTrue("<text " not in svg)
        self.assertTrue('viewBox="0 0 800 640"' in svg)

    def test_static_fallback_and_script_boundary_escaping(self):
        model = self.model(180)
        model["palette"][0]["name"] = '</script><script>alert(1)</script>{{TOTAL}}'
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder) / "dragon", Path(folder) / "site"
            source.mkdir()
            (source / "stats.json").write_text(json.dumps(self.stats(model)))
            (source / "dragon.svg").write_text(render_living(model))
            build(source, output)
            html = (output / "index.html").read_text()
            self.assertTrue("320 more commits to Mature" in html)
            self.assertTrue("<noscript>" in html)
            self.assertTrue('</script><script>alert' not in html)
            self.assertTrue('\\u003c/script>' in html)
            self.assertTrue('&lt;/script&gt;' in html)
            self.assertTrue('{{TOTAL}}' in html)  # API text is not expanded again.
            self.assertTrue((output / "app.js").exists())
            self.assertTrue((output / "refresh.js").exists())
            self.assertEqual(json.loads((output / "stats.json").read_text()), self.stats(model))
            self.assertIn('id="refresh-dragon"', html)
            self.assertIn('actions/workflows/dragon.yml', html)
