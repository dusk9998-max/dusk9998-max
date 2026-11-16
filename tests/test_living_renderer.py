import base64
import hashlib
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from living_model import develop
from living_renderer import render_living


class RendererTests(unittest.TestCase):
    def model(self, total=180, recent=12):
        return develop({"total": total, "recent": recent, "daily": {},
                        "palette": [{"name": "Python", "color": "#3572A5", "weight": 1}]},
                       {}, {}, __import__("datetime").date(2026, 11, 16))

    def test_all_five_forms_are_distinct_embedded_assets(self):
        fingerprints = set()
        for total in (0, 50, 150, 500, 1500):
            svg = render_living(self.model(total))
            root = ET.fromstring(svg)
            sprite = root.find(".//{http://www.w3.org/2000/svg}image[@id='dragon-art']")
            fingerprints.add(hashlib.sha256(base64.b64decode(sprite.attrib["href"].split(",")[1])).hexdigest())
            self.assertLess(len(svg), 4_000_000)
        self.assertEqual(len(fingerprints), 5)

    def test_animation_changes_body_not_just_position_and_has_static_fallback(self):
        animated = render_living(self.model())
        self.assertTrue("feDisplacementMap" in animated, "Body deformation is missing")
        self.assertTrue("@keyframes swim" in animated, "Swimming motion is missing")
        self.assertTrue("prefers-reduced-motion: no-preference" in animated, "Reduced-motion guard is missing")
        still = render_living(self.model(), animated=False)
        self.assertTrue("<animate " not in still, "Still image contains SMIL motion")
        self.assertTrue("<style>" not in still, "Still image contains CSS motion")
        ET.fromstring(still)

    def test_language_panel_colors_and_no_external_resources(self):
        svg = render_living(self.model())
        self.assertIn("Python", svg)
        self.assertIn("hueRotate", svg)
        self.assertNotIn("https://", svg)
        self.assertNotIn("<script", svg)
