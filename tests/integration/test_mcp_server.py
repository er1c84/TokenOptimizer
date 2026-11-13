import asyncio
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from src.integrations.mcp.server import create_server

MCP_AVAILABLE = importlib.util.find_spec("mcp") is not None


@unittest.skipUnless(MCP_AVAILABLE, "Install the optional [mcp] extra to run MCP tests")
class McpServerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "README.md").write_text("General project notes\n", encoding="utf-8")
        (self.root / "login.py").write_text("def login(): return True\n", encoding="utf-8")

    async def test_discovery_declares_read_only_tool_and_fixed_project(self):
        from mcp import Client
        async with Client(create_server(self.root)) as client:
            listing = await client.list_tools()
            self.assertEqual([tool.name for tool in listing.tools], ["get_project_context"])
            tool = listing.tools[0]
            self.assertTrue(tool.annotations.read_only_hint)
            self.assertFalse(tool.annotations.open_world_hint)
            self.assertEqual(set(tool.input_schema["properties"]), {"task", "budget"})
            self.assertIsNotNone(tool.output_schema)

    async def test_tool_returns_compact_budgeted_context(self):
        from mcp import Client
        async with Client(create_server(self.root)) as client:
            result = await client.call_tool("get_project_context", {"task": "login", "budget": 15})
            self.assertFalse(result.is_error)
            data = result.structured_content
            self.assertIn("def login()", data["context"])
            self.assertNotIn("General project notes", data["context"])
            self.assertLessEqual(data["estimated_tokens"], 15)
            self.assertEqual(data["token_budget"], 15)
            self.assertEqual(data["included_file_count"], 1)
            self.assertEqual(data["omitted_file_count"], 1)
            self.assertNotIn("task_selection", data)

    async def test_default_budget_and_fallback_warning(self):
        from mcp import Client
        async with Client(create_server(self.root)) as client:
            result = await client.call_tool("get_project_context", {"task": "unmatchedkeyword"})
            self.assertFalse(result.is_error)
            self.assertEqual(result.structured_content["token_budget"], 4000)
            self.assertIn("No scanned files match", " ".join(result.structured_content["warnings"]))

    async def test_invalid_arguments_return_tool_errors(self):
        from mcp import Client
        async with Client(create_server(self.root)) as client:
            for arguments in ({"task": "login", "budget": 0}, {"task": "   "}, {"task": "login", "budget": "invalid"}):
                with self.subTest(arguments=arguments):
                    result = await client.call_tool("get_project_context", arguments)
                    self.assertTrue(result.is_error)

    @unittest.skipUnless(shutil.which("git"), "Git is not installed")
    async def test_ignores_apply_and_requests_do_not_write_project_files(self):
        from mcp import Client
        subprocess.run(["git", "init", "--quiet", str(self.root)], capture_output=True, check=True)
        (self.root / ".gitignore").write_text("ignored_login.py\n", encoding="utf-8")
        (self.root / "ignored_login.py").write_text("PRIVATE_LOGIN_MARKER\n", encoding="utf-8")
        before = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        async with Client(create_server(self.root)) as client:
            result = await client.call_tool("get_project_context", {"task": "login"})
            self.assertFalse(result.is_error)
            self.assertNotIn("PRIVATE_LOGIN_MARKER", result.structured_content["context"])
            self.assertGreater(result.structured_content["skipped_file_count"], 0)
        self.assertEqual(before, {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()})

    def test_project_must_be_an_existing_directory(self):
        with self.assertRaises(FileNotFoundError):
            create_server(self.root / "missing")
        with self.assertRaises(NotADirectoryError):
            create_server(self.root / "README.md")

    async def test_installed_server_over_stdio_including_legacy_client(self):
        from mcp import Client, StdioServerParameters
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "tokenoptimizer.integrations.mcp.server", "--project", str(self.root)],
            cwd=self.root,
        )
        for mode in ("auto", "legacy"):
            with self.subTest(mode=mode):
                async with asyncio.timeout(20):
                    async with Client(parameters, mode=mode) as client:
                        listing = await client.list_tools()
                        self.assertEqual(listing.tools[0].name, "get_project_context")
                        result = await client.call_tool("get_project_context", {"task": "login", "budget": 15})
                        self.assertFalse(result.is_error)
                        self.assertIn("def login()", result.structured_content["context"])
                        self.assertLessEqual(result.structured_content["estimated_tokens"], 15)


if __name__ == "__main__":
    unittest.main()
