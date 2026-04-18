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

    @patch("smalltalk_validator_mcp_server.core.TonelTreeSitterParser")
    def test_successful_validation_full_parser(self, mock_parser_class):
        """Test successful validation with full parser."""
        mock_parser = Mock()
        mock_parser.parse_from_file.return_value = {"valid": True, "errors": []}
        mock_parser_class.return_value = mock_parser

        with tempfile.NamedTemporaryFile(mode="w", suffix=".st", delete=False) as f:
            f.write("Class { #name : #TestClass }")
            temp_path = f.name

        try:
            result = validate_tonel_smalltalk_from_file(temp_path)

            assert result["valid"] is True
            assert result["file_path"] == temp_path
            assert result["parser_type"] == "full"
            assert "errors" not in result
            mock_parser_class.assert_called_once_with(ignore_method_body_errors=False)
            mock_parser.parse_from_file.assert_called_once_with(temp_path)
        finally:
            os.unlink(temp_path)

    @patch("smalltalk_validator_mcp_server.core.TonelTreeSitterParser")
    def test_successful_validation_tonel_only(self, mock_parser_class):
        """Test successful validation with tonel-only parser."""
        mock_parser = Mock()
        mock_parser.parse_from_file.return_value = {"valid": True, "errors": []}
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
            mock_parser_class.assert_called_once_with(ignore_method_body_errors=True)
            mock_parser.parse_from_file.assert_called_once_with(temp_path)
        finally:
            os.unlink(temp_path)

    @patch("smalltalk_validator_mcp_server.core.TonelTreeSitterParser")
    def test_validation_with_errors(self, mock_parser_class):
        """Test validation that returns errors."""
        mock_parser = Mock()
        error_list = [
            {
                "type": "ERROR",
                "start_point": [0, 0],
                "end_point": [0, 21],
                "text": "Invalid Tonel Content",
                "parent_type": None,
                "context": None,
            }
        ]
        mock_parser.parse_from_file.return_value = {
            "valid": False,
            "errors": error_list,
        }
        mock_parser_class.return_value = mock_parser

        with tempfile.NamedTemporaryFile(mode="w", suffix=".st", delete=False) as f:
            f.write("Invalid Tonel Content")
            temp_path = f.name

        try:
            result = validate_tonel_smalltalk_from_file(temp_path)

            assert result["valid"] is False
            assert result["errors"] == error_list
            assert result["parser_type"] == "full"
        finally:
            os.unlink(temp_path)

    @patch("smalltalk_validator_mcp_server.core.TonelTreeSitterParser")
    def test_parser_exception(self, mock_parser_class):
        """Test handling of parser exceptions."""
        mock_parser = Mock()
        mock_parser.parse_from_file.side_effect = ValueError("Parser error")
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

    @patch("smalltalk_validator_mcp_server.core.TonelTreeSitterParser")
    def test_successful_validation(self, mock_parser_class):
        """Test successful content validation."""
        mock_parser = Mock()
        mock_parser.parse.return_value = {"valid": True, "errors": []}
        mock_parser_class.return_value = mock_parser

        content = "Class { #name : #TestClass }"
        result = validate_tonel_smalltalk(content)

        assert result["valid"] is True
        assert result["content_length"] == len(content)
        assert result["parser_type"] == "full"
        assert "errors" not in result
        mock_parser.parse.assert_called_once_with(content)

    @patch("smalltalk_validator_mcp_server.core.TonelTreeSitterParser")
    def test_tonel_only_validation(self, mock_parser_class):
        """Test validation with tonel-only option."""
        mock_parser = Mock()
        mock_parser.parse.return_value = {"valid": True, "errors": []}
        mock_parser_class.return_value = mock_parser

        content = "Class { #name : #TestClass }"
        result = validate_tonel_smalltalk(
            content, options={"without-method-body": True}
        )

        assert result["valid"] is True
        assert result["parser_type"] == "tonel_only"
        mock_parser_class.assert_called_once_with(ignore_method_body_errors=True)
        mock_parser.parse.assert_called_once_with(content)

    @patch("smalltalk_validator_mcp_server.core.TonelTreeSitterParser")
    def test_validation_with_errors(self, mock_parser_class):
        """Test content validation with errors."""
        mock_parser = Mock()
        error_list = [
            {
                "type": "ERROR",
                "start_point": [1, 0],
                "end_point": [1, 15],
                "text": "missing bracket",
                "parent_type": "method_definition",
                "context": None,
            }
        ]
        mock_parser.parse.return_value = {"valid": False, "errors": error_list}
        mock_parser_class.return_value = mock_parser

        content = "Invalid content"
        result = validate_tonel_smalltalk(content)

        assert result["valid"] is False
        assert result["errors"] == error_list
        assert result["content_length"] == len(content)

    @patch("smalltalk_validator_mcp_server.core.TonelTreeSitterParser")
    def test_content_validation_exception(self, mock_parser_class):
        """Test handling of content validation exceptions."""
        mock_parser = Mock()
        mock_parser.parse.side_effect = RuntimeError("Content error")
        mock_parser_class.return_value = mock_parser

        content = "Test content"
        result = validate_tonel_smalltalk(content)

        assert result["valid"] is False
        assert "Validation failed: Content error" in result["error"]
        assert result["exception"] == "RuntimeError"
        assert result["content_length"] == len(content)


class TestValidateSmalltalkMethodBody:
    """Tests for validate_smalltalk_method_body function."""

    @patch("smalltalk_validator_mcp_server.core.SmalltalkMethodParser")
    def test_successful_method_validation(self, mock_parser_class):
        """Test successful method body validation."""
        mock_parser = Mock()
        mock_parser.parse.return_value = {"valid": True, "errors": []}
        mock_parser_class.return_value = mock_parser

        method_body = "^ self name"
        result = validate_smalltalk_method_body(method_body)

        assert result["valid"] is True
        assert result["content_length"] == len(method_body)
        assert result["parser_type"] == "smalltalk_method"
        assert "errors" not in result
        mock_parser.parse.assert_called_once_with(method_body)

    @patch("smalltalk_validator_mcp_server.core.SmalltalkMethodParser")
    def test_method_validation_with_errors(self, mock_parser_class):
        """Test method validation with syntax errors."""
        mock_parser = Mock()
        error_list = [
            {
                "type": "ERROR",
                "start_point": [0, 0],
                "end_point": [0, 24],
                "text": "invalid method syntax ^^",
                "parent_type": "method_body",
                "context": None,
            }
        ]
        mock_parser.parse.return_value = {"valid": False, "errors": error_list}
        mock_parser_class.return_value = mock_parser

        method_body = "invalid method syntax ^^"
        result = validate_smalltalk_method_body(method_body)

        assert result["valid"] is False
        assert result["errors"] == error_list
        assert result["parser_type"] == "smalltalk_method"

    @patch("smalltalk_validator_mcp_server.core.SmalltalkMethodParser")
    def test_method_validation_exception(self, mock_parser_class):
        """Test handling of method validation exceptions."""
        mock_parser = Mock()
        mock_parser.parse.side_effect = SyntaxError("Method syntax error")
        mock_parser_class.return_value = mock_parser

        method_body = "test method"
        result = validate_smalltalk_method_body(method_body)

        assert result["valid"] is False
        assert "Method validation failed: Method syntax error" in result["error"]
        assert result["exception"] == "SyntaxError"
        assert result["content_length"] == len(method_body)
