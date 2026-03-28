# Implementation Status

## Completed

### Tier 1 — Instant commands
- [x] `classpath.py` — Maven classpath resolution cached in `target/java-nav/classpath.txt`
- [x] `classpath.py` — Per-JAR dependency source extraction (finds `-sources.jar` in `~/.m2/`, extracts only what's needed)
- [x] `classpath.py` — `find_source_roots()` auto-discovers source dirs in multi-module Maven projects
- [x] `api` — javap wrapper (`-public/-protected/-private`), clear error on class not found
- [x] `source` — locate source from project or deps, line ranges (`-l`), javap fallback when no source JAR
- [x] `grep` — ripgrep/grep with `--deps` and `--test`, multi-module aware, helpful "no matches" message with hints
- [x] `deps` — jdeps wrapper with `--package`, searches submodule `target/classes/` too

### Tier 2 — Bytecode scanning
- [x] ClassGraph scanner JAR (`tools/classgraph-scanner/` → `src/java_nav/jars/classgraph-scanner.jar`)
- [x] `impls` — find all implementations of an interface
- [x] `subtypes` — find all subclasses

### Tier 3 — LSP semantic queries (jdtls via multilspy)
- [x] `lsp start/stop/status` — persistent jdtls daemon with PID+port file management
- [x] `refs` — find all references, text-based input (`Class.method`), resolves to position internally
- [x] `def` — go to definition, shows source context around definition
- [x] `find` — semantic workspace symbol search (classes, interfaces, enums)
- [x] `symbols` — document symbols with line numbers and kinds
- [x] On-demand mode (no daemon, ~5-15s per query) + daemon mode (<200ms per query)

### Infrastructure
- [x] `install-skill` — writes `.claude/skills/java-nav/SKILL.md` with strict agent rules
- [x] Playground test fixture (Repository × 2 impls, AbstractProcessor × 2 subtypes, UserService + Guava)
- [x] spring-petclinic integration tests (12 tests via git submodule)
- [x] LSP integration tests (8 tests against playground)
- [x] ruff lint + format (E, W, F, I, UP, B, SIM)
- [x] pytest with integration marker separation (26 unit + 20 integration)
- [x] Agent-friendly error messages on all commands (no silent failures)
- [x] Multi-module Maven support (grep, source, deps)

## Not yet implemented

- [ ] Gradle support (currently Maven-only)
- [ ] Inner class support for `source` (`Foo.Bar` → `Foo.java`)
- [ ] typeHierarchy via LSP (multilspy doesn't expose; ClassGraph covers most cases)
- [ ] Deep multi-module (only scans one level of submodules)
- [ ] PyPI publishing
