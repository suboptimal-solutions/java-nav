# java-nav Development Guide

CLI tools for IDE-like Java navigation in AI agents. Python + Click, distributed via `uvx`.

## Quick reference

```bash
uv sync                      # install deps
uv run pytest -v             # unit tests (26 tests, ~10s)
uv run pytest -m integration # integration tests (12 petclinic + 8 LSP, ~3-4min)
uv run pytest -m ''          # all 46 tests
uv run ruff check src/ tests/   # lint
uv run ruff format src/ tests/  # format
uv tool install --force .       # install locally
```

## Architecture

Three-tier design — agent picks the lightest tool for each query:

- **Tier 1 (instant):** `api` (javap), `source` (file lookup + javap fallback), `grep` (ripgrep/grep), `deps` (jdeps)
- **Tier 2 (~2s):** `impls`, `subtypes` (ClassGraph bytecode scan via bundled JAR)
- **Tier 3 (~5-15s on-demand, <200ms with daemon):** `refs`, `def`, `find`, `symbols` (jdtls via multilspy)

All Tier 1/2 commands share `classpath.py:resolve_classpath()` for Maven classpath caching.
Tier 3 commands use jdtls via multilspy — on-demand by default, or via persistent daemon (`lsp start`).

## Key files

- `src/java_nav/cli.py` — entry point, wires all commands
- `src/java_nav/classpath.py` — classpath resolution, per-JAR dep source extraction, source root discovery (multi-module aware)
- `src/java_nav/commands/` — one file per command (api, source, grep, deps, impls, refs, definition, find, symbols, lsp_cmd, install)
- `src/java_nav/lsp/` — jdtls lifecycle: server.py (daemon), client.py (query routing), _daemon_proc.py (subprocess)
- `src/java_nav/jars/classgraph-scanner.jar` — bundled fat JAR for Tier 2
- `src/java_nav/java-nav/SKILL.md` — skill template installed by `install-skill` command
- `tools/classgraph-scanner/` — Maven project that builds the scanner JAR
- `playground/` — small Maven project used as unit test fixture
- `tests/fixtures/spring-petclinic` — git submodule for integration tests

## Multi-module Maven support

- `grep` and `source` auto-discover submodule source directories via `find_source_roots()` in classpath.py
- `deps` searches both root and submodule `target/classes/` directories
- Detection: checks for `<modules>` in pom.xml, scans subdirectories with their own pom.xml

## Caching & dependency sources

Cached in `target/java-nav/` inside the Java project being analyzed:
- `classpath.txt` — Maven classpath string (auto-invalidates when pom.xml changes)
- `dep-sources/` — per-JAR extracted source files (only the requested JAR, not all deps)
- `dep-sources-all.marker` — tracks whether full bulk unpack was done (for `grep --deps`)
- `jdtls.pid`, `jdtls.port` — daemon state (Tier 3)

`source` extracts only the single `-sources.jar` needed. `grep --deps` unpacks all deps (slower, one-time).
If source JAR doesn't exist, `source` falls back to javap output.

## Agent UX principles

Every command must give the agent clear guidance on failure:
- **What went wrong** — e.g. "Class not found: X" not raw tool stderr
- **What to try next** — e.g. "Try --deps to include dependency sources"
- **Multi-module hints** — e.g. "For multi-module projects, try -d <submodule-dir>"
- **No silent failures** — exit code 1 with no output is never acceptable

## Building the scanner JAR

After editing `tools/classgraph-scanner/src/main/java/tools/FindTypes.java`:

```bash
cd tools/classgraph-scanner && mvn -q package
cp target/classgraph-scanner-1.0.jar ../../src/java_nav/jars/classgraph-scanner.jar
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

- **Gradle support:** Currently Maven-only
- **Inner class support:** `source` command doesn't handle `Foo.Bar` → `Foo.java` resolution
- **typeHierarchy via LSP:** multilspy doesn't expose this; ClassGraph `impls`/`subtypes` covers most cases
- **Deep multi-module:** Only scans one level of submodules, not nested module hierarchies
