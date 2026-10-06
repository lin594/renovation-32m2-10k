from __future__ import annotations
import tempfile
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from scripts import generate_diagrams

EXPECTED = {
    "00-overall-coordination.svg": "overall-coordination",
    "01-kitchen-coordination.svg": "kitchen-coordination",
    "02-bathroom-coordination.svg": "bathroom-coordination",
    "07-openings-pet-safety.svg": "openings-pet-safety",
    "10-water-gas-overview.svg": "water-gas-overview",
    "20-electrical-overview.svg": "electrical-overview",
    "27-electrical-nodes.svg": "electrical-nodes",
    "30-masonry-overview.svg": "masonry-overview",
    "40-coating-overview.svg": "coating-overview",
    "50-woodwork-overview.svg": "woodwork-overview",
    "58-door-window-schedule.svg": "door-window-schedule",
}

LEGACY_FILENAMES = {
    "00-existing-survey.svg",
    "10-furniture-circulation.svg",
    "20-plumbing-gas.svg",
    "30-five-route-electrical.svg",
    "31-electrical-node-schedule.svg",
    "40-doors-windows-cats.svg",
    "50-kitchen-bath-details.svg",
    "60-finishes-materials.svg",
}

class GenerateDiagramsTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir=tempfile.TemporaryDirectory(); self.output_dir=Path(self.temp_dir.name); generate_diagrams.generate_all(self.output_dir)
    def tearDown(self): self.temp_dir.cleanup()
    def test_generates_exactly_the_current_eleven_svg_files(self):
        self.assertEqual({p.name for p in self.output_dir.glob("*.svg")}, set(EXPECTED))
    def test_each_svg_has_role_title_and_valid_xml(self):
        for filename,role in EXPECTED.items():
            path=self.output_dir/filename; root=ET.parse(path).getroot(); self.assertEqual(root.attrib["data-diagram-role"],role); self.assertTrue(path.read_text(encoding="utf-8").strip())

    def test_overall_coordination_does_not_contain_electrical_termination_detail(self):
        for filename in ("00-overall-coordination.svg", "01-kitchen-coordination.svg", "02-bathroom-coordination.svg"):
            svg=(self.output_dir/filename).read_text(encoding="utf-8")
            self.assertNotIn("PCT-42",svg)
            self.assertNotIn("PCT-62",svg)
            self.assertNotIn("九主节点接线",svg)

    def test_electrical_overview_and_nodes_own_electrical_detail(self):
        d=(self.output_dir/"20-electrical-overview.svg").read_text(encoding="utf-8")
        for circuit in ("C1-BED","C2-KIT","C3-LIV","C4-AC-FR","C5-BATH"): self.assertIn(circuit,d)
        nodes=(self.output_dir/"27-electrical-nodes.svg").read_text(encoding="utf-8")
        for node in ("B1","B2","K1","K2","H1","L1","W1","A1","BATH1"): self.assertIn(node,nodes)
        self.assertIn("PCT-42",nodes); self.assertIn("PCT-62",nodes)
        self.assertIn("智能开关",d + nodes)

    def test_current_closeout_facts_are_visible(self):
        plumbing=(self.output_dir/"10-water-gas-overview.svg").read_text(encoding="utf-8")
        finishes=(self.output_dir/"40-coating-overview.svg").read_text(encoding="utf-8")
        self.assertIn("厨房漏点已完全修补；修补后疑似堵塞",plumbing)
        self.assertIn("2500ml管道疏通剂无改善；1月定位处理",plumbing)
        self.assertIn("实际一底一面；油漆工400元，角落不细",finishes)
        self.assertIn("1月DIY补缝/角落打磨并完成第二遍面漆",finishes)
        self.assertIn("卫生间闭水通过后已铺2.8kg环氧",finishes)

    def test_checked_in_outputs_match_generator(self):
        checked=Path(__file__).resolve().parents[1]/"diagrams"
        for filename in EXPECTED: self.assertEqual((checked/filename).read_text(encoding="utf-8"),(self.output_dir/filename).read_text(encoding="utf-8"),f"{filename} 已过期，请运行 make diagrams")
    def test_diagram_directory_contains_only_current_flat_outputs(self):
        diagrams=Path(__file__).resolve().parents[1]/"diagrams"; self.assertFalse(any(p.is_dir() for p in diagrams.iterdir())); actual={p.name for p in diagrams.glob("*.svg")}; self.assertEqual(actual,set(EXPECTED)); self.assertFalse(actual & LEGACY_FILENAMES)

if __name__=="__main__": unittest.main()
