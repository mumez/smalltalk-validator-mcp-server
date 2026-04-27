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

Triggers when a method reads or writes an instance variable directly (without going through an accessor) outside of `accessing` or `initializing` categories.

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
