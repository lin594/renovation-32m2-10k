#!/usr/bin/env python3
"""Safely append one expense or income row and refresh the public status page."""

from __future__ import annotations

import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "ledger.csv"
PREFIX = {"expense": "EXP", "income": "INC"}
DEFAULT_PAYMENT = {"expense": "paid", "income": "received"}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("flow", choices=("expense", "income"))
    result.add_argument("--amount", required=True, help="正数人民币金额，例如 89.90")
    result.add_argument("--item", required=True)
    result.add_argument("--category", required=True)
    result.add_argument("--room", required=True)
    result.add_argument("--date", default=date.today().isoformat())
    result.add_argument("--counterparty", default="")
    result.add_argument("--payment-status")
    result.add_argument("--project-status", default="completed")
    result.add_argument("--note", default="")
    result.add_argument("--dry-run", action="store_true")
    return result


def next_id(rows: list[dict[str, str]], flow: str) -> str:
    prefix = PREFIX[flow]
    numbers = [
        int(row["id"].split("-", 1)[1])
        for row in rows
        if row["id"].startswith(f"{prefix}-") and row["id"].split("-", 1)[1].isdigit()
    ]
    return f"{prefix}-{max(numbers, default=0) + 1:04d}"


def main() -> int:
    args = parser().parse_args()
    try:
        amount = Decimal(args.amount)
    except InvalidOperation:
        print("金额不是有效数字", file=sys.stderr)
        return 2
    if amount <= 0:
        print("金额必须大于0", file=sys.stderr)
        return 2
    try:
        date.fromisoformat(args.date)
    except ValueError:
        print("日期必须使用 YYYY-MM-DD", file=sys.stderr)
        return 2

    with LEDGER.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or ())
        rows = list(reader)

    row = {
        "id": next_id(rows, args.flow),
        "date": args.date,
        "flow": args.flow,
        "category": args.category,
        "room": args.room,
        "item": args.item,
        "counterparty": args.counterparty,
        "amount_cny": format(amount, "f"),
        "payment_status": args.payment_status or DEFAULT_PAYMENT[args.flow],
        "project_status": args.project_status,
        "note": args.note,
    }
    print("将追加：", row)
    if args.dry_run:
        return 0

    rows.append(row)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=LEDGER.parent, delete=False
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(handle.name)
    temporary.replace(LEDGER)

    subprocess.run(["make", "check"], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
