"""Check a wheel in a fresh environment outside the checkout.

Usage: python tests/check_install.py dist/tokenoptimizer-0.1.0a3-py3-none-any.whl
"""

import argparse
from email.parser import BytesParser
import json
import os
from pathlib import Path
import subprocess
import tempfile
import venv
from zipfile import ZipFile


def run(command, cwd):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    return subprocess.run(
        [str(part) for part in command], cwd=cwd, env=env,
        capture_output=True, encoding="utf-8", check=True,
    ).stdout


def check(wheel):
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata = BytesParser().parsebytes(archive.read(next(name for name in names if name.endswith(".dist-info/METADATA"))))
        assert all('extra == "mcp"' in item for item in metadata.get_all("Requires-Dist", [])), "Unexpected base runtime dependencies"
        assert metadata.get_all("Provides-Extra") == ["mcp"], "Missing optional MCP extra"
        assert any(name.endswith(".dist-info/licenses/LICENSE") for name in names), "Missing license"
        assert "tokenoptimizer/core/scanner/gitignore.py" in names, "Missing scanner module"
        assert "tokenoptimizer/core/context/ranking.py" in names, "Missing ranking module"
        assert "tokenoptimizer/integrations/mcp/server.py" in names, "Missing MCP server"
        assert "tokenoptimizer/integrations/mcp/context_tool.py" in names, "Missing context builder"
        assert not any(name.startswith(("src/", "tests/")) for name in names), "Checkout files included in wheel"

    with tempfile.TemporaryDirectory(prefix="tokenoptimizer-install-") as directory:
        root = Path(directory)
        environment = root / "environment"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = next(path for path in (
            environment / "Scripts/python.exe", environment / "bin/python.exe", environment / "bin/python",
        ) if path.exists())
        command = python.parent / ("tokenoptimizer.exe" if os.name == "nt" else "tokenoptimizer")
        mcp_command = python.parent / ("tokenoptimizer-mcp.exe" if os.name == "nt" else "tokenoptimizer-mcp")
        run([python, "-m", "pip", "install", "--no-index", "--no-deps", wheel], root)
        expected_version = f"tokenoptimizer {metadata['Version']}"
        assert run([command, "--version"], root).strip() == expected_version
        assert run([python, "-I", "-m", "tokenoptimizer", "--version"], root).strip() == expected_version
        assert "context" in run([command, "--help"], root)
        assert "--project" in run([mcp_command, "--help"], root)

        project = root / "project with spaces"
        project.mkdir()
        (project / "README.md").write_text("Example project\n", encoding="utf-8")
        (project / "notes.txt").write_text("Background notes\n" * 100, encoding="utf-8")
        before = {path.name: path.read_bytes() for path in project.iterdir()}
        arguments = ["context", ".", "--budget", "30", "--format", "json"]
        result = json.loads(run([command, *arguments], project))
        assert result["files_included"] == ["README.md"]
        assert result["files_omitted"][0]["path"] == "notes.txt"
        assert result["estimated_tokens_after"] <= 30
        assert result == json.loads(run([python, "-I", "-m", "tokenoptimizer", *arguments], project))
        assert before == {path.name: path.read_bytes() for path in project.iterdir()}
        (project / "login.py").write_text("def login(name): return name.strip()\n", encoding="utf-8")
        before = {path.name: path.read_bytes() for path in project.iterdir()}
        task_arguments = [*arguments, "--task", "fix the login bug"]
        result = json.loads(run([command, *task_arguments], project))
        assert result["files_included"][0] == "login.py"
        assert result["task_selection"]["keywords"] == ["login"]
        assert result["task_selection"]["ranking"][0]["score"] == 5
        assert result == json.loads(run([python, "-I", "-m", "tokenoptimizer", *task_arguments], project))
        assert before == {path.name: path.read_bytes() for path in project.iterdir()}
        run([python, "-m", "pip", "uninstall", "--yes", "TokenOptimizer"], root)
        assert not command.exists(), "Uninstall left the command behind"
        assert not mcp_command.exists(), "Uninstall left the MCP command behind"
    print("Install check passed: clean install, command/module entry points, context scan, and uninstall.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    check(parser.parse_args().wheel.resolve(strict=True))
