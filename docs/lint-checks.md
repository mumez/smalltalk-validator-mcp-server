# Lint Checks

The linter (`lint_tonel_smalltalk` / `lint_tonel_smalltalk_from_file`) performs the following checks.

Each issue has a `severity` of either `warning` or `error`.

## Class-level Checks

### Class Naming Convention

**Severity:** warning

Checks that the class name starts with a project prefix (two or more uppercase letters, or a pattern like `AbC`).

- `BaselineOf*` and `*Test` classes are exempt.

Example trigger: class named `MyClass` instead of `MvMyClass`.

______________________________________________________________________

### Too Many Instance Variables

**Severity:** warning

Triggers when a class declares more than 10 instance variables.

Suggestion: consider splitting responsibilities into smaller classes.

______________________________________________________________________

### Singleton Class Variable

**Severity:** warning

Triggers when a class variable name matches one of the common singleton holder patterns:

| Variable name    |
| ---------------- |
| `Default`        |
| `SoleInstance`   |
| `Current`        |
| `UniqueInstance` |
| `Instance`       |

Suggestion: use a class instance variable instead (define it via `class >> instanceVariableNames`).

______________________________________________________________________

### Missing Class Comment

**Severity:** warning

Triggers when a class defined via `Class { ... }` (not a trait or extension) has no class comment (the `"..."` section at the top of the Tonel file, before the class definition) **and** the class is deemed important enough to warrant one.

Importance is estimated with a complexity score, based on the same formula used by the [smalltalk-commenter](https://github.com/mumez/smalltalk-dev-plugin/blob/main/skills/smalltalk-commenter/SKILL.md#phase-1-discovery--analysis) skill:

```
score = (methods × 2) + (instance_vars × 3) + (collaborators × 2) + (LOC / 50)
```

- `methods` — number of method definitions in the file.
- `instance_vars` — number of declared instance variables.
- `collaborators` — approximated as the number of distinct capitalized identifiers referenced across the class's method bodies (a proxy for other classes referenced, since the linter has no cross-file/image access).
- `LOC` — total line count of the file.

The check is skipped entirely (no warning, regardless of score) when:

- The class name starts with `BaselineOf` or ends with `Test`, `Tests`, or `TestCase`.
- The class has fewer than 5 methods (treated as a simple utility class).
- The computed score is below 10 (too simple to need documentation).

Otherwise, a warning is raised and labeled with a priority:

| Score range | Priority |
| ----------- | -------- |
| 10 – 29     | moderate |
| ≥ 30        | high     |

Suggestion: add a CRC-style class comment (e.g. via the smalltalk-commenter skill) describing the class's responsibility, collaborators, and public API.

## Method-level Checks

### Method Too Long

**Severity:** warning or error depending on length and category.

| Category                                                              | Warning threshold | Error threshold |
| --------------------------------------------------------------------- | ----------------- | --------------- |
| Normal                                                                | > 15 lines        | > 24 lines      |
| Special (`building`, `initialization`, `testing`, `data`, `examples`) | > 40 lines        | —               |

______________________________________________________________________

### Direct Instance Variable Access

**Severity:** warning

Triggers when an instance method reads or writes an instance variable directly (without going through an accessor) outside of `accessing` or `initializing` categories.

- Only applies to instance methods; class methods are exempt.
- Instance variables shadowed by a method argument, temporary, or block argument of the same name are excluded.

Suggestion: use accessor messages (`self name: 'foo'` / `^ self name`) instead.

______________________________________________________________________

### Direct Own-Class Reference

**Severity:** warning

Triggers when a method directly references its own class name even though `self` / `self class` can resolve it.

- In instance methods, prefer `self class` over direct class-name reference.
- In class methods, prefer `self` over direct class-name reference.

Suggestion: replace direct class-name sends like `MyClass new` with `self class new` (instance side) or `self new` (class side).

______________________________________________________________________

### `isKindOf:` Usage

**Severity:** warning

Triggers when a method uses `isKindOf:` for type branching.

Suggestion: prefer dedicated predicate messages such as `isDictionary` (or other `isXxx` methods), or remove branching via polymorphism.

______________________________________________________________________

### Nil-Safe Branching

**Severity:** warning

Triggers when a method uses `isNil` or `notNil` combined with `ifTrue:` / `ifFalse:` instead of the dedicated nil-safe messages.

| Detected pattern                      | Preferred alternative          |
| ------------------------------------- | ------------------------------ |
| `isNil ifTrue: [...]`                 | `ifNil: [...]`                 |
| `notNil ifTrue: [...]`                | `ifNotNil: [...]`              |
| `isNil ifFalse: [...]`                | `ifNotNil: [...]`              |
| `notNil ifFalse: [...]`               | `ifNil: [...]`                 |
| `isNil ifTrue: [...] ifFalse: [...]`  | `ifNil: [...] ifNotNil: [...]` |
| `isNil ifFalse: [...] ifTrue: [...]`  | `ifNil: [...] ifNotNil: [...]` |
| `notNil ifTrue: [...] ifFalse: [...]` | `ifNil: [...] ifNotNil: [...]` |
| `notNil ifFalse: [...] ifTrue: [...]` | `ifNil: [...] ifNotNil: [...]` |

Two-branch patterns (`ifTrue:ifFalse:` / `ifFalse:ifTrue:`) are reported as a single issue suggesting `ifNil:ifNotNil:`.

______________________________________________________________________

### Collection Branching

**Severity:** warning

Triggers when a method uses `isEmpty` or `notEmpty` combined with `ifTrue:` / `ifFalse:` instead of the dedicated collection branching messages.

| Detected pattern                        | Preferred alternative              |
| --------------------------------------- | ---------------------------------- |
| `isEmpty ifTrue: [...]`                 | `ifEmpty: [...]`                   |
| `notEmpty ifTrue: [...]`                | `ifNotEmpty: [...]`                |
| `isEmpty ifFalse: [...]`                | `ifNotEmpty: [...]`                |
| `notEmpty ifFalse: [...]`               | `ifEmpty: [...]`                   |
| `isEmpty ifTrue: [...] ifFalse: [...]`  | `ifEmpty: [...] ifNotEmpty: [...]` |
| `isEmpty ifFalse: [...] ifTrue: [...]`  | `ifEmpty: [...] ifNotEmpty: [...]` |
| `notEmpty ifTrue: [...] ifFalse: [...]` | `ifEmpty: [...] ifNotEmpty: [...]` |
| `notEmpty ifFalse: [...] ifTrue: [...]` | `ifEmpty: [...] ifNotEmpty: [...]` |

Two-branch patterns (`ifTrue:ifFalse:` / `ifFalse:ifTrue:`) are reported as a single issue suggesting `ifEmpty:ifNotEmpty:`.

______________________________________________________________________

### Idiomatic Collection Access

**Severity:** warning

Triggers when a method uses `at:` with a small integer literal or a collection size expression where a dedicated accessor message is available.

#### `at: N` → positional accessor

| Detected pattern | Preferred alternative |
| ---------------- | --------------------- |
| `col at: 1`      | `col first`           |
| `col at: 2`      | `col second`          |
| `col at: 3`      | `col third`           |
| `col at: 4`      | `col fourth`          |
| `col at: 5`      | `col fifth`           |
| `col at: 6`      | `col sixth`           |

`at:put:`, `at:ifAbsent:`, and similar multi-keyword forms are excluded.
Arithmetic in the argument (e.g. `at: 1 + offset`) is also excluded.

#### `at: <collection> size` → `last`

| Detected pattern     | Preferred alternative |
| -------------------- | --------------------- |
| `col at: col size`   | `col last`            |
| `col at: (col size)` | `col last`            |

Expressions with arithmetic after `size` (e.g. `at: col size - 1`) are excluded.
