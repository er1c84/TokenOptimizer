"""Check TokenOptimizer through Codex without starting a model turn.

Run from a checkout after configuring the MCP server:
    python tests/check_codex.py
"""

import asyncio
import json
from pathlib import Path
import shutil
import tempfile


async def check():
    codex = shutil.which("codex")
    if codex is None:
        raise RuntimeError("Codex CLI is not on PATH")
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryFile(mode="w+b") as log:
        process = await asyncio.create_subprocess_exec(
            codex, "app-server", "--stdio", cwd=root,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=log,
        )
        request_id = 0

        async def request(method, params):
            nonlocal request_id
            request_id += 1
            identifier = request_id
            message = {"id": identifier, "method": method, "params": params}
            process.stdin.write((json.dumps(message) + "\n").encode())
            await process.stdin.drain()
            async with asyncio.timeout(45):
                while line := await process.stdout.readline():
                    response = json.loads(line)
                    if "method" in response and "id" in response:
                        raise RuntimeError(f"Codex requested unsupported interaction: {response['method']}")
                    if response.get("id") == identifier:
                        if "error" in response:
                            raise RuntimeError(f"{method}: {response['error']}")
                        return response["result"]
            raise RuntimeError(f"Codex exited before replying to {method}")

        try:
            await request("initialize", {"clientInfo": {
                "name": "tokenoptimizer_connection_check", "version": "0.1.0",
            }})
            process.stdin.write(b'{"method":"initialized"}\n')
            await process.stdin.drain()
            started = await request("thread/start", {"cwd": str(root), "ephemeral": True})
            thread_id = started["thread"]["id"]
            listing = await request("mcpServerStatus/list", {
                "threadId": thread_id, "serverName": "tokenoptimizer",
                "detail": "toolsAndAuthOnly",
            })
            server = next((item for item in listing["data"] if item["name"] == "tokenoptimizer"), None)
            if server is None:
                raise RuntimeError("TokenOptimizer is not configured for this checkout")
            if server.get("toolsError"):
                raise RuntimeError(server["toolsError"])
            if not any(tool.get("name") == "get_project_context" for tool in server["tools"].values()):
                raise RuntimeError("Codex did not discover get_project_context")
            result = await request("mcpServer/tool/call", {
                "threadId": thread_id, "server": "tokenoptimizer",
                "tool": "get_project_context",
                "arguments": {"task": "gitignore scanner", "budget": 1000},
            })
            if result.get("isError"):
                raise RuntimeError(f"Context request failed: {result['content']}")
            data = result.get("structuredContent")
            if not data or "src/core/scanner/gitignore.py" not in data.get("context", ""):
                raise RuntimeError("The server did not return context from this checkout")
            if not 0 < data["estimated_tokens"] <= 1000:
                raise RuntimeError("The returned context exceeded the estimated token budget")
            print(
                "Codex MCP check passed: get_project_context returned "
                f"{data['included_file_count']} files, {data['estimated_tokens']} estimated tokens."
            )
        finally:
            process.stdin.close()
            try:
                await asyncio.wait_for(process.wait(), 5)
            except TimeoutError:
                process.kill()
                await process.wait()


if __name__ == "__main__":
    try:
        asyncio.run(check())
    except (OSError, RuntimeError, TimeoutError) as error:
        raise SystemExit(f"Codex MCP check failed: {error}") from None
