"""
Unit tests for the Smalltalk Validator MCP Server.
"""

import os
import tempfile
from unittest.mock import Mock, patch

from smalltalk_validator_mcp_server.core import (
    validate_smalltalk_method_body_impl as validate_smalltalk_method_body,
)
from smalltalk_validator_mcp_server.core import (
    validate_tonel_smalltalk_from_file_impl as validate_tonel_smalltalk_from_file,
)
from smalltalk_validator_mcp_server.core import (
    validate_tonel_smalltalk_impl as validate_tonel_smalltalk,
)


class TestValidateTonelSmalltalkFromFile:
    """Tests for validate_tonel_smalltalk_from_file function."""

    def test_file_not_found(self):
        """Test validation when file doesn't exist."""
        result = validate_tonel_smalltalk_from_file("/non/existent/file.st")

        assert result["valid"] is False
        assert "File not found" in result["error"]
        assert result["file_path"] == "/non/existent/file.st"

    @patch("smalltalk_validator_mcp_server.core.TonelFullParser")
    def test_successful_validation_full_parser(self, mock_parser_class):
        """Test successful validation with full parser."""
        mock_parser = Mock()
        mock_parser.validate_from_file.return_value = (True, None)
        mock_parser_class.return_value = mock_parser

        with tempfile.NamedTemporaryFile(mode="w", suffix=".st", delete=False) as f:
            f.write("Class { #name : #TestClass }")
            temp_path = f.name

        try:
            result = validate_tonel_smalltalk_from_file(temp_path)

            assert result["valid"] is True
            assert result["file_path"] == temp_path
            assert result["parser_type"] == "full"
            assert "error" not in result
            mock_parser.validate_from_file.assert_called_once_with(temp_path)
        finally:
            os.unlink(temp_path)

    @patch("smalltalk_validator_mcp_server.core.TonelParser")
    def test_successful_validation_tonel_only(self, mock_parser_class):
        """Test successful validation with tonel-only parser."""
        mock_parser = Mock()
        mock_parser.validate_from_file.return_value = (True, None)
        mock_parser_class.return_value = mock_parser

        with tempfile.NamedTemporaryFile(mode="w", suffix=".st", delete=False) as f:
            f.write("Class { #name : #TestClass }")
            temp_path = f.name

        try:
            result = validate_tonel_smalltalk_from_file(
                temp_path, options={"without-method-body": True}
            )

            assert result["valid"] is True
            assert result["parser_type"] == "tonel_only"
            mock_parser.validate_from_file.assert_called_once_with(temp_path)
        finally:
            os.unlink(temp_path)

    @patch("smalltalk_validator_mcp_server.core.TonelFullParser")
    def test_validation_with_errors(self, mock_parser_class):
        """Test validation that returns errors."""
        mock_parser = Mock()
        error_info = {
            "reason": "Syntax error",
            "line": 1,
            "error_text": "invalid syntax",
        }
        mock_parser.validate_from_file.return_value = (False, error_info)
        mock_parser_class.return_value = mock_parser

        with tempfile.NamedTemporaryFile(mode="w", suffix=".st", delete=False) as f:
            f.write("Invalid Tonel Content")
            temp_path = f.name

        try:
            result = validate_tonel_smalltalk_from_file(temp_path)

            assert result["valid"] is False
            assert result["error"] == error_info
            assert result["parser_type"] == "full"
        finally:
            os.unlink(temp_path)

    @patch("smalltalk_validator_mcp_server.core.TonelFullParser")
    def test_parser_exception(self, mock_parser_class):
        """Test handling of parser exceptions."""
        mock_parser = Mock()
        mock_parser.validate_from_file.side_effect = ValueError("Parser error")
        mock_parser_class.return_value = mock_parser

        with tempfile.NamedTemporaryFile(mode="w", suffix=".st", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            result = validate_tonel_smalltalk_from_file(temp_path)

            assert result["valid"] is False
            assert "Validation failed: Parser error" in result["error"]
            assert result["exception"] == "ValueError"
        finally:
            os.unlink(temp_path)


class TestValidateTonelSmalltalk:
    """Tests for validate_tonel_smalltalk function."""

    @patch("smalltalk_validator_mcp_server.core.TonelFullParser")
    def test_successful_validation(self, mock_parser_class):
        """Test successful content validation."""
        mock_parser = Mock()
        mock_parser.validate.return_value = (True, None)
        mock_parser_class.return_value = mock_parser

        content = "Class { #name : #TestClass }"
        result = validate_tonel_smalltalk(content)

        assert result["valid"] is True
        assert result["content_length"] == len(content)
        assert result["parser_type"] == "full"
        assert "error" not in result
        mock_parser.validate.assert_called_once_with(content)

    @patch("smalltalk_validator_mcp_server.core.TonelParser")
    def test_tonel_only_validation(self, mock_parser_class):
        """Test validation with tonel-only option."""
        mock_parser = Mock()
        mock_parser.validate.return_value = (True, None)
        mock_parser_class.return_value = mock_parser

        content = "Class { #name : #TestClass }"
        result = validate_tonel_smalltalk(
            content, options={"without-method-body": True}
        )

        assert result["valid"] is True
        assert result["parser_type"] == "tonel_only"
        mock_parser.validate.assert_called_once_with(content)

    @patch("smalltalk_validator_mcp_server.core.TonelFullParser")
    def test_validation_with_errors(self, mock_parser_class):
        """Test content validation with errors."""
        mock_parser = Mock()
        error_info = {
            "reason": "Invalid class definition",
            "line": 2,
            "error_text": "missing bracket",
        }
        mock_parser.validate.return_value = (False, error_info)
        mock_parser_class.return_value = mock_parser

        content = "Invalid content"
        result = validate_tonel_smalltalk(content)

        assert result["valid"] is False
        assert result["error"] == error_info
        assert result["content_length"] == len(content)

    @patch("smalltalk_validator_mcp_server.core.TonelFullParser")
    def test_content_validation_exception(self, mock_parser_class):
        """Test handling of content validation exceptions."""
        mock_parser = Mock()
        mock_parser.validate.side_effect = RuntimeError("Content error")
        mock_parser_class.return_value = mock_parser

        content = "Test content"
        result = validate_tonel_smalltalk(content)

        assert result["valid"] is False
        assert "Validation failed: Content error" in result["error"]
        assert result["exception"] == "RuntimeError"
        assert result["content_length"] == len(content)


class TestValidateSmalltalkMethodBody:
    """Tests for validate_smalltalk_method_body function."""

    @patch("smalltalk_validator_mcp_server.core.SmalltalkParser")
    def test_successful_method_validation(self, mock_parser_class):
        """Test successful method body validation."""
        mock_parser = Mock()
        mock_parser.validate.return_value = (True, None)
        mock_parser_class.return_value = mock_parser

        method_body = "^ self name"
        result = validate_smalltalk_method_body(method_body)

        assert result["valid"] is True
        assert result["content_length"] == len(method_body)
        assert result["parser_type"] == "smalltalk_method"
        assert "error" not in result
        mock_parser.validate.assert_called_once_with(method_body)

    @patch("smalltalk_validator_mcp_server.core.SmalltalkParser")
    def test_method_validation_with_errors(self, mock_parser_class):
        """Test method validation with syntax errors."""
        mock_parser = Mock()
        error_info = {
            "reason": "Syntax error in method",
            "line": 1,
            "error_text": "unexpected token",
        }
        mock_parser.validate.return_value = (False, error_info)
        mock_parser_class.return_value = mock_parser

        method_body = "invalid method syntax ^^"
        result = validate_smalltalk_method_body(method_body)

        assert result["valid"] is False
        assert result["error"] == error_info
        assert result["parser_type"] == "smalltalk_method"

    @patch("smalltalk_validator_mcp_server.core.SmalltalkParser")
    def test_method_validation_exception(self, mock_parser_class):
        """Test handling of method validation exceptions."""
        mock_parser = Mock()
        mock_parser.validate.side_effect = SyntaxError("Method syntax error")
        mock_parser_class.return_value = mock_parser

        method_body = "test method"
        result = validate_smalltalk_method_body(method_body)

        assert result["valid"] is False
        assert "Method validation failed: Method syntax error" in result["error"]
        assert result["exception"] == "SyntaxError"
        assert result["content_length"] == len(method_body)
