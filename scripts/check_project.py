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
import subprocess
import sys
from urllib.parse import unquote
import xml.etree.ElementTree as ET

try:
    from scripts import photo
except ModuleNotFoundError:  # Direct execution via `python3 scripts/check_project.py`.
    import photo  # type: ignore[no-redef]


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
    "data/photos.csv",
    "data/project.yaml",
    "data/procurement.yaml",
    "data/risks.yaml",
    "data/schedule.yaml",
    "docs/reviews/2026-08-31-third-party-repository-audit.md",
    "docs/reviews/2026-08-31-two-wire-electrical-reassessment.md",
    "docs/reviews/2026-09-01-public-repository-audit.md",
    "docs/decisions/README.md",
    "diagrams/README.md",
    "media/photos/README.md",
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

BASELINE_PHOTOS = {
    "PHOTO-0001": ("2026-08-24", "before", "bedroom", "overview"),
    "PHOTO-0002": ("2026-08-24", "before", "kitchen", "overview"),
    "PHOTO-0003": ("2026-08-24", "before", "living", "overview"),
    "PHOTO-0004": ("2026-08-24", "before", "hall_a", "overview"),
    "PHOTO-0005": ("2026-08-24", "before", "hall_b", "overview"),
    "PHOTO-0006": ("2026-08-24", "before", "balcony", "east"),
    "PHOTO-0007": ("2026-08-24", "before", "balcony", "west"),
    "PHOTO-0008": ("2026-08-27", "progress", "bath", "toilet-removal"),
}


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


def validate_local_markdown_links(errors: list[str], relative_paths: tuple[str, ...]) -> None:
    for relative_path in relative_paths:
        document = ROOT / relative_path
        if not document.is_file():
            continue
        content = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
            clean_target = unquote(target.split("#", 1)[0]).strip()
            if not clean_target or re.match(r"^[a-z]+://", clean_target):
                continue
            resolved = (document.parent / clean_target).resolve()
            if not resolved.exists():
                errors.append(f"{relative_path} 包含失效本地链接：{target}")


def house_room_ids() -> set[str]:
    content = (ROOT / "house.yaml").read_text(encoding="utf-8")
    rooms_block = content.split("\nrooms:\n", 1)[1].split("\ndoors:\n", 1)[0]
    return set(re.findall(r"\bid:\s*([a-z][a-z0-9_]*)", rooms_block))


def validate_photos(errors: list[str]) -> None:
    catalog = ROOT / "data/photos.csv"
    gallery = ROOT / "media/photos/README.md"
    if not catalog.is_file():
        return
    try:
        rows = photo.read_catalog(catalog)
        photo.validate_catalog(rows)
    except (OSError, photo.PhotoError) as exc:
        errors.append(f"照片目录无效：{exc}")
        return

    known_rooms = house_room_ids()
    for row in rows:
        if row["room"] not in known_rooms:
            errors.append(f"照片 {row['id']} 引用了 house.yaml 中不存在的房间 {row['room']}")

    indexed = {row["id"]: row for row in rows}
    for photo_id, expected in BASELINE_PHOTOS.items():
        row = indexed.get(photo_id)
        actual = None if row is None else tuple(row[key] for key in ("date", "stage", "room", "view"))
        if actual != expected:
            errors.append(f"当前照片基线缺失或被改写：{photo_id} 应为 {expected}")

    catalog_files = {row["file"] for row in rows}
    disk_files = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "media/photos").rglob("*.jpg")
    }
    for missing in sorted(catalog_files - disk_files):
        errors.append(f"照片目录登记文件不存在：{missing}")
    for orphan in sorted(disk_files - catalog_files):
        errors.append(f"发现未登记的公开照片：{orphan}")
    for relative_path in sorted(catalog_files & disk_files):
        try:
            photo.validate_public_jpeg(ROOT / relative_path)
        except photo.PhotoError as exc:
            errors.append(str(exc))

    expected_gallery = photo.gallery_markdown(rows)
    if not gallery.is_file() or gallery.read_text(encoding="utf-8") != expected_gallery:
        errors.append("media/photos/README.md 已过期，请运行 make gallery")

    try:
        tracked = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
        ).stdout.decode("utf-8").split("\0")
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as exc:
        errors.append(f"无法检查Git照片跟踪范围：{exc}")
        return
    forbidden = [
        path for path in tracked
        if path and (path.startswith(".local/") or Path(path).suffix.lower() == ".heic")
    ]
    if forbidden:
        errors.append(f"Git不应跟踪HEIC或.local原件：{', '.join(sorted(forbidden))}")


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
    validate_local_markdown_links(errors, ("README.md", "media/photos/README.md"))
    validate_photos(errors)
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
