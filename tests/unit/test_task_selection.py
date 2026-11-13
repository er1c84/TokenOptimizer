import unittest

from src.core.context import ProjectFile, ScanResult, render_context
from src.core.optimizer import select_context
from src.core.tokenizer import estimate_tokens


class TaskSelectionTests(unittest.TestCase):
    def test_related_code_and_tests_fit_before_unrelated_readme(self):
        login = ProjectFile("src/login.py", "def login(name):\n    return name.strip()\n")
        test = ProjectFile("tests/test_login.py", "assert login(' user ') == 'user'\n")
        files = (ProjectFile("README.md", "General project notes\n"), test, login)
        budget = estimate_tokens(render_context([login, test]))
        result = select_context(ScanResult(files, ()), budget, task="fix the login bug")
        self.assertEqual(result.files_included, (login.path, test.path))
        self.assertEqual(result.context, render_context([login, test]))
        self.assertLessEqual(result.estimated_tokens_after, budget)
        self.assertEqual(result.task_selection.keywords, ("login",))
        first = result.to_dict()["task_selection"]["ranking"][0]
        self.assertEqual(first["path_matches"], ("login",))
        self.assertEqual(first["content_matches"], ("login",))
        self.assertEqual(first["score"], 5)

    def test_path_matches_outweigh_content_only_matches(self):
        files = (ProjectFile("README.md", "login\n"), ProjectFile("src/login.py", "pass\n"))
        result = select_context(ScanResult(files, ()), None, task="login")
        self.assertEqual(result.files_included, ("src/login.py", "README.md"))
        self.assertEqual([rank.score for rank in result.task_selection.ranking], [4, 1])

    def test_repeated_words_do_not_inflate_scores(self):
        files = (ProjectFile("a.txt", "login " * 1000), ProjectFile("b.txt", "login"))
        result = select_context(ScanResult(files, ()), None, task="login login LOGIN")
        self.assertEqual(result.task_selection.keywords, ("login",))
        self.assertEqual([rank.score for rank in result.task_selection.ranking], [1, 1])

    def test_snake_case_camel_case_and_acronyms(self):
        files = (
            ProjectFile("src/userLogin.py", "def user_login(): pass\n"),
            ProjectFile("src/HTTPLogin.py", "HTTPLogin\n"),
            ProjectFile("catalog.py", "catalog\n"),
        )
        result = select_context(ScanResult(files, ()), None, task="LOGIN")
        self.assertEqual(result.files_included, ("src/HTTPLogin.py", "src/userLogin.py", "catalog.py"))
        self.assertEqual([rank.score for rank in result.task_selection.ranking], [5, 5, 0])

    def test_whole_words_do_not_match_substrings(self):
        files = (ProjectFile("catalog.py", "catalog"), ProjectFile("log_parser.py", "log_line"))
        result = select_context(ScanResult(files, ()), None, task="log")
        self.assertEqual(result.files_included[0], "log_parser.py")
        self.assertEqual(result.task_selection.ranking[-1].score, 0)

    def test_unicode_matches_ignore_case(self):
        files = (ProjectFile("notes.txt", "unrelated"), ProjectFile("caf\u00e9.py", "caf\u00e9"))
        result = select_context(ScanResult(files, ()), None, task="CAF\u00c9")
        self.assertEqual(result.files_included[0], "caf\u00e9.py")
        self.assertEqual(result.task_selection.ranking[0].score, 5)

    def test_missing_matches_fall_back_without_losing_scan_warnings(self):
        scan = ScanResult((ProjectFile("src/a.py", "code"), ProjectFile("README.md", "notes")), (), ("scan warning",))
        default = select_context(scan, 100)
        result = select_context(scan, 100, task="login")
        self.assertEqual(result.context, default.context)
        self.assertEqual(result.files_included, default.files_included)
        self.assertEqual(result.warnings[0], "scan warning")
        self.assertIn("No scanned files match", result.warnings[1])
        self.assertEqual(result.task_selection.fallback_reason, result.warnings[1])

    def test_generic_or_punctuation_only_task_falls_back(self):
        scan = ScanResult((ProjectFile("a.py", "fix a bug"),), ())
        for task in ("fix the bug please", "!!!"):
            with self.subTest(task=task):
                result = select_context(scan, 100, task=task)
                self.assertEqual(result.files_included, ("a.py",))
                self.assertEqual(result.task_selection.keywords, ())
                self.assertIn("no searchable keywords", result.warnings[0])

    def test_empty_task_rejected(self):
        for task in ("", " \t\n"):
            with self.subTest(task=task), self.assertRaisesRegex(ValueError, "task must not be empty"):
                select_context(ScanResult((), ()), 100, task=task)

    def test_empty_project_has_fallback_and_zero_estimates(self):
        result = select_context(ScanResult((), ()), 100, task="login")
        self.assertEqual(result.context, "")
        self.assertEqual(result.estimated_tokens_before, 0)
        self.assertEqual(result.estimated_tokens_after, 0)
        self.assertIsNotNone(result.task_selection.fallback_reason)

    def test_large_match_is_omitted_and_later_small_match_stays_intact(self):
        scan = ScanResult((ProjectFile("src/login.py", "login " * 100), ProjectFile("tests/test_login.py", "login\n")), ())
        result = select_context(scan, 20, task="login")
        self.assertEqual(result.files_included, ("tests/test_login.py",))
        self.assertEqual(result.files_omitted[0].path, "src/login.py")
        self.assertTrue(result.context.endswith("login\n"))
        self.assertLessEqual(result.estimated_tokens_after, 20)

    def test_tied_scores_are_deterministic(self):
        files = (ProjectFile("tests/login.py", "login"), ProjectFile("src/login.py", "login"))
        self.assertEqual(
            select_context(ScanResult(files, ()), 100, task="login"),
            select_context(ScanResult(tuple(reversed(files)), ()), 100, task="login"),
        )

    def test_raw_keeps_unmatched_files_and_same_baseline(self):
        scan = ScanResult((ProjectFile("README.md", "notes"), ProjectFile("login.py", "login")), ())
        default = select_context(scan, None)
        result = select_context(scan, None, task="login")
        self.assertEqual(result.files_included, ("login.py", "README.md"))
        self.assertEqual(result.estimated_tokens_before, default.estimated_tokens_before)
        self.assertEqual(result.estimated_tokens_after, result.estimated_tokens_before)
        self.assertEqual(result.estimated_savings_percent, 0)

    def test_without_task_retains_original_order_and_json_fields(self):
        scan = ScanResult((ProjectFile("login.py", "login"), ProjectFile("README.md", "notes")), ())
        result = select_context(scan, 100)
        self.assertEqual(result.files_included, ("README.md", "login.py"))
        self.assertNotIn("task_selection", result.to_dict())
        self.assertEqual(result.warnings, ())


if __name__ == "__main__":
    unittest.main()
