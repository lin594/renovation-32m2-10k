from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GenerateStatusTest(unittest.TestCase):
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
