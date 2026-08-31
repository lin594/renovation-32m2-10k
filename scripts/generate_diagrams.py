#!/usr/bin/env python3
"""Generate the responsibility-separated V5 renovation diagrams."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable


WIDTH = 1400
HEIGHT = 850
SCALE = 100
ORIGIN_X = 100
ORIGIN_Y = 130
ROOT = Path(__file__).resolve().parents[1]

OUTPUTS: dict[str, tuple[str, str, Callable[[], str]]] = {}


def sx(y: float) -> float:
    """Source east/west coordinate y -> SVG x."""
    return ORIGIN_X + y * SCALE


def sy(x: float) -> float:
    """Source north/south coordinate x -> SVG y."""
    return ORIGIN_Y + x * SCALE


def rect(x1: float, x2: float, y1: float, y2: float, css: str, extra: str = "") -> str:
    return (
        f'<rect x="{sx(y1):g}" y="{sy(x1):g}" width="{(y2-y1)*SCALE:g}" '
        f'height="{(x2-x1)*SCALE:g}" class="{css}" {extra}/>'
    )


def text(x: float, y: float, value: str, css: str = "note", extra: str = "") -> str:
    return f'<text x="{x:g}" y="{y:g}" class="{css}" {extra}>{value}</text>'


DEFS = r"""
<defs>
  <pattern id="hatch" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="12" height="12" fill="#f1f5f9"/><line y2="12" stroke="#cbd5e1" stroke-width="4"/>
  </pattern>
  <pattern id="danger" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="10" height="10" fill="#fff1f2"/><line y2="10" stroke="#fecaca" stroke-width="3"/>
  </pattern>
  <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0 0L8 4 0 8z" fill="#334155"/></marker>
  <marker id="blue-arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0 0L8 4 0 8z" fill="#2563eb"/></marker>
  <style>
    text{font-family:"Source Han Sans SC","Heiti SC","Arial Unicode MS",sans-serif}
    .wall{fill:none;stroke:#1f2937;stroke-width:7;stroke-linecap:square;stroke-linejoin:miter}
    .iw{fill:none;stroke:#475569;stroke-width:5;stroke-linecap:square}
    .win{stroke:#0284c7;stroke-width:8}.winc{stroke:#e0f2fe;stroke-width:2.5}
    .title{font-size:30px;font-weight:750;fill:#172033}.subtitle{font-size:14px;fill:#64748b}
    .room{font-size:18px;font-weight:750;fill:#334155;text-anchor:middle}.roomsub{font-size:12px;fill:#64748b;text-anchor:middle}
    .note{font-size:14px;fill:#334155}.small{font-size:12px;fill:#526175}.micro{font-size:10px;fill:#64748b}
    .panel{fill:#fff;stroke:#d6dae1;stroke-width:1.5}.fixed{fill:#fffdf8;stroke:#64748b;stroke-width:2}
    .planned{fill:#fff7ed;stroke:#f97316;stroke-width:2;stroke-dasharray:7 5}
    .water{fill:none;stroke:#0284c7;stroke-width:4}.hot{fill:none;stroke:#dc2626;stroke-width:4}
    .drain{fill:none;stroke:#0f766e;stroke-width:5}.gas{fill:none;stroke:#ea580c;stroke-width:4}
    .power{fill:none;stroke:#2563eb;stroke-width:3}.network{fill:none;stroke:#7c3aed;stroke-width:3;stroke-dasharray:7 5}
    .danger{fill:#fff1f2;stroke:#dc2626;stroke-width:2}.cat{fill:none;stroke:#16a34a;stroke-width:6;stroke-dasharray:8 5}
    .dim{fill:none;stroke:#64748b;stroke-width:1.5}.dimtext{font-size:12px;fill:#475569;text-anchor:middle}
    .center{text-anchor:middle}.bold{font-weight:700}.orange{fill:#c2410c}.red{fill:#b91c1c}.blue{fill:#1d4ed8}.green{fill:#15803d}.purple{fill:#6d28d9}
  </style>
</defs>
"""


def document(role: str, title_value: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" data-diagram-role="{role}" role="img">
<title>{title_value}</title>
<desc>{subtitle}</desc>
{DEFS}
<rect width="{WIDTH}" height="{HEIGHT}" fill="#fbfaf7"/>
<text x="70" y="52" class="title">{title_value}</text>
<text x="70" y="78" class="subtitle">{subtitle}</text>
{body}
<text x="100" y="800" class="small">V5 讨论图｜北↑ 东→｜坐标和尺寸以 house.yaml 与现场复测为准，不替代施工放样或专项验收。</text>
</svg>
'''


def room_fields(mut: bool = False) -> str:
    alpha = ' opacity="0.68"' if mut else ""
    return f'''
<rect x="100" y="130" width="300" height="400" fill="#f7ead7"{alpha}/>
<rect x="100" y="530" width="300" height="100" fill="#e6f3e8"{alpha}/>
<rect x="400" y="130" width="200" height="200" fill="#f9efd0"{alpha}/>
<rect x="400" y="330" width="100" height="120" fill="#dff3f7"{alpha}/>
<rect x="500" y="330" width="100" height="120" fill="#edf1f5"{alpha}/>
<rect x="400" y="450" width="200" height="80" fill="#edf1f5"{alpha}/>
<rect x="600" y="130" width="300" height="300" fill="#ece8f7"{alpha}/>
<rect x="600" y="430" width="300" height="100" fill="url(#hatch)"/>
'''


def base_walls() -> str:
    # Openings are cut out after drawing the shared wall network.
    return '''
<path class="wall" d="M100 130H900V430H600V530H400V630H100Z"/>
<path class="iw" d="M400 130V450M400 330H520M500 330V450M400 450H405M475 450H500M600 130V345M600 425V530M600 430H900M100 530H250"/>
<g data-connection="hall-a-b-open"><!-- 走廊A与走廊B在x=3.2、y[4,5]处无隔墙并连续连通 --></g>
<path d="M400 450V530" stroke="#f7ead7" stroke-width="10"/>
<path d="M520 330H600" stroke="#edf1f5" stroke-width="10"/>
<path d="M405 450H475" stroke="#edf1f5" stroke-width="10"/>
<path d="M600 345V425" stroke="#ece8f7" stroke-width="10"/>
<path d="M600 450V530" stroke="#f1f5f9" stroke-width="10"/>
<path d="M250 530H400" stroke="#e6f3e8" stroke-width="10"/>
'''


def windows() -> str:
    paths = "M200 130H300M450 130H550M700 130H800M100 535V625M110 630H390M435 330H485"
    return f'<path class="win" d="{paths}"/><path class="winc" d="{paths}"/>'


def room_labels() -> str:
    return '''
<text x="250" y="270" class="room">客厅</text><text x="250" y="291" class="roomsub">净4.0×3.0m</text>
<text x="500" y="225" class="room">厨房</text><text x="500" y="246" class="roomsub">约2.0×&lt;2.0m</text>
<text x="450" y="388" class="room">卫生间</text><text x="450" y="408" class="roomsub">设计基准约1.05×0.75m</text>
<text x="750" y="280" class="room">卧室</text><text x="750" y="301" class="roomsub">净3.0×3.0m</text>
<text x="550" y="390" class="room">走廊B</text><text x="500" y="492" class="room">玄关 / 走廊A</text>
<text x="250" y="586" class="room">转角阳台</text><text x="750" y="482" class="room">公共走廊（非套内）</text>
'''


def plan_base(labels: bool = True, muted: bool = False) -> str:
    return room_fields(muted) + base_walls() + windows() + (room_labels() if labels else "")


def sidebar(title_value: str, lines: list[str], legend: list[tuple[str, str]] | None = None) -> str:
    items = [f'<rect x="970" y="120" width="370" height="560" rx="14" class="panel"/>',
             f'<text x="994" y="160" class="note bold">{title_value}</text>']
    y = 196
    for line in lines:
        css = "note"
        if line.startswith("!"):
            line, css = line[1:], "note red"
        items.append(f'<text x="994" y="{y}" class="{css}">{line}</text>')
        y += 29
    if legend:
        y = max(y + 10, 520)
        items.append(f'<line x1="994" y1="{y-18}" x2="1316" y2="{y-18}" stroke="#e2e8f0"/>')
        for color, label in legend:
            items.append(f'<line x1="998" y1="{y}" x2="1030" y2="{y}" stroke="{color}" stroke-width="5"/>')
            items.append(f'<text x="1044" y="{y+4}" class="small">{label}</text>')
            y += 29
    return "".join(items)


def existing_survey() -> str:
    markers = '''
<circle cx="400" cy="330" r="9" fill="#0f766e"/><text x="414" y="334" class="small">唯一排水立管</text>
<circle cx="400" cy="350" r="8" fill="#0284c7"/><text x="414" y="354" class="small">入户水</text>
<circle cx="598" cy="165" r="9" fill="#ea580c"/><text x="610" y="160" class="small orange">燃气入口</text>
<rect x="579" y="430" width="36" height="22" rx="3" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/><text x="620" y="424" class="small blue">配电箱</text>
<rect x="160" y="509" width="74" height="20" rx="5" fill="#eff6ff" stroke="#0284c7" stroke-width="2"/><text x="197" y="500" class="small center">客厅空调</text>
<rect x="602" y="155" width="20" height="74" rx="5" fill="#eff6ff" stroke="#0284c7" stroke-width="2"/><text x="635" y="151" class="small">卧室空调</text>
<circle cx="750" cy="280" r="13" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2"/><text x="750" y="306" class="small center">吊扇</text>
<circle cx="250" cy="330" r="10" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2"/><text x="250" y="354" class="small center">吊扇钩</text>
<rect x="486" y="346" width="13" height="38" class="danger"/><text x="478" y="343" class="small red" text-anchor="end">浴霸</text>
<text x="560" y="319" class="small orange">厨房旧门已拆</text><text x="445" y="470" class="small orange">卫浴旧门已拆</text>
<text x="640" y="340" class="small orange">卧室旧门已拆</text><text x="375" y="520" class="small orange" text-anchor="end">通道旧门已拆</text>
'''
    side = sidebar("本图只确认“现场有什么”", [
        "墙体、洞口、窗户和公共走廊",
        "固定的水、排水、燃气和配电点",
        "已有空调、吊扇、吊扇钩和浴霸",
        "四个室内旧门均已拆除",
        "卧室门洞较旧图北移约5cm",
        "不表达家具购买和假定线路",
    ], [("#1f2937", "墙体/固定边界"), ("#0284c7", "水或固定设备"), ("#ea580c", "燃气点")])
    return document("existing-survey", "00 现状测量图", "固定空间、门窗洞口与已确认现场点位", plan_base() + markers + side)


def furniture_circulation() -> str:
    furniture = f'''
<path d="M880 480H520V470H360V510" fill="none" stroke="#16a34a" stroke-width="18" opacity=".20" stroke-linecap="round"/>
<path d="M880 480H520V470H360" fill="none" stroke="#15803d" stroke-width="2.5" stroke-dasharray="8 6" marker-end="url(#arrow)"/>
{rect(0,1.6,0,.9,"planned",'data-status="not-purchased"')}<text x="145" y="215" class="small center">双人沙发｜未购买</text>
<g data-furniture="robot-vacuum" data-status="existing" data-power="always-on">
  <rect x="105" y="300" width="40" height="40" rx="8" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/>
  <circle cx="125" cy="320" r="14" fill="none" stroke="#0284c7" stroke-width="2"/>
  <text x="150" y="315" class="micro blue">扫地机｜已有</text><text x="150" y="329" class="micro blue">低位常电</text>
</g>
<g data-furniture="robot-over-table" data-status="not-purchased" data-clear-under="true">
  <rect x="100" y="290" width="45" height="85" class="planned"/>
  <path d="M145 298V365" stroke="#f97316" stroke-width="3"/>
  <text x="155" y="350" class="micro orange">上方窄桌/储物台</text>
</g>
<path d="M145 320H215" fill="none" stroke="#16a34a" stroke-width="3" stroke-dasharray="7 5" marker-end="url(#arrow)" data-robot-approach="east-clear"/>
<g data-outlet-branch="LR-SOFA-ROBOT">
  <rect x="102" y="335" width="10" height="10" fill="#2563eb"/><text x="116" y="343" class="micro blue">上部充电</text>
  <rect x="102" y="305" width="10" height="10" fill="#1d4ed8"/><text x="116" y="303" class="micro blue">机器人常电</text>
</g>
{rect(2.5,3.2,0,1.3,"fixed",'data-status="existing-to-refinish"')}<text x="165" y="402" class="small center">书桌｜已有</text><text x="165" y="419" class="micro center">待改黑胡桃色</text>
<circle cx="175" cy="355" r="18" class="planned" data-status="not-purchased"/>
<text x="175" y="359" class="micro center">椅</text>
{rect(3.3,4,.6,1.3,"fixed")}<text x="195" y="494" class="small center">冰箱</text>
{rect(3.2,4,0,.6,"planned")}<text x="130" y="483" class="small center">角落</text><text x="130" y="499" class="micro center">功能待定</text>
{rect(2.4,3.2,2.2,3,"planned",'data-status="not-purchased"')}<circle cx="360" cy="411" r="24" fill="none" stroke="#f97316" stroke-width="2"/><text x="360" y="382" class="small center">洗烘一体机｜未购买</text>
{rect(1.6,2.4,2.2,3,"fixed")}<text x="360" y="330" class="small center">餐桌</text>
{rect(0,1.3,5,7,"fixed")}<text x="700" y="198" class="small center">双人床1.3×2.0</text>
{rect(0,3,7.2,8,"fixed")}<text x="860" y="320" class="small center" transform="rotate(-90 860 320)">衣柜深0.8m｜帘子</text>
{rect(1.3,1.7,5,7,"planned")}<text x="700" y="287" class="small center">长窄柜/书桌｜尺寸待定</text>
{rect(2,2.58,3.1,3.5,"planned",'data-status="not-purchased"')}<text x="430" y="373" class="micro center">马桶</text>
{rect(2.8,3.2,3.7,4,"planned",'data-status="not-purchased"')}<text x="485" y="438" class="micro center">浴室柜</text>
<rect x="350" y="536" width="44" height="88" class="fixed"/><text x="372" y="580" class="small center" transform="rotate(-90 372 580)">阳台柜</text>
<path d="M114 548H342" stroke="#15803d" stroke-width="3" stroke-dasharray="10 6"/><text x="230" y="570" class="micro center">可升降</text>
<path d="M130 590H330" stroke="#64748b" stroke-width="3"/><text x="230" y="609" class="micro center">损坏后固定使用</text>
<circle cx="1000" cy="720" r="0" fill="none"/>
'''
    # Intentionally no open bath-slider leaf: circulation must remain readable.
    side = sidebar("采购与摆放状态", [
        "橙虚线：未购买、未定制或尺寸待定",
        "书桌已有，待做黑胡桃色小样改色",
        "椅子、沙发和洗烘机尚未购买",
        "马桶、浴室柜尚未购买",
        "扫地机器人已有，停靠在沙发与书桌之间",
        "上方窄桌下部无前腿，不挡回充与取出",
        "低位机器人常电；上部充电可选智能插座",
        "主通道仍需保持约0.7m净宽",
        "卫生间移门不在本图画开启门扇",
        "!家具下单前必须现场复测",
    ], [("#64748b", "已有/固定/明确摆位"), ("#f97316", "计划或未购买"), ("#15803d", "主要通行路径")])
    return document("furniture-circulation", "10 家具与动线图", "家具采购状态、计划摆位与主要通道净空", plan_base(False) + furniture + room_labels() + side)


def plumbing_gas() -> str:
    routes = '''
<circle cx="400" cy="350" r="9" fill="#0284c7"/><text x="386" y="345" class="small blue" text-anchor="end">入户水</text>
<path class="water" d="M400 350V365H430M400 350V430H480M400 350V290H425M400 350H360V410" marker-end="url(#blue-arrow)"/>
<text x="438" y="365" class="micro blue">马桶冷水</text><text x="484" y="432" class="micro blue">浴室柜冷水</text><text x="326" y="408" class="micro blue">洗衣机冷水</text>
<path class="hot" d="M425 280V340H450V400M450 340H480"/>
<text x="435" y="270" class="small red">热水器出水回卫生间</text>
<circle cx="400" cy="330" r="11" fill="#0f766e"/><text x="414" y="326" class="small green">排水立管</text>
<circle cx="430" cy="430" r="9" fill="#0f766e"/><text x="444" y="434" class="small green">扬子纯铜防臭地漏</text>
<path class="drain" d="M360 410H430V430M430 365L400 330M430 430L400 330" stroke-dasharray="8 5"/>
<circle cx="430" cy="365" r="7" fill="#fff" stroke="#0f766e" stroke-width="3"/><text x="440" y="382" class="micro">马桶坑位：距北墙0.35m</text>
<circle cx="598" cy="165" r="10" fill="#ea580c"/><text x="610" y="160" class="small orange">燃气入口</text>
<path class="gas" d="M588 165H550" marker-end="url(#arrow)"/><text x="518" y="181" class="small orange">燃气灶直连支路</text>
<path class="gas" d="M588 165V145H420V270" marker-end="url(#arrow)"/><text x="500" y="136" class="small orange center">热水器支路：沿北墙向西约2m</text>
<rect x="405" y="255" width="42" height="62" rx="4" fill="#fff7ed" stroke="#ea580c" stroke-width="2"/><text x="454" y="283" class="small orange">燃气热水器</text>
'''
    side = sidebar("本图只回答管线连接", [
        "蓝：冷水；红：热水回路",
        "绿：排水及唯一立管",
        "橙：燃气入口和两条支路",
        "地漏已安装，包含于500元服务",
        "水泥/沙子/堵漏王用于固定改管",
        "!燃气管遮盖和检修仍需验收确认",
        "!封闭饰面前应做联合排水测试",
    ], [("#0284c7", "冷水"), ("#dc2626", "热水"), ("#0f766e", "排水"), ("#ea580c", "燃气")])
    return document("plumbing-gas", "20 给排水与燃气图", "冷热水、排水、地漏、马桶坑位与燃气双支路", plan_base(False, True) + routes + room_labels() + side)


def electrical_low_voltage() -> str:
    points = '''
<rect x="575" y="430" width="44" height="25" rx="3" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/><text x="625" y="424" class="small blue">入户配电箱</text>
<circle cx="600" cy="345" r="11" fill="#2563eb"/><text x="600" y="349" fill="#fff" class="small center">1</text>
<circle cx="520" cy="330" r="11" fill="#2563eb"/><text x="520" y="334" fill="#fff" class="small center">2</text>
<circle cx="475" cy="450" r="11" fill="#2563eb"/><text x="475" y="454" fill="#fff" class="small center">3</text>
<circle cx="400" cy="450" r="11" fill="#2563eb"/><text x="400" y="454" fill="#fff" class="small center">4</text>
<path class="power" d="M590 442L600 345M590 442L520 330M590 442L475 450M590 442L400 450" stroke-dasharray="7 6" opacity=".45"/>
<rect x="190" y="518" width="11" height="11" fill="#1e3a8a"/><text x="180" y="550" class="micro">冰箱南侧暗盒</text>
<rect x="394" y="402" width="11" height="11" fill="#1e3a8a"/><text x="318" y="398" class="micro">洗衣机东侧暗盒</text>
<rect x="594" y="326" width="11" height="11" fill="#1e3a8a"/><text x="610" y="321" class="micro">卧室门北侧暗盒</text>
<rect x="160" y="509" width="74" height="20" rx="5" fill="#eff6ff" stroke="#0284c7" stroke-width="2"/><text x="197" y="500" class="small center">客厅空调</text>
<rect x="602" y="155" width="20" height="74" rx="5" fill="#eff6ff" stroke="#0284c7" stroke-width="2"/><text x="636" y="151" class="small">卧室空调</text>
<circle cx="196" cy="520" r="9" fill="#fff" stroke="#dc2626" stroke-width="2" data-device-protection="SRCD-AC-LIV"/><text x="208" y="540" class="micro red">空调末端漏保</text>
<circle cx="612" cy="190" r="9" fill="#fff" stroke="#dc2626" stroke-width="2" data-device-protection="SRCD-AC-BED"/><text x="630" y="190" class="micro red">末端漏保</text>
<circle cx="360" cy="405" r="9" fill="#fff" stroke="#dc2626" stroke-width="2" data-device-protection="SRCD-WASHER"/><text x="322" y="422" class="micro red">洗烘专用漏保</text>
<circle cx="750" cy="280" r="13" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2"/><text x="750" y="306" class="small center">卧室吊扇</text>
<circle cx="250" cy="330" r="10" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2"/><text x="250" y="354" class="small center">客厅吊扇钩</text>
<rect x="486" y="346" width="13" height="38" class="danger"/><text x="478" y="343" class="small red" text-anchor="end">浴霸待核验</text>
<rect x="470" y="410" width="28" height="20" rx="3" fill="#fff1f2" stroke="#dc2626" stroke-width="2" data-device-protection="RCD-BATH-01"/><text x="466" y="440" class="micro red" text-anchor="end">双极30mA</text>
<rect x="102" y="305" width="12" height="12" fill="#2563eb" data-outlet="robot-always-on"/><rect x="102" y="337" width="12" height="12" fill="#7c3aed" data-outlet="sofa-charge"/>
<text x="122" y="315" class="micro blue">扫地机常电</text><text x="122" y="348" class="micro purple">沙发上部充电</text>
<circle cx="600" cy="450" r="9" fill="#7c3aed"/><path class="network" d="M600 450H540V506"/>
<rect x="488" y="506" width="104" height="24" rx="3" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2" data-device-shelf="hall-a" data-wall-anchor="hall-a-south-wall"/><text x="540" y="520" class="micro purple center">光猫 / Wi-Fi / EVE V</text>
<text x="540" y="550" class="micro purple center">背面贴走廊A南墙｜至少4个常电位</text>
<text x="610" y="466" class="micro purple">网线与入户电线同洞口位置</text>
'''
    side = sidebar("点位图，不是最终回路图", [
        "1卧室门北端；2厨房门西端",
        "3卫生间门东端；4客厅通道北端",
        "深蓝方块：优先复用的现有暗盒",
        "紫：网线入口和玄关设备架",
        "EVE V长期运行，架内短网线接路由器",
        "光猫/路由器/EVE V需至少4个常电位",
        "扫地机低位常电+沙发上部充电各1点",
        "空调×2、洗烘机均有设备级漏保候选",
        "卫生间由MCB-05经双极末端漏保供电",
        "已确认两线制无PE；三孔面板须持久标识",
        "!蓝色6mm²余线改色方案未批准",
        "不在本图假定线径和最终线槽路线",
    ], [("#2563eb", "强电/穿墙点"), ("#1e3a8a", "现有暗盒"), ("#7c3aed", "弱电/网络"), ("#dc2626", "安全待核验")])
    return document("electrical-low-voltage", "30 强弱电点位图", "强电、设备、暗盒、穿墙洞和网络设备点位", plan_base(False, True) + points + room_labels() + side)


def electrical_routes() -> str:
    routes = '''
<rect x="575" y="430" width="44" height="25" rx="3" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/><text x="626" y="426" class="small blue">配电箱｜5支路</text>
<g data-route-kind="surface" fill="none" stroke="#2563eb" stroke-width="4">
  <path d="M590 442L600 345V255" data-circuit="RCBO-01"/><path d="M590 442L520 330V235" data-circuit="RCBO-02"/>
  <path d="M590 442H400V315" data-circuit="RCBO-03"/>
</g>
<g data-route-kind="lighting-surface" fill="none" stroke="#f59e0b" stroke-width="3" stroke-dasharray="9 5">
  <path d="M590 438L600 345H690" data-circuit="MCB-04"/><path d="M590 438L520 330H560" data-circuit="MCB-04"/>
  <path d="M590 450H520V478" data-circuit="MCB-04"/><path d="M590 438H400V280" data-circuit="MCB-04"/>
</g>
<path d="M590 446H475V410" fill="none" stroke="#dc2626" stroke-width="4" data-circuit="MCB-05" data-bath-feeder="continuous-no-joint"/>
<circle cx="600" cy="345" r="11" fill="#fff" stroke="#2563eb" stroke-width="3" data-electrical-hole="E-HOLE-01"/><text x="600" y="349" class="micro center">01</text>
<circle cx="520" cy="330" r="11" fill="#fff" stroke="#2563eb" stroke-width="3" data-electrical-hole="E-HOLE-02"/><text x="520" y="334" class="micro center">02</text>
<circle cx="475" cy="450" r="11" fill="#fff" stroke="#2563eb" stroke-width="3" data-electrical-hole="E-HOLE-03"/><text x="475" y="454" class="micro center">03</text>
<circle cx="400" cy="450" r="11" fill="#fff" stroke="#2563eb" stroke-width="3" data-electrical-hole="E-HOLE-04"/><text x="400" y="454" class="micro center">04</text>
<g data-device-protection="RCD-BATH-01" data-location-preference="bath-dry-high" data-fallback="hall-a-outside">
  <rect x="455" y="390" width="40" height="28" rx="4" fill="#fff1f2" stroke="#dc2626" stroke-width="2"/>
  <text x="475" y="402" class="micro red center">2P</text><text x="475" y="414" class="micro red center">30mA</text>
  <text x="450" y="382" class="micro red" text-anchor="end">进门后先保护</text>
</g>

<rect x="488" y="506" width="104" height="24" rx="3" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2" data-device-shelf="hall-a" data-wall-anchor="hall-a-south-wall"/>
<line x1="488" y1="530" x2="592" y2="530" stroke="#7c3aed" stroke-width="7" data-shelf-wall-contact="true"/>
<text x="540" y="520" class="micro purple center">设备架｜至少4位常电</text><text x="540" y="550" class="micro purple center">背面贴走廊A南墙</text>
<path class="network" d="M600 450H540V506"/><text x="607" y="469" class="micro purple">网线入口</text>

<rect x="594" y="244" width="15" height="28" fill="#fffbeb" stroke="#f59e0b" stroke-width="2" data-box="E-BOX-BED-FAN"/>
<text x="618" y="292" class="micro orange">调速器暗盒</text>
<path d="M600 345V258" fill="none" stroke="#f59e0b" stroke-width="4" data-fan-feed="surface-after-E-HOLE-01"/>
<path d="M609 258C655 250 695 260 750 280" fill="none" stroke="#7c3aed" stroke-width="4" stroke-dasharray="2 7" data-fan-feed="existing-concealed"/>
<circle cx="750" cy="280" r="14" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2"/><text x="750" y="284" class="micro center">吊扇</text>
<text x="665" y="238" class="micro purple center">既有暗埋线｜先测通断与绝缘</text>

<g data-balcony-power="deferred" data-no-electrical-penetration="true">
  <path d="M250 530H400" stroke="#dc2626" stroke-width="7" stroke-dasharray="10 7"/>
  <circle cx="325" cy="560" r="22" fill="#fff1f2" stroke="#dc2626" stroke-width="3"/><path d="M310 545L340 575M340 545L310 575" stroke="#dc2626" stroke-width="4"/>
  <text x="250" y="600" class="small red center">阳台无穿线孔｜本期无永久220V</text>
  <text x="250" y="620" class="micro red center">不钻孔、不夹移门；充电灯/临时插电入住后再定</text>
</g>
'''
    side = sidebar("31 只看真实空间路径", [
        "四个圆点：现有穿线孔01～04",
        "蓝实线：三个RCBO设备/插座路径",
        "橙虚线：MCB-04全部非卫浴照明",
        "红实线：MCB-05卫生间连续专用馈线",
        "紫点线：吊扇既有暗埋线",
        "设备架背面与走廊A南墙相接",
        "卧室调速器只用原西墙暗盒",
        "阳台没有穿线孔，本期不设永久供电",
        "所有线路止于客厅侧，不跨阳台移门",
        "E-HOLE-03后先接RCD-BATH-01再分支",
        "漏保箱无合格干区时移至走廊A门外",
        "扫地机已定在沙发/书桌之间，余量2m",
        "!本图不表达PCT内部拓扑和通电批准",
    ], [("#2563eb", "三个RCBO设备/插座明线"), ("#f59e0b", "MCB-04非卫浴照明"), ("#dc2626", "MCB-05卫浴馈线/禁入边界"), ("#7c3aed", "既有暗线/弱电")])
    labels = '''
<text x="230" y="230" class="room">客厅</text><text x="475" y="190" class="room">厨房</text>
<text x="450" y="390" class="small center bold">卫生间</text><text x="830" y="335" class="room">卧室</text>
<text x="550" y="390" class="small center bold">走廊B</text><text x="520" y="490" class="small center bold">玄关 / 走廊A</text>
<text x="250" y="585" class="room">转角阳台</text><text x="750" y="482" class="room">公共走廊（非套内）</text>
'''
    return document("electrical-routes", "31 强电真实空间走线图", "四个穿线孔、五回路真实路径、卫生间先漏保与阳台禁入边界", plan_base(False, True) + routes + labels + side)


def electrical_topology_v5() -> str:
    topology = '''
<rect x="55" y="115" width="205" height="575" rx="14" class="panel"/><text x="157" y="150" class="note bold center">配电箱｜固定5支路</text>
<g data-circuit="RCBO-01"><rect x="78" y="180" width="160" height="58" rx="8" fill="#e0f2fe" stroke="#0284c7" stroke-width="3"/><text x="158" y="202" class="small bold center">漏保1｜RCBO-01</text><text x="158" y="222" class="micro center">卧室插座 / 空调</text></g>
<g data-circuit="RCBO-02"><rect x="78" y="270" width="160" height="58" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="3"/><text x="158" y="292" class="small bold center">漏保2｜RCBO-02</text><text x="158" y="312" class="micro center">厨房插座 / 设备</text></g>
<g data-circuit="RCBO-03"><rect x="78" y="360" width="160" height="72" rx="8" fill="#fee2e2" stroke="#dc2626" stroke-width="3"/><text x="158" y="382" class="small bold center">漏保3｜RCBO-03</text><text x="158" y="402" class="micro center">客厅 / 洗烘 / 冰箱</text><text x="158" y="418" class="micro center">玄关设备架</text></g>
<g data-circuit="MCB-04"><rect x="78" y="470" width="160" height="72" rx="8" fill="#fef3c7" stroke="#f59e0b" stroke-width="3"/><text x="158" y="492" class="small bold center">空开4｜MCB-04</text><text x="158" y="512" class="micro center">全部非卫浴照明</text><text x="158" y="528" class="micro center">+ 卧室吊扇</text></g>
<g data-circuit="MCB-05"><rect x="78" y="580" width="160" height="72" rx="8" fill="#ede9fe" stroke="#7c3aed" stroke-width="3"/><text x="158" y="602" class="small bold center">空开5｜MCB-05</text><text x="158" y="622" class="micro center">卫生间专用馈线</text><text x="158" y="638" class="micro center">上游不设分支</text></g>

<g fill="none" stroke="#64748b" stroke-width="2.5" marker-end="url(#arrow)"><path d="M238 209H305"/><path d="M238 299H305"/><path d="M238 396H305"/><path d="M238 506H305"/><path d="M238 616H305"/></g>
<g data-junction="JB-BED" data-terminal-status="logical"><rect x="305" y="175" width="140" height="68" rx="9" class="fixed"/><text x="375" y="200" class="small bold center">JB-BED</text><text x="375" y="220" class="micro center">3个逻辑分支</text></g>
<g data-junction="JB-KIT" data-terminal-status="logical"><rect x="305" y="265" width="140" height="68" rx="9" class="fixed"/><text x="375" y="290" class="small bold center">JB-KIT</text><text x="375" y="310" class="micro center">3个逻辑分支</text></g>
<g data-junction="JB-R3" data-terminal-status="logical"><rect x="305" y="360" width="140" height="68" rx="9" class="fixed"/><text x="375" y="385" class="small bold center">JB-R3</text><text x="375" y="405" class="micro center">设备架 / 客厅</text></g>
<g data-junction="JB-L4" data-terminal-status="logical"><rect x="305" y="470" width="140" height="72" rx="9" class="fixed"/><text x="375" y="495" class="small bold center">JB-L4</text><text x="375" y="515" class="micro center">4个照明分区</text><text x="375" y="531" class="micro center">端子型号待换算</text></g>
<g data-device-protection="RCD-BATH-01"><rect x="305" y="575" width="140" height="82" rx="9" fill="#fff1f2" stroke="#dc2626" stroke-width="3"/><text x="375" y="598" class="small bold center">RCD-BATH-01</text><text x="375" y="618" class="micro center">双极 / ≤30mA</text><text x="375" y="635" class="micro center">TEST / RESET</text><text x="375" y="650" class="micro red center">先保护，后分支</text></g>

<g fill="none" stroke="#94a3b8" stroke-width="2.2" marker-end="url(#arrow)"><path d="M445 209H505"/><path d="M445 299H505"/><path d="M445 394H505"/><path d="M445 506H505"/><path d="M445 616H505"/></g>
<text x="520" y="188" class="small bold" data-device-protection="SRCD-AC-BED">卧室空调 → SRCD-AC-BED</text><text x="520" y="214" class="small">床北常电插座</text><text x="520" y="238" class="small">床南常电插座</text>
<text x="520" y="278" class="small bold">燃气热水器</text><text x="520" y="304" class="small">油烟机</text><text x="520" y="330" class="small">台面电器</text>
<text x="520" y="378" class="small bold">玄关设备架</text><text x="520" y="405" class="small">客厅 → JB-LIV</text>
<g data-junction="JB-LIV" data-terminal-status="logical"><rect x="715" y="360" width="140" height="74" rx="9" class="fixed"/><text x="785" y="385" class="small bold center">JB-LIV</text><text x="785" y="405" class="micro center">空调 / 冰箱 / 洗烘</text><text x="785" y="421" class="micro center">+ 普通插座链</text></g>
<text x="875" y="374" class="small" data-device-protection="SRCD-AC-LIV">空调 → SRCD-AC-LIV</text><text x="875" y="399" class="small" data-device-protection="SRCD-WASHER">洗烘 → SRCD-WASHER</text><text x="875" y="424" class="small">机器人常电 / 沙发充电</text>
<text x="520" y="480" class="small bold">卧室照明 / 吊扇</text><text x="520" y="504" class="small">厨房照明</text><text x="520" y="528" class="small">走廊A/B + 客厅照明</text>
<g data-junction="JB-BATH" data-terminal-status="logical" data-bath-load-downstream="true"><rect x="505" y="575" width="145" height="82" rx="9" class="fixed"/><text x="577" y="600" class="small bold center">JB-BATH</text><text x="577" y="620" class="micro center">漏保下游逻辑分线</text><text x="577" y="638" class="micro center">浴霸 / 镜柜 / 照明</text></g>
<text x="675" y="588" class="small" data-device-protection="SRCD-BATH-HEATER">浴霸设备连接保护</text><text x="675" y="616" class="small" data-device-protection="SRCD-BATH-MIRROR">除雾镜柜设备连接保护</text><text x="675" y="644" class="small">卫生间防潮照明</text>

<rect x="55" y="710" width="920" height="72" rx="12" class="danger"/><text x="78" y="737" class="note red bold">两线制边界：</text><text x="190" y="737" class="note red">三孔面板PE端子不连接并贴“本户无PE”；严禁N/PE短接或管道接地。</text><text x="78" y="764" class="small red">上下级漏保可能同时跳闸；PCT仅为六个逻辑节点，实物型号和数量须现场换算。</text>
'''
    side = sidebar("五回路与保护层", [
        "恰好3个RCBO + 2个MCB",
        "MCB-04：全部非卫浴固定照明",
        "MCB-05：仅卫生间连续馈线",
        "卫生间先经双极≤30mA漏保",
        "六个PCT逻辑节点，不是实购数量",
        "原JB-L5已删除；新增JB-BATH",
        "插座仍为14组，卫浴2点另计设备连接",
        "空调×2、洗烘机增加设备级漏保",
        "普通插座常电；智能墙壁开关零火版",
        "机器人常电不受智能控制",
        "上下级漏保分别实测，不宣称选择性",
        "!所有参数仍受铭牌、负载和专业检测门禁",
    ])
    return document("electrical-topology", "32 五回路与分级漏保拓扑图", "固定五支路、六个逻辑分线节点、设备级漏保和两线制边界", topology + side)


def bathroom_electrical_detail() -> str:
    detail = '''
<rect x="70" y="115" width="850" height="590" rx="16" fill="#f8fafc" stroke="#475569" stroke-width="3"/>
<text x="495" y="150" class="note bold center">卫生间专用馈线与末端保护｜逻辑展开</text>
<g data-circuit="MCB-05"><rect x="105" y="200" width="145" height="72" rx="9" fill="#ede9fe" stroke="#7c3aed" stroke-width="3"/><text x="177" y="225" class="small bold center">MCB-05</text><text x="177" y="246" class="micro center">卫生间专用空开</text></g>
<path d="M250 236H390" fill="none" stroke="#dc2626" stroke-width="5" marker-end="url(#arrow)" data-upstream-segment="continuous-no-joint-no-branch"/>
<text x="320" y="216" class="micro red center">连续 / 机械保护 / 无接头 / 无分支</text>
<g data-device-protection="RCD-BATH-01" data-poles="L+N" data-trip-ma-max="30"><rect x="390" y="185" width="180" height="104" rx="10" fill="#fff1f2" stroke="#dc2626" stroke-width="3"/><text x="480" y="211" class="small bold center">RCD-BATH-01</text><text x="480" y="234" class="small center">L+N双极｜≤30mA</text><text x="480" y="256" class="micro center">TEST / RESET｜高位可检修箱</text><text x="480" y="276" class="micro red center">必须先保护，再产生任何分支</text></g>
<path d="M570 236H640" fill="none" stroke="#64748b" stroke-width="3" marker-end="url(#arrow)"/>
<g data-junction="JB-BATH" data-terminal-status="logical"><rect x="640" y="195" width="150" height="84" rx="9" class="fixed"/><text x="715" y="222" class="small bold center">JB-BATH</text><text x="715" y="244" class="micro center">L/N逻辑分线</text><text x="715" y="263" class="micro center">PCT实物待换算</text></g>

<g data-bath-load-downstream="true">
 <path d="M715 279V360H260" fill="none" stroke="#0284c7" stroke-width="3"/>
 <path d="M715 320H480" fill="none" stroke="#0284c7" stroke-width="3"/>
 <path d="M715 340H700" fill="none" stroke="#0284c7" stroke-width="3"/>
 <g data-device-protection="SRCD-BATH-HEATER"><rect x="120" y="335" width="230" height="110" rx="9" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/><text x="235" y="362" class="small bold center">浴霸连接点</text><text x="235" y="386" class="micro center">说明允许插头：防水插座式漏保</text><text x="235" y="407" class="micro center">只允许固定接线：双极隔离+带盖盒</text><text x="235" y="428" class="micro red center">禁止普通智能插座承载</text></g>
 <g data-device-protection="SRCD-BATH-MIRROR"><rect x="370" y="335" width="230" height="110" rx="9" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/><text x="485" y="362" class="small bold center">智能除雾镜柜连接点</text><text x="485" y="386" class="micro center">说明允许插头：防水插座式漏保</text><text x="485" y="407" class="micro center">只允许固定接线：双极隔离+带盖盒</text><text x="485" y="428" class="micro center">独立于浴霸控制输出</text></g>
 <rect x="620" y="335" width="230" height="110" rx="9" fill="#fffbeb" stroke="#f59e0b" stroke-width="2"/><text x="735" y="362" class="small bold center">防潮基础灯 / 镜前灯</text><text x="735" y="386" class="micro center">零火开关盒到达L/N</text><text x="735" y="407" class="micro center">智能开关受控相线只去灯具</text><text x="735" y="428" class="micro center">保留本地实体控制</text>
</g>

<rect x="105" y="490" width="745" height="80" rx="10" fill="#ecfdf5" stroke="#16a34a" stroke-width="2" data-location-preference="bath-dry-high"/><text x="128" y="518" class="small green bold">首选：卫生间内实测干区高位</text><text x="128" y="543" class="small green">高位不自动等于干区；须按淋浴喷溅范围和产品说明确认，且TEST/RESET可触达。</text>
<rect x="105" y="590" width="745" height="80" rx="10" fill="#fff7ed" stroke="#f97316" stroke-width="2" data-location-fallback="hall-a-outside"/><text x="128" y="618" class="small orange bold">自动降级：走廊A门外</text><text x="128" y="643" class="small orange">室内没有可证明合格的干区时，整套漏保箱移至门外；不得改成湿区裸露安装。</text>
<rect x="285" y="575" width="370" height="20" fill="url(#danger)" opacity=".8" data-wet-zone-no-box="true"/><text x="470" y="586" class="micro red center">喷溅/湿区：禁止用“防水”标签替代安装分区</text>
'''
    side = sidebar("34 卫浴电气验收门禁", [
        "MCB-05只接这一条馈线",
        "漏保箱前无接头、无分支",
        "RCD-BATH-01同时切断L和N",
        "额定动作电流不大于30mA",
        "浴霸/镜柜/照明全部在下游",
        "设备插头方式必须由说明书允许",
        "浴霸不接普通智能插座",
        "智能照明开关统一使用零火版",
        "无PE标识持续保留，严禁N/PE短接",
        "接受上下级同时跳闸并分别实测",
        "!负载、线径、IP和位置均待10月1日冻结",
    ], [("#dc2626", "漏保前连续馈线 / 安全门禁"), ("#0284c7", "漏保后设备分支"), ("#16a34a", "首选干区"), ("#f97316", "门外自动降级")])
    return document("bathroom-electrical-detail", "34 卫生间专用馈线与漏保详图", "漏保前连续段、双极30mA保护、三条下游分支与干区降级规则", detail + side)


def bedroom_electrical_detail() -> str:
    detail = '''
<rect x="90" y="120" width="820" height="560" rx="16" fill="#ece8f7" stroke="#475569" stroke-width="5"/>
<text x="500" y="154" class="note bold center">卧室西墙与床两侧｜局部展开示意</text>
<rect x="255" y="230" width="440" height="250" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/><text x="475" y="355" class="room">双人床</text><text x="475" y="379" class="roomsub">北侧与南侧各需常电插座</text>
<circle cx="120" cy="520" r="14" fill="#fff" stroke="#2563eb" stroke-width="3" data-electrical-hole="E-HOLE-01"/><text x="120" y="524" class="micro center">01</text><text x="92" y="548" class="micro blue">卧室门洞北端</text>

<g data-circuit="MCB-04" data-terminal-scope="fan-control-only">
 <path d="M134 520H165V430H205" fill="none" stroke="#f59e0b" stroke-width="5" data-route-kind="surface"/>
 <rect x="205" y="400" width="82" height="62" rx="5" fill="#fffbeb" stroke="#f59e0b" stroke-width="3" data-box-type="existing-recessed" data-device="fan-speed-controller"/>
 <text x="246" y="423" class="small bold center">原暗盒</text><text x="246" y="443" class="micro center">仅吊扇调速器</text>
 <path d="M287 430C380 165 585 150 740 210" fill="none" stroke="#7c3aed" stroke-width="5" stroke-dasharray="2 8" data-route-kind="existing-concealed"/>
 <circle cx="760" cy="215" r="28" fill="#f5f3ff" stroke="#7c3aed" stroke-width="3"/><text x="760" y="220" class="small center">吊扇</text>
</g>
<text x="430" y="180" class="small purple center">调速器 → 吊扇：既有暗埋线，复用前测通断与绝缘</text>

<g data-circuit="RCBO-01" data-terminal-scope="bed-sockets-only">
 <path d="M134 520H165V500H310V465" fill="none" stroke="#0284c7" stroke-width="5" data-route-kind="surface"/>
 <rect x="305" y="425" width="88" height="72" rx="5" fill="#e0f2fe" stroke="#0284c7" stroke-width="3" data-box-type="surface-bed-south"/>
 <text x="349" y="451" class="small bold center">床南明盒</text><text x="349" y="472" class="micro center">常电插座</text>
 <path d="M165 500V185H720" fill="none" stroke="#0284c7" stroke-width="5" data-route-kind="surface"/>
 <rect x="720" y="155" width="88" height="72" rx="5" fill="#e0f2fe" stroke="#0284c7" stroke-width="3" data-box-type="surface-bed-north"/>
 <text x="764" y="181" class="small bold center">床北明盒</text><text x="764" y="202" class="micro center">常电插座</text>
 <rect x="165" y="482" width="82" height="38" rx="6" fill="#fff" stroke="#0284c7" stroke-width="2" data-junction="JB-BED"/>
 <text x="206" y="497" class="micro bold center">JB-BED</text><text x="206" y="512" class="micro center">PCT短尾线</text>
</g>
<line x1="292" y1="390" x2="292" y2="505" stroke="#dc2626" stroke-width="2" stroke-dasharray="6 5"/><text x="300" y="390" class="micro red">不同回路分盒 / 分槽 / 分端子</text>
<rect x="110" y="590" width="760" height="62" rx="10" fill="#fff1f2" stroke="#dc2626" stroke-width="2"/><text x="132" y="616" class="small red">一个暗盒不够：保留原暗盒给调速器，在旁边加独立明盒插座；不叠压多根铜鼻子。</text><text x="132" y="638" class="small red">两芯L/N没有PE：PE端子保持未连接并贴标；绝缘、极性和漏保实测通过后才通电。</text>
'''
    side = sidebar("33 现场装配检查", [
        "橙：空开4的吊扇控制回路",
        "蓝：漏保1的卧室常电插座回路",
        "紫点线：调速器后的既有暗埋线",
        "床南明盒与调速器暗盒相邻但独立",
        "床北使用独立明装插座",
        "JB-BED另分空调、床北、床南",
        "普通插座不由智能墙壁开关供电",
        "智能插座只插在常电插座上",
        "不同回路不得共用端子",
        "!断电、验电后施工；绝缘需专业仪表",
    ], [("#f59e0b", "吊扇受控相线"), ("#0284c7", "卧室漏保常电"), ("#7c3aed", "既有暗埋线")])
    return document("bedroom-electrical-detail", "33 卧室插座与吊扇控制详图", "原暗盒调速器、床南/床北明装插座及两回路分离规则", detail + side)


def doors_windows_cats() -> str:
    doors = '''
<!-- Entry door: existing -->
<path d="M600 530H680M600 450A80 80 0 0 1 680 530" fill="none" stroke="#7c3aed" stroke-width="3"/><text x="650" y="548" class="small purple">入户门｜已有</text>
<!-- Bedroom door: not purchased -->
<path d="M600 425H680M600 345A80 80 0 0 1 680 425" fill="none" stroke="#f97316" stroke-width="3" stroke-dasharray="7 5"/><text x="645" y="335" class="small orange">卧室门｜待选购</text>
<!-- Kitchen slider: closed representation only -->
<path d="M520 323H600M440 317H510" fill="none" stroke="#f97316" stroke-width="4" stroke-dasharray="7 5"/><text x="540" y="308" class="small orange">厨房移门｜待定制</text>
<!-- Bath slider: mounted on Hall A side; closed normally, slides east for use. -->
<path d="M405 457H475" fill="none" stroke="#f97316" stroke-width="5"/><text x="438" y="480" class="small orange center">卫生间移门｜常闭</text>
<g data-state="bath-slider-open-east" data-intrusion-m="0.4">
  <rect x="500" y="330" width="45" height="120" fill="#fee2e2" fill-opacity=".58" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="5 4"/>
  <path d="M475 457H545" fill="none" stroke="#dc2626" stroke-width="5" stroke-dasharray="7 5"/>
  <path d="M438 438H520" fill="none" stroke="#dc2626" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="548" y="445" class="micro red">向东开启；临时占走廊B约0.4m</text>
</g>
<!-- Balcony slider -->
<path d="M250 523H325M325 537H400" fill="none" stroke="#7c3aed" stroke-width="4"/><text x="300" y="511" class="small purple">阳台推拉门｜西扇有效约0.7m</text>
<!-- Cat screens and scratch boards -->
<path d="M200 126H300" class="cat"/><path d="M450 126H550" class="cat"/><path d="M700 126H800" class="cat"/>
<path d="M96 535V625" class="cat"/><path d="M110 634H390" class="cat"/>
<path d="M106 542V622" class="cat"/><path d="M112 624H388" class="cat"/>
<text x="250" y="650" class="small green center">阳台西墙+南墙窗下猫抓板</text>
<!-- Bathroom slider customization inset: temporary Hall B intrusion is accepted. -->
<g data-detail="bath-slider-constraint">
  <rect x="980" y="360" width="340" height="190" rx="10" fill="#fffaf0" stroke="#f59e0b" stroke-width="1.5"/>
  <text x="998" y="389" class="note bold">卫生间移门定制约束</text>
  <line x1="1000" y1="425" x2="1075" y2="425" stroke="#f97316" stroke-width="6"/>
  <text x="1038" y="447" class="small center">走廊A侧常闭</text>
  <path d="M1085 425H1140" stroke="#dc2626" stroke-width="2" marker-end="url(#arrow)"/>
  <rect x="1185" y="401" width="95" height="52" fill="#fee2e2" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="5 4"/>
  <line x1="1145" y1="425" x2="1240" y2="425" stroke="#dc2626" stroke-width="6" stroke-dasharray="7 5"/>
  <text x="1192" y="474" class="small red center">向东完全开启：约0.4m进入走廊B</text>
  <text x="998" y="505" class="small">日常可按进出需要部分开启；关闭后恢复A/B走廊净空。</text>
  <text x="998" y="530" class="small">门洞有效净宽目标约0.65m；轨道和停泊尺寸下单前复测。</text>
</g>
'''
    side_top = '''
<rect x="970" y="120" width="370" height="210" rx="14" class="panel"/>
<text x="994" y="158" class="note bold">门窗与三猫安全</text>
<text x="994" y="194" class="note">卧室门：待选购</text><text x="994" y="223" class="note">厨房/卫生间移门：待定制</text>
<text x="994" y="252" class="note">所有外窗：防逃纱窗 TODO</text><text x="994" y="281" class="note">阳台猫抓板提高窗台可达性</text>
<text x="994" y="310" class="note red">纱网、边框、锁扣和缝隙需整体验收</text>
'''
    return document("doors-windows-cats", "40 门窗与猫安全图", "门窗选购定制、防逃纱窗与阳台猫抓板", plan_base(False) + doors + room_labels() + side_top)


def kitchen_bath_details() -> str:
    kitchen = '''
<rect x="60" y="115" width="620" height="610" rx="14" class="panel"/>
<text x="85" y="155" class="note bold">厨房：平面 + 架空台面立面</text>
<rect x="120" y="190" width="400" height="400" fill="#fbf3d9" stroke="#1f2937" stroke-width="5"/>
<rect x="120" y="190" width="400" height="100" class="fixed"/><text x="320" y="245" class="note center">原台面约2.0×0.5m</text>
<rect x="140" y="198" width="360" height="80" class="planned"/><path d="M260 198V278M380 198V278" stroke="#f97316" stroke-width="2"/>
<text x="320" y="220" class="small center orange">上层0.4×0.6m瓷砖×3（总长约1.8m）</text>
<rect x="420" y="210" width="75" height="55" fill="#fee2e2" stroke="#b45309" stroke-width="2"/><text x="457" y="242" class="small center">燃气灶</text>
<rect x="120" y="430" width="80" height="150" fill="#effafd" stroke="#16829a" stroke-width="2"/><text x="160" y="510" class="small center">水槽</text>
<rect x="120" y="310" width="80" height="110" class="planned"/><text x="210" y="360" class="small orange">受潮二层木柜</text>
<path class="gas" d="M515 225H470"/><text x="505" y="300" class="small orange" text-anchor="end">燃气灶直连</text>
<path class="gas" d="M515 225V175H135V465"/><text x="310" y="172" class="small orange center">热水器支路沿北墙约2m，再沿西墙向南</text>
<circle cx="135" cy="465" r="8" fill="#fff7ed" stroke="#ea580c" stroke-width="3"/><text x="210" y="452" class="small orange">水槽上方竖向投影</text>
<g data-view="kitchen-west-wall-elevation">
  <rect x="535" y="305" width="125" height="285" rx="8" fill="#fffdf8" stroke="#cbd5e1" stroke-width="1.5"/>
  <text x="597" y="328" class="small bold center">厨房西墙立面</text>
  <line x1="550" y1="340" x2="550" y2="570" stroke="#475569" stroke-width="4"/>
  <line x1="550" y1="570" x2="648" y2="570" stroke="#475569" stroke-width="3"/>
  <rect x="565" y="370" width="70" height="82" rx="4" fill="#fff7ed" stroke="#ea580c" stroke-width="2" data-placement="water-heater-above-sink"/>
  <text x="600" y="405" class="micro orange center">燃气</text><text x="600" y="420" class="micro orange center">热水器</text>
  <path d="M600 457V480" stroke="#ea580c" stroke-width="2" marker-end="url(#arrow)"/>
  <ellipse cx="600" cy="500" rx="35" ry="9" fill="#dff3f7" stroke="#16829a" stroke-width="2"/>
  <rect x="565" y="500" width="70" height="55" fill="#effafd" stroke="#16829a" stroke-width="2"/>
  <text x="600" y="532" class="small center">水槽</text>
  <text x="600" y="466" class="micro orange center">水槽正上方</text>
  <text x="597" y="584" class="micro red center">不在二层木柜上方</text>
</g>
<g transform="translate(120 625)">
  <line x1="0" y1="0" x2="400" y2="0" stroke="#475569" stroke-width="5"/>
  <rect x="20" y="-70" width="360" height="20" fill="#fff7ed" stroke="#f97316" stroke-width="2"/>
  <line x1="50" y1="-50" x2="50" y2="0" stroke="#64748b" stroke-width="5"/><line x1="350" y1="-50" x2="350" y2="0" stroke="#64748b" stroke-width="5"/>
  <text x="200" y="-78" class="small center">架空瓷砖层（高度/支撑待定）</text><text x="200" y="22" class="small center">原0.5m深台面</text>
</g>
<text x="85" y="702" class="small red">安全门禁：燃气管检修、伸缩杆稳定、瓷砖承载和灶台耐热均未关闭。</text>
'''
    bath = '''
<rect x="710" y="115" width="630" height="610" rx="14" class="panel"/>
<text x="735" y="155" class="note bold">卫生间：洁具净空与固定点</text>
<!-- enlarged nominal room: west-east 0.75m, north-south 1.05m -->
<rect x="850" y="195" width="270" height="378" fill="#e7f5f8" stroke="#1f2937" stroke-width="6"/>
<circle cx="850" cy="195" r="12" fill="#0f766e"/><text x="865" y="188" class="small green">排水立管</text>
<!-- toilet 0.58m deep -->
<rect x="885" y="202" width="140" height="209" rx="55" class="planned" data-status="not-purchased"/><ellipse cx="955" cy="255" rx="43" ry="31" fill="none" stroke="#f97316" stroke-width="2"/>
<text x="955" y="330" class="small center">马桶深约0.58m</text>
<circle cx="955" cy="321" r="7" fill="#0f766e"/><path class="dim" d="M1135 195V321"/><text x="1180" y="260" class="small">坑距北墙0.35m</text>
<rect x="850" y="380" width="150" height="185" fill="#d8f2f6" fill-opacity=".55" stroke="#0284c7" stroke-width="2" stroke-dasharray="7 5"/><text x="875" y="535" class="small blue">淋浴湿区</text>
<rect x="1015" y="465" width="105" height="108" class="planned" data-status="not-purchased"/><text x="1067" y="520" class="small center">浴室柜</text>
<rect x="1103" y="230" width="17" height="55" class="danger"/><text x="1093" y="225" class="small red" text-anchor="end">现有浴霸</text>
<circle cx="895" cy="515" r="10" fill="#0f766e"/><text x="910" y="520" class="small green">扬子防臭地漏</text>
<path class="dim" d="M830 195H812M830 573H812M818 195V573"/><text x="790" y="385" class="dimtext" transform="rotate(-90 790 385)">设计基准净长约1.05m</text>
<path class="dim" d="M850 595V613M1120 595V613M850 607H1120"/><text x="985" y="630" class="dimtext">净宽约0.75m</text>
<g data-state="bath-slider-open-east" data-intrusion-m="0.4">
  <rect x="800" y="650" width="490" height="58" rx="6" fill="#fff7ed" stroke="#f59e0b"/>
  <line x1="820" y1="674" x2="925" y2="674" stroke="#f97316" stroke-width="6"/>
  <text x="872" y="697" class="micro center">走廊A侧常闭</text>
  <path d="M940 674H1000" stroke="#dc2626" stroke-width="2" marker-end="url(#arrow)"/>
  <rect x="1110" y="658" width="145" height="32" fill="#fee2e2" stroke="#dc2626" stroke-dasharray="5 4"/>
  <line x1="1015" y1="674" x2="1190" y2="674" stroke="#dc2626" stroke-width="6" stroke-dasharray="7 5"/>
  <text x="1135" y="704" class="micro red center">向东开启，约0.4m临时进入走廊B；可部分开启</text>
</g>
'''
    return document("kitchen-bath-details", "50 厨卫详图", "厨房台面叠层、燃气关系及卫生间洁具关键尺寸", kitchen + bath)


FINISH_DEFS = r'''
<defs>
  <pattern id="wood" width="28" height="12" patternUnits="userSpaceOnUse">
    <rect width="28" height="12" fill="#e8d7bd"/><path d="M0 6Q7 1 14 6T28 6" fill="none" stroke="#b88959" stroke-width="1" opacity=".65"/>
  </pattern>
  <pattern id="tile" width="22" height="22" patternUnits="userSpaceOnUse">
    <rect width="22" height="22" fill="#dceff0"/><path d="M0 0H22V22H0Z" fill="none" stroke="#8bb8ba" stroke-width="1"/>
  </pattern>
  <pattern id="deck-pebble" width="30" height="20" patternUnits="userSpaceOnUse">
    <rect width="30" height="20" fill="#d6b98a"/><path d="M0 10H30M10 0V20M20 0V20" stroke="#8b6542" stroke-width="1.5"/><circle cx="25" cy="5" r="3" fill="#a8a29e"/>
  </pattern>
  <style>
    .moisture{fill:none;stroke:#0891b2;stroke-width:8;stroke-dasharray:9 6}
    .ceiling{fill:#fde68a;fill-opacity:.28;stroke:#ca8a04;stroke-width:2;stroke-dasharray:8 5}
    .tilepaint{fill:none;stroke:#a855f7;stroke-width:9;stroke-dasharray:5 5}
  </style>
</defs>
'''


def finishes_materials() -> str:
    finishes = '''
<!-- Dry-zone overlay: SPC wood-grain floor over existing tile -->
<g data-finish="spc-wood-grain" opacity=".82">
  <rect x="100" y="130" width="300" height="400" fill="url(#wood)"/>
  <rect x="400" y="130" width="200" height="200" fill="url(#wood)"/>
  <rect x="500" y="330" width="100" height="120" fill="url(#wood)"/>
  <rect x="400" y="450" width="200" height="80" fill="url(#wood)"/>
  <rect x="600" y="130" width="300" height="300" fill="url(#wood)"/>
</g>
<rect x="400" y="330" width="100" height="120" fill="url(#tile)" data-finish="bathroom-tile"/>
<rect x="100" y="530" width="300" height="100" fill="url(#deck-pebble)" data-finish="balcony-deck-pebble"/>

<!-- Existing white wall tiles and counter are a separate recoloring system, not latex paint. -->
<g data-finish="tile-recolor">
  <rect x="406" y="136" width="188" height="188" class="tilepaint"/>
  <rect x="406" y="336" width="88" height="108" class="tilepaint"/>
  <rect x="410" y="145" width="180" height="38" fill="#f3e8ff" fill-opacity=".82" stroke="#a855f7" stroke-width="2"/>
</g>
<text x="500" y="202" class="small center purple">厨房四周墙砖高约1.8m</text>
<text x="500" y="219" class="micro center purple">含现有瓷砖灶台改色</text>
<text x="450" y="354" class="micro center purple">四周墙砖高约1.8m</text>

<!-- Moisture treatment extents are indicative and must be measured on site. -->
<rect x="115" y="145" width="270" height="370" rx="12" class="ceiling" data-surface="living-room-ceiling"/>
<path d="M100 365V525M400 330V525M400 250V330" class="moisture" data-surface="suspected-damp-walls"/>
<path d="M105 540V620M115 625H390" class="moisture" data-surface="balcony-non-window-surfaces"/>
<text x="250" y="320" class="small center" fill="#92400e">客厅顶部拟做防潮/防水处理</text>
<text x="112" y="438" class="micro blue" transform="rotate(-90 112 438)">西墙南部疑似受潮</text>
<text x="388" y="418" class="micro blue" transform="rotate(-90 388 418)">东墙南部邻卫生间</text>
<text x="415" y="286" class="micro blue">水槽墙</text>
<text x="450" y="385" class="small center">卫生间自铺地砖</text>
<text x="250" y="585" class="small center">菠萝格地板 + 鹅卵石</text>
<text x="745" y="408" class="small center">干区：瓷砖上叠铺石塑木纹地板</text>
<text x="250" y="660" class="small center">三处罗马杆+窗帘已有｜换布、染色、拆分利用或回收待定</text>
<text x="100" y="690" class="small purple">瓷砖改色粗基数约19.18㎡：待扣厨房窗洞，并补量灶台立面/侧面。</text>
'''
    side = sidebar("饰面体系与施工门禁", [
        "风格：宋氏美学 + 侘寂中古，暖黄色",
        "先修排水渗漏/查潮源，再封闭基层",
        "层高2.65m、无吊顶；先算净面积 A",
        "扣外窗前保守基数：A ≈ 134.70㎡",
        "底漆 = ceil(A÷50)：当前按3桶",
        "面漆理论值 = ceil(A÷30)",
        "本期保守采购：底漆3桶+面漆5桶",
        "工具1套；计划合计 ¥2012",
        "不等待外窗复测再决定第5桶",
        "面漆须同色同批；未开封余桶入库",
        "厨卫墙砖/灶台改色面积单独测算",
        "!卫生间防水不能只凭商品简称",
    ], [("#b88959", "干区石塑木纹地板"), ("#8bb8ba", "卫生间自铺地砖"), ("#a855f7", "既有白色瓷砖改色"), ("#0891b2", "防潮/防水候选区域")])
    body = FINISH_DEFS + room_fields(True) + finishes + base_walls() + windows() + room_labels() + side
    return document("finishes-materials", "60 墙地面饰面图", "墙顶地面材料分区、基层处理顺序与风格方向", body)


OUTPUTS = {
    "00-existing-survey.svg": ("existing-survey", "00 现状测量图", existing_survey),
    "10-furniture-circulation.svg": ("furniture-circulation", "10 家具与动线图", furniture_circulation),
    "20-plumbing-gas.svg": ("plumbing-gas", "20 给排水与燃气图", plumbing_gas),
    "30-electrical-low-voltage.svg": ("electrical-low-voltage", "30 强弱电点位图", electrical_low_voltage),
    "31-electrical-routes.svg": ("electrical-routes", "31 强电真实空间走线图", electrical_routes),
    "32-electrical-topology.svg": ("electrical-topology", "32 五回路与分级漏保拓扑图", electrical_topology_v5),
    "33-bedroom-electrical-detail.svg": ("bedroom-electrical-detail", "33 卧室插座与吊扇控制详图", bedroom_electrical_detail),
    "34-bathroom-electrical-detail.svg": ("bathroom-electrical-detail", "34 卫生间专用馈线与漏保详图", bathroom_electrical_detail),
    "40-doors-windows-cats.svg": ("doors-windows-cats", "40 门窗与猫安全图", doors_windows_cats),
    "50-kitchen-bath-details.svg": ("kitchen-bath-details", "50 厨卫详图", kitchen_bath_details),
    "60-finishes-materials.svg": ("finishes-materials", "60 墙地面饰面图", finishes_materials),
}


def generate_all(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, (_, _, renderer) in OUTPUTS.items():
        (output_dir / filename).write_text(renderer(), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "diagrams" / "v5")
    args = parser.parse_args()
    generate_all(args.output)
    print(f"Generated {len(OUTPUTS)} SVG diagrams in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
