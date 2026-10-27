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


def _is_error_node(node) -> bool:
    """Return True for ERROR nodes and for MISSING nodes inserted by recovery.

    MISSING nodes keep the type of the expected token (e.g. "]"), so they must
    be detected via is_missing rather than by type.
    """
    return node.is_error or node.is_missing


def _error_type(node) -> str:
    return "MISSING" if node.is_missing else node.type


def _make_error_dict(node, context: str | None = None) -> dict[str, Any]:
    """Build a structured error dict from an ERROR/MISSING node."""
    return {
        "type": _error_type(node),
        "start_point": [node.start_point[0], node.start_point[1]],
        "end_point": [node.end_point[0], node.end_point[1]],
        "text": node.text.decode("utf-8") if node.text else "",
        "parent_type": node.parent.type if node.parent else None,
        "context": context,
    }


def _collect_errors(node, ignore_method_body: bool = False) -> list[dict[str, Any]]:
    """Collect ERROR/MISSING nodes from the CST, returning structured error dicts."""
    errors: list[dict[str, Any]] = []
    if _is_error_node(node):
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
_METHOD_PREFIX = "Class { #name : #__Temp__ }\n\n__Temp__ >> __method__ [\n"
_METHOD_SUFFIX = "\n]\n"
_METHOD_PREFIX_BYTES = len(_METHOD_PREFIX.encode("utf-8"))


def _byte_offset_to_point(source: bytes, offset: int) -> list[int]:
    """Convert a byte offset in *source* to a [row, column] point."""
    row = source.count(b"\n", 0, offset)
    line_start = source.rfind(b"\n", 0, offset) + 1
    return [row, offset - line_start]


class SmalltalkMethodParser:
    """Validates a standalone Smalltalk method body by wrapping it in synthetic Tonel."""

    def __init__(self) -> None:
        self._parser = _make_parser()

    def parse(self, method_body_content: str) -> dict[str, Any]:
        body = method_body_content.encode("utf-8")
        wrapped = _METHOD_PREFIX.encode("utf-8") + body + _METHOD_SUFFIX.encode("utf-8")
        tree = self._parser.parse(wrapped)
        # The wrapper itself is valid, so any error in the tree is caused by the
        # body. Errors are not always under method_body: when the body cannot be
        # parsed, recovery may attach them to method_definition or source_file.
        errors = [
            self._make_body_error_dict(node, body)
            for node in self._error_nodes(tree.root_node)
        ]
        return {"valid": len(errors) == 0, "errors": errors}

    def _error_nodes(self, node) -> list:
        nodes = [node] if _is_error_node(node) else []
        for child in node.children:
            nodes.extend(self._error_nodes(child))
        return nodes

    def _make_body_error_dict(self, node, body: bytes) -> dict[str, Any]:
        """Build an error dict with the node's range clipped to the method body."""
        start = min(max(node.start_byte - _METHOD_PREFIX_BYTES, 0), len(body))
        end = min(max(node.end_byte - _METHOD_PREFIX_BYTES, start), len(body))
        return {
            "type": _error_type(node),
            "start_point": _byte_offset_to_point(body, start),
            "end_point": _byte_offset_to_point(body, end),
            "text": body[start:end].decode("utf-8", errors="replace"),
            "parent_type": node.parent.type if node.parent else None,
            "context": None,
        }
