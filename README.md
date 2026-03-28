# java-nav

CLI tools for IDE-like Java navigation in AI agents.

Gives AI coding agents (Claude Code, etc.) fast, accurate Java code navigation
without requiring a running IDE. Three-tier architecture: instant JDK tool wrappers,
ClassGraph bytecode scanning for type hierarchy, and jdtls LSP for semantic queries.

## Prerequisites

**Required:**
- **JDK 17+** — provides `javap`, `jdeps`, and `java` runtime
- **Maven** — for classpath resolution and dependency management
- **Python 3.10+** — runtime for the CLI itself

**Optional:**
- **JDK 21+** — required for Tier 3 LSP commands (`refs`, `def`, `find`, `symbols`)
- **ripgrep** (`rg`) — faster search in `grep` command; falls back to GNU `grep` if not installed

## Getting started

```bash
# Install
uv tool install java-nav

# Or run without installing
uvx java-nav --help

# Navigate to your Java project and try it
cd /path/to/your/java/project
mvn compile                              # ensure project is compiled
java-nav api com.example.UserService     # see what methods are available
java-nav impls com.example.Repository    # find all implementations

# Install AI agent skill (writes .claude/skills/java-nav/SKILL.md)
java-nav install-skill
```

## Usage

All commands accept `-d <path>` to specify the Maven project directory (defaults to `.`).
All class names are fully qualified (e.g. `com.example.service.UserService`).
Works with multi-module Maven projects — source directories are auto-discovered.

### Tier 1 — Instant commands

```bash
# Show public API surface of a class (project, dependency, or JDK)
java-nav api com.example.UserService
java-nav api java.util.List

# Show source code with optional line range (falls back to javap if no source JAR)
java-nav source com.example.UserService
java-nav source com.example.UserService -l 10:30

# Search Java source code (uses ripgrep if available, falls back to grep)
java-nav grep "methodName"
java-nav grep --deps "checkArgument"    # also search dependency sources
java-nav grep --test "TestHelper"       # also search test sources

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

### Tier 3 — Semantic queries (jdtls via multilspy)

```bash
# Find all references to a symbol (type-aware, not text search)
java-nav refs com.example.UserService.createUser

# Go to definition, show source context
java-nav def com.example.UserService.createUser

# Search symbols by name (classes, interfaces, enums)
java-nav find Repository

# List all symbols in a file with line numbers
java-nav symbols src/main/java/com/example/service/UserService.java
```

For faster Tier 3 queries, start the daemon:
```bash
java-nav lsp start    # ~30s first time, then <200ms per query
java-nav lsp status   # check daemon
java-nav lsp stop     # shutdown
```

### AI agent skill

```bash
# Install SKILL.md into your project for Claude Code auto-discovery
java-nav install-skill

# Overwrite existing skill file
java-nav install-skill --force
```

This writes `.claude/skills/java-nav/SKILL.md` which Claude Code reads automatically,
teaching it when and how to use each command — with strict rules to prevent the agent
from falling back to grep/manual file browsing.

## Caching

Expensive operations are cached in `target/java-nav/` inside your Java project:

| Cache | What | Invalidated when |
|---|---|---|
| `classpath.txt` | Maven classpath string | `pom.xml` changes |
| `dep-sources/` | Per-JAR extracted source files | On demand (only requested JARs) |
| `dep-sources-all.marker` | Full dep source unpack flag | `pom.xml` changes |
| `jdtls.pid`, `jdtls.port` | LSP daemon state | `lsp stop` or process exit |

Caches are created lazily on first use. Run `mvn clean` to clear everything.

## Development

```bash
# Clone and install dev dependencies
git clone <repo-url>
cd java-nav
uv sync

# Run tests
uv run pytest -v                    # 26 unit tests (~10s)
uv run pytest -m integration        # 20 integration tests (~3-4min)
uv run pytest -m ''                 # all 46 tests

# Lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Build the ClassGraph scanner JAR (needed after changes to tools/)
cd tools/classgraph-scanner && mvn -q package
cp target/classgraph-scanner-1.0.jar ../../src/java_nav/jars/classgraph-scanner.jar

# Install locally for testing
uv tool install --force .
```
