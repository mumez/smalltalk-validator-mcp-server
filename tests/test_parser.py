"""
Tests for the tree-sitter based parsers using the real grammar (no mocks).
"""

import pytest

from smalltalk_validator_mcp_server.parser import (
    SmalltalkMethodParser,
    TonelTreeSitterParser,
)

_CLASS_HEADER = (
    "Class {\n\t#name : #Foo,\n\t#superclass : #Object,\n\t#category : #Bar\n}\n\n"
)


class TestSmalltalkMethodParser:
    """Tests for SmalltalkMethodParser."""

    @pytest.mark.parametrize(
        "body",
        [
            "",
            "^ 1 + 2",
            "| t |\nt := 1.\n^ t",
            "<pragma: 1>\naStream nextPutAll: 'x'; print: 3",
            "^ [:x | x * 2] value: 3",
            "^ #(1 $a #b 'c') , {1. 2}",
            '"comment" ^ self',
            "^ 'あいう' size",
        ],
    )
    def test_valid_body(self, body):
        result = SmalltalkMethodParser().parse(body)

        assert result["valid"] is True
        assert result["errors"] == []

    @pytest.mark.parametrize(
        "body",
        [
            "^ (",
            "^ (1 + ",
            "^ 3 +",
            "^ 'abc",
            '"unterminated',
        ],
    )
    def test_invalid_body_reports_one_error(self, body):
        """One defect is reported as one error, even if recovery nests ERRORs."""
        result = SmalltalkMethodParser().parse(body)

        assert result["valid"] is False
        assert [error["type"] for error in result["errors"]] == ["ERROR"]

    @pytest.mark.parametrize(
        "body",
        [
            "^ #(1 2",
            "^ {1. 2",
            "^ [:x | x",
            "| a ^ a",
        ],
    )
    def test_invalid_body_reports_one_missing(self, body):
        result = SmalltalkMethodParser().parse(body)

        assert result["valid"] is False
        assert [error["type"] for error in result["errors"]] == ["MISSING"]

    def test_body_with_selector_is_invalid(self):
        """The selector line is supplied by the wrapper, not the body."""
        result = SmalltalkMethodParser().parse("foo\n    ^ 1 + 2")

        assert result["valid"] is False

    def test_error_location_is_relative_to_body(self):
        result = SmalltalkMethodParser().parse("| t |\nt := 1.\n^ t +")

        assert result["errors"] == [
            {
                "type": "ERROR",
                "start_point": [2, 4],
                "end_point": [2, 5],
                "text": "+",
                "parent_type": "method_definition",
                "context": None,
            }
        ]

    def test_error_range_is_clipped_to_body(self):
        """Errors spanning the synthetic wrapper are clipped to the body."""
        result = SmalltalkMethodParser().parse("^ (")

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["start_point"] == [0, 0]
        assert result["errors"][0]["end_point"] == [0, 3]
        assert result["errors"][0]["text"] == "^ ("

    def test_error_column_is_byte_based(self):
        """Columns are byte offsets (as in tree-sitter), not character offsets."""
        result = SmalltalkMethodParser().parse("^ 'あいう' +")

        assert len(result["errors"]) == 1
        assert result["errors"][0]["start_point"] == [0, 14]
        assert result["errors"][0]["end_point"] == [0, 15]
        assert result["errors"][0]["text"] == "+"


class TestTonelTreeSitterParser:
    """Tests for TonelTreeSitterParser."""

    def test_valid_method(self):
        result = TonelTreeSitterParser().parse(
            _CLASS_HEADER + "Foo >> bar [\n\t^ 3\n]\n"
        )

        assert result["valid"] is True

    def test_missing_node_in_method_body(self):
        result = TonelTreeSitterParser().parse(
            _CLASS_HEADER + "Foo >> bar [\n\t^ #(1 2\n]\n"
        )

        assert result["valid"] is False
        assert result["errors"][0]["type"] == "MISSING"
        assert result["errors"][0]["context"] == "Foo >> bar"

    def test_nested_errors_reported_once(self):
        result = TonelTreeSitterParser().parse(
            _CLASS_HEADER + "Foo >> bar [\n\t^ 'abc\n]\n"
        )

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["type"] == "ERROR"

    def test_missing_node_ignored_in_tonel_only_mode(self):
        result = TonelTreeSitterParser(ignore_method_body_errors=True).parse(
            _CLASS_HEADER + "Foo >> bar [\n\t^ #(1 2\n]\n"
        )

        assert result["valid"] is True
