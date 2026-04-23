"""
Tree-sitter based linter for Tonel Smalltalk source code.
"""

import re
from pathlib import Path

from smalltalk_validator_mcp_server.parser import (
    _make_parser,
    _ston_list_strings,
    _ston_map_get,
    _ston_symbol_text,
)

# Pre-compiled regex patterns for selector extraction
_RE_KEYWORDS = re.compile(r"[A-Za-z_][A-Za-z0-9_]*:")
_RE_BINARY_OP = re.compile(r"([^\s\w]+)")
_RE_UNARY_ID = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)")


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


def _extract_var_list(ston_map_node, key: str) -> list[str]:
    val = _ston_map_get(ston_map_node, key)
    return _ston_list_strings(val) if val is not None else []


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
        class_name, inst_vars, class_vars = self._extract_class_info(root)

        if class_name:
            issues.extend(self._check_class_prefix(class_name))
            issues.extend(self._check_instance_variables(class_name, inst_vars))
            issues.extend(self._check_singleton_class_vars(class_name, class_vars))

        for child in root.children:
            if child.type == "method_definition":
                issues.extend(self._check_method(child, inst_vars))

        return issues

    def _extract_class_info(self, root) -> tuple[str, list[str], list[str]]:
        """Return (class_name, inst_vars, class_vars) from the source_file's definition node."""
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
                    inst_vars = _extract_var_list(ston_child, "#instVars")
                    class_vars = _extract_var_list(ston_child, "#classVars")
                    return class_name or "", inst_vars, class_vars
        return "", [], []

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
                    f"Too many instance variables: {len(inst_vars)} (consider splitting responsibilities)",
                    class_name=class_name,
                )
            ]
        return []

    # Class variable names commonly used to hold a singleton instance.
    _SINGLETON_CLASS_VAR_NAMES = frozenset(
        {"Default", "SoleInstance", "Current", "UniqueInstance", "Instance"}
    )

    def _check_singleton_class_vars(
        self, class_name: str, class_vars: list[str]
    ) -> list[LintIssue]:
        return [
            LintIssue(
                "warning",
                f"Class variable '{var}' looks like a singleton holder (use a class instance variable instead)",
                class_name=class_name,
            )
            for var in class_vars
            if var in self._SINGLETON_CLASS_VAR_NAMES
        ]

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
            issues.extend(
                self._check_self_class_reference(
                    body_text,
                    class_name,
                    selector,
                    is_class_method,
                )
            )
            issues.extend(
                self._check_iskindof_usage(
                    body_text,
                    class_name,
                    selector,
                    is_class_method,
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

    def _check_self_class_reference(
        self,
        body_text: str,
        class_name: str,
        selector: str,
        is_class_method: bool,
    ) -> list[LintIssue]:
        if not class_name:
            return []

        sanitized = re.sub(r'"[^"\n]*"', "", body_text)
        sanitized = re.sub(r"'(?:''|[^'])*'", "''", sanitized)
        sanitized = re.sub(r"#'(?:''|[^'])*'", "#''", sanitized)
        sanitized = re.sub(r"#[A-Za-z_][A-Za-z0-9_]*", "#", sanitized)

        if not re.search(rf"\b{re.escape(class_name)}\b", sanitized):
            return []

        replacement = "self" if is_class_method else "self class"
        return [
            LintIssue(
                "warning",
                f"Direct reference to own class '{class_name}' (use {replacement} instead)",
                class_name=class_name,
                selector=selector,
                is_class_method=is_class_method,
            )
        ]

    def _check_iskindof_usage(
        self,
        body_text: str,
        class_name: str,
        selector: str,
        is_class_method: bool,
    ) -> list[LintIssue]:
        sanitized = re.sub(r'"[^"\n]*"', "", body_text)
        sanitized = re.sub(r"'(?:''|[^'])*'", "''", sanitized)
        sanitized = re.sub(r"#'(?:''|[^'])*'", "#''", sanitized)
        sanitized = re.sub(r"#[A-Za-z_][A-Za-z0-9_]*", "#", sanitized)

        if not re.search(r"\bisKindOf\s*:", sanitized):
            return []

        return [
            LintIssue(
                "warning",
                "Avoid isKindOf: checks (prefer isXxx predicate or polymorphism)",
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
