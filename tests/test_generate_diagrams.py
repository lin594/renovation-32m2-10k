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
    "30-five-route-electrical.svg": ("five-route-electrical-freeze", "五路明装电路讨论墙面走槽图"),
    "31-electrical-node-schedule.svg": ("electrical-node-schedule", "九主节点接线与材料复算图"),
    "40-doors-windows-cats.svg": ("doors-windows-cats", "门窗与猫安全图"),
    "50-kitchen-bath-details.svg": ("kitchen-bath-details", "厨卫详图"),
    "60-finishes-materials.svg": ("finishes-materials", "墙地面饰面图"),
}

class GenerateDiagramsTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir=tempfile.TemporaryDirectory(); self.output_dir=Path(self.temp_dir.name); generate_diagrams.generate_all(self.output_dir)
    def tearDown(self): self.temp_dir.cleanup()
    def test_generates_exactly_eight_svg_files(self):
        self.assertEqual({p.name for p in self.output_dir.glob("*.svg")}, set(EXPECTED))
    def test_each_svg_has_role_title_and_valid_xml(self):
        for filename,(role,title) in EXPECTED.items():
            path=self.output_dir/filename; root=ET.parse(path).getroot(); self.assertEqual(root.attrib["data-diagram-role"],role); self.assertIn(title,path.read_text(encoding="utf-8"))
    def test_furniture_plan_does_not_draw_bath_slider_in_passage(self):
        furniture=(self.output_dir/"10-furniture-circulation.svg").read_text(encoding="utf-8"); doors=(self.output_dir/"40-doors-windows-cats.svg").read_text(encoding="utf-8")
        self.assertNotIn('data-state="bath-slider-open-in-passage"',furniture); self.assertIn('data-detail="bath-slider-constraint"',doors)
    def test_existing_desk_and_unpurchased_chair_are_distinct(self):
        furniture=(self.output_dir/"10-furniture-circulation.svg").read_text(encoding="utf-8")
        self.assertIn('data-status="existing-to-refinish"',furniture); self.assertIn("书桌｜已有",furniture); self.assertIn("待改黑胡桃色",furniture)
    def test_sofa_bed_guest_mode_and_optional_privacy_are_explicit(self):
        furniture=(self.output_dir/"10-furniture-circulation.svg").read_text(encoding="utf-8")
        self.assertIn('data-furniture="sofa-bed" data-mode="sofa"',furniture); self.assertIn('data-furniture="sofa-bed" data-mode="bed-open"',furniture); self.assertIn('data-privacy-curtain="candidate"',furniture)
    def test_bath_slider_opens_east_and_temporarily_intrudes_hall_b(self):
        for svg in ((self.output_dir/"40-doors-windows-cats.svg").read_text(encoding="utf-8"),(self.output_dir/"50-kitchen-bath-details.svg").read_text(encoding="utf-8")):
            self.assertIn('data-state="bath-slider-open-east"',svg); self.assertIn('data-intrusion-m="0.4"',svg)
    def test_water_heater_is_directly_above_sink_not_wood_cabinet(self):
        d=(self.output_dir/"50-kitchen-bath-details.svg").read_text(encoding="utf-8"); self.assertIn('data-placement="water-heater-above-sink"',d); self.assertIn("水槽正上方",d)
    def test_hall_a_and_hall_b_are_openly_connected(self):
        for filename in EXPECTED:
            svg=(self.output_dir/filename).read_text(encoding="utf-8")
            if filename not in {"30-five-route-electrical.svg","31-electrical-node-schedule.svg","50-kitchen-bath-details.svg"}:
                self.assertIn('data-connection="hall-a-b-open"',svg)
    def test_30_is_current_five_route_diagram(self):
        d=(self.output_dir/"30-five-route-electrical.svg").read_text(encoding="utf-8")
        for circuit in ("C1-BED","C2-KIT","C3-LIV","C4-AC-FR","C5-BATH"): self.assertIn(circuit,d)
        for node in ("B1","B2","K1","K2","H1","L1","W1","A1","BATH1"): self.assertIn(node,d)
        self.assertIn("L1：洗烘/小厨电 / JZ-N2",d); self.assertIn("W1：投影 / 沙发娱乐区 / 书桌",d)
    def test_31_has_only_nine_main_nodes(self):
        d=(self.output_dir/"31-electrical-node-schedule.svg").read_text(encoding="utf-8")
        for node in ("B1","B2","K1","K2","H1","L1","W1","A1","BATH1"): self.assertIn(node,d)
        self.assertIn("PCT-42：1对L/N输入→2对L/N输出",d); self.assertIn("PCT-62：1对L/N输入→3对L/N输出",d)
        self.assertIn("理论4只",d); self.assertIn("理论5只",d); self.assertIn("2.5→投影 / 2.5→沙发娱乐区 / 2.5→书桌",d)
    def test_unresolved_electrical_work_is_explicitly_blocked(self):
        routes = (self.output_dir / "30-five-route-electrical.svg").read_text(encoding="utf-8")
        schedule = (self.output_dir / "31-electrical-node-schedule.svg").read_text(encoding="utf-8")
        for svg in (routes, schedule):
            self.assertIn('data-drawing-property="discussion"', svg)
            self.assertIn("走廊B", svg)
            self.assertIn("blocked", svg)
            self.assertNotIn("详见39图", svg)
            self.assertNotIn("另4个局部子节点", svg)
        root = ET.fromstring(routes)
        pending = [element for element in root.iter() if element.attrib.get("data-route-status") == "blocked-pending-setout"]
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].attrib["data-route-direction"], "north-then-west")
        self.assertIn("stroke-dasharray", pending[0].attrib)
        self.assertNotIn("客厅南侧高位向西→西墙向北", routes)
        self.assertIn("蓝芯重标及N预留待专业确认", schedule)
        self.assertIn("具体SKU证实", schedule)

    def test_checked_in_outputs_match_generator(self):
        checked=Path(__file__).resolve().parents[1]/"diagrams"
        for filename in EXPECTED: self.assertEqual((checked/filename).read_text(encoding="utf-8"),(self.output_dir/filename).read_text(encoding="utf-8"),f"{filename} 已过期，请运行 make diagrams")
    def test_diagram_directory_contains_only_current_flat_outputs(self):
        diagrams=Path(__file__).resolve().parents[1]/"diagrams"; self.assertFalse(any(p.is_dir() for p in diagrams.iterdir())); self.assertEqual({p.name for p in diagrams.glob("*.svg")},set(EXPECTED))

if __name__=="__main__": unittest.main()
