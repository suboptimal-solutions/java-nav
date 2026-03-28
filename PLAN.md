# CLI tools for IDE-like Java navigation in AI agents

**Eclipse JDT Language Server (jdtls) is the strongest single tool for giving an AI agent full semantic Java navigation**, but a layered approach combining lightweight JDK tools (`javap`, `jdeps`), Maven plugins, `ripgrep`, and a small ClassGraph wrapper delivers **80% of the value at 10% of the complexity** — with jdtls reserved for queries that demand compiler-level accuracy. No single tool covers all four capabilities well as a simple CLI command, so the practical answer is a composite toolkit orchestrated by a shell skill.

The landscape splits cleanly into three tiers: zero-setup JDK/Maven tools that work instantly, a small custom bytecode scanner for type-hierarchy queries, and a persistent LSP server for full semantic analysis. Several projects already wrap jdtls for AI agents (multilspy, JavaLens MCP, LSP4J-MCP), but since the user wants a Claude Code *skill* (shell commands, not MCP), the right architecture is a set of shell scripts that call the lightweight tools directly and optionally communicate with a background jdtls process for semantic queries.

---

## The lightweight tier handles most queries instantly

Three JDK/Maven tools combine to cover "get API surface," "get source code," and crude "find usages" with **zero additional setup** beyond a working Maven project.

**`javap` is the hidden gem for API surface extraction.** Given any class on the compiled classpath, it prints public methods, fields, constructors, and generic signatures in a clean, AI-consumable format:

```bash
CP=$(mvn -q dependency:build-classpath -DincludeScope=compile -Dmdep.outputFile=/dev/stdout):target/classes
javap -public -cp "$CP" com.example.service.UserService
```

Output is concise — typically **10–30 lines per class** — showing full method signatures with parameter types, return types, and generic type parameters. This directly answers "what can I call on this class?" without parsing source code. It works for project classes *and* every dependency JAR on the classpath, including JDK classes.

**`mvn dependency:unpack-dependencies` enables source-level search across dependencies.** Running `mvn dependency:unpack-dependencies -Dclassifier=sources -DoutputDirectory=target/dep-sources -DfailOnMissingClassifierArtifact=false` extracts all dependency `.java` files into a flat directory. Combined with `ripgrep`, this enables text-based "find usages" across the entire dependency tree:

```bash
rg --json -tjava "\.methodName\(" src/ target/dep-sources/
```

Ripgrep's `--json` flag outputs structured results (file, line number, match offset) perfect for AI consumption. It searches thousands of files in sub-seconds. The obvious limitation is **text matching, not type resolution** — `rg "\.save\("` returns every `.save()` call regardless of receiver type. For common method names, this produces noise. For distinctive names or class-level patterns (`implements MyInterface`, `extends BaseProcessor`), it works surprisingly well.

**`mvn dependency:build-classpath`** is the foundation command that makes everything else work. It resolves the full transitive dependency tree and outputs a classpath string usable with `javap`, `jdeps`, `jshell`, and custom Java tools. The resolved classpath is **cached to `target/java-nav/classpath.txt`** so that subsequent calls are instant. The cache is invalidated automatically when `pom.xml` is newer than the cache file (mtime comparison). Storing the cache under `target/` ensures it is auto-ignored by `.gitignore` in every standard Java project and cleaned up by `mvn clean`.

---

## ClassGraph fills the "find implementations" gap cheaply

Text search cannot reliably find all implementations of an interface — a class implementing `Serializable` doesn't necessarily contain the text "implements Serializable" if it inherits the implementation. **ClassGraph**, a fast bytecode-scanning library, solves this with ~50 lines of custom Java:

```java
// FindImplementations.java — run via mvn exec:java
try (ScanResult scan = new ClassGraph()
        .enableClassInfo().enableMethodInfo()
        .overrideClasspath(classpathString).scan()) {
    scan.getClassesImplementing("com.example.MyInterface")
        .forEach(ci -> System.out.println(ci.getName()));
}
```

ClassGraph reads `.class` files directly (no class loading), handles the full type hierarchy including transitive inheritance, and scans the entire Maven classpath in **1–3 seconds** for typical projects. It cannot find *method-level* usages, but for "which classes implement this interface?" and "which classes extend this base class?" it's **more accurate than any text-search approach** and far lighter than a full LSP server. A compiled wrapper JAR invocable as `java -cp tool.jar:$CP tools.FindImpls com.example.MyInterface` integrates cleanly into a shell skill.

For even quicker structural queries without compilation, **ast-grep** (`sg`) provides tree-sitter-based pattern matching:

```bash
sg -p 'class $NAME implements $IFACE { $$$ }' -l java --json
sg -p 'public $RET $NAME($$$PARAMS) { $$$ }' -l java --json
```

ast-grep is blazing fast and produces structured JSON, but it operates on syntax trees without type resolution — it can't follow inheritance chains or distinguish overloaded methods. Best used as a complement to ClassGraph, not a replacement.

---

## jdtls delivers full semantic analysis when accuracy matters

Eclipse JDT Language Server provides **compiler-level Java intelligence** matching what IntelliJ or Eclipse offer. All four capabilities map directly to LSP methods:

| Capability | LSP method | Output |
|---|---|---|
| Find all usages/references | `textDocument/references` | List of file:line:column locations |
| Find implementations | `textDocument/implementation` + `textDocument/typeHierarchy` | Implementing class locations |
| Get API surface | `textDocument/documentSymbol` | Hierarchical symbol tree with kinds, ranges |
| Get source code | `textDocument/definition` + `java/classFileContents` | Source or decompiled bytecode |

jdtls **auto-imports Maven projects** via M2Eclipse, downloads dependencies, resolves the full type system including generics, annotations, and overloaded methods. The custom `java/classFileContents` endpoint even decompiles `.class` files in dependency JARs when source JARs aren't available.

The challenge is **invocation from shell scripts**. jdtls communicates via JSON-RPC over stdio, requiring a persistent process with proper initialization. Three viable approaches exist for wrapping it:

**Microsoft's multilspy** (Python library, NeurIPS 2023) is the most practical wrapper. It manages jdtls lifecycle, handles LSP initialization, and exposes clean Python methods:

```python
from multilspy import SyncLanguageServer, MultilspyConfig
config = MultilspyConfig.from_dict({"code_language": "java"})
lsp = SyncLanguageServer.create(config, logger, "/path/to/project/")
with lsp.start_server():
    refs = lsp.request_references("src/main/java/Foo.java", line, col)
```

A thin CLI wrapper around multilspy (~100 lines of Python) would accept commands like `java-nav references src/Foo.java 42 10` and output JSON results. The key design decision is **keeping jdtls as a persistent background daemon** rather than starting/stopping per query — first startup takes **30 seconds to 2+ minutes** for Maven dependency resolution and indexing, but subsequent queries resolve in **50–200ms**. Use a Unix socket or simple file-based IPC to communicate between the CLI script and the persistent server process.

**Startup and resource costs are significant.** jdtls requires **Java 21+ runtime**, allocates **1–2 GB of heap**, and the initial indexing of a large Maven project can take over a minute. The `-data` directory must be persisted between restarts to avoid full reindexing. For a Claude Code skill, this means the skill should include an `init` command that starts the jdtls daemon and waits for indexing to complete, with subsequent navigation commands connecting to the running daemon.

---

## Existing projects purpose-built for AI agent Java navigation

Several projects already solve this exact problem, though most use MCP rather than plain CLI:

**JavaLens MCP** (`pzalutski-pixel/javalens-mcp`) is the most comprehensive, offering **56 semantic analysis tools** built directly on Eclipse JDT Core via OSGi/Equinox. It provides `find_references` with 16 fine-grained reference types (casts, annotations, throws, catch blocks, instanceof, method references), `find_implementations`, `analyze_type`, and `search_symbols`. It doesn't modify the project and creates a separate JDT workspace for indexing.

**`@mariozechner/lsp-cli`** (npm package) wraps LSP servers into a CLI that outputs structured JSON with class hierarchies, methods, fields, type parameters, and supertypes. It supports Java via jdtls and is designed for exactly this use case — run `lsp-cli /path/to/project java types.json`.

**The archived `lsp-client/lsp-cli`** (Python, LSAP protocol) was explicitly designed for AI agents with commands like `lsp reference --locate "models.py@UserClass"`. It included an **Agent Skill file** (`SKILL.md`) that instructed AI agents to prefer LSP over grep. Though archived in January 2026, its architecture — background server manager, unified `--locate` syntax, token-optimized output — is the right model to follow.

**GitHub Copilot CLI's Java LSP plugin** (`jdubois/java-lsp-eclipse-jdt-ls`) demonstrated that the LSP approach **reduces token usage by 50–70%** compared to grep-only navigation, because LSP returns precise, structured results (3 locations) versus grep returning hundreds of noisy text matches.

Claude Code itself has **native LSP tool support** (since v2.0.74+, enabled via `ENABLE_LSP_TOOL=1` environment variable), with jdtls plugins available from `Piebald-AI/claude-code-lsps` and the official Anthropic marketplace. However, users report reliability issues, and the skill-based approach gives more control over output formatting and tool composition.

---

## Tools that don't justify their complexity

**IntelliJ IDEA headless mode** cannot perform code navigation from CLI. The `idea inspect` command runs inspections only. JetBrains added a built-in MCP server in IntelliJ 2025.2, but it requires a running GUI IDE instance — not suitable for headless CLI use. A third-party plugin (`jetbrains-index-mcp-plugin`) exposes find-usages and find-implementations via HTTP, but still needs a running IntelliJ process consuming **2+ GB of RAM**.

**OpenGrok** requires a Java servlet container (Tomcat), Lucene indexing, and a web server. It's designed for large organizations indexing many repositories. The REST API could theoretically be queried from scripts, but setup overhead is extreme for a single project. Modern versions removed the old CLI search tool.

**Sourcegraph CLI (`src`)** is a thin client requiring a Sourcegraph server instance. There is no local-only mode. The **scip-java** indexer it uses is excellent — it hooks into `javac` as a compiler plugin and produces a highly accurate SCIP index — but the index can only be queried through Sourcegraph's server or by parsing the Protobuf directly. The experimental `scip expt-convert` command converts to SQLite, but the schema stores occurrences as opaque blobs, making ad-hoc queries difficult.

**JavaParser/java-symbol-solver** is a pure Java library with no CLI. Building a custom wrapper is feasible but the symbol solver has **known issues with generics** (GitHub issues #2397, #3034), incomplete lambda type inference, and requires manual JAR registration. For the effort of building a custom tool, jdtls via multilspy provides strictly better accuracy.

**Universal Ctags** generates definitions well (with `inherits` field for inheritance tracking and JSON output mode), but **cannot find references/usages** — only where symbols are defined. GNU Global adds token-based reference tracking via `global -rx symbol`, but it's text-level matching without type awareness. Neither tool can index inside JAR files. **cscope** is C-centric and handles Java poorly.

---

## Recommended architecture for a Claude Code skill

The optimal design is a **three-tier shell skill** where the AI agent picks the lightest tool that can answer each query:

**Tier 1 — Instant commands (no daemon, no indexing):**
- `java-nav api com.example.UserService` → runs `javap -public` with Maven classpath
- `java-nav source com.example.UserService` → locates and cats the source file from `src/` or unpacked dependency sources
- `java-nav grep "methodName" [--deps]` → ripgrep across project and optionally dependency sources
- `java-nav deps com.example.UserService` → runs `jdeps` for class-level dependency graph

All Tier 1 commands share a cached classpath resolved from Maven. The cache lives in `target/java-nav/classpath.txt` and auto-invalidates when `pom.xml` changes. Dependency source unpacking (`mvn dependency:unpack-dependencies`) is triggered lazily on first use of `grep --deps` or `source` for a dependency class — no separate `init-sources` step required.

**Tier 2 — Fast bytecode scan (~2s):**
- `java-nav impls com.example.MyInterface` → ClassGraph scan of compiled classpath
- `java-nav subtypes com.example.BaseClass` → ClassGraph subclass scan

**Tier 3 — Full semantic (requires running daemon):**
- `java-nav start` → starts jdtls via multilspy, waits for indexing
- `java-nav refs src/main/java/Foo.java 42 10` → LSP textDocument/references
- `java-nav hierarchy com.example.MyInterface` → LSP textDocument/typeHierarchy
- `java-nav symbols src/main/java/Foo.java` → LSP textDocument/documentSymbol

This layered approach means **most queries complete in under a second** with zero daemon overhead, while the full power of jdtls remains available for semantic queries where text search would produce too much noise. The skill's `SKILL.md` should instruct the AI agent to prefer Tier 1 for broad exploration and Tier 3 for precise "find all callers of this specific overloaded method" queries.

### Caching strategy

All expensive operations cache their results under `target/java-nav/` inside the Java project directory:

| Cache file | Produced by | Invalidated when |
|---|---|---|
| `classpath.txt` | `mvn dependency:build-classpath` | `pom.xml` mtime > cache mtime |
| `dep-sources/` | `mvn dependency:unpack-dependencies` | `pom.xml` mtime > cache mtime |

Storing caches under `target/` means they are automatically ignored by `.gitignore`, cleaned up by `mvn clean`, and scoped per-project. No user action is needed to populate or refresh caches — they are created lazily on first use and re-created when stale.

## Conclusion

The Java tooling ecosystem has no single CLI tool that matches IDE navigation quality out of the box. But the building blocks exist and compose well. `javap` for API surface, ClassGraph for type hierarchy, and jdtls for semantic references cover all four capabilities with compiler-level accuracy. The key architectural insight is that **jdtls should be a persistent background daemon, not started per-query** — its 30-second+ startup is amortized to near-zero over a coding session. The lightweight tools (`javap`, ripgrep, ClassGraph) handle the majority of queries where startup latency matters. Expensive operations (classpath resolution, dependency source unpacking) are cached under `target/java-nav/` and lazily invalidated via `pom.xml` mtime — no manual setup commands needed. For anyone building this today, starting with multilspy as the jdtls wrapper and a 50-line ClassGraph scanner as the implementation finder, fronted by a Python CLI (distributed via `uvx`) that routes queries to the appropriate tier, would yield a working system in a day or two of development.