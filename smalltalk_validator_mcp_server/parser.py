"""
Tree-sitter based parsers for Tonel Smalltalk source code.
"""

import warnings
from typing import Any

from tree_sitter import Parser

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    import tree_sitter_tonel_smalltalk as ts_tonel

    _LANGUAGE = ts_tonel.language()


def _make_parser() -> Parser:
    return Parser(_LANGUAGE)


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
    """Extract string content from a ston_value that holds a ston_symbol or string."""
    for child in value_node.children:
        if child.type == "ston_symbol":
            raw = child.text.decode("utf-8") if child.text else ""
            raw = raw.lstrip("#")
            if raw.startswith("'") and raw.endswith("'"):
                raw = raw[1:-1]
            return raw
        if child.type == "string":
            raw = child.text.decode("utf-8") if child.text else ""
            if raw.startswith("'") and raw.endswith("'"):
                raw = raw[1:-1].replace("''", "'")
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
