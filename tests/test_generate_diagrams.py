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
    "31-electrical-routes.svg": ("electrical-routes", "强电真实空间走线图"),
    "32-electrical-topology.svg": ("electrical-topology", "五回路与分级漏保拓扑图"),
    "33-bedroom-electrical-detail.svg": ("bedroom-electrical-detail", "卧室插座与吊扇控制详图"),
    "34-bathroom-electrical-detail.svg": ("bathroom-electrical-detail", "卫生间专用馈线与漏保详图"),
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

    def test_generates_exactly_eleven_svg_files(self) -> None:
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

    def test_robot_dock_table_and_two_outlets_are_explicit(self) -> None:
        furniture = (self.output_dir / "10-furniture-circulation.svg").read_text(encoding="utf-8")
        points = (self.output_dir / "30-electrical-low-voltage.svg").read_text(encoding="utf-8")
        self.assertIn('data-furniture="robot-vacuum"', furniture)
        self.assertIn('data-clear-under="true"', furniture)
        self.assertIn('data-robot-approach="east-clear"', furniture)
        self.assertIn('data-outlet-branch="LR-SOFA-ROBOT"', furniture)
        self.assertIn('data-outlet="robot-always-on"', points)
        self.assertIn('data-outlet="sofa-charge"', points)

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
        self.assertIn("底漆3桶+面漆5桶", finishes)
        self.assertIn("不等待外窗复测再决定第5桶", finishes)
        self.assertIn("面漆须同色同批", finishes)
        self.assertIn('data-finish="tile-recolor"', finishes)
        self.assertIn("19.18㎡", finishes)
        self.assertIn("宋氏美学", finishes)

    def test_eve_v_and_route_aware_five_circuit_plan_are_present(self) -> None:
        points = (self.output_dir / "30-electrical-low-voltage.svg").read_text(encoding="utf-8")
        routes = (self.output_dir / "31-electrical-routes.svg").read_text(encoding="utf-8")
        circuits = (self.output_dir / "32-electrical-topology.svg").read_text(encoding="utf-8")
        self.assertIn("光猫 / Wi-Fi / EVE V", points)
        self.assertIn("至少4个常电位", points)
        self.assertIn("架内短网线接路由器", points)
        for circuit_id in ("RCBO-01", "RCBO-02", "RCBO-03", "MCB-04", "MCB-05"):
            self.assertIn(f'data-circuit="{circuit_id}"', circuits)
        self.assertEqual(circuits.count('data-circuit="'), 5)
        self.assertIn('data-wall-anchor="hall-a-south-wall"', routes)

    def test_31_has_real_boundaries_holes_and_distinct_fan_routes(self) -> None:
        routes = (self.output_dir / "31-electrical-routes.svg").read_text(encoding="utf-8")
        for hole_id in ("E-HOLE-01", "E-HOLE-02", "E-HOLE-03", "E-HOLE-04"):
            self.assertIn(f'data-electrical-hole="{hole_id}"', routes)
        self.assertIn('data-shelf-wall-contact="true"', routes)
        self.assertIn('data-fan-feed="surface-after-E-HOLE-01"', routes)
        self.assertIn('data-fan-feed="existing-concealed"', routes)
        self.assertIn('data-no-electrical-penetration="true"', routes)
        self.assertIn('data-balcony-power="deferred"', routes)

    def test_no_electrical_diagram_draws_permanent_balcony_route(self) -> None:
        for filename in (
            "30-electrical-low-voltage.svg",
            "31-electrical-routes.svg",
            "32-electrical-topology.svg",
            "33-bedroom-electrical-detail.svg",
            "34-bathroom-electrical-detail.svg",
        ):
            svg = (self.output_dir / filename).read_text(encoding="utf-8")
            self.assertNotIn('data-permanent-route="balcony"', svg)
            self.assertNotIn("阳台固定照明", svg)

    def test_32_has_five_circuits_six_logical_nodes_and_layered_rcd(self) -> None:
        topology = (self.output_dir / "32-electrical-topology.svg").read_text(encoding="utf-8")
        self.assertEqual(topology.count('data-circuit="'), 5)
        self.assertEqual(topology.count('data-terminal-status="logical"'), 6)
        for node in ("JB-L4", "JB-R3", "JB-BED", "JB-KIT", "JB-LIV", "JB-BATH"):
            self.assertIn(f'data-junction="{node}"', topology)
        self.assertNotIn('data-junction="JB-L5"', topology)
        self.assertIn('data-device-protection="RCD-BATH-01"', topology)
        self.assertIn('data-device-protection="SRCD-AC-BED"', topology)
        self.assertIn('data-device-protection="SRCD-AC-LIV"', topology)
        self.assertIn('data-device-protection="SRCD-WASHER"', topology)
        self.assertIn("实物型号和数量须现场换算", topology)

    def test_31_routes_mcb05_only_to_bath_rcd(self) -> None:
        routes = (self.output_dir / "31-electrical-routes.svg").read_text(encoding="utf-8")
        self.assertEqual(routes.count('data-circuit="MCB-05"'), 1)
        self.assertIn('data-bath-feeder="continuous-no-joint"', routes)
        self.assertIn('data-device-protection="RCD-BATH-01"', routes)
        self.assertIn('data-fallback="hall-a-outside"', routes)

    def test_34_has_continuous_feeder_three_downstream_loads_and_dry_fallback(self) -> None:
        detail = (self.output_dir / "34-bathroom-electrical-detail.svg").read_text(encoding="utf-8")
        self.assertIn('data-upstream-segment="continuous-no-joint-no-branch"', detail)
        self.assertIn('data-poles="L+N"', detail)
        self.assertIn('data-trip-ma-max="30"', detail)
        self.assertIn('data-bath-load-downstream="true"', detail)
        self.assertIn('data-device-protection="SRCD-BATH-HEATER"', detail)
        self.assertIn('data-device-protection="SRCD-BATH-MIRROR"', detail)
        self.assertIn('data-location-preference="bath-dry-high"', detail)
        self.assertIn('data-location-fallback="hall-a-outside"', detail)
        self.assertIn("禁止普通智能插座承载", detail)

    def test_33_separates_controller_and_bed_sockets(self) -> None:
        detail = (self.output_dir / "33-bedroom-electrical-detail.svg").read_text(encoding="utf-8")
        self.assertIn('data-box-type="existing-recessed"', detail)
        self.assertIn('data-device="fan-speed-controller"', detail)
        self.assertIn('data-box-type="surface-bed-south"', detail)
        self.assertIn('data-box-type="surface-bed-north"', detail)
        self.assertIn('data-terminal-scope="fan-control-only"', detail)
        self.assertIn('data-terminal-scope="bed-sockets-only"', detail)
        self.assertIn('data-circuit="MCB-04"', detail)
        self.assertIn('data-circuit="RCBO-01"', detail)
        self.assertIn("PE端子保持未连接并贴标", detail)

    def test_electrical_bom_excludes_recolored_blue_wire_and_switched_outlets(self) -> None:
        root = Path(__file__).resolve().parents[1]
        procurement = (root / "data/procurement.yaml").read_text(encoding="utf-8")
        electrical = (root / "data/electrical.yaml").read_text(encoding="utf-8")
        self.assertNotIn("用改色电工胶布", procurement)
        self.assertIn("不采用蓝线改色", procurement)
        self.assertIn("普通插座保持常电", electrical)
        self.assertIn("智能墙壁开关只控制灯具", electrical)
        self.assertNotIn("smart_switch_output: general_socket", electrical)

    def test_hall_a_and_hall_b_are_openly_connected(self) -> None:
        for filename in EXPECTED:
            svg = (self.output_dir / filename).read_text(encoding="utf-8")
            if filename not in {"32-electrical-topology.svg", "33-bedroom-electrical-detail.svg", "34-bathroom-electrical-detail.svg", "50-kitchen-bath-details.svg"}:
                self.assertIn('data-connection="hall-a-b-open"', svg)
                self.assertNotIn("M475 450H600", svg)

    def test_checked_in_outputs_match_generator(self) -> None:
        checked_in = Path(__file__).resolve().parents[1] / "diagrams" / "v5"
        for filename in EXPECTED:
            self.assertEqual(
                (checked_in / filename).read_text(encoding="utf-8"),
                (self.output_dir / filename).read_text(encoding="utf-8"),
                f"{filename} 已过期，请运行 make diagrams",
            )

    def test_v4_remains_archived_and_marked_v4(self) -> None:
        archived = Path(__file__).resolve().parents[1] / "diagrams" / "v4"
        self.assertEqual(len(list(archived.glob("*.svg"))), 10)
        for path in archived.glob("*.svg"):
            self.assertIn("V4 讨论图", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
