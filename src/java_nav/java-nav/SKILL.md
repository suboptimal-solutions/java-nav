---
name: java-nav
description: IDE-like Java code navigation CLI. Use when exploring Java classes, finding implementations, searching source code, or analyzing dependencies.
---

# java-nav — Java code navigation

This project has `java-nav` CLI installed for IDE-like Java navigation.
Use it instead of grep when exploring Java code — it's faster and more accurate.

## Commands (use `-d <path>` if not in project root)

### Tier 1 — Instant
```bash
java-nav api <class>                # Public API surface (methods, fields, generics)
java-nav source <class>             # Show source code (project + dependencies)
java-nav source <class> -l 10:30   # Show specific line range
java-nav grep "pattern"             # Search project Java sources
java-nav grep "pattern" --deps      # Also search dependency sources
java-nav deps <class>               # Class-level dependency graph
```

### Tier 2 — Bytecode scan (~2s)
```bash
java-nav impls <interface>          # Find all implementations
java-nav subtypes <class>           # Find all subclasses
```

## When to use which command

- **"What methods does X have?"** → `java-nav api`
- **"Show me the code for X"** → `java-nav source`
- **"Where is X used?"** → `java-nav grep`
- **"What depends on X?"** → `java-nav deps`
- **"Who implements X?"** → `java-nav impls`
- **"Who extends X?"** → `java-nav subtypes`

## Notes

- All class names are fully qualified: `com.example.service.UserService`
- Works for project classes, dependency JARs, and JDK stdlib
- Results are cached in `target/java-nav/` (auto-invalidates when pom.xml changes)
- Requires: JDK 17+, Maven
