#!/usr/bin/env python3
"""Validate the renovation repository and summarize its ledger."""

from __future__ import annotations

import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import re
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
    "docs/decisions/README.md",
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
LEDGER_ID = re.compile(r"^(EXP|INC)-\d{4}$")
LEDGER_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LEDGER_REQUIRED_TEXT = (
    "category",
    "room",
    "item",
    "payment_status",
    "project_status",
)


def ledger_error(errors: list[str], line_number: int, message: str) -> None:
    errors.append(f"data/ledger.csv 第 {line_number} 行：{message}")


def ledger_cell(row: dict[str | None, str | list[str] | None], field: str) -> str:
    value = row.get(field)
    return value.strip() if isinstance(value, str) else ""


def github_annotation(error: str) -> str | None:
    match = re.match(r"^data/ledger\.csv 第 (\d+) 行：(.*)$", error)
    if not match:
        return None
    line_number, message = match.groups()
    safe_message = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return f"::error file=data/ledger.csv,line={line_number}::{safe_message}"
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


def read_ledger(
    errors: list[str], path: Path | None = None
) -> list[dict[str, str]]:
    path = path or ROOT / "data/ledger.csv"
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != LEDGER_COLUMNS:
            errors.append(
                "data/ledger.csv 表头不符合约定；请从 docs/editing-guide.md 复制标准表头，不要增删或调换列"
            )
            return []
        rows = list(reader)

    seen_ids: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        if None in row:
            ledger_error(errors, line_number, "列数多于表头；请检查项目或备注中未被正确引用的英文逗号")
        if any(row.get(field) is None for field in LEDGER_COLUMNS):
            ledger_error(errors, line_number, "列数少于表头；空字段也必须保留相邻逗号")

        entry_id = ledger_cell(row, "id")
        if not entry_id:
            ledger_error(errors, line_number, "缺少 id；支出使用 EXP-0001 格式，收入使用 INC-0001 格式")
        elif not LEDGER_ID.fullmatch(entry_id):
            ledger_error(errors, line_number, f"id {entry_id!r} 格式错误；应为 EXP-四位数字 或 INC-四位数字")
        elif entry_id in seen_ids:
            ledger_error(errors, line_number, f"id {entry_id} 重复；每笔账必须使用唯一编号")
        seen_ids.add(entry_id)
        flow = ledger_cell(row, "flow")
        if flow not in {"expense", "income"}:
            ledger_error(errors, line_number, "flow 必须是 expense 或 income")
        elif entry_id and LEDGER_ID.fullmatch(entry_id):
            expected_prefix = "EXP" if flow == "expense" else "INC"
            if not entry_id.startswith(f"{expected_prefix}-"):
                ledger_error(errors, line_number, f"id 与 flow 不匹配；{flow} 必须使用 {expected_prefix}- 前缀")

        entry_date = ledger_cell(row, "date")
        if entry_date:
            try:
                if not LEDGER_DATE.fullmatch(entry_date):
                    raise ValueError
                date.fromisoformat(entry_date)
            except ValueError:
                ledger_error(errors, line_number, f"日期 {entry_date!r} 无效；请使用 YYYY-MM-DD，例如 2026-10-01")

        for field in LEDGER_REQUIRED_TEXT:
            if not ledger_cell(row, field):
                ledger_error(errors, line_number, f"{field} 不能为空；字段说明见 docs/editing-guide.md")
        amount_text = ledger_cell(row, "amount_cny")
        try:
            amount = Decimal(amount_text)
            if not amount.is_finite() or amount <= 0:
                ledger_error(errors, line_number, "amount_cny 必须是大于 0 的有限数字；收入和支出方向由 flow 表示")
        except (InvalidOperation, ValueError):
            ledger_error(errors, line_number, f"amount_cny {amount_text!r} 不是有效数字")
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
            if os.environ.get("GITHUB_ACTIONS") == "true":
                annotation = github_annotation(error)
                if annotation:
                    print(annotation, file=sys.stderr)
        return 1

    if not args.summary:
        print(f"OK: 项目结构、{len(rows)} 条账目和 SVG/XML 校验通过")
    print(f"累计支出：¥{expenses:.2f}")
    print(f"累计收入：¥{income:.2f}")
    print(f"净现金流出：¥{net_outflow:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
