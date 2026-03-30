"""
Tree-sitter based parsers and linter for Tonel Smalltalk source code.
"""

import re
import warnings
from pathlib import Path
from typing import Any

from tree_sitter import Parser

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    import tree_sitter_tonel_smalltalk as ts_tonel

    _LANGUAGE = ts_tonel.language()


def _make_parser() -> Parser:
    return Parser(_LANGUAGE)


# Pre-compiled regex patterns for selector extraction
_RE_KEYWORDS = re.compile(r"[A-Za-z_][A-Za-z0-9_]*:")
_RE_BINARY_OP = re.compile(r"([^\s\w]+)")
_RE_UNARY_ID = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)")


def _is_inside_method_body(node) -> bool:
    """Return True if node is a descendant of a method_body node."""
    current = node.parent
    while current:
        if current.type == "method_body":
            return True
        current = current.parent
    return False


def _resolve_context(node) -> str | None:
    """Walk up to the enclosing method_definition and return its reference text."""
    current = node.parent
    while current:
        if current.type == "method_definition":
            for child in current.children:
                if child.type == "method_reference":
                    return child.text.decode("utf-8") if child.text else None
        current = current.parent
    return None


def _make_error_dict(
    node, row_offset: int = 0, context: str | None = None
) -> dict[str, Any]:
    """Build a structured error dict from an ERROR/MISSING node."""
    return {
        "type": node.type,
        "start_point": [node.start_point[0] - row_offset, node.start_point[1]],
        "end_point": [node.end_point[0] - row_offset, node.end_point[1]],
        "text": node.text.decode("utf-8") if node.text else "",
        "parent_type": node.parent.type if node.parent else None,
        "context": context,
    }


def _collect_errors(node, ignore_method_body: bool = False) -> list[dict[str, Any]]:
    """Collect ERROR/MISSING nodes from the CST, returning structured error dicts."""
    errors: list[dict[str, Any]] = []
    if node.type in ("ERROR", "MISSING"):
        if not (ignore_method_body and _is_inside_method_body(node)):
            errors.append(_make_error_dict(node, context=_resolve_context(node)))
    for child in node.children:
        errors.extend(_collect_errors(child, ignore_method_body))
    return errors


def _ston_map_get(ston_map_node, key: str):
    """Return the ston_value node for *key* in a ston_map, or None."""
    for child in ston_map_node.children:
        if child.type != "ston_pair":
            continue
        key_node = None
        value_node = None
        for pair_child in child.children:
            if pair_child.type == "ston_key":
                key_node = pair_child
            elif pair_child.type == "ston_value":
                value_node = pair_child
        if key_node is None or value_node is None:
            continue
        key_text = key_node.text.decode("utf-8") if key_node.text else ""
        if key_text == key:
            return value_node
    return None


def _ston_symbol_text(value_node) -> str | None:
    """Extract string content from a ston_value that holds a ston_symbol."""
    for child in value_node.children:
        if child.type == "ston_symbol":
            raw = child.text.decode("utf-8") if child.text else ""
            raw = raw.lstrip("#")
            if raw.startswith("'") and raw.endswith("'"):
                raw = raw[1:-1]
            return raw
    return None


def _ston_list_strings(value_node) -> list[str]:
    """Extract list of string values from a ston_value that holds a ston_list."""
    for child in value_node.children:
        if child.type != "ston_list":
            continue
        items: list[str] = []
        for list_child in child.children:
            if list_child.type != "ston_value":
                continue
            for inner in list_child.children:
                if inner.type == "string":
                    raw = inner.text.decode("utf-8") if inner.text else ""
                    raw = raw[1:-1].replace("''", "'")
                    items.append(raw)
        return items
    return []


class TonelTreeSitterParser:
    """Validates Tonel formatted Smalltalk source using tree-sitter.

    Args:
        ignore_method_body_errors: When True, errors inside method_body nodes
            are suppressed (equivalent to old TonelParser / tonel-only mode).
    """

    def __init__(self, ignore_method_body_errors: bool = False) -> None:
        self._ignore = ignore_method_body_errors
        self._parser = _make_parser()

    def parse(self, content: str) -> dict[str, Any]:
        tree = self._parser.parse(content.encode("utf-8"))
        errors = _collect_errors(tree.root_node, self._ignore)
        return {"valid": len(errors) == 0, "errors": errors}

    def parse_from_file(self, file_path: str) -> dict[str, Any]:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        return self.parse(content)


# Synthetic Tonel wrapper for method-body-only validation.
# 3 lines of prefix keep column numbers intact for error reporting.
_METHOD_PREFIX = "Class { #name : #__Temp__ }\n\n__Temp__ >> __method__ [\n"
_METHOD_PREFIX_ROWS = _METHOD_PREFIX.count("\n")  # == 3


class SmalltalkMethodParser:
    """Validates a standalone Smalltalk method body by wrapping it in synthetic Tonel."""

    def __init__(self) -> None:
        self._parser = _make_parser()

    def parse(self, method_body_content: str) -> dict[str, Any]:
        wrapped = _METHOD_PREFIX + method_body_content + "\n]\n"
        tree = self._parser.parse(wrapped.encode("utf-8"))
        errors = self._method_body_errors(tree.root_node)
        return {"valid": len(errors) == 0, "errors": errors}

    def _method_body_errors(self, root) -> list[dict[str, Any]]:
        method_body = self._find_method_body(root)
        if method_body is None:
            return []
        return self._errors_under(method_body)

    def _find_method_body(self, node):
        if node.type == "method_body":
            return node
        for child in node.children:
            result = self._find_method_body(child)
            if result is not None:
                return result
        return None

    def _errors_under(self, node) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        if node.type in ("ERROR", "MISSING"):
            errors.append(_make_error_dict(node, row_offset=_METHOD_PREFIX_ROWS))
        for child in node.children:
            errors.extend(self._errors_under(child))
        return errors


class LintIssue:
    """Represents a single linting issue."""

    def __init__(
        self,
        severity: str,
        message: str,
        class_name: str | None = None,
        selector: str | None = None,
        is_class_method: bool | None = None,
    ) -> None:
        self.severity = severity
        self.message = message
        self.class_name = class_name
        self.selector = selector
        self.is_class_method = is_class_method


def _selector_from_after_arrow(after_arrow: str) -> str:
    """Extract the selector string from the text after '>>' in a method reference."""
    text = after_arrow.strip()
    keywords = _RE_KEYWORDS.findall(text)
    if keywords:
        return "".join(keywords)
    m = _RE_BINARY_OP.match(text)
    if m:
        return m.group(1)
    m = _RE_UNARY_ID.match(text)
    if m:
        return m.group(1)
    return text


def _parse_method_ref(method_ref_node) -> tuple[str, str, bool]:
    """Return (class_name, selector, is_class_method) from a method_reference node."""
    text = method_ref_node.text.decode("utf-8") if method_ref_node.text else ""
    is_class_method = False
    class_name = ""
    selector = ""

    if ">>" in text:
        before, after = text.split(">>", 1)
        before = before.strip()
        if before.endswith(" class"):
            is_class_method = True
            before = before[: -len(" class")].strip()
        class_name = before
        selector = _selector_from_after_arrow(after)

    return class_name, selector, is_class_method


def _get_method_category(method_def_node) -> str:
    """Extract the category string from a method_definition's method_metadata."""
    for child in method_def_node.children:
        if child.type != "method_metadata":
            continue
        for meta_child in child.children:
            if meta_child.type != "ston_map":
                continue
            val_node = _ston_map_get(meta_child, "#category")
            if val_node is not None:
                return _ston_symbol_text(val_node) or ""
    return ""


class TonelCSTLinter:
    """Lints Tonel files for Smalltalk best practices using tree-sitter CST."""

    def __init__(self) -> None:
        self._parser = _make_parser()
        self.warnings = 0
        self.errors = 0

    def lint(self, content: str) -> list[LintIssue]:
        self.warnings = 0
        self.errors = 0
        tree = self._parser.parse(content.encode("utf-8"))
        issues = self._run_checks(tree.root_node)
        for issue in issues:
            if issue.severity == "error":
                self.errors += 1
            else:
                self.warnings += 1
        return issues

    def lint_from_file(self, file_path: Path) -> list[LintIssue]:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            return self.lint(content)
        except Exception as exc:
            issue = LintIssue("error", f"Failed to read file: {exc}")
            self.errors += 1
            return [issue]

    def _run_checks(self, root) -> list[LintIssue]:
        issues: list[LintIssue] = []
        class_name, inst_vars = self._extract_class_info(root)

        if class_name:
            issues.extend(self._check_class_prefix(class_name))
            issues.extend(self._check_instance_variables(class_name, inst_vars))

        for child in root.children:
            if child.type == "method_definition":
                issues.extend(self._check_method(child, inst_vars))

        return issues

    def _extract_class_info(self, root) -> tuple[str, list[str]]:
        """Return (class_name, inst_vars) from the source_file's definition node."""
        for child in root.children:
            if child.type != "definition":
                continue
            for def_child in child.children:
                if def_child.type not in (
                    "class_definition",
                    "trait_definition",
                    "extension_definition",
                ):
                    continue
                for ston_child in def_child.children:
                    if ston_child.type != "ston_map":
                        continue
                    name_val = _ston_map_get(ston_child, "#name")
                    class_name = (
                        _ston_symbol_text(name_val) if name_val is not None else ""
                    )
                    vars_val = _ston_map_get(ston_child, "#instVars")
                    inst_vars = (
                        _ston_list_strings(vars_val) if vars_val is not None else []
                    )
                    return class_name or "", inst_vars
        return "", []

    def _check_class_prefix(self, class_name: str) -> list[LintIssue]:
        if class_name.startswith("BaselineOf") or class_name.endswith("Test"):
            return []
        has_prefix = len(class_name) >= 3 and (
            re.match(r"^[A-Z]{2,}", class_name)
            or re.match(r"^[A-Z][a-z][A-Z]", class_name)
        )
        if not has_prefix:
            return [
                LintIssue(
                    "warning",
                    "No class prefix (consider adding project prefix)",
                    class_name=class_name,
                )
            ]
        return []

    def _check_instance_variables(
        self, class_name: str, inst_vars: list[str]
    ) -> list[LintIssue]:
        if len(inst_vars) > 10:
            return [
                LintIssue(
                    "warning",
                    (
                        f"Too many instance variables: {len(inst_vars)} "
                        "(consider splitting responsibilities)"
                    ),
                    class_name=class_name,
                )
            ]
        return []

    def _check_method(self, method_def_node, inst_vars: list[str]) -> list[LintIssue]:
        issues: list[LintIssue] = []

        class_name, selector, is_class_method = "", "", False
        for child in method_def_node.children:
            if child.type == "method_reference":
                class_name, selector, is_class_method = _parse_method_ref(child)
                break

        category = _get_method_category(method_def_node)

        body_node = None
        for child in method_def_node.children:
            if child.type == "method_body":
                body_node = child
                break

        if body_node is not None:
            body_text = body_node.text.decode("utf-8") if body_node.text else ""
            issues.extend(
                self._check_method_length(
                    body_text, class_name, selector, is_class_method, category
                )
            )
            issues.extend(
                self._check_direct_access(
                    body_text,
                    class_name,
                    selector,
                    is_class_method,
                    category,
                    inst_vars,
                )
            )

        return issues

    def _check_method_length(
        self,
        body_text: str,
        class_name: str,
        selector: str,
        is_class_method: bool,
        category: str,
    ) -> list[LintIssue]:
        body_lines = len(body_text.strip().split("\n"))
        is_special = any(
            kw in category.lower()
            for kw in ["building", "initialization", "testing", "data", "examples"]
        )
        limit = 40 if is_special else 15

        if body_lines <= limit:
            return []

        if body_lines > 24 and limit == 15:
            return [
                LintIssue(
                    "error",
                    f"Method too long: {body_lines} lines (limit: {limit})",
                    class_name=class_name,
                    selector=selector,
                    is_class_method=is_class_method,
                )
            ]
        return [
            LintIssue(
                "warning",
                f"Method long: {body_lines} lines (recommended: {limit})",
                class_name=class_name,
                selector=selector,
                is_class_method=is_class_method,
            )
        ]

    def _check_direct_access(
        self,
        body_text: str,
        class_name: str,
        selector: str,
        is_class_method: bool,
        category: str,
        inst_vars: list[str],
    ) -> list[LintIssue]:
        if not inst_vars:
            return []

        cat_lower = category.lower()
        if "accessing" in cat_lower or "initializ" in cat_lower:
            return []

        issues: list[LintIssue] = []
        for line in body_text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            for var in inst_vars:
                if (
                    re.search(rf"\b{re.escape(var)}\s*:=", line)
                    or re.search(rf"^\^\s*{re.escape(var)}\b", line)
                ) and "self" not in line.split(var)[0]:
                    issues.append(
                        LintIssue(
                            "warning",
                            f"Direct access to '{var}' (use self {var})",
                            class_name=class_name,
                            selector=selector,
                            is_class_method=is_class_method,
                        )
                    )
                    break

        return issues
