from pathlib import Path
import tempfile
import unittest

from src.integrations.mcp.context_tool import build_context


class ContextToolTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "README.md").write_text("General notes\n", encoding="utf-8")
        (self.root / "login.py").write_text("def login(): return True\n", encoding="utf-8")

    def test_passes_task_and_budget_and_keeps_files_unchanged(self):
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        result = build_context(str(self.root), "login", 15)
        self.assertEqual(result.files_included, ("login.py",))
        self.assertEqual(result.task_selection.keywords, ("login",))
        self.assertLessEqual(result.estimated_tokens_after, 15)
        self.assertEqual(result.token_budget, 15)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})

    def test_default_budget_accepts_path_object(self):
        result = build_context(self.root, "login")
        self.assertEqual(result.token_budget, 4000)

    def test_invalid_folder_and_budget_are_rejected(self):
        with self.assertRaises(FileNotFoundError):
            build_context(self.root / "missing", "login")
        with self.assertRaises(ValueError):
            build_context(self.root, "login", 0)


if __name__ == "__main__":
    unittest.main()
