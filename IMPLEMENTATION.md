# Implementation Plan — Tier 1 & Tier 2 (everything except jdtls)

## Current state

Done:
- `java-nav api <class>` — javap wrapper (Tier 1)
- `classpath.py` — Maven classpath resolution with `target/java-nav/classpath.txt` caching
- Playground Java project for testing
- Test suite (9 tests passing)

## What to build

### 1. Shared: lazy dependency source unpacking (`classpath.py`)

Add `ensure_dep_sources(project_dir)` to `classpath.py`. Runs `mvn dependency:unpack-dependencies -Dclassifier=sources` into `target/java-nav/dep-sources/`. Same mtime-based cache invalidation as classpath. Returns the path to the unpacked sources dir. Used by `source` and `grep --deps`.

Files: `src/java_nav/classpath.py`

### 2. Tier 1: `java-nav source <class>`

Locates and prints source code for a class.

Logic:
1. Convert fully qualified class name to path (`com.example.Foo` → `com/example/Foo.java`)
2. Search in `src/main/java/` first (project source)
3. If not found, call `ensure_dep_sources()` and search in `target/java-nav/dep-sources/`
4. Print the file content with line numbers
5. Optional `--line` / `-l` to show a specific line range (e.g. `-l 10:30`)

Files: `src/java_nav/commands/source.py`, tests

### 3. Tier 1: `java-nav grep <pattern>`

Ripgrep wrapper for searching Java source code.

Logic:
1. Default: search `src/` with `-tjava`
2. `--deps` flag: also search `target/java-nav/dep-sources/` (lazy unpack)
3. `--test` flag: also search `src/test/`
4. Pass through to `rg --json` for structured output, then format for readability
5. Supports ripgrep regex patterns as-is

Files: `src/java_nav/commands/grep.py`, tests

### 4. Tier 1: `java-nav deps <class>`

jdeps wrapper for class-level dependency analysis.

Logic:
1. Resolve classpath
2. Run `jdeps -verbose:class -cp $CP <class>`
3. Parse and display which classes this class depends on
4. Optional `--package` flag for package-level summary (`jdeps -s`)

Files: `src/java_nav/commands/deps.py`, tests

### 5. Tier 2: ClassGraph Java wrapper

Small Java tool that uses ClassGraph to scan bytecode for type hierarchy queries.

Logic:
- Single Java file `FindTypes.java` with two modes:
  - `impls <classname>` — find all classes implementing an interface
  - `subtypes <classname>` — find all subclasses of a class
- Output: one fully-qualified class name per line (simple, grep-friendly)
- Build as a standalone Maven project under `tools/classgraph-scanner/` with `mvn package` producing a fat JAR
- The fat JAR is checked into the repo (or built on first use) so `uvx java-nav` works without Maven on the tool side

Files: `tools/classgraph-scanner/pom.xml`, `tools/classgraph-scanner/src/.../FindTypes.java`

### 6. Tier 2: `java-nav impls <class>`

Python command wrapping the ClassGraph scanner.

Logic:
1. Resolve classpath
2. Run `java -cp scanner.jar:$CP tools.FindTypes impls <classname>`
3. Print results

Files: `src/java_nav/commands/impls.py`, tests

### 7. Tier 2: `java-nav subtypes <class>`

Same as impls but calls `subtypes` mode. Could be a flag on `impls` or a separate command.

Decision: make it `java-nav impls <class>` and `java-nav subtypes <class>` — two commands, both thin wrappers around FindTypes with different mode argument.

Files: `src/java_nav/commands/impls.py` (both commands), tests

## Implementation order

```
1. ensure_dep_sources() in classpath.py     — foundation for source + grep
2. source command                            — simple, high value
3. grep command                              — high value for AI agents
4. deps command                              — straightforward jdeps wrapper
5. ClassGraph scanner (Java tool)            — build the JAR
6. impls + subtypes commands                 — wire up the JAR
```

Each step: implement → add tests → wire into cli.py → verify.

## Playground additions needed

The current playground is good for Tier 1 testing. For Tier 2 (impls/subtypes), consider adding:
- A second `Repository` implementation (e.g. `FileUserRepository`) to test finding multiple implementations
- A class hierarchy (e.g. `AbstractProcessor` → `EmailProcessor`, `SmsProcessor`) to test subtypes

## Verification

After each command:
- `uv run pytest -v` — all tests pass
- Manual smoke test against playground
- `uv run java-nav --help` — new command appears
