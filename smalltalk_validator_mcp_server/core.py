"""
Core validation functions for Smalltalk and Tonel code.
"""

import os
from typing import Any

from tonel_smalltalk_parser import SmalltalkParser, TonelFullParser, TonelParser


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

        if without_method_body:
            parser = TonelParser()
        else:
            parser = TonelFullParser()

        is_valid, error_info = parser.validate_from_file(file_path)

        result = {
            "valid": is_valid,
            "file_path": file_path,
            "parser_type": "tonel_only" if without_method_body else "full",
        }

        if error_info:
            result["error"] = error_info

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

        if without_method_body:
            parser = TonelParser()
        else:
            parser = TonelFullParser()

        is_valid, error_info = parser.validate(file_content)

        result = {
            "valid": is_valid,
            "content_length": len(file_content),
            "parser_type": "tonel_only" if without_method_body else "full",
        }

        if error_info:
            result["error"] = error_info

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
        parser = SmalltalkParser()
        is_valid, error_info = parser.validate(method_body_content)

        result = {
            "valid": is_valid,
            "content_length": len(method_body_content),
            "parser_type": "smalltalk_method",
        }

        if error_info:
            result["error"] = error_info

        return result

    except Exception as e:
        return {
            "valid": False,
            "error": f"Method validation failed: {str(e)}",
            "content_length": len(method_body_content),
            "exception": type(e).__name__,
        }
