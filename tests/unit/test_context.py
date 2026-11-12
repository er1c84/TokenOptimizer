from pathlib import Path
import tempfile
import unittest

from src.config import Settings
from src.core.context import ProjectFile, ScanResult, render_context
from src.core.optimizer import select_context
from src.core.scanner import scan_project
from src.core.tokenizer import estimate_tokens


class BudgetTests(unittest.TestCase):
    def test_estimator_rounding_and_utf8(self):
        self.assertEqual(estimate_tokens(""), 0)
        self.assertEqual(estimate_tokens("abcde"), 2)
        self.assertEqual(estimate_tokens("\U0001f600"), 1)

    def test_budget_counts_headers_and_separators(self):
        files = (ProjectFile("README.md", "hello"), ProjectFile("src/main.py", "print('ok')\n"))
        scan = ScanResult(files, ())
        full = render_context(files)
        budget = estimate_tokens(full)
        result = select_context(scan, budget)
        self.assertEqual(result.context, full)
        self.assertEqual(result.estimated_tokens_after, budget)
        self.assertEqual(len(select_context(scan, budget - 1).files_included), 1)

    def test_large_file_omitted_but_later_small_file_fits(self):
        scan = ScanResult((ProjectFile("README.md", "x" * 1000), ProjectFile("src/a.py", "ok\n")), ())
        result = select_context(scan, 20)
        self.assertEqual(result.files_included, ("src/a.py",))
        self.assertEqual(result.files_omitted[0].path, "README.md")
        self.assertIn("ok\n", result.context)
        self.assertLessEqual(result.estimated_tokens_after, 20)

    def test_raw_preserves_whitespace_and_has_zero_savings(self):
        text = "  x = 1\r\n\r\n  # keep this comment\n"
        scan = ScanResult((ProjectFile("a.py", text),), ())
        result = select_context(scan, None)
        self.assertTrue(result.context.endswith(text))
        self.assertEqual(result.estimated_savings_percent, 0)
        self.assertIsNone(result.token_budget)

    def test_tiny_budget_and_empty_project(self):
        scan = ScanResult((ProjectFile("a.txt", "hello"),), ())
        result = select_context(scan, 1)
        self.assertEqual(result.context, "")
        self.assertEqual(result.estimated_savings_percent, 100)
        self.assertEqual(select_context(ScanResult((), ()), 1).estimated_savings_percent, 0)

    def test_selection_is_deterministic(self):
        files = (ProjectFile("z.txt", "z"), ProjectFile("src/a.py", "a"), ProjectFile("README.md", "r"))
        self.assertEqual(
            select_context(ScanResult(files, ()), 40),
            select_context(ScanResult(tuple(reversed(files)), ()), 40),
        )

    def test_invalid_budget_rejected(self):
        with self.assertRaises(ValueError):
            select_context(ScanResult((), ()), 0)


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_exclusions_binary_and_file_limits(self):
        self.write("src/hello.py", b"print('ok')\n")
        self.write(".env", b"SECRET=not-for-context")
        self.write(".git/config", b"git metadata")
        self.write("node_modules/vendor.js", b"generated")
        self.write("private/notes.txt", b"private")
        self.write("image.bin", b"\x00\x01")
        self.write("legacy.txt", b"\xff")
        self.write("large.txt", b"x" * 101)
        self.write("credentials.pem", b"key material")
        scan = scan_project(self.root, Settings(max_file_bytes=100, exclude=("private",)))
        self.assertEqual([file.path for file in scan.files], ["src/hello.py"])
        reasons = {item.path: item.reason for item in scan.skipped}
        self.assertEqual(reasons["private/"], "user exclusion")
        self.assertEqual(reasons[".env"], "hidden path")
        self.assertEqual(reasons["large.txt"], "file size limit exceeded")
        self.assertEqual(reasons["legacy.txt"], "not UTF-8 text")

    def test_globs_and_total_read_limit_do_not_return_partial_files(self):
        self.write("a.txt", b"a" * 10)
        self.write("b.txt", b"b" * 10)
        self.write("src/debug.log", b"log")
        scan = scan_project(self.root, Settings(max_scan_bytes=15, exclude=("*.log",)))
        self.assertEqual([file.path for file in scan.files], ["a.txt"])
        self.assertIn("scan read limit reached", [item.reason for item in scan.skipped])
        self.assertIn("user exclusion", [item.reason for item in scan.skipped])

    def test_symlink_is_not_followed(self):
        target = self.write("a.txt", b"actual file")
        try:
            (self.root / "link.txt").symlink_to(target)
            (self.root / "loop").symlink_to(self.root, target_is_directory=True)
        except OSError:
            self.skipTest("Creating symlinks is unavailable on this system")
        scan = scan_project(self.root, Settings())
        self.assertEqual([file.path for file in scan.files], ["a.txt"])
        self.assertEqual(len(scan.skipped), 2)

    def test_root_must_be_directory(self):
        file = self.write("a.txt", b"x")
        with self.assertRaises(NotADirectoryError):
            scan_project(file, Settings())


if __name__ == "__main__":
    unittest.main()
