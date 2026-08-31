from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from scripts import generate_diagrams


EXPECTED = {
    "00-existing-survey.svg": ("existing-survey", "现状测量图"),
    "10-furniture-circulation.svg": ("furniture-circulation", "家具与动线图"),
    "20-plumbing-gas.svg": ("plumbing-gas", "给排水与燃气图"),
    "30-electrical-low-voltage.svg": ("electrical-low-voltage", "强弱电点位图"),
    "40-doors-windows-cats.svg": ("doors-windows-cats", "门窗与猫安全图"),
    "50-kitchen-bath-details.svg": ("kitchen-bath-details", "厨卫详图"),
    "60-finishes-materials.svg": ("finishes-materials", "墙地面饰面图"),
}


class GenerateDiagramsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        generate_diagrams.generate_all(self.output_dir)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_generates_exactly_seven_svg_files(self) -> None:
        actual = {path.name for path in self.output_dir.glob("*.svg")}
        self.assertEqual(actual, set(EXPECTED))

    def test_each_svg_has_role_title_and_valid_xml(self) -> None:
        for filename, (role, title) in EXPECTED.items():
            path = self.output_dir / filename
            root = ET.parse(path).getroot()
            self.assertEqual(root.attrib["data-diagram-role"], role)
            self.assertIn(title, path.read_text(encoding="utf-8"))

    def test_furniture_plan_does_not_draw_bath_slider_in_passage(self) -> None:
        furniture = (self.output_dir / "10-furniture-circulation.svg").read_text(encoding="utf-8")
        doors = (self.output_dir / "40-doors-windows-cats.svg").read_text(encoding="utf-8")
        self.assertNotIn('data-state="bath-slider-open-in-passage"', furniture)
        self.assertIn('data-detail="bath-slider-constraint"', doors)

    def test_existing_desk_and_unpurchased_chair_are_distinct(self) -> None:
        furniture = (self.output_dir / "10-furniture-circulation.svg").read_text(encoding="utf-8")
        self.assertIn('data-status="existing-to-refinish"', furniture)
        self.assertIn("书桌｜已有", furniture)
        self.assertIn("待改黑胡桃色", furniture)
        self.assertIn("椅子、沙发和洗烘机尚未购买", furniture)

    def test_bath_slider_opens_east_and_temporarily_intrudes_hall_b(self) -> None:
        doors = (self.output_dir / "40-doors-windows-cats.svg").read_text(encoding="utf-8")
        details = (self.output_dir / "50-kitchen-bath-details.svg").read_text(encoding="utf-8")
        for svg in (doors, details):
            self.assertIn('data-state="bath-slider-open-east"', svg)
            self.assertIn('data-intrusion-m="0.4"', svg)
        self.assertIn("按进出需要部分开启", doors)

    def test_water_heater_is_directly_above_sink_not_wood_cabinet(self) -> None:
        details = (self.output_dir / "50-kitchen-bath-details.svg").read_text(encoding="utf-8")
        self.assertIn('data-placement="water-heater-above-sink"', details)
        self.assertIn("水槽正上方", details)
        self.assertIn("不在二层木柜上方", details)

    def test_status_and_specialty_layers_are_present(self) -> None:
        furniture = (self.output_dir / "10-furniture-circulation.svg").read_text(encoding="utf-8")
        plumbing = (self.output_dir / "20-plumbing-gas.svg").read_text(encoding="utf-8")
        electrical = (self.output_dir / "30-electrical-low-voltage.svg").read_text(encoding="utf-8")
        finishes = (self.output_dir / "60-finishes-materials.svg").read_text(encoding="utf-8")
        self.assertIn('data-status="not-purchased"', furniture)
        self.assertIn("燃气灶直连支路", plumbing)
        self.assertIn("光猫 / Wi-Fi", electrical)
        self.assertIn('data-finish="spc-wood-grain"', finishes)
        self.assertIn("ceil(A÷50)", finishes)
        self.assertIn("ceil(A÷30)", finishes)
        self.assertNotIn("¥518", finishes)
        self.assertIn("134.70㎡", finishes)
        self.assertIn("¥2012", finishes)
        self.assertIn('data-finish="tile-recolor"', finishes)
        self.assertIn("19.18㎡", finishes)
        self.assertIn("宋氏美学", finishes)

    def test_hall_a_and_hall_b_are_openly_connected(self) -> None:
        for filename in EXPECTED:
            svg = (self.output_dir / filename).read_text(encoding="utf-8")
            if filename != "50-kitchen-bath-details.svg":
                self.assertIn('data-connection="hall-a-b-open"', svg)
                self.assertNotIn("M475 450H600", svg)

    def test_checked_in_outputs_match_generator(self) -> None:
        checked_in = Path(__file__).resolve().parents[1] / "diagrams" / "v4"
        for filename in EXPECTED:
            self.assertEqual(
                (checked_in / filename).read_text(encoding="utf-8"),
                (self.output_dir / filename).read_text(encoding="utf-8"),
                f"{filename} 已过期，请运行 make diagrams",
            )


if __name__ == "__main__":
    unittest.main()
