# Implementation Status

## Completed

### Tier 1 — Instant commands
- [x] `classpath.py` — Maven classpath resolution + dep source unpacking, both cached in `target/java-nav/`
- [x] `api` — javap wrapper (`-public/-protected/-private`)
- [x] `source` — locate and display source from project or dependencies (`-l` line range)
- [x] `grep` — ripgrep/grep with `--deps` and `--test` flags
- [x] `deps` — jdeps wrapper with `--package` flag

### Tier 2 — Bytecode scanning
- [x] ClassGraph scanner JAR (`tools/classgraph-scanner/` → `src/java_nav/jars/classgraph-scanner.jar`)
- [x] `impls` — find all implementations of an interface
- [x] `subtypes` — find all subclasses

### Infrastructure
- [x] `install-skill` — writes `.claude/skills/java-nav/SKILL.md` into target project
- [x] Playground test fixture (Repository interface × 2 impls, AbstractProcessor × 2 subtypes, UserService + Guava)
- [x] spring-petclinic integration tests (12 tests via git submodule)
- [x] ruff lint + format
- [x] pytest with integration marker separation

## Not yet implemented

### Tier 3 — LSP semantic queries (jdtls via multilspy)
- [ ] `start` — start jdtls daemon, wait for indexing
- [ ] `stop` — stop daemon
- [ ] `refs <file> <line> <col>` — find all references (textDocument/references)
- [ ] `hierarchy <class>` — type hierarchy (textDocument/typeHierarchy)
- [ ] `symbols <file>` — document symbols (textDocument/documentSymbol)

Requires: `multilspy` Python package, JDK 21+ for jdtls, persistent daemon with PID file management.

### Other future work
- [ ] Gradle support (currently Maven-only)
- [ ] PyPI/npm publishing
- [ ] Inner class support for `source` command (e.g. `Foo.Bar` → `Foo.java`)
