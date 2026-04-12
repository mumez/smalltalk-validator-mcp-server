"""
Core validation functions for Smalltalk and Tonel code.
"""

import os
from pathlib import Path
from typing import Any

from smalltalk_validator_mcp_server.linter import TonelCSTLinter
from smalltalk_validator_mcp_server.parser import (
    SmalltalkMethodParser,
    TonelTreeSitterParser,
)


def _convert_lint_issues_to_dicts(issues: list) -> list[dict[str, Any]]:
    return [
        {
            "severity": issue.severity,
            "message": issue.message,
            "class_name": issue.class_name,
            "selector": issue.selector,
            "is_class_method": issue.is_class_method,
        }
        for issue in issues
    ]


def validate_tonel_smalltalk_from_file_impl(
    file_path: str, options: dict[str, Any] | None = None
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
    try:
        if not os.path.exists(file_path):
            return {
                "valid": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path,
            }

        options = options or {}
        without_method_body = options.get("without-method-body", False)

        parser = TonelTreeSitterParser(ignore_method_body_errors=without_method_body)
        parse_result = parser.parse_from_file(file_path)

        result: dict[str, Any] = {
            "valid": parse_result["valid"],
            "file_path": file_path,
            "parser_type": "tonel_only" if without_method_body else "full",
        }

        if parse_result["errors"]:
            result["errors"] = parse_result["errors"]

        return result

    except Exception as e:
        return {
            "valid": False,
            "error": f"Validation failed: {str(e)}",
            "file_path": file_path,
            "exception": type(e).__name__,
        }


def validate_tonel_smalltalk_impl(
    file_content: str, options: dict[str, Any] | None = None
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
    try:
        options = options or {}
        without_method_body = options.get("without-method-body", False)

        parser = TonelTreeSitterParser(ignore_method_body_errors=without_method_body)
        parse_result = parser.parse(file_content)

        result: dict[str, Any] = {
            "valid": parse_result["valid"],
            "content_length": len(file_content),
            "parser_type": "tonel_only" if without_method_body else "full",
        }

        if parse_result["errors"]:
            result["errors"] = parse_result["errors"]

        return result

    except Exception as e:
        return {
            "valid": False,
            "error": f"Validation failed: {str(e)}",
            "content_length": len(file_content),
            "exception": type(e).__name__,
        }


def validate_smalltalk_method_body_impl(method_body_content: str) -> dict[str, Any]:
    """
    Validate a Smalltalk method body for syntax correctness.

    Args:
        method_body_content: The Smalltalk method body content as a string

    Returns:
        Dictionary with validation results including success status and error details
    """
    try:
        parser = SmalltalkMethodParser()
        parse_result = parser.parse(method_body_content)

        result: dict[str, Any] = {
            "valid": parse_result["valid"],
            "content_length": len(method_body_content),
            "parser_type": "smalltalk_method",
        }

        if parse_result["errors"]:
            result["errors"] = parse_result["errors"]

        return result

    except Exception as e:
        return {
            "valid": False,
            "error": f"Method validation failed: {str(e)}",
            "content_length": len(method_body_content),
            "exception": type(e).__name__,
        }


def lint_tonel_smalltalk_from_file_impl(file_path: str) -> dict[str, Any]:
    """
    Lint Tonel formatted Smalltalk source code from a file.

    Args:
        file_path: Path to the Tonel file to lint

    Returns:
        Dictionary with lint results including issues found
    """
    try:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path,
            }

        linter = TonelCSTLinter()
        issues = linter.lint_from_file(Path(file_path))

        issue_list = _convert_lint_issues_to_dicts(issues)

        return {
            "success": True,
            "file_path": file_path,
            "issue_list": issue_list,
            "warnings_count": linter.warnings,
            "errors_count": linter.errors,
            "issues_count": len(issue_list),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Linting failed: {str(e)}",
            "file_path": file_path,
            "exception": type(e).__name__,
        }


def lint_tonel_smalltalk_impl(file_content: str) -> dict[str, Any]:
    """
    Lint Tonel formatted Smalltalk source code from content string.

    Args:
        file_content: The Tonel file content as a string

    Returns:
        Dictionary with lint results including issues found
    """
    try:
        linter = TonelCSTLinter()
        issues = linter.lint(file_content)

        issue_list = _convert_lint_issues_to_dicts(issues)

        return {
            "success": True,
            "content_length": len(file_content),
            "issue_list": issue_list,
            "warnings_count": linter.warnings,
            "errors_count": linter.errors,
            "issues_count": len(issue_list),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Linting failed: {str(e)}",
            "content_length": len(file_content),
            "exception": type(e).__name__,
        }
