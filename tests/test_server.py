"""
Unit tests for the Smalltalk Validator MCP Server.
"""

import os
import tempfile
from unittest.mock import Mock, patch

from smalltalk_validator_mcp_server.core import (
    lint_tonel_smalltalk_from_file_impl as lint_tonel_smalltalk_from_file,
)
from smalltalk_validator_mcp_server.core import (
    lint_tonel_smalltalk_impl as lint_tonel_smalltalk,
)
from smalltalk_validator_mcp_server.core import (
    validate_smalltalk_method_body_impl as validate_smalltalk_method_body,
)
from smalltalk_validator_mcp_server.core import (
    validate_tonel_smalltalk_from_file_impl as validate_tonel_smalltalk_from_file,
)
from smalltalk_validator_mcp_server.linter import TonelCSTLinter
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


class TestLintTonelSmalltalkFromFile:
    """Tests for lint_tonel_smalltalk_from_file function."""

    def test_file_not_found(self):
        """Test linting when file doesn't exist."""
        result = lint_tonel_smalltalk_from_file("/non/existent/file.st")

        assert result["success"] is False
        assert "File not found" in result["error"]
        assert result["file_path"] == "/non/existent/file.st"

    @patch("smalltalk_validator_mcp_server.core.TonelCSTLinter")
    def test_successful_linting_no_issues(self, mock_linter_class):
        """Test successful linting with no issues."""
        mock_linter = Mock()
        mock_linter.lint_from_file.return_value = []
        mock_linter.warnings = 0
        mock_linter.errors = 0
        mock_linter_class.return_value = mock_linter

        with tempfile.NamedTemporaryFile(mode="w", suffix=".st", delete=False) as f:
            f.write("Class { #name : #TestClass }")
            temp_path = f.name

        try:
            result = lint_tonel_smalltalk_from_file(temp_path)

            assert result["success"] is True
            assert result["file_path"] == temp_path
            assert result["issue_list"] == []
            assert result["issues_count"] == 0
            assert result["warnings_count"] == 0
            assert result["errors_count"] == 0
        finally:
            os.unlink(temp_path)

    @patch("smalltalk_validator_mcp_server.core.TonelCSTLinter")
    def test_linting_with_issues(self, mock_linter_class):
        """Test linting that returns issues."""
        mock_issue = Mock()
        mock_issue.severity = "warning"
        mock_issue.message = "Long method detected"
        mock_issue.class_name = "TestClass"
        mock_issue.selector = "longMethod"
        mock_issue.is_class_method = False

        mock_linter = Mock()
        mock_linter.lint_from_file.return_value = [mock_issue]
        mock_linter.warnings = 1
        mock_linter.errors = 0
        mock_linter_class.return_value = mock_linter

        with tempfile.NamedTemporaryFile(mode="w", suffix=".st", delete=False) as f:
            f.write("Class { #name : #TestClass }")
            temp_path = f.name

        try:
            result = lint_tonel_smalltalk_from_file(temp_path)

            assert result["success"] is True
            assert result["issues_count"] == 1
            assert result["warnings_count"] == 1
            assert result["errors_count"] == 0
            assert len(result["issue_list"]) == 1
            assert result["issue_list"][0]["severity"] == "warning"
            assert result["issue_list"][0]["message"] == "Long method detected"
            assert result["issue_list"][0]["class_name"] == "TestClass"
            assert result["issue_list"][0]["selector"] == "longMethod"
            assert result["issue_list"][0]["is_class_method"] is False
        finally:
            os.unlink(temp_path)

    @patch("smalltalk_validator_mcp_server.core.TonelCSTLinter")
    def test_linter_exception(self, mock_linter_class):
        """Test handling of linter exceptions."""
        mock_linter = Mock()
        mock_linter.lint_from_file.side_effect = ValueError("Linter error")
        mock_linter_class.return_value = mock_linter

        with tempfile.NamedTemporaryFile(mode="w", suffix=".st", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            result = lint_tonel_smalltalk_from_file(temp_path)

            assert result["success"] is False
            assert "Linting failed: Linter error" in result["error"]
            assert result["exception"] == "ValueError"
        finally:
            os.unlink(temp_path)


class TestLintTonelSmalltalk:
    """Tests for lint_tonel_smalltalk function."""

    @patch("smalltalk_validator_mcp_server.core.TonelCSTLinter")
    def test_successful_linting(self, mock_linter_class):
        """Test successful content linting."""
        mock_linter = Mock()
        mock_linter.lint.return_value = []
        mock_linter.warnings = 0
        mock_linter.errors = 0
        mock_linter_class.return_value = mock_linter

        content = "Class { #name : #TestClass }"
        result = lint_tonel_smalltalk(content)

        assert result["success"] is True
        assert result["content_length"] == len(content)
        assert result["issue_list"] == []
        assert result["issues_count"] == 0
        assert result["warnings_count"] == 0
        assert result["errors_count"] == 0
        mock_linter.lint.assert_called_once_with(content)

    @patch("smalltalk_validator_mcp_server.core.TonelCSTLinter")
    def test_linting_with_multiple_issues(self, mock_linter_class):
        """Test linting with multiple issues."""
        mock_issue1 = Mock()
        mock_issue1.severity = "error"
        mock_issue1.message = "Invalid class name"
        mock_issue1.class_name = "testClass"
        mock_issue1.selector = None
        mock_issue1.is_class_method = None

        mock_issue2 = Mock()
        mock_issue2.severity = "warning"
        mock_issue2.message = "Too many instance variables"
        mock_issue2.class_name = "testClass"
        mock_issue2.selector = None
        mock_issue2.is_class_method = None

        mock_linter = Mock()
        mock_linter.lint.return_value = [mock_issue1, mock_issue2]
        mock_linter.warnings = 1
        mock_linter.errors = 1
        mock_linter_class.return_value = mock_linter

        content = "Class { #name : #testClass }"
        result = lint_tonel_smalltalk(content)

        assert result["success"] is True
        assert result["issues_count"] == 2
        assert result["warnings_count"] == 1
        assert result["errors_count"] == 1
        assert len(result["issue_list"]) == 2
        assert result["issue_list"][0]["severity"] == "error"
        assert result["issue_list"][0]["class_name"] == "testClass"
        assert result["issue_list"][1]["severity"] == "warning"
        assert result["issue_list"][1]["class_name"] == "testClass"

    @patch("smalltalk_validator_mcp_server.core.TonelCSTLinter")
    def test_content_linting_exception(self, mock_linter_class):
        """Test handling of content linting exceptions."""
        mock_linter = Mock()
        mock_linter.lint.side_effect = RuntimeError("Content linting error")
        mock_linter_class.return_value = mock_linter

        content = "Test content"
        result = lint_tonel_smalltalk(content)

        assert result["success"] is False
        assert "Linting failed: Content linting error" in result["error"]
        assert result["exception"] == "RuntimeError"
        assert result["content_length"] == len(content)


class TestSingletonClassVarCheck:
    """Tests for singleton class variable detection in TonelCSTLinter."""

    def _lint(self, content: str):
        return TonelCSTLinter().lint(content)

    def _singleton_issues(self, issues):
        return [i for i in issues if "singleton holder" in i.message]

    _CLASS_TEMPLATE = (
        "Class {{\n"
        "    #name : #MyNs,\n"
        "    #superclass : #Object,\n"
        "    #classVars : [ {vars} ],\n"
        "    #category : #SomePackage\n"
        "}}"
    )

    def _class_with_vars(self, *var_names: str) -> str:
        vars_str = ", ".join(f"'{v}'" for v in var_names)
        return self._CLASS_TEMPLATE.format(vars=vars_str)

    def test_detects_default_class_var(self):
        issues = self._singleton_issues(self._lint(self._class_with_vars("Default")))
        assert len(issues) == 1
        assert "Default" in issues[0].message
        assert issues[0].severity == "warning"
        assert issues[0].class_name == "MyNs"

    def test_detects_sole_instance_class_var(self):
        issues = self._singleton_issues(self._lint(self._class_with_vars("SoleInstance")))
        assert len(issues) == 1
        assert "SoleInstance" in issues[0].message

    def test_detects_current_class_var(self):
        issues = self._singleton_issues(self._lint(self._class_with_vars("Current")))
        assert len(issues) == 1
        assert "Current" in issues[0].message

    def test_detects_unique_instance_class_var(self):
        issues = self._singleton_issues(self._lint(self._class_with_vars("UniqueInstance")))
        assert len(issues) == 1
        assert "UniqueInstance" in issues[0].message

    def test_detects_instance_class_var(self):
        issues = self._singleton_issues(self._lint(self._class_with_vars("Instance")))
        assert len(issues) == 1
        assert "Instance" in issues[0].message

    def test_no_issue_for_unrelated_class_var(self):
        issues = self._singleton_issues(self._lint(self._class_with_vars("Counter")))
        assert len(issues) == 0

    def test_no_issue_without_class_vars(self):
        content = (
            "Class {\n"
            "    #name : #MyNs,\n"
            "    #superclass : #Object,\n"
            "    #instVars : [ 'foo' ],\n"
            "    #category : #SomePackage\n"
            "}"
        )
        issues = self._singleton_issues(self._lint(content))
        assert len(issues) == 0

    def test_multiple_singleton_vars_each_reported(self):
        issues = self._singleton_issues(
            self._lint(self._class_with_vars("Default", "Current"))
        )
        assert len(issues) == 2
