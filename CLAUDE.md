# java-nav Development Guide

CLI tools for IDE-like Java navigation in AI agents. Python + Click, distributed via `uvx`.

## Quick reference

```bash
uv sync                      # install deps
uv run pytest -v             # unit tests (25 tests, ~10s)
uv run pytest -m integration # integration tests against spring-petclinic (12 tests, ~90s)
uv run pytest -m ''          # all 37 tests
uv run ruff check src/ tests/   # lint
uv run ruff format src/ tests/  # format
```

## Architecture

Three-tier design — agent picks the lightest tool for each query:

- **Tier 1 (instant):** `api` (javap), `source` (file lookup), `grep` (ripgrep/grep), `deps` (jdeps)
- **Tier 2 (~2s):** `impls`, `subtypes` (ClassGraph bytecode scan via bundled JAR)
- **Tier 3 (not yet implemented):** LSP semantic queries via multilspy/jdtls

All commands share `classpath.py:resolve_classpath()` for Maven classpath caching.

## Key files

- `src/java_nav/cli.py` — entry point, wires all commands
- `src/java_nav/classpath.py` — classpath resolution + dep source unpacking (both cached in `target/java-nav/`)
- `src/java_nav/commands/` — one file per command
- `src/java_nav/jars/classgraph-scanner.jar` — bundled fat JAR for Tier 2
- `src/java_nav/java-nav/SKILL.md` — skill template installed by `install-skill` command
- `tools/classgraph-scanner/` — Maven project that builds the scanner JAR
- `playground/` — small Maven project used as unit test fixture
- `tests/fixtures/spring-petclinic` — git submodule for integration tests

## Caching

Cached in `target/java-nav/` inside the Java project being analyzed:
- `classpath.txt` — Maven classpath string
- `dep-sources/` — unpacked dependency source JARs

Both auto-invalidate when `pom.xml` mtime > cache mtime. Cleaned by `mvn clean`.

## Building the scanner JAR

After editing `tools/classgraph-scanner/src/main/java/tools/FindTypes.java`:

```bash
cd tools/classgraph-scanner && mvn -q package
cp target/classgraph-scanner-1.0.jar ../../src/java_nav/jars/classgraph-scanner.jar
```

## Installing locally

```bash
uv tool install --force .
```

## Test fixtures

- **playground/**: Auto-compiled by `tests/conftest.py`. Has `Repository<T>` interface with 2 implementations, `AbstractProcessor` with 2 subclasses, and `UserService` using Guava.
- **spring-petclinic**: Git submodule. Init with `git submodule update --init`. Has `BaseEntity` hierarchy (8 subtypes), Spring `Repository` implementations, controllers with Spring annotations.

## Code style

- ruff with E, W, F, I, UP, B, SIM rules
- Line length: 100
- Target: Python 3.10
- No docstrings on test functions
- All commands use Click decorators and accept `-d/--project-dir`

## What's not implemented yet

- **Tier 3 (jdtls/LSP):** `start`, `refs`, `hierarchy`, `symbols` commands via multilspy
- **Gradle support:** Currently Maven-only
