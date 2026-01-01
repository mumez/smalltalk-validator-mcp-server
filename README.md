# smalltalk-validator-mcp-server

A simple MCP server for validating and linting Tonel formatted Smalltalk source code using
[tonel-smalltalk-parser](https://github.com/mumez/tonel-smalltalk-parser).

- The purpose is that we would like to validate and lint AI-generated tonel files and
  Smalltalk method definitions before loading them into a real Smalltalk environment.

## Tools

### Validation Tools

#### validate_tonel_smalltalk_from_file(file_path, options)

- Validate Tonel formatted Smalltalk source code from a file

#### validate_tonel_smalltalk(file_content, options)

- Validate Tonel formatted Smalltalk source code from content string

#### validate_smalltalk_method_body(method_body_content)

- Validate a Smalltalk method body for syntax correctness

#### Validation Options

```
without-method-body: true
    if true, it only validates tonel structure only (mainly for testing)
```

### Linting Tools

#### lint_tonel_smalltalk_from_file(file_path)

- Lint Tonel formatted Smalltalk source code from a file
- Checks for best practices and style issues such as:
  - Class naming conventions
  - Excessive instance variables
  - Method length
  - Direct instance variable access

#### lint_tonel_smalltalk(file_content)

- Lint Tonel formatted Smalltalk source code from content string
- Provides the same linting checks as lint_tonel_smalltalk_from_file

## Installation

### Quick install (uvx)

Run directly without cloning:

```bash
uvx --from git+https://github.com/mumez/smalltalk-validator-mcp-server.git@main smalltalk-validator-mcp-server
```

### Development setup (git clone)

```bash
git clone https://github.com/your-username/smalltalk-validator-mcp-server.git
cd smalltalk-validator-mcp-server
uv sync
```

## Usage

### Running the MCP Server

- Using uvx (recommended for quick run):

```bash
uvx --from git+https://github.com/mumez/smalltalk-validator-mcp-server.git@main smalltalk-validator-mcp-server
```

- From a cloned repo:

```bash
uv run smalltalk-validator-mcp-server
```

### Configuration Examples

#### Cursor Configuration

Add to your `.cursor/settings.json`:

```json
{
  "mcpServers": {
    "smalltalk-validator": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/mumez/smalltalk-validator-mcp-server.git@main",
        "smalltalk-validator-mcp-server"
      ]
    }
  }
}
```

If you prefer using a local clone, use this instead:

```json
{
  "mcpServers": {
    "smalltalk-validator": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/smalltalk-validator-mcp-server",
        "run",
        "smalltalk-validator-mcp-server"
      ]
    }
  }
}
```

#### Claude Code Configuration

Add to your Claude Code settings:

```bash
claude mcp add smalltalk-validator -- uvx --from git+https://github.com/mumez/smalltalk-validator-mcp-server.git@main smalltalk-validator-mcp-server
```

Using a local clone instead:

```bash
claude mcp add smalltalk-validator -- uv --directory /path/to/smalltalk-validator-mcp-server run smalltalk-validator-mcp-server
```

### Tool Usage Examples

#### Validate Tonel file from filesystem

```python
# Validate a complete Tonel file with method bodies
validate_tonel_smalltalk_from_file("/path/to/MyClass.st")

# Validate only Tonel structure (without method body validation)
validate_tonel_smalltalk_from_file("/path/to/MyClass.st", {"without-method-body": true})
```

#### Validate Tonel content directly

```python
tonel_content = """
Class {
    #name : #MyClass,
    #superclass : #Object,
    #category : #'My-Package'
}

{ #category : #accessing }
MyClass >> getValue [
    ^ 42
]
"""

validate_tonel_smalltalk(tonel_content)
```

#### Validate Smalltalk method body

```python
method_body = "^ self name asUppercase"
validate_smalltalk_method_body(method_body)
```

#### Lint Tonel file from filesystem

```python
# Lint a Tonel file for best practices and style issues
result = lint_tonel_smalltalk_from_file("/path/to/MyClass.st")

# Example result:
# {
#   "success": true,
#   "file_path": "/path/to/MyClass.st",
#   "issue_list": [
#     {
#       "severity": "warning",
#       "message": "Method 'longMethod' long: 18 lines (recommended: 15)",
#       "line_number": null
#     }
#   ],
#   "issues_count": 1,
#   "warnings_count": 0,
#   "errors_count": 0
# }
```

#### Lint Tonel content directly

```python
tonel_content = """
Class {
    #name : #MyClass,
    #superclass : #Object,
    #instVars : [
        'name',
        'age'
    ],
    #category : #'My-Package'
}

{ #category : #accessing }
MyClass >> getName [
    ^ name
]
"""

result = lint_tonel_smalltalk(tonel_content)
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint and format
uv run ruff check
uv run ruff format

# Install pre-commit hooks
uv run pre-commit install
```
