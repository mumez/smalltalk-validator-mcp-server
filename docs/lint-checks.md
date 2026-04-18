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
