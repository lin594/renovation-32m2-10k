#!/usr/bin/env python3
"""Generate the current responsibility-separated renovation diagrams."""

from __future__ import annotations

import argparse
from html import escape
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
<text x="100" y="800" class="small">当前讨论图｜北↑ 东→｜墙线仍为名义示意；9/28新尺寸优先，关联墙线待复测。非施工放样或验收图。</text>
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
<circle cx="750" cy="280" r="13" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2"/><text x="750" y="306" class="small center">吊扇退役｜拆除待核</text>
<circle cx="250" cy="330" r="10" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2"/><text x="250" y="354" class="small center">吊扇钩</text>
<rect x="486" y="346" width="13" height="38" class="danger"/><text x="478" y="343" class="small red" text-anchor="end">浴霸</text>
<text x="560" y="319" class="small orange">厨房旧门已拆</text><text x="445" y="470" class="small orange">卫浴旧门已拆</text>
<text x="640" y="340" class="small orange">卧室旧门已拆</text><text x="375" y="520" class="small orange" text-anchor="end">通道旧门已拆</text>
'''
    side = sidebar("本图只确认“现场有什么”", [
        "墙体、洞口、窗户和公共走廊",
        "固定的水、排水、燃气和配电点",
        "空调/浴霸；吊扇确定退役，拆除待核",
        "四个室内旧门均已拆除",
        "走廊A口述宽约1.05m，墙线待复位",
        "不表达家具购买和假定线路",
    ], [("#1f2937", "墙体/固定边界"), ("#0284c7", "水或固定设备"), ("#ea580c", "燃气点")])
    return document("existing-survey", "00 现状测量图", "固定空间、门窗洞口与已确认现场点位", plan_base() + markers + side)


def overall_coordination() -> str:
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
{rect(.45,1.05,3,3.5,"fixed",'data-appliance="dishwasher" data-status="owned-placement-planned"')}<text x="425" y="194" class="micro center">西侧：洗碗机</text><text x="425" y="210" class="micro center">已有｜底部&gt;70cm</text>
{rect(.45,1.05,3.55,4.05,"planned",'data-furniture="small-appliance-rack" data-status="not-purchased"')}<text x="480" y="194" class="micro center">双层架</text><text x="480" y="210" class="micro center">饭煲/高压锅</text>
{rect(.25,.95,4.25,4.9,"planned",'data-appliance="gas-stove" data-placement="east"')}<text x="557" y="190" class="micro center">东侧灶台</text>
{rect(0,1.3,5,7,"fixed")}<text x="700" y="198" class="small center">双人床1.3×2.0</text>
{rect(0,3,7.52,8,"planned")}<text x="860" y="320" class="small center" transform="rotate(-90 860 320)">衣架空间深0.48m×高2.05m｜架子待购</text>
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
        "厨房计划：西侧洗碗机+双层电器架，东侧灶台",
        "保留约80cm受潮木柜；承重/防潮待核",
        "马桶、浴室柜尚未购买",
        "扫地机器人已有，停靠在沙发与书桌之间",
        "上方窄桌下部无前腿，不挡回充与取出",
        "主通道仍需保持约0.7m净宽",
        "卫生间移门不在本图画开启门扇",
        "!家具下单前必须现场复测",
    ], [("#64748b", "已有/固定/明确摆位"), ("#f97316", "计划或未购买"), ("#15803d", "主要通行路径")])
    return document("overall-coordination", "00 整体｜全屋协调图", "固定边界、家具设备占位、主要动线与跨房间冲突", plan_base(False) + furniture + room_labels() + side)


def water_gas_overview() -> str:
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
        "厨房漏点已完全修补；修补后疑似堵塞",
        "2500ml管道疏通剂无改善；1月定位处理",
        "!燃气管、阀门保持可见可检修；不再做架空遮盖",
        "!封闭饰面前应做联合排水测试",
    ], [("#0284c7", "冷水"), ("#dc2626", "热水"), ("#0f766e", "排水"), ("#ea580c", "燃气")])
    return document("water-gas-overview", "10 水气｜全屋系统图", "给水、热水、排水、燃气与两类排烟的全屋关系", plan_base(False, True) + routes + room_labels() + side)


def kitchen_water_gas_elevations() -> str:
    body = r'''
<rect x="55" y="112" width="650" height="570" rx="14" class="panel"/>
<text x="80" y="150" class="note bold">平面｜固定关系与洗碗机接口</text>
<rect x="115" y="185" width="470" height="410" fill="#fffdf8" stroke="#1f2937" stroke-width="5"/>
<rect x="115" y="185" width="470" height="105" class="fixed"/><text x="350" y="275" class="small center">既有北台面 193×46×65cm｜保留</text>
<path d="M245 185H455" class="win"/><path d="M245 185H455" class="winc"/>
<text x="350" y="172" class="micro center">固定窗｜与客厅/卧室整窗同尺寸｜宽×高TBD｜无纱窗</text>
<rect x="125" y="468" width="95" height="105" fill="#dff3f7" stroke="#0284c7" stroke-width="2"/><text x="172" y="515" class="small center">水槽</text><text x="172" y="535" class="micro center">宽约55cm</text>
<rect x="235" y="415" width="115" height="145" class="planned"/><text x="292" y="455" class="small center">洗碗机</text><text x="292" y="476" class="micro center">440×413×424</text><text x="292" y="497" class="micro center">底部&gt;70cm</text><text x="292" y="518" class="micro center">承载二选一TBD</text>
<rect x="485" y="205" width="80" height="70" fill="#fee2e2" stroke="#ea580c" stroke-width="2"/><text x="525" y="237" class="small center">灶台</text><text x="525" y="257" class="micro center">东侧planned</text>
<path class="water" d="M172 450V400H292V415" marker-end="url(#blue-arrow)"/>
<circle cx="242" cy="400" r="8" fill="#fff" stroke="#0284c7" stroke-width="3"/><text x="250" y="388" class="micro blue">冷水三通</text>
<rect x="268" y="390" width="22" height="20" fill="#fff" stroke="#0284c7" stroke-width="2"/><text x="302" y="407" class="micro blue">独立止水阀｜可检修</text>
<path class="drain" d="M292 425V375H202V468" stroke-dasharray="7 5" marker-end="url(#arrow)"/><text x="310" y="368" class="micro green">排水软管按说明直排水槽并可靠固定</text>
<path class="gas" d="M582 220H550" marker-end="url(#arrow)"/><path class="gas" d="M582 220V195H138V350" marker-end="url(#arrow)"/>
<text x="405" y="315" class="micro orange">燃气：东/北入口→灶；另一支沿北墙约2m→西墙热水器</text>
<circle cx="160" cy="555" r="8" fill="#0f766e"/><text x="360" y="585" class="micro green center">水槽旧排水检修口：漏点已修补；修补后疑似堵塞，2500ml疏通剂无改善</text>

<rect x="735" y="112" width="610" height="570" rx="14" class="panel"/>
<text x="760" y="150" class="note bold">北墙 / 西墙展开｜接口和检修门禁</text>
<line x1="775" y1="330" x2="1295" y2="330" stroke="#475569" stroke-width="5"/>
<rect x="820" y="190" width="170" height="100" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/><text x="905" y="225" class="small center">固定窗</text><text x="905" y="248" class="micro center">同客/卧尺寸；宽高TBD</text><text x="905" y="270" class="micro center">油烟机排烟孔另设</text>
<rect x="1080" y="230" width="110" height="80" fill="#fee2e2" stroke="#ea580c" stroke-width="2"/><text x="1135" y="270" class="small center">灶/烟机区</text>
<text x="775" y="357" class="micro">北墙：燃气阀/管全程可见可检修；不得用新增台面或封板遮盖</text>
<line x1="775" y1="615" x2="1295" y2="615" stroke="#475569" stroke-width="5"/>
<rect x="805" y="390" width="145" height="120" fill="#fff7ed" stroke="#ea580c" stroke-width="2"/><text x="878" y="430" class="small center">燃气热水器</text><text x="878" y="452" class="micro center">冷水 / 热水 / 燃气</text><text x="878" y="474" class="micro center">独立烟管→室外</text>
<path class="gas" d="M878 510V550"/><path class="water" d="M840 510V570"/><path class="hot" d="M915 510V570"/>
<ellipse cx="1110" cy="510" rx="85" ry="18" fill="#dff3f7" stroke="#0284c7" stroke-width="2"/><rect x="1025" y="510" width="170" height="90" fill="#effafd" stroke="#0284c7" stroke-width="2"/><text x="1110" y="555" class="small center">水槽 / 检修口</text>
<text x="775" y="645" class="micro red">排烟分离：油烟机排烟与热水器烟管不得共管；管径、坡度、接头及终端按设备说明/燃气公司复核。</text>

<rect x="55" y="705" width="1290" height="70" rx="10" fill="#fff1f2" stroke="#dc2626" stroke-width="2"/>
<text x="80" y="733" class="small red">状态：本图为讨论图。冷水分支、止水、排水软管固定、支架、接口管径/标高均未施工或未验收；电源只作为接口，参见20/21/27。</text>
<text x="80" y="758" class="small red">先疏通并满盆排水复核，再装洗碗机；不得继续盲倒药剂。风险：SAF-0001 / 0005 / 0011 / 0022 / 0025。</text>
'''
    return document(
        "kitchen-water-gas-elevations",
        "11 水气｜厨房给排水、燃气与排烟展开",
        "厨房固定几何、洗碗机进排水、燃气/热水器与两类排烟接口；讨论图",
        body,
    )


def bathroom_water_elevations() -> str:
    body = r'''
<rect x="55" y="112" width="635" height="570" rx="14" class="panel"/>
<text x="80" y="150" class="note bold">平面｜给排水关系与洁具接口</text>
<rect x="155" y="185" width="300" height="420" fill="#e7f5f8" stroke="#1f2937" stroke-width="6"/>
<circle cx="155" cy="185" r="12" fill="#0f766e"/><text x="173" y="180" class="small green">西北唯一排水立管</text>
<circle cx="155" cy="235" r="10" fill="#0284c7"/><text x="173" y="240" class="small blue">西墙偏北入户冷水</text>
<rect x="205" y="205" width="135" height="205" rx="48" class="planned"/><text x="272" y="285" class="small center">马桶</text><text x="272" y="307" class="micro center">坑距约350mm</text><text x="272" y="327" class="micro center">目标深约580mm</text>
<rect x="345" y="475" width="100" height="115" class="planned"/><text x="395" y="520" class="small center">浴室柜</text><text x="395" y="542" class="micro center">冷水已确认</text><text x="395" y="562" class="micro red center">热水/排水TBD</text>
<circle cx="220" cy="535" r="10" fill="#0f766e"/><text x="235" y="540" class="micro green">防臭地漏</text>
<path class="water" d="M155 235H272V205M155 235V520H345M155 235V165H505" marker-end="url(#blue-arrow)"/>
<path class="water" d="M155 235H95" marker-end="url(#blue-arrow)"/><text x="62" y="220" class="micro blue">穿西墙→</text><text x="62" y="236" class="micro blue">客厅洗衣机</text>
<text x="480" y="160" class="micro blue">穿北墙→厨房热水器冷水</text>
<path class="hot" d="M505 185H180V455" marker-end="url(#arrow)"/><text x="490" y="205" class="micro red" text-anchor="end">热水器回水→淋浴冷热</text>
<path class="drain" d="M272 350L155 185M220 535L155 185" stroke-dasharray="7 5"/>
<path class="drain" d="M95 485H220V535" stroke-dasharray="7 5" marker-end="url(#arrow)"/><text x="72" y="465" class="micro green">洗衣机低位</text><text x="72" y="481" class="micro green">穿墙排水</text>
<path d="M420 580L180 220" stroke="#64748b" stroke-width="2" stroke-dasharray="5 5" marker-end="url(#arrow)"/><text x="470" y="610" class="micro">设计向西北找坡｜实际排水待验</text>

<rect x="720" y="112" width="625" height="570" rx="14" class="panel"/>
<text x="745" y="150" class="note bold">西墙 / 北墙展开｜完成面标高均TBD</text>
<line x1="760" y1="340" x2="1305" y2="340" stroke="#475569" stroke-width="5"/>
<rect x="790" y="205" width="115" height="115" class="planned"/><text x="848" y="250" class="small center">浴室柜</text><text x="848" y="273" class="micro center blue">冷水 confirmed</text><text x="848" y="296" class="micro red center">热水/排水 TBD</text>
<rect x="990" y="195" width="120" height="125" fill="#d8f2f6" stroke="#0284c7" stroke-width="2"/><text x="1050" y="240" class="small center">淋浴</text><text x="1050" y="263" class="micro center">冷热接口</text><text x="1050" y="286" class="micro center">高度TBD</text>
<rect x="1185" y="225" width="90" height="95" rx="30" class="planned"/><text x="1230" y="275" class="small center">马桶</text>
<text x="760" y="370" class="micro">西墙：浴室柜冷水事实已确认；不得提前把热水或排水画成已完成。</text>
<line x1="760" y1="615" x2="1305" y2="615" stroke="#475569" stroke-width="5"/>
<rect x="790" y="425" width="115" height="175" fill="#ecfeff" stroke="#0f766e" stroke-width="3"/><text x="848" y="475" class="small center">23×23cm</text><text x="848" y="499" class="small center">L型PVC包管</text><text x="848" y="523" class="micro center">planned</text><text x="848" y="548" class="micro center">最小净22×22</text>
<path class="drain" d="M848 425V390"/><text x="930" y="430" class="micro green">立管必须保留检修条件</text>
<text x="930" y="475" class="small">共管关系</text><text x="930" y="500" class="micro">洗衣机→防臭地漏→与马桶末端共用排水</text><text x="930" y="525" class="micro red">满流/返水/异味必须联合测试</text><text x="930" y="550" class="micro red">湿区穿墙后恢复防水并留照片</text>

<rect x="55" y="705" width="1290" height="70" rx="10" fill="#fff1f2" stroke="#dc2626" stroke-width="2"/>
<text x="80" y="733" class="small red">状态：讨论图。管径、接口螺纹、完成面高度、浴室柜热水/排水、实际找坡均TBD；不得据本图封墙或采购错误配件。</text>
<text x="80" y="758" class="small red">环氧层不替代找坡/排水验收；浴霸与镜灯电气只作跨专业接口，参见22/27，所有湿区用电须位于≤30mA双极保护下游。</text>
'''
    return document(
        "bathroom-water-elevations",
        "12 水气｜卫生间给排水展开",
        "入户水、冷热分支、洁具接口、洗衣机穿墙排水及西北立管；讨论图",
        body,
    )


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
        "本图为点位图，路线见20图",
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
 <circle cx="820" cy="545" r="38" fill="#f5f3ff" stroke="#7c3aed" stroke-width="3"/><text x="820" y="550" class="small center">吊扇退役｜拆除待核</text>
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
 <circle cx="760" cy="215" r="28" fill="#f5f3ff" stroke="#7c3aed" stroke-width="3"/><text x="760" y="220" class="small center">吊扇退役｜拆除待核</text>
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


def openings_pet_safety() -> str:
    doors = '''
<!-- Entry door: existing -->
<path d="M600 530H680M600 450A80 80 0 0 1 680 530" fill="none" stroke="#7c3aed" stroke-width="3"/><text x="650" y="548" class="small purple">入户门｜已有</text>
<!-- Bedroom door: not purchased -->
<path d="M600 425H680" fill="none" stroke="#94a3b8" stroke-width="3" stroke-dasharray="7 5"/><text x="645" y="335" class="small" fill="#64748b">卧室门｜本阶段不做</text>
<!-- Kitchen slider: closed representation only -->
<path d="M520 323H600M440 317H510" fill="none" stroke="#f97316" stroke-width="4" stroke-dasharray="7 5"/><text x="540" y="308" class="small orange">厨房阳光板门｜暂定</text>
<!-- Bath slider: mounted on Hall A side; closed normally, slides east for use. -->
<path d="M405 457H475" fill="none" stroke="#f97316" stroke-width="5"/><text x="438" y="480" class="small orange center">卫生间阳光板门｜暂定</text>
<g data-state="bath-slider-open-east" data-intrusion-m="0.4">
  <rect x="500" y="330" width="45" height="120" fill="#fee2e2" fill-opacity=".58" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="5 4"/>
  <path d="M475 457H545" fill="none" stroke="#dc2626" stroke-width="5" stroke-dasharray="7 5"/>
  <path d="M438 438H520" fill="none" stroke="#dc2626" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="548" y="445" class="micro red">向东开启；临时占走廊B约0.4m</text>
</g>
<!-- Balcony slider -->
<path d="M250 523H325M325 537H400" fill="none" stroke="#7c3aed" stroke-width="4"/><text x="300" y="511" class="small purple">阳台推拉门｜西扇有效约0.7m</text>
<!-- Cat screens and scratch boards -->
<path d="M200 126H300" class="cat"/><text x="250" y="112" class="micro green center">客厅95×47cm</text>
<text x="500" y="112" class="micro orange center">厨房固定窗｜同客/卧尺寸｜宽高TBD</text>
<path d="M700 126H800" class="cat"/><text x="750" y="112" class="micro green center">卧室95×47cm</text>
<path d="M96 535V625" class="cat"/><path d="M110 634H390" class="cat"/>
<path d="M106 542V622" class="cat"/><path d="M112 624H388" class="cat"/>
<text x="82" y="585" class="micro green center" transform="rotate(-90 82 585)">西窗90×47cm</text>
<text x="250" y="650" class="small green center">南窗128×74cm×2｜窗下猫抓板</text>
<path d="M105 545V620M115 625H385" stroke="#16a34a" stroke-width="2" stroke-dasharray="3 5"/><text x="250" y="675" class="micro green center">阳台四周适合墙面暂定猫抓板贴纸｜先做耐潮小样</text>
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
  <text x="998" y="530" class="small">洞口67×198cm；净宽/停泊位按框轨及柜体重测。</text>
</g>
'''
    side_top = '''
<rect x="970" y="120" width="370" height="210" rx="14" class="panel"/>
<text x="994" y="158" class="note bold">门窗与三猫安全</text>
<text x="994" y="194" class="note">卧室门：本阶段不做</text><text x="994" y="223" class="note">厨74×195 / 卫67×198cm：阳光板暂定</text>
<text x="994" y="252" class="note">纱窗5扇：卧1/客1/阳台3；安装状态待核</text><text x="994" y="281" class="note">95×47×2；90×47×1；128×74×2</text>
<text x="994" y="310" class="note red">纱网、边框、锁扣和缝隙需整体验收</text>
'''
    return document("openings-pet-safety", "07 整体｜门窗与猫安全图", "门洞开启协调、防逃边界与三猫入住前验收点", plan_base(False) + doors + room_labels() + side_top)


def kitchen_bath_detail_parts() -> tuple[str, str]:
    kitchen = '''
<rect x="60" y="115" width="620" height="610" rx="14" class="panel"/>
<text x="85" y="155" class="note bold">厨房：实测平面 + 错层设备布局</text>
<rect x="120" y="190" width="400" height="400" fill="#fbf3d9" stroke="#1f2937" stroke-width="5"/>
<rect x="120" y="190" width="400" height="100" class="fixed"/><text x="320" y="278" class="small center">原北台面：193×46cm｜高65cm</text>
<g data-layout="kitchen-west-appliances-east-stove" data-status="planned">
  <rect x="130" y="198" width="92" height="72" class="planned" data-appliance="dishwasher"/><text x="176" y="220" class="small center">京造洗碗机</text><text x="176" y="240" class="micro center">440×413×424mm</text><text x="176" y="257" class="micro center">下翻门｜底部&gt;70cm</text>
  <rect x="235" y="198" width="85" height="72" class="planned" data-furniture="two-tier-appliance-rack"/><text x="277" y="220" class="small center">双层架</text><text x="277" y="240" class="micro center">上：电饭煲</text><text x="277" y="257" class="micro center">下：高压锅</text>
  <rect x="420" y="205" width="82" height="58" fill="#fee2e2" stroke="#b45309" stroke-width="2" data-appliance="gas-stove"/><text x="461" y="230" class="small center">东侧灶台</text><text x="461" y="250" class="micro center">烟机随位微调</text>
</g>
<text x="330" y="214" class="micro">既有北台面保留</text><text x="330" y="232" class="micro red">新增垫高台面已撤销</text><text x="330" y="250" class="micro">不再作为承载方案</text>
<rect x="120" y="470" width="80" height="110" fill="#effafd" stroke="#16829a" stroke-width="2"/><text x="160" y="525" class="small center">水槽55cm</text>
<rect x="120" y="310" width="80" height="160" fill="#e8d7bd" stroke="#8b5e3c" stroke-width="2" data-furniture="retained-wood-cabinet"/><text x="160" y="375" class="small center">保留木柜</text><text x="160" y="395" class="micro center">宽80cm</text><text x="160" y="413" class="micro center">高约70+cm</text><text x="160" y="431" class="micro red center">受潮变形待核</text>
<rect x="500" y="305" width="20" height="140" fill="#fef3c7" stroke="#d97706" stroke-width="2" data-fixture="east-niche"/><text x="494" y="375" class="micro orange" text-anchor="end">东墙壁龛深10cm</text><text x="494" y="392" class="micro orange" text-anchor="end">只放小瓶调料</text>
<path class="dim" d="M100 190H82M100 290H82M100 470H82M100 590H82M88 190V590"/><text x="74" y="400" class="dimtext" transform="rotate(-90 74 400)">西墙南北：水槽55 + 木柜80 + 北台深46 ≈181cm</text>
<text x="215" y="330" class="small">西侧设备区｜位置为planned</text><text x="215" y="352" class="micro">保留木柜或独立支架，二选一待复测</text><text x="215" y="374" class="micro red">承重/水平/抗振/开门模板仍待核</text><text x="215" y="396" class="micro">冷水分支+独立止水；排水直入水槽并固定</text>
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
  <rect x="20" y="-55" width="140" height="55" fill="#e8d7bd" stroke="#8b5e3c" stroke-width="2"/>
  <rect x="240" y="-55" width="140" height="55" fill="#fff7ed" stroke="#f97316" stroke-width="2" stroke-dasharray="7 5"/>
  <text x="90" y="-25" class="small center">保留木柜</text><text x="310" y="-25" class="small center">独立支架TBD</text>
  <text x="200" y="22" class="small center">洗碗机底部需高于地面70cm；两种承载方式复测后二选一</text>
</g>
<text x="85" y="687" class="small red">安全门禁：布局已明确，安装未确认；燃气净空、台面/木柜承重、排水和无PE保护均未关闭。</text>
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
    return kitchen, bath


def kitchen_coordination() -> str:
    kitchen, _ = kitchen_bath_detail_parts()
    side = sidebar("01图只回答空间协调", [
        "固定几何：193×46×65cm北台面",
        "西墙尺寸链：55+80+46≈181cm",
        "西侧：洗碗机+双层小家电架",
        "东侧：灶台；壁龛深10cm",
        "木柜本阶段保留，受潮/承重待核",
        "洗碗机底部须高于地面70cm",
        "门洞74×195cm；外窗固定、无纱窗",
        "外窗与客/卧整窗同尺寸；宽高TBD",
        "水气展开见11；木作见50",
        "设备支撑与燃气检修仍blocked",
    ])
    return document("kitchen-coordination", "01 整体｜厨房协调图", "厨房固定几何、设备布局、竖向关系和跨专业净空", kitchen + side)


def bathroom_coordination() -> str:
    _, bath = kitchen_bath_detail_parts()
    shifted = f'<g transform="translate(-650 0)">{bath}</g>'
    side = sidebar("02图只回答空间协调", [
        "外墙实测约1.3×1.0m",
        "设计基准净区约1.05×0.75m",
        "门洞67×198cm；有效净宽TBD",
        "移门走廊A侧，向东临占B约0.4m",
        "马桶坑距北墙约35cm",
        "候选马桶深约58cm，须成品复测",
        "浴室柜30×40cm仍为候选",
        "西北排水立管、全间按湿区协调",
        "水气展开见12；瓦作见30；涂层见40",
    ])
    return document("bathroom-coordination", "02 整体｜卫生间协调图", "卫生间洁具占位、门洞运行、湿区边界和关键净空", shifted + side)


FINISH_DEFS = r'''
<defs>
  <pattern id="wood" width="28" height="12" patternUnits="userSpaceOnUse">
    <rect width="28" height="12" fill="#e8d7bd"/><path d="M0 6Q7 1 14 6T28 6" fill="none" stroke="#b88959" stroke-width="1" opacity=".65"/>
  </pattern>
  <pattern id="tile" width="22" height="22" patternUnits="userSpaceOnUse">
    <rect width="22" height="22" fill="#dceff0"/><path d="M0 0H22V22H0Z" fill="none" stroke="#8bb8ba" stroke-width="1"/>
  </pattern>
  <pattern id="deck-grid" width="30" height="30" patternUnits="userSpaceOnUse">
    <rect width="30" height="30" fill="#d6b98a"/><path d="M0 0H30V30H0ZM5 0V30M15 0V30M25 0V30" fill="none" stroke="#8b6542" stroke-width="1.5"/>
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
<g data-finish="spc-wood-grain" data-status="not-started" opacity=".24">
  <rect x="100" y="130" width="300" height="400" fill="url(#wood)"/>
  <rect x="400" y="130" width="200" height="200" fill="url(#wood)"/>
  <rect x="500" y="330" width="100" height="120" fill="url(#wood)"/>
  <rect x="400" y="450" width="200" height="80" fill="url(#wood)"/>
  <rect x="600" y="130" width="300" height="300" fill="url(#wood)"/>
</g>
<rect x="400" y="330" width="100" height="120" fill="#e7d4b5" stroke="#b45309" stroke-width="2" data-finish="bathroom-epoxy" data-status="installed"/>
<rect x="100" y="530" width="300" height="100" fill="url(#deck-grid)" data-finish="balcony-30x30-grid-deck"/>

<!-- Existing white wall tiles and counter are a separate recoloring system, not latex paint. -->
<g data-finish="tile-recolor">
  <rect x="406" y="136" width="188" height="188" class="tilepaint"/>
  <rect x="406" y="336" width="88" height="108" class="tilepaint"/>
  <rect x="410" y="145" width="180" height="38" fill="#f3e8ff" fill-opacity=".82" stroke="#a855f7" stroke-width="2"/>
</g>
<text x="500" y="176" class="small center purple">厨房四周墙砖高约1.8m</text>
<text x="500" y="195" class="micro center purple">含现有瓷砖灶台改色</text>
<text x="450" y="354" class="micro center purple">四周墙砖高约1.8m</text>

<!-- Moisture treatment extents are indicative and must be measured on site. -->
<rect x="115" y="420" width="70" height="95" rx="12" class="ceiling" data-surface="living-room-ceiling"/>
<path d="M100 365V525M400 330V525M400 250V330" class="moisture" data-surface="suspected-damp-walls"/>
<path d="M105 540V620M115 625H390" class="moisture" data-surface="balcony-non-window-surfaces"/>
<text x="250" y="320" class="small center" fill="#92400e">西南顶漏源待查；不整面封闭</text>
<text x="112" y="438" class="micro blue" transform="rotate(-90 112 438)">西墙南部疑似受潮</text>
<text x="388" y="418" class="micro blue" transform="rotate(-90 388 418)">东墙南部邻卫生间</text>
<text x="415" y="286" class="micro blue">水槽墙</text>
<text x="450" y="405" class="micro center">环氧已铺2×1.4kg</text><text x="450" y="423" class="micro center">闭水通过后施工</text><text x="450" y="441" class="micro orange center">1月拟加5kg｜先核层间</text>
<text x="250" y="610" class="small center">30×30cm格栅地板｜暂定、可掀开排水</text>
<text x="745" y="408" class="small center">干区SPC｜未购买、未开工</text>
<text x="250" y="660" class="small center">三处罗马杆+窗帘已有｜换布、染色、拆分利用或回收待定</text>
<text x="100" y="690" class="small purple">瓷砖改色粗基数约19.18㎡：待扣厨房窗洞，并补量灶台立面/侧面。</text>
'''
    side = sidebar("饰面体系与施工门禁", [
        "风格：宋氏美学 + 侘寂中古，暖黄色",
        "先修排水渗漏/查潮源，再封闭基层",
        "实际一底一面；油漆工400元，角落不细",
        "底漆3桶用完；面漆4桶余2桶",
        "1月DIY补缝/角落打磨并完成第二遍面漆",
        "S2已刷四区域，业主估计约1遍",
        "卫生间闭水通过后已铺2.8kg环氧",
        "1月拟加5kg；先核跨月层间附着/防滑",
        "厨卫墙砖/灶台改色面积单独测算",
        "!S2厚度/固化及闭水过程证据待补",
    ], [("#b88959", "干区SPC计划（未开工）"), ("#b45309", "卫生间已铺环氧"), ("#a855f7", "既有白色瓷砖改色"), ("#0891b2", "防潮/防水区域")])
    body = FINISH_DEFS + room_fields(True) + finishes + base_walls() + windows() + room_labels() + side
    return document("finishes-materials", "60 墙地面饰面图", "墙顶地面材料分区、基层处理顺序与风格方向", body)


def masonry_overview() -> str:
    layers = '''
<g data-system="dry-floor-spc" data-status="not-started" opacity=".30">
  <rect x="100" y="130" width="300" height="400" fill="url(#wood)"/>
  <rect x="400" y="130" width="200" height="200" fill="url(#wood)"/>
  <rect x="500" y="330" width="100" height="120" fill="url(#wood)"/>
  <rect x="400" y="450" width="200" height="80" fill="url(#wood)"/>
  <rect x="600" y="130" width="300" height="300" fill="url(#wood)"/>
</g>
<rect x="400" y="330" width="100" height="120" fill="#cffafe" stroke="#0891b2" stroke-width="4" data-system="bathroom-s2-waterproof" data-status="flood-test-passed"/>
<text x="450" y="382" class="small center">S2防水层</text><text x="450" y="402" class="micro center">闭水通过</text><text x="450" y="422" class="micro purple center">表层环氧见40</text>
<rect x="100" y="530" width="300" height="100" fill="url(#deck-grid)" opacity=".65" data-system="balcony-30x30-grid-floor"/>
<path d="M100 365V525M400 330V525M400 250V330" class="moisture" data-system="substrate-review"/>
<text x="250" y="322" class="small center" fill="#92400e">受潮/漏源复核后再封闭基层</text>
<text x="745" y="405" class="small center">干区SPC｜未购买、未开工</text>
<text x="250" y="610" class="small center">阳台30×30cm格栅模块｜暂定</text>
'''
    side = sidebar("30图只管基层与地面", [
        "卫生间S2防水层闭水试验已通过",
        "闭水时长/水位/照片仍待归档",
        "原卫生间自铺地砖方案已取消",
        "环氧是防水层上饰面，状态见40",
        "干区SPC未购买、未开工",
        "门槛、平整度、收边仍需复测",
        "厨房不新增垫高台面；保留既有台面",
        "阳台先做3×3模块试排与排水测试",
        "!瓦作验收不能由涂层观感替代",
    ], [("#0891b2", "防水/基层复核"), ("#b88959", "计划地面系统")])
    body = FINISH_DEFS + room_fields(True) + layers + base_walls() + windows() + room_labels() + side
    return document("masonry-overview", "30 瓦作｜全屋基层与地面图", "基层、防水、闭水、地面系统及尚未施工的SPC", body)


def coating_overview() -> str:
    coatings = '''
<g data-coating="latex-paint" data-status="primer-one-topcoat-one" opacity=".20">
  <rect x="100" y="130" width="300" height="400" fill="#fef3c7"/>
  <rect x="600" y="130" width="300" height="300" fill="#fef3c7"/>
  <rect x="400" y="450" width="200" height="80" fill="#fef3c7"/>
</g>
<g data-coating="tile-recolor" data-status="planned">
  <rect x="406" y="136" width="188" height="188" class="tilepaint"/>
  <rect x="406" y="336" width="88" height="108" class="tilepaint"/>
</g>
<rect x="400" y="330" width="100" height="120" fill="#e7d4b5" stroke="#b45309" stroke-width="3" data-coating="bathroom-epoxy" data-status="installed"/>
<text x="450" y="382" class="small center">环氧已铺</text><text x="450" y="402" class="micro center">2×1.4kg</text><text x="450" y="422" class="micro orange center">1月拟加5kg</text>
<rect x="100" y="380" width="130" height="70" fill="none" stroke="#8b5cf6" stroke-width="3" data-coating="wood-wax-oil" data-status="planned"/>
<text x="165" y="414" class="micro purple center">书桌木蜡油小样待做</text>
<path d="M100 365V525M400 330V525M400 250V330" class="moisture" data-coating-gate="damp-source-review"/>
<text x="250" y="322" class="small center" fill="#92400e">持续受潮处不封闭涂刷</text>
<text x="500" y="178" class="small purple center">厨卫瓷砖改色｜计划</text>
<path d="M105 545V620M115 625H390" stroke="#16a34a" stroke-width="5" stroke-dasharray="6 5" data-coating="balcony-cat-scratch-sticker"/><text x="250" y="608" class="small green center">四周适合墙面猫抓板贴纸｜先小样</text>
'''
    side = sidebar("40图只管涂层", [
        "实际一底一面；油漆工400元，角落不细",
        "底漆3桶用完；面漆4桶余2桶",
        "1月DIY补缝/角落打磨并完成第二遍面漆",
        "卫生间闭水通过后已铺2.8kg环氧",
        "拟加5kg前核层间附着/防滑/固化",
        "厨卫瓷砖改色尚未施工",
        "!涂层不替代防水、找坡或基层验收",
    ], [("#ca8a04", "乳胶漆施工区"), ("#a855f7", "计划改色"), ("#b45309", "已铺环氧")])
    body = FINISH_DEFS + room_fields(True) + coatings + base_walls() + windows() + room_labels() + side
    return document("coating-overview", "40 涂装｜全屋涂层状态图", "乳胶漆、环氧、瓷砖改色和木器涂层的实际与计划状态", body)


def woodwork_overview() -> str:
    woodwork = f'''
{rect(2.5,3.2,0,1.3,"fixed",'data-woodwork="existing-desk"')}<text x="165" y="402" class="small center">已有书桌</text><text x="165" y="420" class="micro center">木蜡油小样待做</text>
{rect(0.55,2.45,7.52,8,"planned",'data-woodwork="wardrobe-frame"')}<text x="876" y="280" class="small center" transform="rotate(-90 876 280)">卧室塑料衣架+帘｜未购买</text>
<rect x="410" y="195" width="42" height="76" fill="#e8d7bd" stroke="#8b5e3c" stroke-width="2" data-woodwork="retained-kitchen-cabinet"/><text x="431" y="215" class="micro center">保留</text><text x="431" y="231" class="micro center">木柜</text><text x="431" y="248" class="micro red center">受潮</text>
<rect x="458" y="195" width="65" height="50" class="planned" data-woodwork="kitchen-appliance-rack"/><text x="490" y="217" class="micro center">双层电器架</text>
<path d="M520 323H600M405 457H475" fill="none" stroke="#f97316" stroke-width="5" stroke-dasharray="7 5" data-woodwork="planned-polycarbonate-doors"/>
<path d="M600 345H680" fill="none" stroke="#94a3b8" stroke-width="4" stroke-dasharray="7 5" data-woodwork="bedroom-door-deferred"/>
<text x="540" y="307" class="micro orange">厨房阳光板门</text><text x="440" y="480" class="micro orange center">卫生间阳光板门</text><text x="644" y="335" class="micro">卧室门延期</text>
<rect x="102" y="300" width="45" height="80" class="planned" data-woodwork="robot-over-table"/><text x="154" y="350" class="micro orange">扫地机上方窄桌</text>
'''
    side = sidebar("50图只管木作与定制件", [
        "厨房约80cm旧木柜本阶段保留",
        "木柜受潮变形；承重/水平/防潮待核",
        "西侧双层架：上电饭煲、下高压锅",
        "洗碗机用保留木柜或独立支架，待选",
        "厨卫阳光板门暂定，规格/框轨待核",
        "卧室门本阶段不做",
        "已有书桌拟做黑胡桃木蜡油小样",
        "卧室衣架/帘与客厅窄桌均未购买",
        "门窗洞口与猫安全见07；尺寸表见58",
        "!固定、承重和开启净空均需现场复测",
    ], [("#64748b", "已有木作"), ("#f97316", "计划木作/门窗")])
    return document("woodwork-overview", "50 木作｜全屋木作布置图", "柜体、家具、门扇、置物架及定制件的当前状态", plan_base(False, True) + woodwork + room_labels() + side)


def door_window_schedule() -> str:
    rows = [
        ("门", "厨房门洞", "74×195cm", "已实测；阳光板门暂定，框轨TBD"),
        ("门", "卫生间门洞", "67×198cm", "已实测；阳光板门暂定，有效净宽TBD"),
        ("门", "卧室门", "洞口名义80cm", "旧门已拆；本阶段不做"),
        ("窗", "客厅纱窗", "95×47cm×1", "已定做；安装验收待核"),
        ("窗", "卧室纱窗", "95×47cm×1", "已定做；安装验收待核"),
        ("窗", "阳台西窗", "90×47cm×1", "已定做；活动区对应待验收"),
        ("窗", "阳台南窗", "128×74cm×2", "已定做；两扇映射待验收"),
        ("窗", "厨房外窗", "与客厅/卧室整窗同尺寸；宽高TBD", "固定封闭、无纱窗；不得由纱窗反推"),
    ]
    parts = [
        '<rect x="70" y="115" width="1260" height="585" rx="14" class="panel"/>',
        '<rect x="90" y="140" width="1220" height="46" fill="#f1f5f9"/>',
        '<text x="110" y="170" class="note bold">类别</text><text x="240" y="170" class="note bold">对象</text><text x="520" y="170" class="note bold">已知尺寸</text><text x="790" y="170" class="note bold">状态与边界</text>',
    ]
    y = 186
    for category, item, size, state in rows:
        y += 58
        parts.append(f'<line x1="90" y1="{y-40}" x2="1310" y2="{y-40}" stroke="#e2e8f0"/>')
        parts.append(f'<text x="110" y="{y}" class="note">{category}</text><text x="240" y="{y}" class="note">{item}</text><text x="520" y="{y}" class="note">{size}</text><text x="790" y="{y}" class="note">{state}</text>')
    parts.append('<text x="90" y="735" class="note red">纱窗尺寸是成品尺寸，不得乘二或反推为整窗洞口；五扇总价500元已付清，但安装和防猫验收仍待确认。</text>')
    return document("door-window-schedule", "58 木作｜门窗尺寸表", "门洞、窗扇与五扇防猫纱窗的尺寸、映射和当前状态", "".join(parts))


FIVE_ROUTE_ELECTRICAL_SVG = r"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1120" viewBox="0 0 1600 1120" data-diagram-role="electrical-overview" data-drawing-property="discussion" role="img">
<title>20 电气｜全屋路线图</title>
<desc>讨论图：客厅先北后西沿未来隔帘线横穿并兼顾主照明，精确位置待放样；走廊B独立灯暂时取消，由A长灯条覆盖，不得据图施工。</desc>
<style>
  text{font-family:"Source Han Sans SC","Heiti SC","Arial Unicode MS",sans-serif}
  .title{font-size:28px;font-weight:800;fill:#111827}.sub{font-size:14px;fill:#475569}
  .room{font-size:18px;font-weight:700;fill:#334155;text-anchor:middle}.micro{font-size:12px;fill:#475569}.small{font-size:14px;fill:#334155}.bold{font-weight:700}
  .wall{fill:none;stroke:#1f2937;stroke-width:7}.iw{fill:none;stroke:#64748b;stroke-width:5}.panel{fill:#fff;stroke:#cbd5e1;stroke-width:1.5}.node{fill:#fff;stroke:#111827;stroke-width:2}
  .c1{fill:none;stroke:#7c3aed;stroke-width:6}.c2{fill:none;stroke:#ea580c;stroke-width:6}.c3{fill:none;stroke:#2563eb;stroke-width:6}.c4{fill:none;stroke:#dc2626;stroke-width:6}.c5{fill:none;stroke:#0f766e;stroke-width:6}
  .drop{fill:none;stroke:#64748b;stroke-width:3;stroke-dasharray:7 5}.retired{fill:none;stroke:#94a3b8;stroke-width:3;stroke-dasharray:6 5}
</style>
<rect width="1600" height="1120" fill="#fbfaf7"/>
<text x="60" y="52" class="title">20 电气｜全屋路线图（2026-10-07整理）</text>
<text x="60" y="80" class="sub">实际：电气未完成；两只智能开关因物流退货、现场0只，计划1月重购。路线仍为讨论图，不能据图施工。</text>

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
<text x="650" y="461" class="small bold">配电箱</text>

<path class="c1" d="M618 450 L618 350 L640 350 L640 205"/>
<circle cx="640" cy="305" r="9" class="node"/><text x="654" y="355" class="micro">卧01（B1）：双开点位（现场0只）/ 床南</text>
<circle cx="640" cy="205" r="9" class="node"/><text x="654" y="191" class="micro">卧02（B2）：卧室空调 + 床北</text>
<path class="drop" d="M640 305 H760M640 205 H760"/>
<text x="110" y="625" class="small" fill="#7c3aed">① 卧室：配电箱向北 → 卧室门头 → 西墙高位卧01 → 卧02；展开见24。</text>

<circle cx="790" cy="285" r="16" class="retired"/><path d="M780 275L800 295M800 275L780 295" class="retired"/>
<text x="790" y="315" class="micro" text-anchor="middle">吊扇拆除｜无新供电</text>

<path class="c2" d="M610 450 L610 335 L535 335 L535 275 L445 275 L445 180"/>
<circle cx="535" cy="285" r="9" class="node"/><text x="548" y="292" class="micro">厨01（K1）：灯/开关</text>
<circle cx="445" cy="180" r="9" class="node"/><text x="458" y="171" class="micro">厨02（K2）：西墙家电组</text>
<text x="110" y="660" class="small" fill="#ea580c">② 厨房：与①向北并行，①退出后经厨房门头 → 厨01 → 厨02；展开见21。</text>

<path class="c4" d="M602 450 L602 530 L420 530 L420 485 L235 485"/>
<path class="c3" d="M594 450 L594 520 L430 520 L430 475 L385 475 L385 455"/>
<path class="c3" stroke-dasharray="10 7" data-route-status="blocked-pending-setout" data-route-direction="north-then-west" d="M385 455 L385 260 L125 260"/>
<path class="c5" d="M586 450 L586 510 L440 510 L440 465 L485 465 L485 420"/>
<text x="655" y="566" class="micro">玄关公共墙段，侧墙从靠顶到靠下建议：④ / ③ / ⑤；三路独立槽并排</text>

<circle cx="520" cy="520" r="9" class="node"/><text x="445" y="578" class="micro">玄01（H1）：设备架 / 灯带</text>
<circle cx="385" cy="455" r="9" class="node"/><text x="318" y="438" class="micro">客01（L1）：洗烘/小厨电 / 双开点位（现场0只）</text>
<circle cx="125" cy="260" r="9" class="node" stroke-dasharray="4 3"/><text x="142" y="245" class="micro">客02（W1）：投影 / 沙发 / 书桌（定位TBD）</text>
<text x="110" y="695" class="small" fill="#2563eb">③ 客01先北再沿未来隔帘线西穿→客02；兼顾主照明，标高/位置TBD；展开见23/26。</text>

<circle cx="235" cy="485" r="9" class="node"/><text x="155" y="513" class="micro">客03（A1）：客厅空调 + 冰箱</text>
<text x="110" y="730" class="small" fill="#dc2626">④ 空调冰箱：独立回路，经客厅南侧到A1后分两个末端。</text>

<circle cx="485" cy="420" r="9" class="node"/><text x="420" y="440" class="micro">卫01（BATH1）</text>
<text x="110" y="765" class="small" fill="#0f766e">⑤ 卫生间：公共墙段 → 通道/门头 → 卫生间南墙 → 卫01；展开见22。</text>

<rect x="990" y="120" width="550" height="410" rx="12" class="panel"/>
<text x="1020" y="158" class="small bold">现场走槽规则</text>
<text x="1020" y="192" class="small">1. 主干钉在侧墙高位；默认上沿距顶约50mm，可统一调到30～80mm。</text>
<text x="1020" y="224" class="small">2. 北向①②；南向③④⑤。公共段不交叉，保持固定上下顺序。</text>
<text x="1020" y="256" class="small">3. 90°转弯、续槽、绕门框：直接拼线槽，不加盒。</text>
<text x="1020" y="288" class="small">4. 只有导体接续/分叉/缩径才形成卧01…卫01电气节点。</text>
<text x="1020" y="320" class="small">5. 四分槽优先承载单回路；③④⑤公共段基线为三根独立槽并排。</text>
<text x="1020" y="352" class="small">6. 底槽先钉，腻子可收到底槽边，但不要堵盖板卡槽；最终穿线后再扣盖。</text>
<text x="1020" y="384" class="small">7. 每段底槽内部标 C1-BED / C2-KIT / C3-LIV / C4-AC-FR / C5-BATH。</text>
<text x="1020" y="416" class="small">8. 阳台不做永久220V；吊扇拆除，不复用原调速器线路。</text>
<text x="1020" y="456" class="small bold" data-cancelled-load="hall-b-light">走廊B独立灯暂取消；A长灯条覆盖，开关在入户与卧室门之间。</text>
<text x="1020" y="486" class="small" fill="#dc2626">10/6收口：材料已购较多，但线路/端接/专业终检未完成。</text>

<rect x="990" y="555" width="550" height="220" rx="12" class="panel"/>
<text x="1020" y="592" class="small bold">PCT-42 / 分线盒：两版现场实现</text>
<text x="1020" y="626" class="small">A｜PCT规格待证实：先取制造商/SKU/说明书，核导体适配，再试装；</text>
<text x="1045" y="654" class="small">用低轮廓的线槽配套接线/分线构件或短段加宽、可独立开盖的分线腔。</text>
<text x="1020" y="690" class="small">B｜放不下：纯2.5mm²用86深明盒/小分线盒；6mm²多分支用约100×100×50。</text>
<text x="1020" y="728" class="small">普通线槽本体能打开，不等于随便把接头裸塞在线槽腔里。</text>
<text x="1020" y="756" class="small">9个已编号主节点+设备区局部分配；走廊B独立灯暂取消，点位见27图。</text>

<rect x="990" y="800" width="550" height="215" rx="12" class="panel"/>
<text x="1020" y="837" class="small bold">罗马杆/旧支架：两版放样</text>
<text x="1020" y="872" class="small">A｜不冲突：拆杆；支架易拆则临时拆下并保留原孔，线槽保持统一高位。</text>
<text x="1020" y="908" class="small">B｜冲突：优先整体调整罗马杆；若支架位置必须保留，则整段线槽统一降低。</text>
<text x="1020" y="944" class="small">不要为了单个支架做“下去—绕过—再上来”的蛇形。</text>
<text x="1020" y="980" class="small">现场先用一根2m底槽全屋比划，再正式钉槽。</text>

<line x1="110" y1="1045" x2="165" y2="1045" class="c1"/><text x="175" y="1050" class="micro">①卧室</text>
<line x1="270" y1="1045" x2="325" y2="1045" class="c2"/><text x="335" y="1050" class="micro">②厨房</text>
<line x1="430" y1="1045" x2="485" y2="1045" class="c3"/><text x="495" y="1050" class="micro">③客厅生活</text>
<line x1="620" y1="1045" x2="675" y2="1045" class="c4"/><text x="685" y="1050" class="micro">④空调+冰箱</text>
<line x1="830" y1="1045" x2="885" y2="1045" class="c5"/><text x="895" y="1050" class="micro">⑤卫生间</text>
<text x="110" y="1085" class="micro">讨论图属性：未决路线/供电/灯控/PCT门禁关闭前不得施工或下料，不得宣称采购完结；通电另须专业验收。</text>
</svg>"""


def electrical_overview() -> str:
    return FIVE_ROUTE_ELECTRICAL_SVG


ELECTRICAL_NODE_SCHEDULE_SVG = r"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1110" viewBox="0 0 1600 1110" data-diagram-role="electrical-nodes" data-drawing-property="discussion" role="img">
<title>27 电气｜主节点与材料图</title>
<desc>九个主节点、PCT-42/62双极语义、末端局部分配原则与材料复算</desc>
<style>
 text{font-family:"Source Han Sans SC","Heiti SC","Arial Unicode MS",sans-serif}
 .title{font-size:28px;font-weight:800;fill:#111827}.sub{font-size:14px;fill:#475569}
 .h{font-size:16px;font-weight:700;fill:#111827}.t{font-size:13px;fill:#1f2937}.s{font-size:12px;fill:#475569}
 .head{fill:#f8fafc;stroke:#cbd5e1;stroke-width:1.4}.main{fill:#eff6ff;stroke:#60a5fa;stroke-width:1.4}
 .warn{fill:#fff7ed;stroke:#f59e0b;stroke-width:1.4}.ok{fill:#f0fdf4;stroke:#16a34a;stroke-width:1.4}
</style>
<rect width="1600" height="1110" fill="#fbfaf7"/>
<text x="55" y="52" class="title">27 电气｜主节点与材料图｜10/7中文编号整理</text>
<text x="55" y="80" class="sub">电气未完成；智能开关2只已退货、现场0只，计划1月重购。PCT须由具体SKU证实6mm²适配，当前仍blocked，不得据图端接。</text>
<rect x="55" y="110" width="1490" height="44" class="head"/>
<text x="70" y="138" class="h">节点</text><text x="150" y="138" class="h">端子</text><text x="350" y="138" class="h">输入</text><text x="590" y="138" class="h">输出</text><text x="1280" y="138" class="h">说明</text>
<rect x="55" y="154" width="1490" height="62" class="main"/><text x="70" y="192" class="h">卧01(B1)</text><text x="150" y="192" class="t">PCT-62×1</text><text x="350" y="192" class="t">C1 6mm² L/N</text><text x="590" y="192" class="t">卧02主干 / 卧室双开点位（现场0只） / 床南常电</text><text x="1280" y="192" class="t">6mm继续</text>
<rect x="55" y="216" width="1490" height="62" class="main"/><text x="70" y="254" class="h">卧02(B2)</text><text x="150" y="254" class="t">PCT-42×1</text><text x="350" y="254" class="t">卧01 6mm² L/N</text><text x="590" y="254" class="t">卧室空调 / 床北常电</text><text x="1280" y="254" class="t">主干结束</text>
<rect x="55" y="278" width="1490" height="70" class="main"/><text x="70" y="320" class="h">厨01(K1)</text><text x="150" y="320" class="t">PCT-42×1</text><text x="350" y="320" class="t">C2 6mm² L/N</text><text x="590" y="307" class="t">厨02主干 / 厨房照明支路</text><text x="590" y="332" class="s">L/Lsw、蓝芯重标及N预留待专业确认，不得照此端接</text><text x="1280" y="320" class="t">6mm继续</text>
<rect x="55" y="348" width="1490" height="62" class="main"/><text x="70" y="386" class="h">厨02(K2)</text><text x="150" y="386" class="t">PCT-42×1</text><text x="350" y="386" class="t">厨01 6mm² L/N</text><text x="590" y="386" class="t">厨房西南设备组 / 台面·油烟机·预留设备组</text><text x="1280" y="386" class="t">两条2.5支线</text>
<rect x="55" y="410" width="1490" height="62" class="main"/><text x="70" y="448" class="h">玄01(H1)</text><text x="150" y="448" class="t">PCT-62×1</text><text x="350" y="448" class="t">C3 6mm² L/N</text><text x="590" y="448" class="t">客01主干 / 玄关设备架 / 玄关灯带·开关</text><text x="1280" y="448" class="t">6mm继续</text>
<rect x="55" y="472" width="1490" height="62" class="main"/><text x="70" y="510" class="h">客01(L1)</text><text x="150" y="510" class="t">PCT-62×1</text><text x="350" y="510" class="t">玄01 6mm² L/N</text><text x="590" y="510" class="t">客02主干 / 洗烘·小厨电 / 客厅双开点位（现场0只）</text><text x="1280" y="510" class="t">6mm继续</text>
<rect x="55" y="534" width="1490" height="70" class="main"/><text x="70" y="576" class="h">客02(W1)</text><text x="150" y="576" class="t">PCT-62×1</text><text x="350" y="576" class="t">客01 6mm² L/N</text><text x="590" y="563" class="t">2.5→投影 / 2.5→沙发娱乐区 / 2.5→书桌</text><text x="590" y="588" class="s">沙发区本地分扫地机低位+置物台上部；书桌本地分上下插座</text><text x="1280" y="576" class="t">主干结束</text>
<rect x="55" y="604" width="1490" height="62" class="main"/><text x="70" y="642" class="h">客03(A1)</text><text x="150" y="642" class="t">PCT-42×1</text><text x="350" y="642" class="t">C4 BVVB 2×2.5</text><text x="590" y="642" class="t">客厅空调 / 冰箱</text><text x="1280" y="642" class="t">独立第④路</text>
<rect x="55" y="666" width="1490" height="70" class="main"/><text x="70" y="708" class="h">卫01</text><text x="150" y="708" class="t">PCT-62×1</text><text x="350" y="708" class="t">C5 BVVB 2×2.5</text><text x="590" y="695" class="t">浴霸 / 镜柜 / 独立主灯·机械开关</text><text x="590" y="720" class="s">旧ID BATH1；必须位于卫生间≤30mA剩余电流保护下游</text><text x="1280" y="708" class="t">独立第⑤路</text>
<rect x="55" y="770" width="720" height="260" rx="10" class="warn"/>
<text x="75" y="805" class="h">末端局部分配：供电尚未全部闭合</text>
<text x="75" y="840" class="t">厨房：K2两条2.5支线到两个设备簇后，本地分相邻插座。</text>
<text x="75" y="875" class="t">洗烘：L1一条2.5到洗烘/小厨电区，再局部分洗烘与1～2个小厨电点。</text>
<text x="75" y="910" class="t">沙发：W1一条2.5到娱乐区，再局部分扫地机低位与置物台上部常电。</text>
<text x="75" y="945" class="t">书桌：W1一条2.5到书桌区域，再局部分桌下/桌上常电。</text>
<text x="75" y="980" class="t">走廊B独立灯暂取消：由A长灯条覆盖，开关在入户门与卧室门之间。</text>
<rect x="800" y="770" width="745" height="260" rx="10" class="ok"/>
<text x="820" y="805" class="h">候选端子与待复算预算（未放行采购）</text>
<text x="820" y="840" class="t">PCT-42：1对L/N输入→2对L/N输出；理论4只→暂按10只装估价。</text>
<text x="820" y="875" class="t">PCT-62：1对L/N输入→3对L/N输出；理论5只→暂按10只装估价。</text>
<text x="820" y="910" class="t">四分线槽：目标40m；已购20m，预计再补20m。</text>
<text x="820" y="945" class="t">6mm²：每极净约21.2m，按25m准备；相线买30m。</text>
<text x="820" y="980" class="t">BVVB 2×2.5：净约59～65m，按80～85m施工预算；原采购预算100m，待复核。</text>
<text x="55" y="1070" class="s">讨论图：先闭合灯控导体、PCT规格并复测客厅转弯位置/长度；不得据此施工或下料，通电另须专业验收。</text>
</svg>"""


def electrical_nodes() -> str:
    return ELECTRICAL_NODE_SCHEDULE_SVG


def electrical_room_sheet(
    role: str,
    title_value: str,
    room_name: str,
    circuit: str,
    route: str,
    nodes: list[tuple[str, str, list[str]]],
    points: list[str],
    lighting: list[str],
    gates: list[str],
) -> str:
    node_parts: list[str] = []
    node_y = 205
    previous_y: int | None = None
    for display_id, legacy_id, outputs in nodes:
        if previous_y is not None:
            node_parts.append(
                f'<path d="M250 {previous_y + 48}V{node_y - 18}" class="power" marker-end="url(#blue-arrow)"/>'
            )
        node_parts.extend(
            [
                f'<rect x="95" y="{node_y - 18}" width="310" height="68" rx="10" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>',
                f'<text x="115" y="{node_y + 7}" class="note bold">{escape(display_id)}（{escape(legacy_id)}）</text>',
                f'<text x="115" y="{node_y + 30}" class="small">{escape(" / ".join(outputs))}</text>',
            ]
        )
        previous_y = node_y
        node_y += 118

    point_parts: list[str] = []
    point_y = 180
    for index, point in enumerate(points, start=1):
        point_parts.append(
            f'<rect x="850" y="{point_y - 20}" width="455" height="38" rx="6" class="planned"/>'
            f'<text x="868" y="{point_y + 5}" class="small">{index:02d}｜{escape(point)}｜建议点位·未施工</text>'
        )
        point_y += 46

    notes: list[str] = []
    y = max(530, node_y + 8)
    notes.append(f'<text x="90" y="{y}" class="small bold">照明 / 控制</text>')
    for item in lighting:
        y += 23
        notes.append(f'<text x="110" y="{y}" class="small">• {escape(item)}</text>')

    gate_parts: list[str] = []
    gate_y = 718
    for gate in gates[:2]:
        gate_parts.append(f'<text x="80" y="{gate_y}" class="small red">• {escape(gate)}</text>')
        gate_y += 24

    body = f'''
<rect x="55" y="112" width="760" height="570" rx="14" class="panel"/>
<text x="80" y="150" class="note bold">{escape(room_name)}路线与中文节点</text>
<text x="80" y="177" class="small blue">回路：{escape(circuit)}｜路线：{escape(route)}</text>
<path d="M95 205H65V160" class="power"/><text x="80" y="202" class="micro blue">来自副保护盒</text>
{''.join(node_parts)}
{''.join(notes)}
<rect x="840" y="112" width="505" height="570" rx="14" class="panel"/>
<text x="865" y="150" class="note bold">末端点位表｜位置/标高均TBD</text>
{''.join(point_parts)}
<text x="865" y="655" class="micro">虚线橙框=建议点位；现场用卷尺放样、拍照、填标高后才转施工图。</text>
<rect x="55" y="696" width="1290" height="72" rx="10" fill="#fff1f2" stroke="#dc2626" stroke-width="2"/>
{''.join(gate_parts)}
'''
    return document(role, title_value, f"{room_name}明装电气节点、末端点位与照明控制；讨论图", body)


def kitchen_electrical() -> str:
    return electrical_room_sheet(
        "kitchen-electrical",
        "21 电气｜厨房节点与点位图",
        "厨房",
        "RCBO-02 → 副箱2P C20",
        "配电箱向北，与卧室路并行；过厨房门头到厨01，再沿墙到厨02",
        [
            ("厨01 门侧照明节点", "K1", ["厨02主干", "厨房主灯/普通开关"]),
            ("厨02 西墙设备节点", "K2", ["西南设备组", "台面/烟机/预留设备组"]),
        ],
        ["燃气热水器常电", "油烟机", "台面电器", "洗碗机三孔常电（不接智能开关）"],
        ["基础漫射灯：普通实体开关", "台面任务灯入住后按需，优先成套插接式低压灯"],
        ["本户无PE：三孔面板PE端保持未连接并持久标识；严禁N/PE短接。", "厨01机械开关导体配置、各设备插头/功率及点位净空未核，通电前由电工验收。"],
    )


def bathroom_electrical() -> str:
    return electrical_room_sheet(
        "bathroom-electrical",
        "22 电气｜卫生间节点与点位图",
        "卫生间",
        "MCB-05 → 副箱2P C20 → 卫生间2P≤30mA保护",
        "沿玄关公共段向西，在通道脱离后经卫生间门头进入卫01",
        [("卫01 卫浴设备末端节点", "BATH1", ["浴霸", "镜柜/镜灯", "防潮主灯/机械开关"])],
        ["浴霸高位连接点", "浴室柜/镜灯连接点", "防潮基础灯", "门外或干区机械开关（功能键数TBD）"],
        ["不新增通用插座", "所有卫生间负载均位于同一2P≤30mA剩余电流保护下游"],
        ["浴霸/镜柜铭牌、防护等级、喷溅距离和接线方式未核，不得仅凭图端接。", "无PE且属湿区：主箱/门外RCD二选一须由电工确认，绝缘和漏保动作实测后才通电。"],
    )


def living_electrical() -> str:
    return electrical_room_sheet(
        "living-electrical",
        "23 电气｜客厅节点与点位图",
        "客厅",
        "RCBO-03生活路 + MCB-04空调冰箱专路；两路不得混接",
        "客01先北，再沿未来隔帘线向西到客02；客03沿南侧最短墙边",
        [
            ("客01 入口生活节点", "L1", ["客02主干", "洗烘/小厨电", "客厅双开"]),
            ("客02 西侧生活节点", "W1", ["投影", "沙发/扫地机", "书桌"]),
            ("客03 空调冰箱节点", "A1", ["客厅空调", "冰箱"]),
        ],
        ["洗烘一体机", "洗烘旁小厨电×2", "书桌下常电", "书桌上常电", "投影仪", "沙发上部充电", "扫地机低位常电", "客厅空调末端漏保", "冰箱末端漏保", "客厅双开暗盒（非插座）"],
        ["双开第1键→客厅主灯；第2键→餐区双头射灯", "沙发背景灯插常电；不得切断扫地机或其他通用插座"],
        ["客01→客02路线/标高、隔帘关系仍待现场弹线；智能双开现场0只，1月重购。", "空调和冰箱须各用≤30mA、L/N双极切断、带TEST/RESET的末端漏保；铭牌待核。"],
    )


def bedroom_electrical() -> str:
    return electrical_room_sheet(
        "bedroom-electrical",
        "24 电气｜卧室节点与点位图",
        "卧室",
        "RCBO-01 → 副箱2P C20",
        "配电箱向北，经卧室门头入室，贴西墙高位由卧01到卧02",
        [
            ("卧01 门侧主节点", "B1", ["卧02主干", "卧室双开", "床南常电"]),
            ("卧02 北侧末端节点", "B2", ["卧室空调", "床北常电"]),
        ],
        ["卧室空调专用点", "床北常电", "床南常电", "床下灯10A二孔专用受控点（不计通用插座）"],
        ["双开第1键→卧室主灯；第2键→仅床下灯专用点", "旧吊扇/调速器退役：原暗线两端绝缘，旧盒盖空白盖板"],
        ["床侧常电不得受智能开关控制；智能双开现场0只，1月到货后核端子/盒深。", "本户无PE；空调插头10A/16A、铭牌与现有连接方式未核，专业测试前保持断开。"],
    )


def hall_electrical() -> str:
    return electrical_room_sheet(
        "hall-electrical",
        "26 电气｜玄关走廊节点与点位图",
        "玄关 / 走廊A、B",
        "RCBO-03 → 副箱2P C20",
        "配电箱向南，经玄关南墙高位到玄01，再继续客厅；三条南向线槽并排不混线",
        [("玄01 设备架节点", "H1", ["客01主干", "设备架常电", "长灯带/普通开关"])],
        ["壁挂设备架≥4位常电", "高位专用受控插座：仅走廊灯带", "入户门与卧室门之间普通实体开关", "走廊B不设独立灯"],
        ["约2m厂家成套插头灯带覆盖走廊A/B", "光猫、路由器、EVE V保持常电，不受照明开关控制"],
        ["设备架需通风、可检修、强弱电分区；灯带保留厂家插头/整流接头/尾塞。", "南向④/③/⑤为三路独立线槽与独立L/N；不得共享中性线或端子。"],
    )


OUTPUTS = {
    "00-overall-coordination.svg": ("overall-coordination", "00 整体｜全屋协调图", overall_coordination),
    "01-kitchen-coordination.svg": ("kitchen-coordination", "01 整体｜厨房协调图", kitchen_coordination),
    "02-bathroom-coordination.svg": ("bathroom-coordination", "02 整体｜卫生间协调图", bathroom_coordination),
    "07-openings-pet-safety.svg": ("openings-pet-safety", "07 整体｜门窗与猫安全图", openings_pet_safety),
    "10-water-gas-overview.svg": ("water-gas-overview", "10 水气｜全屋系统图", water_gas_overview),
    "11-kitchen-water-gas-elevations.svg": ("kitchen-water-gas-elevations", "11 水气｜厨房给排水、燃气与排烟展开", kitchen_water_gas_elevations),
    "12-bathroom-water-elevations.svg": ("bathroom-water-elevations", "12 水气｜卫生间给排水展开", bathroom_water_elevations),
    "20-electrical-overview.svg": ("electrical-overview", "20 电气｜全屋路线图", electrical_overview),
    "21-kitchen-electrical.svg": ("kitchen-electrical", "21 电气｜厨房节点与点位图", kitchen_electrical),
    "22-bathroom-electrical.svg": ("bathroom-electrical", "22 电气｜卫生间节点与点位图", bathroom_electrical),
    "23-living-electrical.svg": ("living-electrical", "23 电气｜客厅节点与点位图", living_electrical),
    "24-bedroom-electrical.svg": ("bedroom-electrical", "24 电气｜卧室节点与点位图", bedroom_electrical),
    "26-hall-electrical.svg": ("hall-electrical", "26 电气｜玄关走廊节点与点位图", hall_electrical),
    "27-electrical-nodes.svg": ("electrical-nodes", "27 电气｜主节点与材料图", electrical_nodes),
    "30-masonry-overview.svg": ("masonry-overview", "30 瓦作｜全屋基层与地面图", masonry_overview),
    "40-coating-overview.svg": ("coating-overview", "40 涂装｜全屋涂层状态图", coating_overview),
    "50-woodwork-overview.svg": ("woodwork-overview", "50 木作｜全屋木作布置图", woodwork_overview),
    "58-door-window-schedule.svg": ("door-window-schedule", "58 木作｜门窗尺寸表", door_window_schedule),
}


def generate_all(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    expected = set(OUTPUTS)
    for path in output_dir.glob("*.svg"):
        if path.name not in expected:
            path.unlink()
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
