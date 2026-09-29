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
    "38-five-route-electrical.svg": ("five-route-electrical-freeze", "五路明装电路最终墙面走槽图"),
    "39-electrical-node-schedule.svg": ("electrical-node-schedule", "九节点接线与材料复算图"),
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

    def test_generates_exactly_eight_svg_files(self) -> None:
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
        self.assertIn("椅子、沙发床和洗烘机尚未购买", furniture)

    def test_sofa_bed_guest_mode_and_optional_privacy_are_explicit(self) -> None:
        furniture = (self.output_dir / "10-furniture-circulation.svg").read_text(encoding="utf-8")
        self.assertIn('data-furniture="sofa-bed" data-mode="sofa"', furniture)
        self.assertIn('data-furniture="sofa-bed" data-mode="bed-open"', furniture)
        self.assertIn('data-privacy-curtain="candidate"', furniture)
        self.assertIn("临时客卧", furniture)

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

    def test_hall_a_and_hall_b_are_openly_connected(self) -> None:
        for filename in EXPECTED:
            svg = (self.output_dir / filename).read_text(encoding="utf-8")
            if filename not in {"38-five-route-electrical.svg", "39-electrical-node-schedule.svg", "50-kitchen-bath-details.svg"}:
                self.assertIn('data-connection="hall-a-b-open"', svg)
                self.assertNotIn("M475 450H600", svg)

    def test_38_is_only_current_electrical_diagram(self) -> None:
        current = set(EXPECTED)
        self.assertIn("38-five-route-electrical.svg", current)
        for old in range(30, 38):
            self.assertFalse(any(name.startswith(f"{old:02d}-") for name in current))
        detail = (self.output_dir / "38-five-route-electrical.svg").read_text(encoding="utf-8")
        self.assertIn("五路明装电路最终墙面走槽图", detail)
        for circuit in ("C1-BED", "C2-KIT", "C3-LIV", "C4-AC-FR", "C5-BATH"):
            self.assertIn(circuit, detail)
        for node in ("B1", "B2", "K1", "K2", "H1", "L1", "W1", "A1", "BATH1"):
            self.assertIn(node, detail)
        self.assertIn("吊扇拆除", detail)
        self.assertIn("90°转弯", detail)
        self.assertIn("PCT-42", detail)
        self.assertIn("罗马杆", detail)

    def test_39_has_nine_nodes_and_recomputed_takeoff(self) -> None:
        detail = (self.output_dir / "39-electrical-node-schedule.svg").read_text(encoding="utf-8")
        for node in ("B1", "B2", "K1", "K2", "H1", "L1", "W1", "A1", "BATH1"):
            self.assertIn(node, detail)
        self.assertIn("PCT-42：1对L/N输入→2对L/N输出", detail)
        self.assertIn("PCT-62：1对L/N输入→3对L/N输出", detail)
        self.assertIn("K2A", detail)
        self.assertIn("L1A", detail)
        self.assertIn("W1A", detail)
        self.assertIn("W1B", detail)
        self.assertIn("理论6只", detail)
        self.assertIn("理论7只", detail)
        self.assertIn("采购100m继续成立", detail)

    def test_checked_in_outputs_match_generator(self) -> None:
        checked_in = Path(__file__).resolve().parents[1] / "diagrams"
        for filename in EXPECTED:
            self.assertEqual(
                (checked_in / filename).read_text(encoding="utf-8"),
                (self.output_dir / filename).read_text(encoding="utf-8"),
                f"{filename} 已过期，请运行 make diagrams",
            )

    def test_diagram_directory_contains_only_current_flat_outputs(self) -> None:
        diagrams = Path(__file__).resolve().parents[1] / "diagrams"
        self.assertFalse(any(path.is_dir() for path in diagrams.iterdir()))
        self.assertEqual({path.name for path in diagrams.glob("*.svg")}, set(EXPECTED))


if __name__ == "__main__":
    unittest.main()
