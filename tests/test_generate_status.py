from __future__ import annotations

import csv
from collections import defaultdict
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GenerateStatusTest(unittest.TestCase):
    def test_available_balance_accounts_for_future_reserves(self):
        data = json.loads(subprocess.check_output(
            ["ruby", "-rjson", "-ryaml", "-e",
             'puts JSON.generate(ARGV.map { |path| YAML.load_file(path) })',
             str(ROOT / "data/budget.yaml"), str(ROOT / "data/procurement.yaml")],
            text=True,
        ))
        budget, procurement = data
        gate = budget["current_gate"]
        with (ROOT / "data/ledger.csv").open(encoding="utf-8-sig", newline="") as handle:
            expenses = sum((Decimal(row["amount_cny"]) for row in csv.DictReader(handle)
                            if row["flow"] == "expense"), Decimal(0))
        reserves = sum((Decimal(str(gate[key])) for key in (
            "october_trip_reserve_cny", "paint_and_tools_plan_cny", "contingency_cny"
        )), Decimal(0))
        reserves += sum((Decimal(str(item.get("unpaid_balance_cny", 0)))
                         for item in procurement["items"]), Decimal(0))
        reserves += sum((Decimal(str(item["reserve_cny"]))
                         for item in gate["future_purchase_reserves"]), Decimal(0))
        expected = Decimal(str(budget["overall_budget_cny"])) - expenses - reserves
        status = (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")
        actual = re.search(r"可用上限（保守，不用收入冲抵）\*\* \| \*\*¥(-?[\d.]+)", status)
        self.assertIsNotNone(actual)
        self.assertEqual(Decimal(actual.group(1)), expected)
        self.assertIn("预留只是预算占位", status)

    def test_expense_categories_use_deterministic_tie_breaker(self):
        totals: dict[str, float] = defaultdict(float)
        with (ROOT / "data/ledger.csv").open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["flow"] == "expense":
                    totals[row["category"]] += float(row["amount_cny"])

        expected = [name for name, _ in sorted(totals.items(), key=lambda item: (-item[1], item[0]))]
        status = (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")
        table = status.split("### 支出分类", 1)[1].split("### 最近五笔", 1)[0]
        actual = re.findall(r"^\| `([^`]+)` \| ¥", table, flags=re.MULTILINE)

        self.assertEqual(actual, expected)
        self.assertEqual(totals["plumbing"], totals["windows"])
        self.assertLess(actual.index("plumbing"), actual.index("windows"))


if __name__ == "__main__":
    unittest.main()
