from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

from scripts import check_project


class LedgerValidationTest(unittest.TestCase):
    def write_ledger(self, rows: list[dict[str, str]]) -> Path:
        temporary = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False
        )
        with temporary as handle:
            writer = csv.DictWriter(handle, fieldnames=check_project.LEDGER_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        self.addCleanup(Path(temporary.name).unlink, missing_ok=True)
        return Path(temporary.name)

    def valid_row(self) -> dict[str, str]:
        return {
            "id": "EXP-0001",
            "date": "2026-10-01",
            "flow": "expense",
            "category": "material",
            "room": "kitchen",
            "item": "排水配件",
            "counterparty": "建材商",
            "amount_cny": "89.90",
            "payment_status": "paid",
            "project_status": "completed",
            "note": "",
        }

    def test_valid_row_and_undated_historical_row_pass(self) -> None:
        first = self.valid_row()
        second = self.valid_row() | {"id": "INC-0001", "date": "", "flow": "income"}
        errors: list[str] = []
        rows = check_project.read_ledger(errors, self.write_ledger([first, second]))
        self.assertEqual(len(rows), 2)
        self.assertEqual(errors, [])

    def test_bad_direct_edit_reports_exact_csv_line_and_fixes(self) -> None:
        bad = self.valid_row() | {
            "id": "INC-1",
            "date": "2026-02-30",
            "flow": "expense",
            "item": "",
            "amount_cny": "-12",
        }
        errors: list[str] = []
        check_project.read_ledger(errors, self.write_ledger([bad]))
        self.assertTrue(errors)
        self.assertTrue(all(error.startswith("data/ledger.csv 第 2 行：") for error in errors))
        self.assertTrue(any("EXP-四位数字" in error for error in errors))
        self.assertTrue(any("YYYY-MM-DD" in error for error in errors))
        self.assertTrue(any("item 不能为空" in error for error in errors))
        self.assertTrue(any("大于 0" in error for error in errors))

    def test_id_prefix_must_match_flow(self) -> None:
        bad = self.valid_row() | {"id": "INC-0001", "flow": "expense"}
        errors: list[str] = []
        check_project.read_ledger(errors, self.write_ledger([bad]))
        self.assertTrue(any("id 与 flow 不匹配" in error for error in errors))

    def test_ledger_error_becomes_github_file_annotation(self) -> None:
        annotation = check_project.github_annotation(
            "data/ledger.csv 第 9 行：amount_cny 必须是大于 0 的有限数字"
        )
        self.assertEqual(
            annotation,
            "::error file=data/ledger.csv,line=9::amount_cny 必须是大于 0 的有限数字",
        )

    def test_short_row_reports_error_instead_of_crashing(self) -> None:
        temporary = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        temporary.close()
        path = Path(temporary.name)
        self.addCleanup(path.unlink, missing_ok=True)
        path.write_text(
            ",".join(check_project.LEDGER_COLUMNS) + "\nEXP-0001,2026-10-01,expense\n",
            encoding="utf-8",
        )
        errors: list[str] = []
        check_project.read_ledger(errors, path)
        self.assertTrue(any("列数少于表头" in error for error in errors))

    def test_unquoted_extra_comma_reports_error(self) -> None:
        path = self.write_ledger([self.valid_row()])
        with path.open("a", encoding="utf-8") as handle:
            handle.write(
                "EXP-0002,2026-10-02,expense,material,kitchen,排水,配件,建材商,12,paid,completed,\n"
            )
        errors: list[str] = []
        check_project.read_ledger(errors, path)
        self.assertTrue(any("列数多于表头" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
