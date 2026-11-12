import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

LAUNCHER = Path(__file__).resolve().parents[2] / "tokenoptimizer.py"


class CliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "README.md").write_text("Small project\n", encoding="utf-8")
        (self.root / "notes.txt").write_text("large notes\n" * 100, encoding="utf-8")

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(LAUNCHER), *args], cwd=self.root,
            capture_output=True, encoding="utf-8", check=False,
        )

    def test_json_workflow_is_read_only_and_reports_omissions(self):
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        run = self.run_cli("context", ".", "--budget", "30", "--format", "json")
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result["files_included"], ["README.md"])
        self.assertEqual(result["files_omitted"][0]["path"], "notes.txt")
        self.assertLessEqual(result["estimated_tokens_after"], 30)
        self.assertGreater(result["estimated_savings_percent"], 0)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})

    def test_raw_bypasses_budget_and_respects_exclusions(self):
        run = self.run_cli("context", ".", "--raw", "--budget", "1", "--exclude", "notes.txt", "--format", "json")
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result["files_included"], ["README.md"])
        self.assertIsNone(result["token_budget"])
        self.assertEqual(result["estimated_savings_percent"], 0)
        self.assertEqual(result["files_skipped"][0]["reason"], "user exclusion")

    def test_text_sends_only_context_to_stdout(self):
        run = self.run_cli("context", ".", "--budget", "30")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("Small project", run.stdout)
        self.assertNotIn("estimated tokens:", run.stdout)
        self.assertIn("estimated tokens:", run.stderr)

    def test_invalid_inputs_have_nonzero_exit_without_traceback(self):
        for arguments in (
            ("context", "missing"), ("context", "README.md"),
            ("context", ".", "--budget", "0"), ("context", ".", "--budget", "nope"),
        ):
            with self.subTest(arguments=arguments):
                run = self.run_cli(*arguments)
                self.assertEqual(run.returncode, 2)
                self.assertNotIn("Traceback", run.stderr)


if __name__ == "__main__":
    unittest.main()
