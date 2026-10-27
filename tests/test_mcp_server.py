"""
Integration tests for the MCP server layer using FastMCP's in-memory client.
"""

import asyncio
from pathlib import Path

from fastmcp import Client

from smalltalk_validator_mcp_server.server import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"

EXPECTED_TOOLS = {
    "validate_tonel_smalltalk_from_file",
    "validate_tonel_smalltalk",
    "validate_smalltalk_method_body",
    "lint_tonel_smalltalk_from_file",
    "lint_tonel_smalltalk",
}


async def _list_tools():
    async with Client(app) as client:
        return await client.list_tools()


async def _call_tool(name, arguments):
    async with Client(app) as client:
        return await client.call_tool(name, arguments)


class TestMCPServer:
    """Test the tools exposed via the MCP protocol."""

    def test_list_tools(self):
        tools = asyncio.run(_list_tools())
        assert {tool.name for tool in tools} == EXPECTED_TOOLS

    def test_tool_annotations(self):
        for tool in asyncio.run(_list_tools()):
            annotations = tool.annotations
            assert annotations.title
            assert annotations.read_only_hint is True
            assert annotations.destructive_hint is False
            assert annotations.idempotent_hint is True
            assert annotations.open_world_hint is False

    def test_call_validate_tonel_smalltalk_from_file(self):
        result = asyncio.run(
            _call_tool(
                "validate_tonel_smalltalk_from_file",
                {"file_path": str(FIXTURES_DIR / "valid_class.st")},
            )
        )
        assert result.data["valid"] is True

    def test_call_validate_tonel_smalltalk_with_options(self):
        content = (FIXTURES_DIR / "valid_class.st").read_text()
        result = asyncio.run(
            _call_tool(
                "validate_tonel_smalltalk",
                {"file_content": content, "options": {"without-method-body": True}},
            )
        )
        assert result.data["valid"] is True
        assert result.data["parser_type"] == "tonel_only"

    def test_call_validate_smalltalk_method_body(self):
        result = asyncio.run(
            _call_tool(
                "validate_smalltalk_method_body",
                {"method_body_content": "^ 1 + 2"},
            )
        )
        assert result.data["valid"] is True

    def test_call_lint_tonel_smalltalk_from_file(self):
        result = asyncio.run(
            _call_tool(
                "lint_tonel_smalltalk_from_file",
                {"file_path": str(FIXTURES_DIR / "valid_class.st")},
            )
        )
        assert result.data["success"] is True
        assert isinstance(result.data["issue_list"], list)

    def test_call_lint_tonel_smalltalk(self):
        content = (FIXTURES_DIR / "valid_class.st").read_text()
        result = asyncio.run(
            _call_tool("lint_tonel_smalltalk", {"file_content": content})
        )
        assert result.data["success"] is True
