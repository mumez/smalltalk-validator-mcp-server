"""
MCP Server for validating Tonel formatted Smalltalk source code.
"""

from typing import Any

from fastmcp import Context, FastMCP

from .core import (
    lint_tonel_smalltalk_from_file_impl,
    lint_tonel_smalltalk_impl,
    validate_smalltalk_method_body_impl,
    validate_tonel_smalltalk_from_file_impl,
    validate_tonel_smalltalk_impl,
)

# FastMCP app setup
app = FastMCP("smalltalk-validator-mcp-server")


@app.tool("validate_tonel_smalltalk_from_file")
def validate_tonel_smalltalk_from_file(
    _: Context, file_path: str, options: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Validate Tonel formatted Smalltalk source code from a file.

    Args:
        file_path: Path to the Tonel file to validate
        options: Optional validation options
            - without-method-body: If true, only validates tonel structure

    Returns:
        Dictionary with validation results including success status and error details
    """
    return validate_tonel_smalltalk_from_file_impl(file_path, options)


@app.tool("validate_tonel_smalltalk")
def validate_tonel_smalltalk(
    _: Context, file_content: str, options: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Validate Tonel formatted Smalltalk source code from content string.

    Args:
        file_content: The Tonel file content as a string
        options: Optional validation options
            - without-method-body: If true, only validates tonel structure

    Returns:
        Dictionary with validation results including success status and error details
    """
    return validate_tonel_smalltalk_impl(file_content, options)


@app.tool("validate_smalltalk_method_body")
def validate_smalltalk_method_body(
    _: Context, method_body_content: str
) -> dict[str, Any]:
    """
    Validate a Smalltalk method body for syntax correctness.

    Args:
        method_body_content: The Smalltalk method body content as a string

    Returns:
        Dictionary with validation results including success status and error details
    """
    return validate_smalltalk_method_body_impl(method_body_content)


@app.tool("lint_tonel_smalltalk_from_file")
def lint_tonel_smalltalk_from_file(_: Context, file_path: str) -> dict[str, Any]:
    """
    Lint Tonel formatted Smalltalk source code from a file.

    Args:
        file_path: Path to the Tonel file to lint

    Returns:
        Dictionary with lint results including issues found
    """
    return lint_tonel_smalltalk_from_file_impl(file_path)


@app.tool("lint_tonel_smalltalk")
def lint_tonel_smalltalk(_: Context, file_content: str) -> dict[str, Any]:
    """
    Lint Tonel formatted Smalltalk source code from content string.

    Args:
        file_content: The Tonel file content as a string

    Returns:
        Dictionary with lint results including issues found
    """
    return lint_tonel_smalltalk_impl(file_content)


def main():
    """Main entry point for the MCP server."""
    app.run()


if __name__ == "__main__":
    main()
