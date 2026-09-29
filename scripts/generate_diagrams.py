#!/usr/bin/env python3
"""Generate the current responsibility-separated renovation diagrams."""

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
<text x="100" y="800" class="small">当前讨论图｜北↑ 东→｜坐标和尺寸以 house.yaml 与现场复测为准，不替代施工放样或专项验收。</text>
</svg>
'''


def construction_document(role: str, title_value: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" data-diagram-role="{role}" data-drawing-property="construction-wiring-final" role="img">
<title>{title_value}</title>
<desc>{subtitle}</desc>
{DEFS}
<rect width="{WIDTH}" height="{HEIGHT}" fill="#fbfaf7"/>
<text x="70" y="52" class="title">{title_value}</text>
<text x="70" y="78" class="subtitle">{subtitle}</text>
{body}
<text x="70" y="813" class="small red">施工接线/下料定稿｜仅供断电放样与端点核对；通电前仍须完成实物参数核验及合格电工绝缘、极性、保护器和漏保测试。</text>
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
{rect(0,1.6,0,2.0,"planned",'data-furniture="sofa-bed" data-mode="bed-open" opacity="0.55"')}<text x="245" y="275" class="micro center orange">展开约1.6×2.0m｜临时客卧</text>
{rect(0,1.6,0,.9,"planned",'data-furniture="sofa-bed" data-mode="sofa" data-status="not-purchased"')}<text x="145" y="215" class="small center">双人沙发床｜未购买</text>
<path d="M100 295H400" fill="none" stroke="#a855f7" stroke-width="3" stroke-dasharray="10 7" data-privacy-curtain="candidate"/><text x="305" y="289" class="micro purple center">后期隐私帘候选｜可完全收起</text>
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
{rect(.6,1.2,3,3.6,"fixed",'data-appliance="dishwasher" data-status="owned-to-move" data-stack-on="wood-cabinet"')}<text x="430" y="210" class="micro center">洗碗机｜已有</text><text x="430" y="226" class="micro center">叠放木柜/替代柜上</text><text x="430" y="242" class="micro center">承重待核</text>
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
        "椅子、沙发床和洗烘机尚未购买",
        "沙发床向东展开，兼作临时客卧",
        "紫虚线：入住后再决定的隐私帘",
        "洗碗机已有；叠放水槽北侧柜体上",
        "马桶、浴室柜尚未购买",
        "扫地机器人已有，停靠在沙发与书桌之间",
        "上方窄桌下部无前腿，不挡回充与取出",
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
<rect x="405" y="195" width="55" height="58" class="fixed" data-appliance="dishwasher"/><text x="432" y="216" class="micro center">洗碗机</text><text x="432" y="234" class="micro center">已有</text>
<path class="water" d="M420 290V253" marker-end="url(#blue-arrow)" data-dishwasher-water="sink-feed-independent-switch"/><path class="drain" d="M445 253V285H420" stroke-dasharray="6 4" marker-end="url(#arrow)" data-dishwasher-drain="direct-to-sink"/><text x="465" y="273" class="micro green">软管直排水槽并固定</text>
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
        "洗碗机：水槽进水独立开关+软管直排水槽",
        "水泥/沙子/堵漏王用于固定改管",
        "!燃气管遮盖和检修仍需验收确认",
        "!封闭饰面前应做联合排水测试",
    ], [("#0284c7", "冷水"), ("#dc2626", "热水"), ("#0f766e", "排水"), ("#ea580c", "燃气")])
    return document("plumbing-gas", "20 给排水与燃气图", "冷热水、排水、地漏、马桶坑位与燃气双支路", plan_base(False, True) + routes + room_labels() + side)


def electrical_low_voltage() -> str:
    points = '''
<rect x="575" y="430" width="44" height="25" rx="3" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/><text x="625" y="424" class="small blue">入户配电箱</text>
<rect x="540" y="458" width="58" height="28" rx="3" fill="#fffbeb" stroke="#f59e0b" stroke-width="2" data-subpanel="five-2p-c20"/><text x="569" y="476" class="micro orange center">副箱5×C20</text>
<rect x="190" y="518" width="11" height="11" fill="#1e3a8a"/><text x="180" y="550" class="micro">冰箱南侧暗盒</text>
<rect x="394" y="402" width="11" height="11" fill="#1e3a8a" data-switch="JZ-N2-living"/><text x="312" y="398" class="micro">客厅JZ-N2暗盒</text>
<rect x="594" y="326" width="11" height="11" fill="#1e3a8a" data-switch="JZ-N2-bedroom"/><text x="610" y="321" class="micro">卧室JZ-N2暗盒</text>
<rect x="250" y="405" width="11" height="11" fill="#1e3a8a"/><text x="245" y="397" class="micro">入户/卧室门间暗盒</text>
<rect x="160" y="509" width="74" height="20" rx="5" fill="#eff6ff" stroke="#0284c7" stroke-width="2"/><text x="197" y="500" class="small center">客厅空调</text>
<rect x="602" y="155" width="20" height="74" rx="5" fill="#eff6ff" stroke="#0284c7" stroke-width="2"/><text x="636" y="151" class="small">卧室空调</text>
<circle cx="176" cy="520" r="8" fill="#fff" stroke="#dc2626" stroke-width="2" data-device-protection="SRCD-AC-LIV"/><text x="154" y="548" class="micro red">空调末端漏保</text>
<circle cx="204" cy="520" r="8" fill="#fff" stroke="#dc2626" stroke-width="2" data-device-protection="SRCD-FRIDGE"/><text x="214" y="548" class="micro red">冰箱漏保插座</text>
<rect x="404" y="194" width="58" height="60" class="fixed" data-appliance="dishwasher"/><text x="433" y="216" class="micro center">洗碗机</text><rect x="451" y="236" width="10" height="10" fill="#2563eb" data-outlet="dishwasher-three-hole"/><text x="474" y="250" class="micro red">三孔常电｜无PE标识</text>
<circle cx="750" cy="280" r="13" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2"/><text x="750" y="306" class="small center">卧室吊扇</text>
<circle cx="250" cy="330" r="10" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2"/><text x="250" y="354" class="small center">客厅吊扇钩</text>
<rect x="486" y="346" width="13" height="38" class="danger"/><text x="478" y="343" class="small red" text-anchor="end">浴霸待核验</text>
<rect x="470" y="410" width="28" height="20" rx="3" fill="#fff1f2" stroke="#dc2626" stroke-width="2" data-device-protection="RCD-BATH-01"/><text x="466" y="440" class="micro red" text-anchor="end">双极30mA</text>
<rect x="102" y="305" width="12" height="12" fill="#2563eb" data-outlet="robot-always-on"/><rect x="102" y="337" width="12" height="12" fill="#7c3aed" data-outlet="sofa-charge"/>
<text x="122" y="315" class="micro blue">扫地机常电</text><text x="122" y="348" class="micro purple">沙发上部充电</text>
<rect x="102" y="270" width="12" height="12" fill="#2563eb" data-outlet="sofa-background-always-on"/><text x="122" y="280" class="micro blue">背景灯独立常电</text>
<rect x="690" y="390" width="12" height="12" fill="#f59e0b" data-outlet="underbed-light-controlled"/><text x="710" y="400" class="micro orange">仅床下灯｜JZ-N2第2键</text>
<rect x="80" y="180" width="12" height="12" fill="#2563eb" data-outlet="desk-lower"/><rect x="102" y="180" width="12" height="12" fill="#2563eb" data-outlet="desk-upper"/><text x="122" y="190" class="micro blue">书桌上下常电</text>
<circle cx="600" cy="450" r="9" fill="#7c3aed"/><path class="network" d="M600 450H540V506"/>
<rect x="488" y="506" width="104" height="24" rx="3" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2" data-device-shelf="hall-a" data-wall-anchor="hall-a-south-wall"/><text x="540" y="520" class="micro purple center">光猫 / Wi-Fi / EVE V</text>
<text x="540" y="550" class="micro purple center">背面贴走廊A南墙｜至少4个常电位</text>
<text x="610" y="466" class="micro purple">网线与入户电线同洞口位置</text>
'''
    side = sidebar("点位图，不是最终回路图", [
        "四个深蓝方块：既有暗盒，无暗管",
        "暗盒只作末端候选；不作为穿线入口",
        "主箱旁增加18模副箱，五路各2P C20",
        "紫：网线入口和玄关设备架",
        "EVE V长期运行，架内短网线接路由器",
        "光猫/路由器/EVE V需至少4个常电位",
        "扫地机低位、沙发上部、书桌上下均常电",
        "客厅JZ-N2双键只控主灯/餐灯",
        "卧室JZ-N2双键只控主灯/床下灯",
        "沙发背景灯为独立常电，由灯具/智能插头控制",
        "洗碗机三孔常电，由RCBO-02统一30mA保护",
        "卧室空调/洗烘由C20 RCBO统一保护；客厅空调与冰箱各自末端漏保",
        "卫生间由MCB-05经门外RCD-BATH-01总漏保供电",
        "已确认两线制无PE；三孔面板须持久标识",
        "!蓝色6mm²库存只作N候选，不改色作L",
        "本图为点位图，路线见31图",
    ], [("#2563eb", "强电点位"), ("#1e3a8a", "现有暗盒"), ("#7c3aed", "弱电/网络"), ("#dc2626", "安全待核验")])
    return document("electrical-low-voltage", "30 强弱电点位图", "强电、设备、既有暗盒和网络设备点位", plan_base(False, True) + points + room_labels() + side)


def electrical_routes() -> str:
    routes = '''
<rect x="575" y="430" width="44" height="25" rx="3" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/><text x="626" y="426" class="small blue">配电箱｜5支路</text>
<rect x="545" y="462" width="68" height="30" rx="3" fill="#fffbeb" stroke="#f59e0b" stroke-width="2" data-subpanel="18-module-five-2p-c20"/><text x="579" y="481" class="micro orange center">副箱5×2P C20</text>
<g data-route-kind="surface" fill="none" stroke="#2563eb" stroke-width="4">
  <path d="M590 442L600 345V255" data-circuit="RCBO-01"/><path d="M590 442L520 330V235" data-circuit="RCBO-02"/>
  <path d="M590 442H400V315" data-circuit="RCBO-03"/>
</g>
<g data-route-kind="high-load-short" fill="none" stroke="#f59e0b" stroke-width="4">
  <path d="M590 438H400V315H220" data-circuit="MCB-04"/>
</g>
<g data-endpoint-protection="MCB-04-two-srcd">
  <circle cx="235" cy="308" r="8" fill="#fff" stroke="#dc2626" stroke-width="2"/><circle cx="257" cy="308" r="8" fill="#fff" stroke="#dc2626" stroke-width="2"/>
  <text x="246" y="292" class="micro red center">两端各自≤30mA漏保</text>
</g>
<path d="M590 446H517V456" fill="none" stroke="#dc2626" stroke-width="4" data-circuit="MCB-05" data-bath-feeder="continuous-no-joint"/>
<path d="M495 470L475 450" fill="none" stroke="#dc2626" stroke-width="3" data-bath-after-rcd="true"/>
<rect x="590" y="335" width="20" height="10" fill="#fff" stroke="#2563eb" stroke-width="2" data-route-transition="E-ROUTE-01"/><text x="616" y="343" class="micro blue">绕卧室门框</text>
<rect x="510" y="323" width="20" height="10" fill="#fff" stroke="#2563eb" stroke-width="2" data-route-transition="E-ROUTE-02"/><text x="536" y="331" class="micro blue">绕厨房门框</text>
<rect x="465" y="444" width="20" height="10" fill="#fff" stroke="#dc2626" stroke-width="2" data-route-transition="E-ROUTE-03"/><text x="455" y="440" class="micro red" text-anchor="end">绕卫浴门框</text>
<rect x="390" y="444" width="20" height="10" fill="#fff" stroke="#2563eb" stroke-width="2" data-route-transition="E-ROUTE-04"/><text x="384" y="440" class="micro blue" text-anchor="end">绕客厅门框</text>
<g data-device-protection="RCD-BATH-01" data-location-preference="hall-a-outside" data-fallback="bath-dry-high">
  <rect x="495" y="456" width="44" height="28" rx="4" fill="#fff1f2" stroke="#dc2626" stroke-width="2"/>
  <text x="517" y="468" class="micro red center">2P</text><text x="517" y="480" class="micro red center">30mA</text>
  <text x="545" y="474" class="micro red">门外先保护</text>
</g>

<rect x="488" y="506" width="104" height="24" rx="3" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2" data-device-shelf="hall-a" data-wall-anchor="hall-a-south-wall"/>
<line x1="488" y1="530" x2="592" y2="530" stroke="#7c3aed" stroke-width="7" data-shelf-wall-contact="true"/>
<text x="540" y="520" class="micro purple center">设备架｜至少4位常电</text><text x="540" y="550" class="micro purple center">背面贴走廊A南墙</text>
<path class="network" d="M600 450H540V506"/><text x="607" y="469" class="micro purple">网线入口</text>

<rect x="594" y="244" width="15" height="28" fill="#fffbeb" stroke="#f59e0b" stroke-width="2" data-box="E-BOX-BED-FAN"/>
<text x="618" y="292" class="micro orange">调速器暗盒</text>
<path d="M600 345V258" fill="none" stroke="#f59e0b" stroke-width="4" data-fan-feed="surface-from-bedroom-trunk"/>
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
        "四个小框：绕门框的明装路径转换",
        "四个既有暗盒均无暗管，不参与走线",
        "蓝实线：前三路6mm²空间主干",
        "橙实线：MCB-04客厅空调+冰箱短主干",
        "红实线：MCB-05卫生间连续专用馈线",
        "紫点线：吊扇既有暗埋线",
        "设备架背面与走廊A南墙相接",
        "卧室调速器只用原西墙暗盒",
        "阳台没有进线通道，本期不设永久供电",
        "所有线路止于客厅侧，不跨阳台移门",
        "卫生间门外先接RCD-BATH-01，再绕门框明装进入",
        "RCD-BATH-01优先走廊A门外；合格时才可改卫生间干区",
        "扫地机已定在沙发/书桌之间，余量2m",
        "6mm²每根计划24m；MCB-04/05副箱后直接2.5mm²",
        "!本图不代表通电批准，端子/负载仍需现场核验",
    ], [("#2563eb", "三个RCBO空间主干"), ("#f59e0b", "MCB-04空调+冰箱短主干"), ("#dc2626", "MCB-05卫浴馈线"), ("#7c3aed", "既有暗线/弱电")])
    labels = '''
<text x="230" y="230" class="room">客厅</text><text x="475" y="190" class="room">厨房</text>
<text x="450" y="390" class="small center bold">卫生间</text><text x="830" y="335" class="room">卧室</text>
<text x="550" y="390" class="small center bold">走廊B</text><text x="520" y="490" class="small center bold">玄关 / 走廊A</text>
<text x="250" y="585" class="room">转角阳台</text><text x="750" y="482" class="room">公共走廊（非套内）</text>
'''
    return document("electrical-routes", "31 强电真实空间走线图", "空间主干、客厅门洞自然分流、卫生间门外漏保与阳台禁入边界", plan_base(False, True) + routes + labels + side)


def electrical_topology_v5() -> str:
    topology = '''
<rect x="55" y="115" width="205" height="575" rx="14" class="panel"/><text x="157" y="150" class="note bold center">主箱保留｜固定5支路</text>
<g data-circuit="RCBO-01"><rect x="78" y="180" width="160" height="58" rx="8" fill="#e0f2fe" stroke="#0284c7" stroke-width="3"/><text x="158" y="202" class="small bold center">漏保1｜RCBO-01</text><text x="158" y="222" class="micro center">保留C40｜卧室上游</text></g>
<g data-circuit="RCBO-02"><rect x="78" y="270" width="160" height="58" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="3"/><text x="158" y="292" class="small bold center">漏保2｜RCBO-02</text><text x="158" y="312" class="micro center">保留C40｜厨房上游</text></g>
<g data-circuit="RCBO-03"><rect x="78" y="360" width="160" height="72" rx="8" fill="#fee2e2" stroke="#dc2626" stroke-width="3"/><text x="158" y="382" class="small bold center">漏保3｜RCBO-03</text><text x="158" y="402" class="micro center">保留C40｜客厅上游</text><text x="158" y="418" class="micro center">玄关 / 洗烘 / 照明</text></g>
<g data-circuit="MCB-04"><rect x="78" y="470" width="160" height="72" rx="8" fill="#fef3c7" stroke="#f59e0b" stroke-width="3"/><text x="158" y="492" class="small bold center">空开4｜MCB-04</text><text x="158" y="512" class="micro center">保留C32｜空调+冰箱</text><text x="158" y="528" class="micro center">两端各自漏保</text></g>
<g data-circuit="MCB-05"><rect x="78" y="580" width="160" height="72" rx="8" fill="#ede9fe" stroke="#7c3aed" stroke-width="3"/><text x="158" y="602" class="small bold center">空开5｜MCB-05</text><text x="158" y="622" class="micro center">保留C32｜卫生间馈线</text><text x="158" y="638" class="micro center">门外总RCD</text></g>

<text x="272" y="158" class="micro orange center">18模副保护盒｜每路2P C20</text>
<g fill="none" stroke="#64748b" stroke-width="2.5" marker-end="url(#arrow)"><path d="M238 209H305"/><path d="M238 299H305"/><path d="M238 396H305"/><path d="M238 506H305"/><path d="M238 616H305"/></g>
<g data-subpanel="five-independent-2p-c20" fill="#fffbeb" stroke="#f59e0b" stroke-width="2">
  <rect x="250" y="194" width="44" height="30" rx="4" data-subpanel-device="C20-01"/><rect x="250" y="284" width="44" height="30" rx="4" data-subpanel-device="C20-02"/>
  <rect x="250" y="381" width="44" height="30" rx="4" data-subpanel-device="C20-03"/><rect x="250" y="491" width="44" height="30" rx="4" data-subpanel-device="C20-04"/>
  <rect x="250" y="601" width="44" height="30" rx="4" data-subpanel-device="C20-05"/>
</g>
<g class="micro orange center"><text x="272" y="213">C20</text><text x="272" y="303">C20</text><text x="272" y="400">C20</text><text x="272" y="510">C20</text><text x="272" y="620">C20</text></g>
<g data-branch-pattern="distributed" data-node-example="TN-BED"><rect x="305" y="175" width="140" height="68" rx="9" class="fixed"/><text x="375" y="200" class="small bold center">TN-BED</text><text x="375" y="220" class="micro center">连续主干｜就地T接</text></g>
<g data-branch-pattern="distributed" data-node-example="TN-KIT"><rect x="305" y="265" width="140" height="68" rx="9" class="fixed"/><text x="375" y="290" class="small bold center">TN-KIT</text><text x="375" y="310" class="micro center">连续主干｜就地T接</text></g>
<g data-branch-pattern="distributed" data-node-example="TN-HALL"><rect x="305" y="360" width="140" height="68" rx="9" class="fixed"/><text x="375" y="385" class="small bold center">TN-HALL</text><text x="375" y="405" class="micro center">玄关就地T接</text></g>
<g data-junction="JB-LIV-HIGH" data-branch-pattern="endpoint-rcd"><rect x="305" y="470" width="140" height="72" rx="9" class="fixed"/><text x="375" y="495" class="small bold center">JB-LIV-HIGH</text><text x="375" y="515" class="micro center">短主干就地T分</text><text x="375" y="531" class="micro center">两端各自漏保</text></g>
<g data-device-protection="RCD-BATH-01"><rect x="305" y="575" width="140" height="82" rx="9" fill="#fff1f2" stroke="#dc2626" stroke-width="3"/><text x="375" y="598" class="small bold center">RCD-BATH-01</text><text x="375" y="618" class="micro center">双极 / ≤30mA</text><text x="375" y="635" class="micro center">TEST / RESET</text><text x="375" y="650" class="micro red center">先保护，后分支</text></g>

<g fill="none" stroke="#94a3b8" stroke-width="2.2" marker-end="url(#arrow)"><path d="M445 209H505"/><path d="M445 299H505"/><path d="M445 394H505"/><path d="M445 506H505"/><path d="M445 616H505"/></g>
<text x="520" y="188" class="small bold">卧室空调｜RCBO-01统一30mA保护</text><text x="520" y="214" class="small">床北 / 床南常电插座</text><text x="520" y="238" class="small">卧室灯 / 吊扇同RCBO主干</text>
<text x="520" y="278" class="small bold">燃气热水器 / 油烟机</text><text x="520" y="304" class="small">台面 / 洗碗机</text><text x="520" y="330" class="small">洗碗机/厨房灯｜RCBO-02统一保护</text>
<text x="520" y="378" class="small bold">玄关设备架 → 就地T接</text><text x="520" y="405" class="small">客厅生活主干 → TN-LIV</text>
<g data-branch-pattern="distributed" data-node-example="TN-LIV"><rect x="715" y="360" width="140" height="74" rx="9" class="fixed"/><text x="785" y="385" class="small bold center">TN-LIV</text><text x="785" y="405" class="micro center">连续生活主干</text><text x="785" y="421" class="micro center">沿途就地T接</text></g>
<text x="875" y="374" class="small">洗烘｜RCBO-03统一30mA保护</text><text x="875" y="399" class="small">书桌 / 投影 / 沙发</text><text x="875" y="424" class="small">机器人低位常电</text>
<text x="520" y="480" class="small bold">MCB-04 两个末端</text><text x="520" y="504" class="small" data-device-protection="SRCD-AC-LIV">客厅空调 → 末端漏保</text><text x="520" y="528" class="small" data-device-protection="SRCD-FRIDGE">冰箱 → 漏保型插座</text>
<g data-junction="JB-BATH" data-bath-load-downstream="true"><rect x="505" y="575" width="145" height="82" rx="9" class="fixed"/><text x="577" y="600" class="small bold center">JB-BATH</text><text x="577" y="620" class="micro center">漏保后短距离分线</text><text x="577" y="638" class="micro center">最终设备现场冻结</text></g>
<text x="675" y="588" class="small" data-device-connection="BATH-HEATER">浴霸连接点｜总RCD下游</text><text x="675" y="616" class="small" data-device-connection="BATH-MIRROR">除雾镜柜设备连接保护</text><text x="675" y="644" class="small">卫生间基础照明</text>

<rect x="55" y="710" width="920" height="72" rx="12" class="danger"/><text x="78" y="737" class="note red bold">两线制边界：</text><text x="190" y="737" class="note red">三孔面板PE端子不连接并贴“本户无PE”；严禁N/PE短接或管道接地。</text><text x="78" y="764" class="small red">主箱后接18模副箱5×2P C20；15个分支节点按221-61x/41x表执行，SKU仍须核验。</text>
'''
    side = sidebar("五回路与保护层", [
        "主箱3×C40 RCBO + 2×C32 MCB全部保留",
        "MCB-04：客厅空调+冰箱短主干",
        "MCB-05：仅卫生间连续馈线",
        "主箱旁18模副保护盒：5×2P C20/6kA",
        "T接节点沿连续主干分布，共15个",
        "C20副保护后才进入2.5mm²新线路",
        "插座共19组，卫浴2点另计设备连接",
        "客厅空调与冰箱故障互不连带断电",
        "普通插座常电；智能墙壁开关零火版",
        "机器人常电不受智能控制",
        "6mm²每根24m；BVVB下料77m；回线24m",
        "连接器须适配主线/支线截面并可检修",
        "!主箱保留；副箱端接与负载仍需电工核定",
    ])
    return document("electrical-topology", "32 五回路与分级漏保拓扑图", "固定五支路、连续空间主干、分布式T接与MCB末端/总漏保", topology + side)


def living_jz_n2_wiring() -> str:
    body = r'''
<rect x="45" y="112" width="880" height="650" rx="14" fill="#f8fafc" stroke="#475569" stroke-width="2"/>
<text x="485" y="140" class="note bold center">客厅主灯 / 餐灯盒内端子与沙发常电分支</text>

<g data-junction="TN-LIV-LIGHT">
 <rect x="75" y="165" width="210" height="190" rx="10" class="panel"/>
 <text x="180" y="190" class="small bold center">TN-LIV-LIGHT 高位盒</text>
 <rect x="105" y="218" width="142" height="34" rx="6" fill="#fff1f2" stroke="#dc2626" stroke-width="2" data-connector="221-613-L"/>
 <text x="176" y="240" class="small center">L｜221-613</text>
 <rect x="105" y="278" width="142" height="34" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2" data-connector="221-615-N"/>
 <text x="176" y="300" class="small center">N｜221-615</text>
 <text x="180" y="334" class="micro center">6mm²进/出；2.5mm²短尾分支</text>
</g>

<path d="M50 235H105" stroke="#dc2626" stroke-width="5" data-conductor="6mm-L"/><text x="54" y="222" class="micro red">6mm² L</text>
<path d="M50 295H105" stroke="#2563eb" stroke-width="5" data-conductor="6mm-N"/><text x="54" y="282" class="micro blue">6mm² N</text>
<path d="M247 235H365" stroke="#dc2626" stroke-width="4" data-cable="BVVB-L-to-switch"/>
<path d="M247 295H365" stroke="#2563eb" stroke-width="4" data-cable="BVVB-N-to-switch"/>
<text x="305" y="220" class="micro center">BVVB 2×2.5 至暗盒</text>

<g data-device="JZ-N2-living" data-box="E-BOX-LIV-JZ">
 <rect x="365" y="172" width="205" height="180" rx="12" fill="#fff7ed" stroke="#f97316" stroke-width="3"/>
 <text x="467" y="199" class="small bold center">京东京造 JZ-N2</text>
 <text x="467" y="216" class="micro center">洗烘机东侧既有暗盒｜零火双开</text>
 <circle cx="382" cy="235" r="13" fill="#fff1f2" stroke="#dc2626" stroke-width="2"/><text x="382" y="239" class="micro center">L</text>
 <circle cx="382" cy="295" r="13" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/><text x="382" y="299" class="micro center">N</text>
 <circle cx="552" cy="245" r="15" fill="#fff" stroke="#dc2626" stroke-width="2"/><text x="552" y="249" class="micro center">L1</text>
 <circle cx="552" cy="305" r="15" fill="#fff" stroke="#c2410c" stroke-width="2"/><text x="552" y="309" class="micro center">L2</text>
 <text x="468" y="254" class="small center">第1键｜主灯</text><text x="468" y="314" class="small center">第2键｜餐灯</text>
 <text x="468" y="338" class="micro red center">盒内仅L / N / L1 / L2；端子不并压两根线</text>
</g>

<path d="M567 245H625" stroke="#dc2626" stroke-width="4" data-controlled-return="living-main"/>
<rect x="625" y="228" width="90" height="34" rx="6" fill="#fff" stroke="#64748b" stroke-width="2" data-connector="221-412-main"/><text x="670" y="250" class="micro center">221-412</text>
<path d="M715 245H758" stroke="#dc2626" stroke-width="4"/>
<rect x="758" y="190" width="135" height="85" rx="8" fill="#fffbeb" stroke="#f59e0b" stroke-width="2" data-load="living-main-light"/><text x="825" y="220" class="small bold center">客厅主灯</text><text x="825" y="241" class="micro center">L1 → 灯L</text><text x="825" y="259" class="micro center">N来自221-615</text>

<path d="M567 305H625" stroke="#c2410c" stroke-width="4" data-controlled-return="living-dining"/>
<rect x="625" y="288" width="90" height="34" rx="6" fill="#fff" stroke="#64748b" stroke-width="2" data-connector="221-412-dining"/><text x="670" y="310" class="micro center">221-412</text>
<path d="M715 305H758" stroke="#c2410c" stroke-width="4"/>
<rect x="758" y="287" width="135" height="85" rx="8" fill="#fff7ed" stroke="#f97316" stroke-width="2" data-load="living-dining-light"/><text x="825" y="317" class="small bold center">餐区双头灯</text><text x="825" y="338" class="micro center">L2 → 灯L</text><text x="825" y="356" class="micro center">N来自221-615</text>
<path d="M247 295H315V390H740M740 390V275M740 390H825V372" fill="none" stroke="#2563eb" stroke-width="3" data-neutral="living-lights"/>
<text x="610" y="383" class="micro blue center">N直接分到两盏灯，不经过开关输出</text>

<g data-junction="TN-LIV-SOFA">
 <rect x="75" y="430" width="210" height="245" rx="10" class="panel"/>
 <text x="180" y="458" class="small bold center">TN-LIV-SOFA 高位盒</text>
 <text x="180" y="480" class="micro center">L/N各1只221-615</text>
 <rect x="108" y="502" width="145" height="34" rx="6" fill="#fff1f2" stroke="#dc2626" stroke-width="2"/><text x="180" y="524" class="small center">L｜221-615</text>
 <rect x="108" y="552" width="145" height="34" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/><text x="180" y="574" class="small center">N｜221-615</text>
 <text x="180" y="615" class="micro center">三个末端只共用此节点</text><text x="180" y="635" class="micro red center">不得串联</text>
</g>
<g data-sofa-branches="three-independent-always-on">
 <path d="M285 520H350V475H410" fill="none" stroke="#dc2626" stroke-width="3"/><path d="M285 568H335V491H410" fill="none" stroke="#2563eb" stroke-width="3"/>
 <path d="M285 520H360V555H410" fill="none" stroke="#dc2626" stroke-width="3"/><path d="M285 568H350V571H410" fill="none" stroke="#2563eb" stroke-width="3"/>
 <path d="M285 520H350V635H410" fill="none" stroke="#dc2626" stroke-width="3"/><path d="M285 568H335V651H410" fill="none" stroke="#2563eb" stroke-width="3"/>
 <rect x="410" y="450" width="300" height="62" rx="8" fill="#fff" stroke="#2563eb" stroke-width="2" data-outlet="robot-always-on"/><text x="430" y="477" class="small bold">BVVB 2×2.5 → 扫地机低位常电</text><text x="430" y="497" class="micro red">禁止智能控制底座电源</text>
 <rect x="410" y="530" width="300" height="62" rx="8" fill="#fff" stroke="#2563eb" stroke-width="2" data-outlet="sofa-upper-always-on"/><text x="430" y="567" class="small bold">BVVB 2×2.5 → 沙发上部常电</text>
 <rect x="410" y="610" width="300" height="62" rx="8" fill="#fff" stroke="#2563eb" stroke-width="2" data-outlet="sofa-background-always-on"/><text x="430" y="637" class="small bold">BVVB 2×2.5 → 背景灯独立常电</text><text x="430" y="657" class="micro">贴“仅背景灯”；灯具本体/智能插头控制</text>
</g>
<rect x="735" y="470" width="160" height="160" rx="9" fill="#fff1f2" stroke="#dc2626" stroke-width="2"/>
<text x="815" y="500" class="small bold center">迁位与停工点</text><text x="755" y="529" class="micro">原暗盒改装JZ-N2</text><text x="755" y="550" class="micro">洗烘插座迁相邻明盒</text><text x="755" y="571" class="micro">端子/盒深/LED负载先核</text><text x="755" y="592" class="micro red">不兼容即停工</text><text x="755" y="613" class="micro red">不削细导体、不强压盒盖</text>
<text x="75" y="728" class="small red">功能验收：两键分别只控制主灯/餐灯；任一灯关闭不得影响三只沙发节点常电插座或洗烘插座。</text>
'''
    side = sidebar("35 施工核对", [
        "开关位置：洗烘机东侧既有暗盒",
        "第1键主灯；第2键餐灯",
        "客厅只保留两条受控回线",
        "L/N由BVVB送到开关盒",
        "L1/L2均用BV 1×2.5返回",
        "两条回线各用221-412收口",
        "灯具N直接来自高位221-615",
        "开关端子禁止并压两根导体",
        "背景灯不接JZ-N2输出",
        "扫地机/沙发/背景灯三支并联常电",
        "洗烘插座迁相邻独立明盒",
        "实物不支持2.5mm²时停工",
        "盒深不足用延长框或深明盒",
        "!断电核L/N/L1/L2；专业终检后通电",
    ], [("#dc2626", "相线/受控L"), ("#2563eb", "中性线N/常电支线"), ("#f97316", "JZ-N2与餐灯")])
    return construction_document("living-jz-n2-wiring", "35 客厅 JZ-N2 施工接线图", "客厅双键盒内端子、主灯/餐灯回线、洗烘迁位与沙发三路独立常电", body + side)


def bedroom_jz_n2_wiring() -> str:
    body = r'''
<rect x="45" y="112" width="880" height="650" rx="14" fill="#f8fafc" stroke="#475569" stroke-width="2"/>
<text x="485" y="140" class="note bold center">卧室主灯 / 床下灯专用插座与吊扇调速器分离</text>
<g data-junction="TN-BED-01">
 <rect x="72" y="172" width="205" height="180" rx="10" class="panel"/>
 <text x="174" y="198" class="small bold center">TN-BED-01 高位盒</text>
 <rect x="103" y="222" width="142" height="34" rx="6" fill="#fff1f2" stroke="#dc2626" stroke-width="2" data-connector="221-615-L"/><text x="174" y="244" class="small center">L｜221-615</text>
 <rect x="103" y="282" width="142" height="34" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2" data-connector="221-615-N"/><text x="174" y="304" class="small center">N｜221-615</text>
 <text x="174" y="337" class="micro center">6mm²主干 → BVVB短尾</text>
</g>
<path d="M47 239H103" stroke="#dc2626" stroke-width="5" data-conductor="6mm-L"/><text x="50" y="225" class="micro red">6mm² L</text>
<path d="M47 299H103" stroke="#2563eb" stroke-width="5" data-conductor="6mm-N"/><text x="50" y="285" class="micro blue">6mm² N</text>
<path d="M245 239H350" stroke="#dc2626" stroke-width="4"/><path d="M245 299H350" stroke="#2563eb" stroke-width="4"/><text x="298" y="218" class="micro center">BVVB 2×2.5</text>

<g data-device="JZ-N2-bedroom" data-box="E-BOX-BED-JZ">
 <rect x="350" y="165" width="245" height="240" rx="12" fill="#fff7ed" stroke="#f97316" stroke-width="3"/>
 <text x="472" y="192" class="small bold center">京东京造 JZ-N2</text><text x="472" y="210" class="micro center">卧室门内右手既有暗盒｜零火双开</text>
 <circle cx="368" cy="239" r="13" fill="#fff1f2" stroke="#dc2626" stroke-width="2"/><text x="368" y="243" class="micro center">L</text>
 <rect x="378" y="282" width="100" height="36" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2" data-connector="221-413-bedroom-N"/><text x="428" y="305" class="small center">N｜221-413</text>
 <path d="M350 299H378" stroke="#2563eb" stroke-width="4"/><path d="M478 299H545" stroke="#2563eb" stroke-width="3"/>
 <circle cx="565" cy="299" r="13" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/><text x="565" y="303" class="micro center">N</text>
 <circle cx="565" cy="239" r="14" fill="#fff" stroke="#dc2626" stroke-width="2"/><text x="565" y="243" class="micro center">L1</text>
 <circle cx="565" cy="359" r="14" fill="#fff" stroke="#c2410c" stroke-width="2"/><text x="565" y="363" class="micro center">L2</text>
 <text x="472" y="246" class="small center">第1键｜主灯</text><text x="472" y="366" class="small center">第2键｜床下灯</text>
 <text x="472" y="391" class="micro red center">端子不并压两根线；N在盒内用221-413分线</text>
</g>

<path d="M579 239H630" stroke="#dc2626" stroke-width="4" data-controlled-return="bedroom-main"/>
<rect x="630" y="222" width="90" height="34" rx="6" fill="#fff" stroke="#64748b" stroke-width="2" data-connector="221-412-bedroom-main"/><text x="675" y="244" class="micro center">221-412</text>
<path d="M720 239H760" stroke="#dc2626" stroke-width="4"/>
<rect x="760" y="188" width="135" height="96" rx="8" fill="#fffbeb" stroke="#f59e0b" stroke-width="2" data-load="bedroom-main-light"/><text x="827" y="220" class="small bold center">卧室主灯</text><text x="827" y="244" class="micro center">L1 → 灯L</text><text x="827" y="264" class="micro center">灯N来自高位221-615</text>
<path d="M245 299H315V425H827V284" fill="none" stroke="#2563eb" stroke-width="3" data-neutral="bedroom-main-light"/>

<path d="M579 359H690V375" fill="none" stroke="#c2410c" stroke-width="4" data-controlled-output="underbed-L"/>
<path d="M478 299H615V420H690" fill="none" stroke="#2563eb" stroke-width="3" data-underbed-neutral="from-221-413"/>
<rect x="690" y="340" width="205" height="112" rx="9" fill="#fff" stroke="#c2410c" stroke-width="3" data-outlet="underbed-light-controlled" data-type="10A-two-pin"/>
<text x="792" y="370" class="small bold center">10A二孔专用受控插座</text><text x="792" y="393" class="small center">贴“仅床下灯”</text><text x="792" y="415" class="micro center">L来自JZ-N2 L2｜N来自221-413</text><text x="792" y="437" class="micro center">BVVB 2×2.5约3m｜可拔插、不被床压住</text>

<g data-fan-separation="true">
 <path d="M245 239H300V525H365" fill="none" stroke="#f59e0b" stroke-width="4" data-fan-feed="independent-from-TN-BED-01"/>
 <path d="M245 299H285V545H365" fill="none" stroke="#2563eb" stroke-width="3"/>
 <rect x="365" y="500" width="185" height="88" rx="9" fill="#fffbeb" stroke="#f59e0b" stroke-width="3" data-device="fan-speed-controller" data-box="E-BOX-BED-FAN"/><text x="457" y="528" class="small bold center">西墙原吊扇调速器</text><text x="457" y="550" class="micro center">独立暗盒 / 独立输出</text><text x="457" y="570" class="micro red center">不与JZ-N2共盒或共输出</text>
 <path d="M550 544C635 500 725 500 785 535" fill="none" stroke="#7c3aed" stroke-width="5" stroke-dasharray="3 8" data-fan-feed="existing-concealed"/>
 <circle cx="820" cy="545" r="38" fill="#f5f3ff" stroke="#7c3aed" stroke-width="3"/><text x="820" y="550" class="small center">吊扇</text>
 <text x="680" y="493" class="micro purple center">既有暗线：先测通断与绝缘</text>
</g>
<rect x="80" y="630" width="815" height="88" rx="9" fill="#fff1f2" stroke="#dc2626" stroke-width="2"/>
<text x="102" y="657" class="small red bold">床下灯安全：</text><text x="205" y="657" class="small red">只用厂家完整220V二脚插头成品；不剪插头、不裸接铜箔。</text><text x="102" y="680" class="small red">插座可拔插且不受床体挤压；灯带远离床品、猫可啃咬位置和积尘散热死角。</text><text x="102" y="703" class="small red">功能验收：两键只控主灯/床下灯；关闭任一键不得影响床侧常电或吊扇。</text>
'''
    side = sidebar("36 施工核对", [
        "开关位置：卧室门内右手既有暗盒",
        "第1键主灯；第2键床下灯",
        "L/N用BVVB送到开关盒",
        "盒内N用221-413一分二",
        "L1用BV 1×2.5经221-412到主灯",
        "L2用BVVB相线到专用插座",
        "床下点只装10A二孔并贴专用标签",
        "厂家完整220V二脚插头，不剪线",
        "西墙调速器暗盒保持独占",
        "既有吊扇暗线先测通断和绝缘",
        "JZ-N2与调速器不共盒、不共输出",
        "盒深不足用延长框或深明盒",
        "!实物不支持2.5mm²或负载不匹配即停工",
        "!断电核L/N/L1/L2；专业终检后通电",
    ], [("#dc2626", "主灯受控L"), ("#c2410c", "床下灯受控L"), ("#2563eb", "N"), ("#7c3aed", "吊扇既有暗线")])
    return construction_document("bedroom-jz-n2-wiring", "36 卧室 JZ-N2 与吊扇分离施工图", "卧室双键、主灯、床下灯专用插座及西墙吊扇调速器的独立接线", body + side)


def electrical_segment_takeoff() -> str:
    rows = [
        ("E6-01", "1×6", "L/N各1", "0.6/芯", "主箱RCBO-01 → 副箱C20-01", "保护器端子"),
        ("E6-02", "1×6", "L/N各1", "0.6/芯", "主箱RCBO-02 → 副箱C20-02", "保护器端子"),
        ("E6-03", "1×6", "L/N各1", "0.6/芯", "主箱RCBO-03 → 副箱C20-03", "保护器端子"),
        ("E6-04", "1×6", "L/N各1", "0.6/芯", "主箱MCB-04 → 副箱C20-04", "保护器端子"),
        ("E6-05", "1×6", "L/N各1", "0.6/芯", "主箱MCB-05 → 副箱C20-05", "保护器端子"),
        ("E6-06", "1×6", "L/N各1", "4.0/芯", "副箱C20-01 → TN-BED-03", "615续接/613末端"),
        ("E6-07", "1×6", "L/N各1", "5.0/芯", "副箱C20-02 → TN-KIT-03", "615续接"),
        ("E6-08", "1×6", "L/N各1", "9.0/芯", "副箱C20-03 → TN-LIV-DESK", "615/613续接"),
        ("EB-01A", "2×2.5", "1根", "2.0", "TN-BED-01 → 卧室JZ-N2", "615→L/N"),
        ("EB-01B", "2×2.5", "1根", "1.0", "TN-BED-01 → 卧室主灯N", "N615/余芯封护"),
        ("EB-02", "2×2.5", "1根", "3.0", "卧室JZ → 床下灯专用插座", "L2 / N经413"),
        ("EB-03", "2×2.5", "1根", "1.0", "TN-BED-01 → 吊扇调速器", "615→调速器"),
        ("EB-04", "2×2.5", "1根", "1.5", "TN-BED-02 → 床南常电", "615→插座"),
        ("EB-05", "2×2.5", "1根", "2.0", "TN-BED-02 → 卧室空调", "615→专用插座"),
        ("EB-06", "2×2.5", "1根", "2.5", "TN-BED-03 → 床北常电", "613→插座"),
        ("EK-01", "2×2.5", "1根", "2.0", "TN-KIT-01 → 燃气热水器", "615→设备点"),
        ("EK-02", "2×2.5", "1根", "2.0", "TN-KIT-01 → 洗碗机", "615→三孔常电"),
        ("EK-03", "2×2.5", "1根", "2.0", "TN-KIT-02 → 油烟机", "615→设备点"),
        ("EK-04", "2×2.5", "1根", "2.0", "TN-KIT-02 → 台面插座", "615→插座"),
        ("EK-05", "2×2.5", "1根", "3.0", "TN-KIT-03 → 厨房灯/开关", "615→L/N与灯N"),
        ("EL-01", "2×2.5", "1根", "2.0", "TN-HALL-01 → 玄关设备架", "615→常电组"),
        ("EL-02", "2×2.5", "1根", "2.0", "TN-HALL-01 → 走廊A灯带/开关", "615→L/N与灯N"),
        ("EL-03", "2×2.5", "1根", "2.0", "TN-HALLB-01 → 走廊B灯/开关", "613/615"),
        ("EL-04", "2×2.5", "1根", "3.0", "TN-LIV-WASH → 洗烘相邻明盒", "615→插座"),
        ("EL-05", "2×2.5", "1根", "3.0", "TN-LIV-WASH → 小厨电双五孔", "615→415"),
        ("EL-06", "2×2.5", "1根", "3.5", "TN-LIV-LIGHT → 客厅JZ-N2", "L613/N615→L/N"),
        ("EL-07A", "2×2.5", "1根", "1.0", "TN-LIV-LIGHT → 客厅主灯N", "N615/余芯封护"),
        ("EL-07B", "2×2.5", "1根", "1.5", "TN-LIV-LIGHT → 餐灯N", "N615/余芯封护"),
        ("EL-08", "2×2.5", "1根", "2.0", "TN-LIV-PROJ → 投影常电", "613→插座"),
        ("EL-09", "2×2.5", "1根", "2.0", "TN-LIV-SOFA → 扫地机", "615→独立常电"),
        ("EL-10", "2×2.5", "1根", "2.0", "TN-LIV-SOFA → 沙发上部", "615→独立常电"),
        ("EL-11", "2×2.5", "1根", "2.0", "TN-LIV-SOFA → 背景灯", "615→仅背景灯"),
        ("EL-12", "2×2.5", "1根", "2.5", "TN-LIV-DESK → 书桌下", "613→插座"),
        ("EL-13", "2×2.5", "1根", "2.5", "TN-LIV-DESK → 书桌上", "613→插座"),
        ("EH-01", "2×2.5", "1根", "4.0", "副箱C20-04 → JB-LIV-HIGH", "连续→413"),
        ("EH-02", "2×2.5", "1根", "1.5", "JB-LIV-HIGH → 客厅空调漏保", "413→SRCD"),
        ("EH-03", "2×2.5", "1根", "1.5", "JB-LIV-HIGH → 冰箱漏保插座", "413→SRCD"),
        ("EW-01", "2×2.5", "1根", "3.0", "副箱C20-05 → RCD-BATH-01", "连续→RCD"),
        ("EW-02", "2×2.5", "1根", "1.0", "RCD-BATH-01 → JB-BATH", "RCD→415"),
        ("EW-03", "2×2.5", "1根", "1.5", "JB-BATH → 浴霸", "415→设备"),
        ("EW-04", "2×2.5", "1根", "0.75", "JB-BATH → 浴室柜/镜灯", "415→设备"),
        ("EW-05", "2×2.5", "1根", "0.75", "JB-BATH → 卫生间灯/开关", "415→L/N与灯N"),
        ("EC-01", "1×2.5", "1根L", "3.5", "客厅JZ L1 → 主灯L", "221-412"),
        ("EC-02", "1×2.5", "1根L", "3.5", "客厅JZ L2 → 餐灯L", "221-412"),
        ("EC-03", "1×2.5", "1根L", "2.5", "走廊A开关 → 灯带插座L", "412/设备端子"),
        ("EC-04", "1×2.5", "1根L", "2.5", "走廊B开关 → 基础灯L", "221-612"),
        ("EC-05", "1×2.5", "1根L", "3.0", "卧室JZ L1 → 主灯L", "221-412"),
        ("EC-06", "1×2.5", "1根L", "3.0", "厨房开关 → 基础灯L", "412/设备端子"),
        ("EC-07", "1×2.5", "1根L", "2.5", "卫生间开关 → 基础灯L", "412/设备端子"),
    ]

    def table_panel(base_x: int, panel_rows: list[tuple[str, str, str, str, str, str]]) -> str:
        parts = [
            f'<rect x="{base_x}" y="108" width="650" height="620" rx="10" fill="#fff" stroke="#cbd5e1" stroke-width="1.5"/>',
            f'<rect x="{base_x}" y="108" width="650" height="30" rx="10" fill="#e2e8f0"/>',
            f'<text x="{base_x + 12}" y="128" class="micro bold">段号</text>',
            f'<text x="{base_x + 62}" y="128" class="micro bold">线型mm²</text>',
            f'<text x="{base_x + 137}" y="128" class="micro bold">根数</text>',
            f'<text x="{base_x + 197}" y="128" class="micro bold">净m</text>',
            f'<text x="{base_x + 245}" y="128" class="micro bold">起点 → 终点</text>',
            f'<text x="{base_x + 500}" y="128" class="micro bold">接头 / 端接</text>',
        ]
        for index, row in enumerate(panel_rows):
            y = 157 + index * 23
            fill = "#f8fafc" if index % 2 == 0 else "#ffffff"
            parts.append(f'<rect x="{base_x + 1}" y="{y - 16}" width="648" height="23" fill="{fill}"/>')
            for offset, value in zip((12, 62, 137, 197, 245, 500), row):
                parts.append(f'<text x="{base_x + offset}" y="{y}" class="micro">{value}</text>')
        return "".join(parts)

    split = 25
    tables = table_panel(35, rows[:split]) + table_panel(715, rows[split:])
    summary = r'''
<rect x="35" y="742" width="1330" height="48" rx="8" fill="#fff7ed" stroke="#f97316" stroke-width="2"/>
<text x="55" y="762" class="small bold">合计：</text><text x="105" y="762" class="small">6mm² 每根净21m / 下料24m；BVVB 2×2.5净69m / 下料77m / 买100m；BV 1×2.5净20.5m / 下料24m / 买30m。</text>
<text x="55" y="782" class="micro red">长度为计划净值；现场弹线超出即先更新表再下料。221端子总采购量不变；实物SKU、导体类型、剥线长度和保护器端接仍须核验。</text>
'''
    return construction_document("electrical-segment-takeoff", "37 全屋逐段下料与端接图", "每一段线型、根数、计划净长、起终点及接头型号；与data/electrical.yaml逐段表同步", tables + summary)


def bathroom_electrical_detail() -> str:
    detail = '''
<rect x="70" y="115" width="850" height="590" rx="16" fill="#f8fafc" stroke="#475569" stroke-width="3"/>
<text x="495" y="150" class="note bold center">卫生间专用馈线与末端保护｜逻辑展开</text>
<g data-circuit="MCB-05"><rect x="105" y="200" width="145" height="72" rx="9" fill="#ede9fe" stroke="#7c3aed" stroke-width="3"/><text x="177" y="225" class="small bold center">MCB-05</text><text x="177" y="246" class="micro center">卫生间专用空开</text></g>
<path d="M250 236H390" fill="none" stroke="#dc2626" stroke-width="5" marker-end="url(#arrow)" data-upstream-segment="continuous-no-joint-no-branch"/>
<text x="320" y="216" class="micro red center">连续 / 机械保护 / 无接头 / 无分支</text>
<g data-device-protection="RCD-BATH-01" data-poles="L+N" data-trip-ma-max="30"><rect x="390" y="185" width="180" height="104" rx="10" fill="#fff1f2" stroke="#dc2626" stroke-width="3"/><text x="480" y="211" class="small bold center">RCD-BATH-01</text><text x="480" y="234" class="small center">L+N双极｜≤30mA</text><text x="480" y="256" class="micro center">TEST / RESET｜门外可检修箱</text><text x="480" y="276" class="micro red center">必须先保护，再产生任何分支</text></g>
<path d="M570 236H640" fill="none" stroke="#64748b" stroke-width="3" marker-end="url(#arrow)"/>
<g data-junction="JB-BATH" data-branch-pattern="post-rcd"><rect x="640" y="195" width="150" height="84" rx="9" class="fixed"/><text x="715" y="222" class="small bold center">JB-BATH</text><text x="715" y="244" class="micro center">L/N逻辑分线</text><text x="715" y="263" class="micro center">T接/分支型号待定</text></g>

<g data-bath-load-downstream="true">
 <path d="M715 279V360H260" fill="none" stroke="#0284c7" stroke-width="3"/>
 <path d="M715 320H480" fill="none" stroke="#0284c7" stroke-width="3"/>
 <path d="M715 340H700" fill="none" stroke="#0284c7" stroke-width="3"/>
 <g data-device-connection="BATH-HEATER"><rect x="120" y="335" width="230" height="110" rx="9" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/><text x="235" y="362" class="small bold center">浴霸连接点</text><text x="235" y="386" class="micro center">说明允许插头时按成品要求连接</text><text x="235" y="407" class="micro center">固定接线时使用可检修带盖盒/隔离</text><text x="235" y="428" class="micro red center">禁止普通智能插座承载</text></g>
 <g data-device-connection="BATH-MIRROR"><rect x="370" y="335" width="230" height="110" rx="9" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/><text x="485" y="362" class="small bold center">浴室柜 / 镜灯｜总RCD下游点</text><text x="485" y="386" class="micro center">说明允许插头时按成品要求连接</text><text x="485" y="407" class="micro center">固定接线时使用可检修带盖盒/隔离</text><text x="485" y="428" class="micro center">独立于浴霸控制输出</text></g>
 <rect x="620" y="335" width="230" height="110" rx="9" fill="#fffbeb" stroke="#f59e0b" stroke-width="2"/><text x="735" y="362" class="small bold center">防潮基础灯 / 镜前灯</text><text x="735" y="386" class="micro center">零火开关盒到达L/N</text><text x="735" y="407" class="micro center">智能开关受控相线只去灯具</text><text x="735" y="428" class="micro center">保留本地实体控制</text>
</g>

<rect x="105" y="490" width="745" height="80" rx="10" fill="#ecfdf5" stroke="#16a34a" stroke-width="2" data-location-preference="hall-a-outside"/><text x="128" y="518" class="small green bold">首选：走廊A卫生间门外</text><text x="128" y="543" class="small green">使用2~4位DIN明装小箱；环境更干燥，TEST/RESET和跳闸复位也更方便。</text>
<rect x="105" y="590" width="745" height="80" rx="10" fill="#fff7ed" stroke="#f97316" stroke-width="2" data-location-fallback="bath-dry-high"/><text x="128" y="618" class="small orange bold">条件允许才改：卫生间内干区高位</text><text x="128" y="643" class="small orange">只有产品说明、安装区域和防护条件均确认合格时才采用；不得放入喷溅/湿区。</text>
<rect x="285" y="575" width="370" height="20" fill="url(#danger)" opacity=".8" data-wet-zone-no-box="true"/><text x="470" y="586" class="micro red center">喷溅/湿区：禁止用“防水”标签替代安装分区</text>
'''
    side = sidebar("34 卫浴电气验收门禁", [
        "MCB-05只接这一条馈线",
        "漏保箱前无接头、无分支",
        "RCD-BATH-01同时切断L和N",
        "额定动作电流不大于30mA",
        "浴霸/浴室柜/镜灯/基础照明全部在下游",
        "设备插头方式必须由说明书允许",
        "浴霸不接普通智能插座",
        "智能照明开关统一使用零火版",
        "无PE标识持续保留，严禁N/PE短接",
        "门外总RCD统一保护卫浴全部负载",
        "!配电箱已确认；剩余设备功率/IP/接线方式待冻结",
    ], [("#dc2626", "漏保前连续馈线 / 安全门禁"), ("#0284c7", "漏保后设备分支"), ("#16a34a", "首选门外"), ("#f97316", "室内干区备选")])
    return document("bathroom-electrical-detail", "34 卫生间专用馈线与漏保详图", "漏保前连续段、双极30mA保护、三条下游分支与干区降级规则", detail + side)


def bedroom_electrical_detail() -> str:
    detail = '''
<rect x="90" y="120" width="820" height="560" rx="16" fill="#ece8f7" stroke="#475569" stroke-width="5"/>
<text x="500" y="154" class="note bold center">卧室西墙与床两侧｜局部展开示意</text>
<rect x="255" y="230" width="440" height="250" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/><text x="475" y="355" class="room">双人床</text><text x="475" y="379" class="roomsub">北侧与南侧各需常电插座</text>
<rect x="108" y="508" width="24" height="14" fill="#fff" stroke="#2563eb" stroke-width="3" data-route-transition="E-ROUTE-01"/><text x="92" y="548" class="micro blue">明装绕卧室门框</text>

<g data-circuit="RCBO-01" data-terminal-scope="fan-control-branch">
 <path d="M134 520H165V430H205" fill="none" stroke="#f59e0b" stroke-width="5" data-route-kind="surface"/>
 <rect x="205" y="400" width="82" height="62" rx="5" fill="#fffbeb" stroke="#f59e0b" stroke-width="3" data-box-type="existing-recessed" data-device="fan-speed-controller"/>
 <text x="246" y="423" class="small bold center">原暗盒</text><text x="246" y="443" class="micro center">仅吊扇调速器</text>
 <path d="M287 430C380 165 585 150 740 210" fill="none" stroke="#7c3aed" stroke-width="5" stroke-dasharray="2 8" data-route-kind="existing-concealed"/>
 <circle cx="760" cy="215" r="28" fill="#f5f3ff" stroke="#7c3aed" stroke-width="3"/><text x="760" y="220" class="small center">吊扇</text>
</g>
<text x="430" y="180" class="small purple center">调速器 → 吊扇：既有暗埋线，复用前测通断与绝缘</text>

<g data-circuit="RCBO-01" data-terminal-scope="bed-socket-branches">
 <path d="M134 520H165V500H310V465" fill="none" stroke="#0284c7" stroke-width="5" data-route-kind="surface"/>
 <rect x="305" y="425" width="88" height="72" rx="5" fill="#e0f2fe" stroke="#0284c7" stroke-width="3" data-box-type="surface-bed-south"/>
 <text x="349" y="451" class="small bold center">床南明盒</text><text x="349" y="472" class="micro center">常电插座</text>
 <path d="M165 500V185H720" fill="none" stroke="#0284c7" stroke-width="5" data-route-kind="surface"/>
 <rect x="720" y="155" width="88" height="72" rx="5" fill="#e0f2fe" stroke="#0284c7" stroke-width="3" data-box-type="surface-bed-north"/>
 <text x="764" y="181" class="small bold center">床北明盒</text><text x="764" y="202" class="micro center">常电插座</text>
 <rect x="165" y="482" width="96" height="38" rx="6" fill="#fff" stroke="#0284c7" stroke-width="2" data-branch-pattern="distributed"/>
 <text x="213" y="497" class="micro bold center">卧室连续主干</text><text x="213" y="512" class="micro center">就地T接短尾线</text>
</g>
<line x1="292" y1="390" x2="292" y2="505" stroke="#dc2626" stroke-width="2" stroke-dasharray="6 5"/><text x="300" y="390" class="micro red">同一RCBO主干；调速器与插座仍分盒</text>
<rect x="110" y="590" width="760" height="62" rx="10" fill="#fff1f2" stroke="#dc2626" stroke-width="2"/><text x="132" y="616" class="small red">一个暗盒不够：保留原暗盒给调速器，在旁边加独立明盒插座；不叠压多根铜鼻子。</text><text x="132" y="638" class="small red">两芯L/N没有PE：PE端子保持未连接并贴标；绝缘、极性和漏保实测通过后才通电。</text>
'''
    side = sidebar("33 现场装配检查", [
        "橙：RCBO-01主干分出的吊扇控制支线",
        "蓝：RCBO-01卧室连续主干 / 常电支线",
        "紫点线：调速器后的既有暗埋线",
        "床南明盒与调速器暗盒相邻但独立",
        "床北使用独立明装插座",
        "不设固定JB-BED；沿主干在需要处T接",
        "普通插座不由智能墙壁开关供电",
        "智能插座只插在常电插座上",
        "不同功能盒保持独立；T接节点必须可检修",
        "!断电、验电后施工；绝缘需专业仪表",
    ], [("#f59e0b", "吊扇受控相线"), ("#0284c7", "卧室漏保常电"), ("#7c3aed", "既有暗埋线")])
    return document("bedroom-electrical-detail", "33 卧室插座与吊扇控制详图", "RCBO-01连续卧室主干、吊扇调速器与床侧明装插座", detail + side)


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
<g data-stack="dishwasher-on-cabinet"><rect x="120" y="310" width="80" height="110" fill="#e8d7bd" stroke="#8b5e3c" stroke-width="2"/><text x="160" y="405" class="micro center">受潮木柜/替代柜</text><rect x="126" y="316" width="68" height="67" class="fixed" data-appliance="dishwasher" data-status="owned-to-move"/><circle cx="160" cy="350" r="20" fill="none" stroke="#64748b" stroke-width="2"/></g><text x="210" y="340" class="small">洗碗机｜已有</text><text x="210" y="360" class="micro">叠放在柜体上方</text><text x="210" y="380" class="micro red">承重/水平/抗振待核</text><text x="210" y="400" class="micro">进水独立开关；排水直入水槽</text>
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
<text x="85" y="687" class="small red">安全门禁：燃气管检修、台面承载、柜体承重、排水固定和无PE保护均未关闭。</text>
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


FIVE_ROUTE_ELECTRICAL_SVG = r"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1120" viewBox="0 0 1600 1120" data-diagram-role="five-route-electrical-freeze" role="img">
<title>38 五路明装电路最终墙面走槽图</title>
<desc>按真实户型和侧墙高位施工语言冻结五路明装路线；卧室吊扇拆除，无新供电。</desc>
<style>
  text{font-family:"Source Han Sans SC","Heiti SC","Arial Unicode MS",sans-serif}
  .title{font-size:28px;font-weight:800;fill:#111827}.sub{font-size:14px;fill:#475569}
  .room{font-size:18px;font-weight:700;fill:#334155;text-anchor:middle}.micro{font-size:12px;fill:#475569}.small{font-size:14px;fill:#334155}.bold{font-weight:700}
  .wall{fill:none;stroke:#1f2937;stroke-width:7}.iw{fill:none;stroke:#64748b;stroke-width:5}.panel{fill:#fff;stroke:#cbd5e1;stroke-width:1.5}.node{fill:#fff;stroke:#111827;stroke-width:2}
  .c1{fill:none;stroke:#7c3aed;stroke-width:6}.c2{fill:none;stroke:#ea580c;stroke-width:6}.c3{fill:none;stroke:#2563eb;stroke-width:6}.c4{fill:none;stroke:#dc2626;stroke-width:6}.c5{fill:none;stroke:#0f766e;stroke-width:6}
  .drop{fill:none;stroke:#64748b;stroke-width:3;stroke-dasharray:7 5}.retired{fill:none;stroke:#94a3b8;stroke-width:3;stroke-dasharray:6 5}
</style>
<rect width="1600" height="1120" fill="#fbfaf7"/>
<text x="60" y="52" class="title">开封32㎡｜38 五路明装电路最终墙面走槽图（2026-09-30）</text>
<text x="60" y="80" class="sub">主干默认钉在侧墙高位，不走天花板平面；90°转弯只是线槽拼接，不设盒；只有导体接续/分叉才设电气节点。</text>

<rect x="90" y="120" width="320" height="430" fill="#f7ead7"/>
<rect x="410" y="120" width="210" height="215" fill="#f9efd0"/>
<rect x="410" y="335" width="105" height="130" fill="#dff3f7"/>
<rect x="515" y="335" width="105" height="130" fill="#edf1f5"/>
<rect x="410" y="465" width="210" height="85" fill="#edf1f5"/>
<rect x="620" y="120" width="320" height="325" fill="#ece8f7"/>
<rect x="620" y="445" width="320" height="105" fill="#f1f5f9"/>
<path class="wall" d="M90 120H940V445H620V550H410V550H90Z"/>
<path class="iw" d="M410 120V465M410 335H535M515 335V465M410 465H620M620 120V350M620 430V550M620 445H940"/>
<text x="250" y="285" class="room">客厅</text><text x="515" y="225" class="room">厨房</text><text x="462" y="402" class="room">卫生间</text>
<text x="567" y="402" class="room">走廊B</text><text x="515" y="515" class="room">玄关 / 走廊A</text><text x="780" y="290" class="room">卧室</text><text x="780" y="505" class="room">公共走廊</text>

<rect x="595" y="435" width="48" height="32" rx="4" fill="#fff" stroke="#111827" stroke-width="2"/>
<text x="650" y="431" class="small bold">配电箱｜卧室门与入户门之间</text>

<path class="c1" d="M618 450 L618 350 L640 350 L640 205"/>
<circle cx="640" cy="305" r="9" class="node"/><text x="654" y="310" class="micro">B1：JZ-N2 + 床南；主干继续</text>
<circle cx="640" cy="205" r="9" class="node"/><text x="654" y="191" class="micro">B2：卧室空调 + 床北</text>
<path class="drop" d="M640 305 H760M640 205 H760"/>
<text x="675" y="335" class="micro" fill="#7c3aed">① C1-BED：配电箱→北→卧室门头→西墙高位→B1→B2</text>

<circle cx="790" cy="285" r="16" class="retired"/><path d="M780 275L800 295M800 275L780 295" class="retired"/>
<text x="790" y="315" class="micro" text-anchor="middle">吊扇拆除｜无新供电</text>

<path class="c2" d="M610 450 L610 335 L535 335 L535 275 L445 275 L445 180"/>
<circle cx="535" cy="285" r="9" class="node"/><text x="548" y="292" class="micro">K1：主灯/入口开关</text>
<circle cx="445" cy="180" r="9" class="node"/><text x="458" y="171" class="micro">K2：西墙家电组</text>
<text x="430" y="315" class="micro" fill="#ea580c">② C2-KIT：与①向北并行，①退出后继续到厨房门头</text>

<path class="c4" d="M602 450 L602 530 L420 530 L420 485 L235 485"/>
<path class="c3" d="M594 450 L594 520 L430 520 L430 475 L385 475 L385 455 L125 455 L125 245"/>
<path class="c5" d="M586 450 L586 510 L440 510 L440 465 L485 465 L485 420"/>
<text x="655" y="566" class="micro">玄关公共墙段，侧墙从靠顶到靠下建议：④ / ③ / ⑤；三路独立槽并排</text>

<circle cx="520" cy="520" r="9" class="node"/><text x="530" y="505" class="micro">H1：设备架 + 玄关灯带</text>
<circle cx="385" cy="455" r="9" class="node"/><text x="335" y="438" class="micro">L1：洗烘 / 餐桌 / JZ-N2</text>
<circle cx="125" cy="300" r="9" class="node"/><text x="142" y="305" class="micro">W1：书桌 / 沙发 / 扫地机 / 投影</text>
<text x="145" y="475" class="micro" fill="#2563eb">③ C3-LIV：南→西→通道→客厅南侧高位向西→西墙向北</text>

<circle cx="235" cy="485" r="9" class="node"/><text x="155" y="513" class="micro">A1：客厅空调 + 冰箱</text>
<text x="245" y="472" class="micro" fill="#dc2626">④ C4-AC-FR：与③共走墙边骨架，到空调/冰箱即结束</text>

<circle cx="485" cy="420" r="9" class="node"/><text x="500" y="410" class="micro">BATH1：浴霸 / 镜柜 / 独立主灯</text>
<text x="495" y="446" class="micro" fill="#0f766e">⑤ C5-BATH：公共墙段→通道/门头→卫生间南墙向东→门头进入</text>

<rect x="990" y="120" width="550" height="410" rx="12" class="panel"/>
<text x="1020" y="158" class="small bold">现场走槽规则</text>
<text x="1020" y="192" class="small">1. 主干钉在侧墙高位；默认上沿距顶约50mm，可统一调到30～80mm。</text>
<text x="1020" y="224" class="small">2. 北向①②；南向③④⑤。公共段不交叉，保持固定上下顺序。</text>
<text x="1020" y="256" class="small">3. 90°转弯、续槽、绕门框：直接拼线槽，不加盒。</text>
<text x="1020" y="288" class="small">4. 只有导体接续/分叉/缩径才形成 B1…BATH1 电气节点。</text>
<text x="1020" y="320" class="small">5. 四分槽优先承载单回路；③④⑤公共段基线为三根独立槽并排。</text>
<text x="1020" y="352" class="small">6. 底槽先钉，腻子可收到底槽边，但不要堵盖板卡槽；最终穿线后再扣盖。</text>
<text x="1020" y="384" class="small">7. 每段底槽内部标 C1-BED / C2-KIT / C3-LIV / C4-AC-FR / C5-BATH。</text>
<text x="1020" y="416" class="small">8. 阳台不做永久220V；吊扇拆除，不复用原调速器线路。</text>
<text x="1020" y="456" class="small bold">图上的路线表示“贴哪面墙、在哪处分流”；实际离顶尺寸以明天放样为准。</text>

<rect x="990" y="555" width="550" height="220" rx="12" class="panel"/>
<text x="1020" y="592" class="small bold">PCT-42 / 分线盒：两版现场实现</text>
<text x="1020" y="626" class="small">A｜实测放得下：PCT-42约39.5×23.4×14.6mm，连导线试装；</text>
<text x="1045" y="654" class="small">用低轮廓的线槽配套接线/分线构件或短段加宽、可独立开盖的分线腔。</text>
<text x="1020" y="690" class="small">B｜放不下：纯2.5mm²用86深明盒/小分线盒；6mm²多分支用约100×100×50。</text>
<text x="1020" y="728" class="small">普通线槽本体能打开，不等于随便把接头裸塞在线槽腔里。</text>
<text x="1020" y="756" class="small">9个主节点负责高位骨架；另4个局部子节点放设备/家具附近，详见39图。</text>

<rect x="990" y="800" width="550" height="215" rx="12" class="panel"/>
<text x="1020" y="837" class="small bold">罗马杆/旧支架：两版放样</text>
<text x="1020" y="872" class="small">A｜不冲突：拆杆；支架易拆则临时拆下并保留原孔，线槽保持统一高位。</text>
<text x="1020" y="908" class="small">B｜冲突：优先整体调整罗马杆；若支架位置必须保留，则整段线槽统一降低。</text>
<text x="1020" y="944" class="small">不要为了单个支架做“下去—绕过—再上来”的蛇形。</text>
<text x="1020" y="980" class="small">明天先用一根2m底槽全屋比划，再正式钉槽。</text>

<line x1="110" y1="1045" x2="165" y2="1045" class="c1"/><text x="175" y="1050" class="micro">①卧室</text>
<line x1="270" y1="1045" x2="325" y2="1045" class="c2"/><text x="335" y="1050" class="micro">②厨房</text>
<line x1="430" y1="1045" x2="485" y2="1045" class="c3"/><text x="495" y="1050" class="micro">③客厅生活</text>
<line x1="620" y1="1045" x2="675" y2="1045" class="c4"/><text x="685" y="1050" class="micro">④空调+冰箱</text>
<line x1="830" y1="1045" x2="885" y2="1045" class="c5"/><text x="895" y="1050" class="micro">⑤卫生间</text>
<text x="110" y="1085" class="micro">施工图属性：断电状态下用于放样、线槽底座和分支位置；最终端接/通电仍受 data/electrical.yaml 保护与验收门禁约束。</text>
</svg>"""


def five_route_electrical_freeze() -> str:
    return FIVE_ROUTE_ELECTRICAL_SVG


ELECTRICAL_NODE_SCHEDULE_SVG = r"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1420" viewBox="0 0 1600 1420" data-diagram-role="electrical-node-schedule" role="img">
<title>39 节点接线与材料复算图</title>
<desc>纠正PCT-42/62双极逻辑后，列出9个主节点、4个局部子节点、复杂开关接法和材料复算</desc>
<style>
 text{font-family:"Source Han Sans SC","Heiti SC","Arial Unicode MS",sans-serif}
 .title{font-size:28px;font-weight:800;fill:#111827}.sub{font-size:14px;fill:#475569}
 .h{font-size:16px;font-weight:700;fill:#111827}.t{font-size:13px;fill:#1f2937}.s{font-size:12px;fill:#475569}
 .box{fill:#fff;stroke:#cbd5e1;stroke-width:1.4}.head{fill:#f8fafc;stroke:#cbd5e1;stroke-width:1.4}
 .main{fill:#eff6ff;stroke:#60a5fa;stroke-width:1.4}.local{fill:#f5f3ff;stroke:#a78bfa;stroke-width:1.4}
 .warn{fill:#fff7ed;stroke:#f59e0b;stroke-width:1.4}.ok{fill:#f0fdf4;stroke:#16a34a;stroke-width:1.4}
</style>
<rect width="1600" height="1420" fill="#fbfaf7"/>
<text x="55" y="52" class="title">39 节点接线与材料复算图｜PCT双极逻辑纠正版</text>
<text x="55" y="80" class="sub">PCT-42：1对L/N输入→2对L/N输出；PCT-62：1对L/N输入→3对L/N输出。一只PCT已同时处理L/N，不再“L一只、N一只”。</text>

<rect x="55" y="110" width="1490" height="44" class="head"/>
<text x="70" y="138" class="h">节点</text><text x="140" y="138" class="h">类型</text><text x="245" y="138" class="h">端子</text><text x="420" y="138" class="h">输入</text><text x="640" y="138" class="h">输出</text><text x="1240" y="138" class="h">空间不足时</text>

<!-- 9 main nodes -->
<rect x="55" y="154" width="1490" height="66" class="main"/><text x="70" y="194" class="h">B1</text><text x="140" y="194" class="t">主节点</text><text x="245" y="194" class="t">PCT-62×1</text><text x="420" y="194" class="t">C1 6mm² L/N</text><text x="640" y="182" class="t">B2主干 / 卧室JZ-N2 / 床南常电</text><text x="640" y="205" class="s">3对输出</text><text x="1240" y="194" class="t">100×100×50</text>
<rect x="55" y="220" width="1490" height="62" class="main"/><text x="70" y="258" class="h">B2</text><text x="140" y="258" class="t">主节点</text><text x="245" y="258" class="t">PCT-42×1</text><text x="420" y="258" class="t">B1 6mm² L/N</text><text x="640" y="258" class="t">卧室空调 / 床北常电</text><text x="1240" y="258" class="t">86深够则86</text>
<rect x="55" y="282" width="1490" height="72" class="main"/><text x="70" y="323" class="h">K1</text><text x="140" y="323" class="t">主节点</text><text x="245" y="323" class="t">PCT-42×1</text><text x="420" y="323" class="t">C2 6mm² L/N</text><text x="640" y="310" class="t">输出1→K2主干；输出2：L→机械开关、N→主灯</text><text x="640" y="334" class="s">开关返回Lsw另用2孔单极端子接主灯L</text><text x="1240" y="323" class="t">100×100×50</text>
<rect x="55" y="354" width="1490" height="66" class="main"/><text x="70" y="394" class="h">K2</text><text x="140" y="394" class="t">主节点</text><text x="245" y="394" class="t">PCT-62×1</text><text x="420" y="394" class="t">K1 6mm² L/N</text><text x="640" y="382" class="t">K2A西南设备组 / 台面电器 / 油烟机</text><text x="640" y="405" class="s">3对输出；主干结束</text><text x="1240" y="394" class="t">100×100×50</text>
<rect x="55" y="420" width="1490" height="66" class="main"/><text x="70" y="460" class="h">H1</text><text x="140" y="460" class="t">主节点</text><text x="245" y="460" class="t">PCT-62×1</text><text x="420" y="460" class="t">C3 6mm² L/N</text><text x="640" y="448" class="t">L1主干 / 玄关设备架 / 灯带开关支路</text><text x="640" y="471" class="s">PCT-62塞不进四分槽→设备架上方加100方盒</text><text x="1240" y="460" class="t">100×100×50</text>
<rect x="55" y="486" width="1490" height="66" class="main"/><text x="70" y="526" class="h">L1</text><text x="140" y="526" class="t">主节点</text><text x="245" y="526" class="t">PCT-62×1</text><text x="420" y="526" class="t">H1 6mm² L/N</text><text x="640" y="514" class="t">W1主干 / L1A洗烘小厨电组 / 客厅JZ-N2</text><text x="640" y="537" class="s">用局部子节点避免4对输出</text><text x="1240" y="526" class="t">100×100×50</text>
<rect x="55" y="552" width="1490" height="66" class="main"/><text x="70" y="592" class="h">W1</text><text x="140" y="592" class="t">主节点</text><text x="245" y="592" class="t">PCT-62×1</text><text x="420" y="592" class="t">L1 6mm² L/N</text><text x="640" y="580" class="t">W1A书桌组 / W1B沙发扫地组 / 投影</text><text x="640" y="603" class="s">3对输出；主干结束</text><text x="1240" y="592" class="t">100×100×50</text>
<rect x="55" y="618" width="1490" height="62" class="main"/><text x="70" y="656" class="h">A1</text><text x="140" y="656" class="t">主节点</text><text x="245" y="656" class="t">PCT-42×1</text><text x="420" y="656" class="t">C4 BVVB L/N</text><text x="640" y="656" class="t">客厅空调 / 冰箱</text><text x="1240" y="656" class="t">86深明盒</text>
<rect x="55" y="680" width="1490" height="72" class="main"/><text x="70" y="722" class="h">BATH1</text><text x="140" y="722" class="t">主节点</text><text x="245" y="722" class="t">PCT-62×1</text><text x="420" y="722" class="t">C5 BVVB L/N</text><text x="640" y="709" class="t">浴霸 / 镜柜 / 主灯机械开关支路</text><text x="640" y="733" class="s">Lsw另用2孔单极端子接主灯L</text><text x="1240" y="722" class="t">固定带盖可检修盒</text>

<!-- local subnodes -->
<rect x="55" y="774" width="1490" height="42" class="head"/><text x="70" y="801" class="h">4个局部子节点：放在设备/家具附近可触及明盒或组合盒，不等于4个高位大白盒</text>
<rect x="55" y="816" width="1490" height="58" class="local"/><text x="70" y="852" class="h">K2A</text><text x="140" y="852" class="t">局部</text><text x="245" y="852" class="t">PCT-42×1</text><text x="420" y="852" class="t">K2一条BVVB</text><text x="640" y="852" class="t">洗碗机 / 燃气热水器控制电源</text><text x="1240" y="852" class="t">设备附近可触及盒</text>
<rect x="55" y="874" width="1490" height="58" class="local"/><text x="70" y="910" class="h">L1A</text><text x="140" y="910" class="t">局部</text><text x="245" y="910" class="t">PCT-42×1</text><text x="420" y="910" class="t">L1一条BVVB</text><text x="640" y="910" class="t">洗烘一体机 / 小厨电五孔组合盒馈线</text><text x="1240" y="910" class="t">洗烘附近组合盒</text>
<rect x="55" y="932" width="1490" height="58" class="local"/><text x="70" y="968" class="h">W1A</text><text x="140" y="968" class="t">局部</text><text x="245" y="968" class="t">PCT-42×1</text><text x="420" y="968" class="t">W1一条BVVB</text><text x="640" y="968" class="t">书桌下常电 / 书桌上常电</text><text x="1240" y="968" class="t">书桌附近可触及盒</text>
<rect x="55" y="990" width="1490" height="58" class="local"/><text x="70" y="1026" class="h">W1B</text><text x="140" y="1026" class="t">局部</text><text x="245" y="1026" class="t">PCT-62×1</text><text x="420" y="1026" class="t">W1一条BVVB</text><text x="640" y="1026" class="t">扫地机 / 沙发上部 / 背景光</text><text x="1240" y="1026" class="t">沙发储物台附近盒</text>

<rect x="55" y="1075" width="720" height="275" rx="10" class="warn"/>
<text x="75" y="1107" class="h">复杂接法</text>
<text x="75" y="1138" class="t">K1：PCT-42输出1→K2；输出2的L→开关、N→主灯；Lsw返回后用2孔单极端子接主灯L。</text>
<text x="75" y="1170" class="t">卧室JZ：B1只送常电L/N；JZ盒N用4孔单极端子分给JZ、主灯、床下灯。</text>
<text x="75" y="1202" class="t">客厅JZ：L1只送常电L/N；JZ盒N用4孔单极端子分给JZ、主灯、餐灯。</text>
<text x="75" y="1234" class="t">H1：正确型号是PCT-62×1；塞不进四分槽就放设备架上方100方盒，不改变供电拓扑。</text>
<text x="75" y="1266" class="t">PCT到货先看极性标识/说明书；完全断电时可用H31通断档辅助复核。</text>
<text x="75" y="1298" class="t">错误说法“一个节点PCT-42×2，L/N各一只”已经废止。</text>

<rect x="800" y="1075" width="745" height="275" rx="10" class="ok"/>
<text x="820" y="1107" class="h">材料复算（采购级）</text>
<text x="820" y="1138" class="t">PCT-42：理论6只 → 若10只装，买1盒。</text>
<text x="820" y="1170" class="t">PCT-62：理论7只 → 若10只装，买1盒。</text>
<text x="820" y="1202" class="t">四分线槽：目标40m；已购20m，仍补20m。6mm²：每极净约21.2m，按25m下料。</text>
<text x="820" y="1234" class="t">BVVB 2×2.5：净量约59～65m，按80～85m施工预算；采购100m继续成立。</text>
<text x="820" y="1266" class="t">2孔2.5mm²单极端子：5只；4孔2.5mm²单极并联端子：4～6只。</text>
<text x="820" y="1298" class="t">PCT纠错不改变五路墙面主干，因此线槽/6mm²总量不重新翻倍。</text>

<text x="55" y="1385" class="s">墙面具体路线看38图。真正剪线前仍以明天墙面实测替换采购级长度。</text>
</svg>"""


def electrical_node_schedule() -> str:
    return ELECTRICAL_NODE_SCHEDULE_SVG


# 2026-09-29: 30~37 are intentionally retired because they encode the superseded
# electrical topology. Do not re-add them to OUTPUTS; Git history preserves them.
LEGACY_ELECTRICAL_OUTPUTS_RETIRED = tuple(f"{n:02d}" for n in range(30, 38))

OUTPUTS = {
    "00-existing-survey.svg": ("existing-survey", "00 现状测量图", existing_survey),
    "10-furniture-circulation.svg": ("furniture-circulation", "10 家具与动线图", furniture_circulation),
    "20-plumbing-gas.svg": ("plumbing-gas", "20 给排水与燃气图", plumbing_gas),
    "38-five-route-electrical.svg": ("five-route-electrical-freeze", "38 五路明装电路最终墙面走槽图", five_route_electrical_freeze),
    "39-electrical-node-schedule.svg": ("electrical-node-schedule", "39 节点接线与材料复算图", electrical_node_schedule),
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
    parser.add_argument("--output", type=Path, default=ROOT / "diagrams")
    args = parser.parse_args()
    generate_all(args.output)
    print(f"Generated {len(OUTPUTS)} SVG diagrams in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
