import json
from pathlib import Path
import shutil
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
            ("context", ".", "--task", ""), ("context", ".", "--task", "   "),
        ):
            with self.subTest(arguments=arguments):
                run = self.run_cli(*arguments)
                self.assertEqual(run.returncode, 2)
                self.assertNotIn("Traceback", run.stderr)

    def test_non_repository_reports_fallback_in_json_and_text(self):
        (self.root / ".gitignore").write_text("notes.txt\n", encoding="utf-8")
        run = self.run_cli("context", ".", "--raw", "--format", "json")
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result["files_included"], ["README.md", "notes.txt"])
        self.assertEqual(len(result["warnings"]), 1)
        text = self.run_cli("context", ".", "--raw")
        self.assertIn("Warning:", text.stderr)
        self.assertNotIn("Warning:", text.stdout)

    @unittest.skipUnless(shutil.which("git"), "Git is not installed")
    def test_git_ignores_apply_in_raw_and_budget_modes_without_writes(self):
        subprocess.run(["git", "init", "--quiet", str(self.root)], capture_output=True, check=True)
        (self.root / ".gitignore").write_text("notes.txt\n", encoding="utf-8")
        before = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        for mode in ((), ("--raw",)):
            with self.subTest(mode=mode):
                run = self.run_cli("context", ".", "--budget", "30", "--format", "json", *mode)
                self.assertEqual(run.returncode, 0, run.stderr)
                result = json.loads(run.stdout)
                self.assertEqual(result["files_included"], ["README.md"])
                self.assertEqual(result["files_omitted"], [])
                reasons = {item["path"]: item["reason"] for item in result["files_skipped"]}
                self.assertEqual(reasons["notes.txt"], "ignored by Git")
                self.assertEqual(result["warnings"], [])
        after = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(after, before)

    def test_task_prioritizes_matching_source_and_reports_evidence(self):
        (self.root / "src").mkdir()
        (self.root / "src/login.py").write_text("def login(name):\n    return name.strip()\n", encoding="utf-8")
        (self.root / "private_login.py").write_text("login\n", encoding="utf-8")
        run = self.run_cli("context", ".", "--task", "fix the LOGIN bug", "--budget", "20", "--exclude", "private*", "--format", "json")
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result["files_included"], ["src/login.py"])
        self.assertEqual(result["task_selection"]["keywords"], ["login"])
        first = result["task_selection"]["ranking"][0]
        self.assertEqual(first["path"], "src/login.py")
        self.assertEqual(first["path_matches"], ["login"])
        self.assertLessEqual(result["estimated_tokens_after"], 20)
        self.assertNotIn("private_login.py", [rank["path"] for rank in result["task_selection"]["ranking"]])

    def test_task_fallback_warning_stays_out_of_text_context(self):
        run = self.run_cli("context", ".", "--task", "login", "--budget", "30")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("No scanned files match", run.stderr)
        self.assertNotIn("No scanned files match", run.stdout)

    @unittest.skipUnless(shutil.which("git"), "Git is not installed")
    def test_task_does_not_reintroduce_git_ignored_files(self):
        subprocess.run(["git", "init", "--quiet", str(self.root)], capture_output=True, check=True)
        (self.root / ".gitignore").write_text("login.py\n", encoding="utf-8")
        (self.root / "login.py").write_text("login\n", encoding="utf-8")
        run = self.run_cli("context", ".", "--task", "login", "--format", "json")
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertNotIn("login.py", result["files_included"])
        self.assertNotIn("login.py", [rank["path"] for rank in result["task_selection"]["ranking"]])
        self.assertIn({"path": "login.py", "reason": "ignored by Git"}, result["files_skipped"])


if __name__ == "__main__":
    unittest.main()
