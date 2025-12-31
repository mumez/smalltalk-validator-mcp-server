# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server project for validating Tonel formatted Smalltalk source code using the tonel-smalltalk-parser. The purpose is to validate AI-generated tonel files and Smalltalk method definitions before loading them into a real Smalltalk environment.

## Architecture

The project implements five main tools:

### Validation Tools

- `validate_tonel_smalltalk_from_file(file_path, options)` - Validate Tonel formatted Smalltalk source code from a file
- `validate_tonel_smalltalk(file_content, options)` - Validate Tonel formatted Smalltalk source code from content string
- `validate_smalltalk_method_body(method_body_content)` - Validate a Smalltalk method body for syntax correctness

### Linting Tools

- `lint_tonel_smalltalk_from_file(file_path)` - Lint Tonel formatted Smalltalk source code from a file
- `lint_tonel_smalltalk(file_content)` - Lint Tonel formatted Smalltalk source code from content string

### Validation Options

- `without-method-body: true` - Only validates tonel structure (for testing)

## Common Commands

- `uv sync` - Install dependencies and sync virtual environment
- `uv run pytest` - Run all tests
- `uv run pytest tests/test_server.py` - Run server tests only
- `uv run pytest -v` - Run tests with verbose output
- `uv run ruff check` - Lint code with ruff
- `uv run ruff format` - Format code with ruff
- `uv run ruff check --fix` - Auto-fix linting issues
- `uv run mdformat --check .` - Check markdown formatting
- `uv run mdformat .` - Format markdown files
- `uv run pre-commit install` - Install pre-commit hooks (run once after clone)
- `uv run pre-commit run --all-files` - Run all pre-commit hooks manually
- `uv run python -m smalltalk_validator_mcp_server` - Run the MCP server

## Pre-commit Hooks

Pre-commit hooks automatically run before each commit to ensure code quality:

- Basic file checks (trailing whitespace, file endings, YAML syntax)
- Ruff linting and formatting for Python code
- Mdformat for markdown files
- Pytest to ensure tests pass

## Development Status

Project is implemented and functional. The MCP server provides five tools (three validation tools and two linting tools) for Smalltalk code using FastMCP framework and tonel-smalltalk-parser.

## Dependencies

- [tonel-smalltalk-parser](https://github.com/mumez/tonel-smalltalk-parser) - Core parsing library (installed from Git)
- FastMCP - MCP server framework
- pytest - Testing framework
