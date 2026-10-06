from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_actions.rb"


class GenerateActionsTests(unittest.TestCase):
    def generate(self, output: Path) -> str:
        env = os.environ.copy()
        env["ACTIONS_OUTPUT"] = str(output)
        subprocess.run(["ruby", str(SCRIPT)], cwd=ROOT, env=env, check=True)
        return output.read_text(encoding="utf-8")

    def test_output_is_deterministic_and_committed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = self.generate(Path(temp_dir) / "first.md")
            second = self.generate(Path(temp_dir) / "second.md")
        self.assertEqual(first, second)
        self.assertEqual(first, (ROOT / "NEXT_ACTIONS.md").read_text(encoding="utf-8"))

    def test_key_owner_decisions_are_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            content = self.generate(Path(temp_dir) / "actions.md")
        for phrase in (
            "厨房下水",
            "电工",
            "洗碗机",
            "改色体系",
            "30×30",
            "阳光板",
            "卧室门",
            "15.14元",
        ):
            self.assertIn(phrase, content)


if __name__ == "__main__":
    unittest.main()
