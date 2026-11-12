import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from src.config import Settings
from src.core.optimizer import select_context
from src.core.scanner import scan_project


@unittest.skipUnless(shutil.which("git"), "Git is not installed")
class GitIgnoreTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        environment = patch.dict(os.environ, {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(self.root / "missing-global-config"),
        })
        environment.start()
        self.addCleanup(environment.stop)
        self.git("init", "--quiet")

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True, check=True,
        )

    def write(self, name, text="content\n"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_root_nested_rules_and_exceptions(self):
        self.write(".gitignore", "*.log\n/root-only.txt\nartifacts/\ndata/*\n!data/keep.txt\n")
        self.write("src/.gitignore", "*.tmp\n!keep.tmp\n!local.log\n")
        for name in (
            "README.md", "root-only.txt", "src/root-only.txt", "debug.log",
            "src/debug.log", "src/local.log", "src/drop.tmp", "src/keep.tmp",
            "artifacts/result.txt", "data/drop.txt", "data/keep.txt",
        ):
            self.write(name)
        scan = scan_project(self.root, Settings())
        self.assertEqual({file.path for file in scan.files}, {
            "README.md", "src/root-only.txt", "src/local.log", "src/keep.tmp", "data/keep.txt",
        })
        reasons = {item.path: item.reason for item in scan.skipped}
        for name in ("root-only.txt", "debug.log", "src/debug.log", "src/drop.tmp", "artifacts/", "data/drop.txt"):
            self.assertEqual(reasons[name], "ignored by Git")
        self.assertEqual(scan.warnings, ())

    def test_tracked_files_survive_ignored_parent_directory(self):
        self.write("tracked.txt")
        self.write("archive/tracked.txt")
        self.git("add", "--", "tracked.txt", "archive/tracked.txt")
        self.write(".gitignore", "tracked.txt\narchive/\n")
        self.write("archive/untracked.txt")
        index_before = (self.root / ".git/index").read_bytes()
        scan = scan_project(self.root, Settings())
        self.assertEqual({file.path for file in scan.files}, {"tracked.txt", "archive/tracked.txt"})
        self.assertIn("archive/untracked.txt", {item.path for item in scan.skipped})
        self.assertEqual((self.root / ".git/index").read_bytes(), index_before)

    def test_explicit_exclusions_and_defaults_still_apply(self):
        self.write(".gitignore", "*.txt\n!keep.txt\n")
        self.write("keep.txt")
        self.write("node_modules/tracked.js")
        self.git("add", "--", "node_modules/tracked.js")
        scan = scan_project(self.root, Settings(exclude=("keep.txt",)))
        self.assertEqual(scan.files, ())
        reasons = {item.path: item.reason for item in scan.skipped}
        self.assertEqual(reasons["keep.txt"], "user exclusion")
        self.assertEqual(reasons["node_modules/"], "generated or dependency directory")

    def test_subdirectory_scan_uses_parent_rules(self):
        self.write(".gitignore", "src/cache/\n*.log\n")
        self.write("src/cache/result.txt")
        self.write("src/debug.log")
        self.write("src/main.py")
        scan = scan_project(self.root / "src", Settings())
        self.assertEqual([file.path for file in scan.files], ["main.py"])
        self.assertEqual({item.path for item in scan.skipped}, {"cache/", "debug.log"})
        self.assertEqual(scan.warnings, ())

    def test_scan_root_itself_is_ignored(self):
        self.write(".gitignore", "scratch/\n")
        self.write("scratch/notes.txt")
        self.write("scratch/deeper/code.py")
        scan = scan_project(self.root / "scratch", Settings())
        self.assertEqual(scan.files, ())
        self.assertEqual({item.path for item in scan.skipped}, {"notes.txt", "deeper/"})
        self.assertTrue(all(item.reason == "ignored by Git" for item in scan.skipped))

    def test_unicode_and_space_in_ignored_filename(self):
        self.write(".gitignore", "private caf\u00e9.txt\n")
        self.write("private caf\u00e9.txt")
        self.write("public caf\u00e9.txt")
        scan = scan_project(self.root, Settings())
        self.assertEqual([file.path for file in scan.files], ["public caf\u00e9.txt"])
        self.assertIn("private caf\u00e9.txt", {item.path for item in scan.skipped})

    def test_repository_and_configured_excludes(self):
        self.write(".git/info/exclude", "local-only.txt\n")
        excludes = self.write(".extra-ignore", "global-only.txt\n")
        self.git("config", "core.excludesFile", str(excludes))
        self.write("local-only.txt")
        self.write("global-only.txt")
        self.write("keep.txt")
        scan = scan_project(self.root, Settings())
        self.assertEqual([file.path for file in scan.files], ["keep.txt"])

    def test_git_environment_does_not_redirect_scan(self):
        self.write(".gitignore", "ignored.txt\n")
        self.write("ignored.txt")
        self.write("keep.txt")
        with patch.dict(os.environ, {"GIT_DIR": str(self.root / "missing-repository")}):
            scan = scan_project(self.root, Settings())
        self.assertEqual([file.path for file in scan.files], ["keep.txt"])
        self.assertEqual(scan.warnings, ())


class GitFallbackTests(unittest.TestCase):
    def test_missing_or_failed_git_preserves_scan_and_reports_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "hello.txt").write_text("hello", encoding="utf-8")
            for error in (FileNotFoundError(), PermissionError(), subprocess.TimeoutExpired("git", 10)):
                with self.subTest(error=type(error).__name__):
                    with patch("src.core.scanner.gitignore.subprocess.run", side_effect=error):
                        scan = scan_project(root, Settings())
                    result = select_context(scan, 100)
                    self.assertEqual(result.files_included, ("hello.txt",))
                    self.assertEqual(len(result.warnings), 1)
                    self.assertIn("ignore rules were not applied", result.to_dict()["warnings"][0])

    def test_git_error_does_not_apply_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "hello.txt").write_text("hello", encoding="utf-8")
            failure = subprocess.CompletedProcess("git", 128, stdout=b"hello.txt\0", stderr=b"fatal")
            with patch("src.core.scanner.gitignore.subprocess.run", return_value=failure):
                scan = scan_project(root, Settings())
            self.assertEqual([file.path for file in scan.files], ["hello.txt"])
            self.assertEqual(len(scan.warnings), 1)


if __name__ == "__main__":
    unittest.main()
