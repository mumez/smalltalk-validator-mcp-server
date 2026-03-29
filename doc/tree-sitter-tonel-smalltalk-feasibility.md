# Feasibility Report: Replacing tonel-smalltalk-parser with tree-sitter-tonel-smalltalk

Date: 2026-03-29

## 1. Current Architecture

The current `tonel-smalltalk-parser` provides three parser classes and one linter:

| Class | Role | API |
|-------|------|-----|
| `TonelParser` | Tonel structure only | `validate(content)` / `validate_from_file(path)` -> `(bool, error_info)` |
| `TonelFullParser` | Structure + method body | Same as above |
| `SmalltalkParser` | Method body only | `validate(content)` -> `(bool, error_info)` |
| `TonelLinter` | Code quality checks (4 rules) | `lint(content)` / `lint_from_file(path)` -> `list[LintIssue]` |

`core.py` wraps these into 5 MCP tools via FastMCP:

- `validate_tonel_smalltalk_from_file` / `validate_tonel_smalltalk` (with `without-method-body` option)
- `validate_smalltalk_method_body`
- `lint_tonel_smalltalk_from_file` / `lint_tonel_smalltalk`

### Parser Return Format

- Valid: `(True, None)`
- Invalid: `(False, {"reason": str, "line": int, "error_text": str})`

### Linter Rules (4 rules)

1. **Class prefix check** - warns if class name lacks a 2+ character prefix
2. **Instance variable count** - warns if >10 instance variables
3. **Method length** - warns at 15 lines, errors at 24 lines (special categories: 40 lines)
4. **Direct instance variable access** - warns on direct access outside accessing/initialization categories

## 2. tree-sitter-tonel-smalltalk Status

| Item | Status |
|------|--------|
| Version | **0.0.1** (early stage) |
| Grammar coverage | Tonel structure (Class/Trait/Extension/Package) + STON metadata + full Smalltalk method body |
| Test cases | 32 (class definitions: 6, method definitions: 10, expressions: 16) |
| Language bindings | **Node.js and Rust only** (no Python binding) |
| PyPI package | **None** |
| pyproject.toml / setup.py | **None** |
| tree-sitter-cli dependency | v0.20.8 |
| License | MIT |

### Grammar Structure (3 layers)

1. **Tonel file level** - `class_comment` + one `definition` + zero or more `method_definition`s
2. **STON metadata** - `ston_map` / `ston_pair` / `ston_value` for class metadata and per-method category
3. **Smalltalk method body** - expressions inside `[ ... ]` delimiters

### Test Corpus

- `class_definitions.txt` - Class, Trait, Extension, Package definitions (6 cases)
- `method_definitions.txt` - Method reference + body including cascades, pragmas, temporaries (10 cases)
- `smalltalk_expressions.txt` - Literals, messages, blocks, arrays, pseudo-variables (16 cases)

## 3. Technical Gap Analysis

### 3.1 No Python Binding (Priority: **High**)

The `bindings/` directory contains only `node/` and `rust/`. No `bindings/python/` exists.

**Resolution options:**

- **Option A (recommended)**: Add Python bindings to tree-sitter-tonel-smalltalk
  - Create `bindings/python/tree_sitter_tonel_smalltalk/__init__.py` and `binding.c`
  - Add `pyproject.toml`
  - Enable `pip install git+https://github.com/mumez/tree-sitter-tonel-smalltalk.git`
  - Template available from any official tree-sitter grammar (e.g., tree-sitter-python)
- **Option B (not recommended)**: Manually compile `src/parser.c` to `.so` and load via `ctypes`
  - Fragile, hard to maintain, not suitable for distribution

### 3.2 Validation API Differences (Priority: **Medium**)

| Current parser | tree-sitter |
|----------------|-------------|
| `validate()` -> `(bool, error_info)` | `parse()` -> Concrete Syntax Tree (CST) |
| Error: `{"reason", "line", "error_text"}` | Errors embedded as `(ERROR ...)` nodes in the tree |
| Explicit valid/invalid | Must traverse tree to detect ERROR/MISSING nodes |

**Resolution**: Implement an adapter layer that:

```python
# Conceptual example
tree = parser.parse(source_bytes)
errors = [node for node in walk(tree.root_node)
          if node.type == "ERROR" or node.is_missing]
is_valid = len(errors) == 0
error_info = build_error_info(errors[0]) if errors else None
```

### 3.3 Three Parser Types vs Single Grammar (Priority: **Medium**)

tree-sitter-tonel-smalltalk has a single grammar covering everything.

| Current class | tree-sitter equivalent |
|---------------|----------------------|
| `TonelParser` (structure only) | Parse full tree, ignore errors inside `method_body` nodes |
| `TonelFullParser` (full) | Full parse, check all ERROR nodes |
| `SmalltalkParser` (method body only) | **Requires workaround** - grammar expects `source_file` as root |

**SmalltalkParser workaround options:**

- Wrap the method body in a synthetic Tonel file structure before parsing
- Modify the grammar to support an alternative entry point for method bodies
- Create a separate tree-sitter grammar for standalone Smalltalk method bodies

### 3.4 No Linter Functionality (Priority: **High**)

tree-sitter is a parser, not a linter. The 4 rules in `TonelLinter` cannot be replaced by tree-sitter alone.

However, tree-sitter's CST can serve as a **better foundation** for linting:

- AST-walk based analysis is more robust than regex-based pattern matching
- Enables richer rules that understand code structure
- The linter would need to be **reimplemented** on top of tree-sitter's CST

### 3.5 py-tree-sitter Version Compatibility (Priority: **Low**)

- `py-tree-sitter` v0.25.2 requires Python >=3.10 (matches this project)
- tree-sitter-tonel-smalltalk's `Cargo.toml` depends on `tree-sitter ~0.20.10`
- ABI compatibility with py-tree-sitter v0.25.x needs verification

## 4. Advantages and Disadvantages

### Advantages

- **Incremental parsing**: tree-sitter supports incremental parsing, beneficial for editor integration
- **Concrete syntax tree**: Full CST enables richer code analysis, refactoring tools, and more robust linting
- **Error recovery**: tree-sitter can parse partially broken code and still produce a useful tree
- **Editor integration**: `queries/highlights.scm` enables syntax highlighting in Neovim, Helix, Zed, etc.
- **Ecosystem**: tree-sitter is widely adopted with strong community support

### Disadvantages

- **Python binding not ready**: Must be added to the tree-sitter-tonel-smalltalk repo
- **Linter reimplementation required**: Parser replacement alone is insufficient
- **API adapter cost**: Need to build compatibility layer for `(bool, error_info)` interface
- **Method body standalone parsing**: Requires workaround for `SmalltalkParser` equivalent
- **Native dependency**: Requires C compiler at build time (current parser is pure Python)
- **Maturity**: v0.0.1 with 32 test cases vs current parser validated against 223 real-world files

## 5. Recommended Approach

**Conclusion: Full replacement is premature at this point. A phased approach is recommended.**

### Phase 1: Add Python Bindings to tree-sitter-tonel-smalltalk

- Add `bindings/python/` following the standard tree-sitter grammar template
- Add `pyproject.toml` for pip-installable distribution
- Verify compatibility with py-tree-sitter v0.25.x

### Phase 2: Adapter Layer PoC

- Implement adapter that converts tree-sitter parse results to `(bool, error_info)` format
- Run identical test cases against both parsers in parallel and compare results
- Evaluate `SmalltalkParser` workaround (synthetic wrapping vs grammar modification)

### Phase 3: Linter Migration

- Reimplement `TonelLinter` 4 rules using tree-sitter CST traversal
- CST-based analysis should be more robust than current regex-based approach

### Phase 4: Production Switch

- Ensure sufficient test coverage and real-world validation
- Switch dependency from `tonel-smalltalk-parser` to `tree-sitter` + `tree-sitter-tonel-smalltalk`

## 6. Effort Estimation

| Task | Effort |
|------|--------|
| Add Python bindings (tree-sitter-tonel-smalltalk side) | Small |
| Validation adapter implementation | Medium |
| Method body standalone parsing support | Small-Medium |
| Linter migration (4 rules) | Medium |
| Test suite and regression testing | Medium |
| **Total** | **Medium-Large** |

Completing through Phase 2 (PoC) will provide a more accurate assessment of full replacement feasibility. Starting with the Python binding addition and a simple parallel comparison is recommended.
