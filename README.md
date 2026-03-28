# java-nav

CLI tools for IDE-like Java navigation in AI agents.

## Prerequisites

**Required:**
- **JDK 17+** — provides `javap`, `jdeps`, and `java` runtime
- **Maven** — for classpath resolution and dependency management
- **Python 3.10+** — runtime for the CLI itself

**Optional:**
- **ripgrep** (`rg`) — faster search in `grep` command; falls back to GNU `grep` if not installed

## Installation

```bash
# With uv (recommended)
uvx java-nav --help

# Or install globally
uv tool install java-nav

# Or with pip
pip install java-nav
```

## Usage

All commands accept `-d <path>` to specify the Maven project directory (defaults to `.`).

### Tier 1 — Instant commands

```bash
# Show public API surface of a class (project, dependency, or JDK)
java-nav api com.example.UserService
java-nav api java.util.List

# Show source code with optional line range
java-nav source com.example.UserService
java-nav source com.example.UserService -l 10:30

# Search Java source code (uses ripgrep if available)
java-nav grep "methodName"
java-nav grep --deps "checkArgument"    # also search dependency sources

# Show class-level dependencies
java-nav deps com.example.UserService
java-nav deps --package com.example.UserService   # package-level summary
```

### Tier 2 — Bytecode scanning (~2s)

```bash
# Find all implementations of an interface
java-nav impls com.example.Repository

# Find all subclasses of a class
java-nav subtypes com.example.AbstractProcessor
```

## Caching

Expensive operations are cached in `target/java-nav/` inside your Java project:

| Cache | Invalidated when |
|---|---|
| `classpath.txt` | `pom.xml` changes |
| `dep-sources/` | `pom.xml` changes |

Caches are created lazily on first use. Run `mvn clean` to clear them.
