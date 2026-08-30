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
    "AGENTS.md",
    "house.yaml",
    "data/budget.yaml",
    "data/inventory.yaml",
    "data/ledger.csv",
    "data/project.yaml",
    "data/procurement.yaml",
    "data/risks.yaml",
    "diagrams/house-plan-v2-framework.svg",
    "diagrams/house-plan-v3-furniture.svg",
    "diagrams/house-plan-v3-services.svg",
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
    for path in sorted((ROOT / "diagrams").glob("*.svg")):
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            errors.append(f"SVG 无法解析：{path.relative_to(ROOT)}：{exc}")


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
