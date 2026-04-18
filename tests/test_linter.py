"""
Unit tests for TonelCSTLinter.
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
from smalltalk_validator_mcp_server.linter import TonelCSTLinter


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
        issues = self._singleton_issues(
            self._lint(self._class_with_vars("SoleInstance"))
        )
        assert len(issues) == 1
        assert "SoleInstance" in issues[0].message

    def test_detects_current_class_var(self):
        issues = self._singleton_issues(self._lint(self._class_with_vars("Current")))
        assert len(issues) == 1
        assert "Current" in issues[0].message

    def test_detects_unique_instance_class_var(self):
        issues = self._singleton_issues(
            self._lint(self._class_with_vars("UniqueInstance"))
        )
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
