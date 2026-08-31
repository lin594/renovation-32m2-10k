#!/usr/bin/env python3
"""Validate the renovation repository and summarize its ledger."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "PROJECT_STATUS.md",
    "AGENTS.md",
    "house.yaml",
    "data/budget.yaml",
    "data/electrical.yaml",
    "data/finishes.yaml",
    "data/inventory.yaml",
    "data/ledger.csv",
    "data/project.yaml",
    "data/procurement.yaml",
    "data/risks.yaml",
    "data/schedule.yaml",
    "docs/reviews/2026-08-31-third-party-repository-audit.md",
    "docs/reviews/2026-08-31-two-wire-electrical-reassessment.md",
    "docs/reviews/2026-09-01-public-repository-audit.md",
    "diagrams/README.md",
    "diagrams/00-existing-survey.svg",
    "diagrams/10-furniture-circulation.svg",
    "diagrams/20-plumbing-gas.svg",
    "diagrams/30-electrical-low-voltage.svg",
    "diagrams/31-electrical-routes.svg",
    "diagrams/32-electrical-topology.svg",
    "diagrams/33-bedroom-electrical-detail.svg",
    "diagrams/34-bathroom-electrical-detail.svg",
    "diagrams/40-doors-windows-cats.svg",
    "diagrams/50-kitchen-bath-details.svg",
    "diagrams/60-finishes-materials.svg",
)
LEDGER_COLUMNS = (
    "id",
    "date",
    "flow",
    "category",
    "room",
    "item",
    "counterparty",
    "amount_cny",
    "payment_status",
    "project_status",
    "note",
)


def validate_required_files(errors: list[str]) -> None:
    for relative_path in REQUIRED:
        if not (ROOT / relative_path).is_file():
            errors.append(f"缺少必需文件：{relative_path}")


def read_ledger(errors: list[str]) -> list[dict[str, str]]:
    path = ROOT / "data/ledger.csv"
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != LEDGER_COLUMNS:
            errors.append("data/ledger.csv 表头不符合约定")
            return []
        rows = list(reader)

    seen_ids: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        entry_id = row["id"].strip()
        if not entry_id:
            errors.append(f"ledger 第 {line_number} 行缺少 id")
        elif entry_id in seen_ids:
            errors.append(f"ledger 出现重复 id：{entry_id}")
        seen_ids.add(entry_id)
        if row["flow"] not in {"expense", "income"}:
            errors.append(f"ledger {entry_id or line_number} 的 flow 必须是 expense 或 income")
        try:
            amount = Decimal(row["amount_cny"])
            if amount < 0:
                errors.append(f"ledger {entry_id or line_number} 的金额不能为负数")
        except InvalidOperation:
            errors.append(f"ledger {entry_id or line_number} 的金额不是有效数字")
    return rows


def validate_svgs(errors: list[str]) -> None:
    for path in sorted((ROOT / "diagrams").rglob("*.svg")):
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            errors.append(f"SVG 无法解析：{path.relative_to(ROOT)}：{exc}")


def validate_public_layout(errors: list[str]) -> None:
    diagrams = ROOT / "diagrams"
    obsolete = [path.name for path in diagrams.iterdir() if path.is_dir()]
    if obsolete:
        errors.append(f"diagrams 只应保留当前平铺图纸，发现目录：{', '.join(sorted(obsolete))}")
    previews = ROOT / "artifacts" / "previews"
    if previews.exists() and any(previews.iterdir()):
        errors.append("artifacts/previews 仍包含无效光栅预览；公开展示应直接使用SVG")


def validate_status_page(
    errors: list[str], expenses: Decimal, income: Decimal, net_outflow: Decimal
) -> None:
    path = ROOT / "PROJECT_STATUS.md"
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")
    expected = (f"¥{expenses:.2f}", f"¥{income:.2f}", f"¥{net_outflow:.2f}")
    if not all(value in content for value in expected):
        errors.append("PROJECT_STATUS.md 与 ledger.csv 汇总不一致，请运行 make status")
    if "自动生成，请修改 data/ 真源" not in content:
        errors.append("PROJECT_STATUS.md 缺少派生文件标识")


def ledger_summary(rows: list[dict[str, str]]) -> tuple[Decimal, Decimal, Decimal]:
    expenses = sum(
        (Decimal(row["amount_cny"]) for row in rows if row["flow"] == "expense"),
        start=Decimal("0"),
    )
    income = sum(
        (Decimal(row["amount_cny"]) for row in rows if row["flow"] == "income"),
        start=Decimal("0"),
    )
    return expenses, income, expenses - income


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true", help="只输出收支摘要")
    args = parser.parse_args()

    errors: list[str] = []
    validate_required_files(errors)
    rows = read_ledger(errors)
    validate_svgs(errors)
    expenses, income, net_outflow = ledger_summary(rows)
    validate_public_layout(errors)
    validate_status_page(errors, expenses, income, net_outflow)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not args.summary:
        print(f"OK: 项目结构、{len(rows)} 条账目和 SVG/XML 校验通过")
    print(f"累计支出：¥{expenses:.2f}")
    print(f"累计收入：¥{income:.2f}")
    print(f"净现金流出：¥{net_outflow:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
