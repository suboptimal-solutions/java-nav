"""Tier 3: semantic symbol search across the workspace."""

import os
import sys

import click

from java_nav.lsp.client import SYMBOL_KINDS, query


@click.command()
@click.argument("pattern")
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Maven project root.",
)
def find(pattern: str, project_dir: str) -> None:
    """Search for Java symbols by name.

    PATTERN is a symbol name or prefix, e.g. UserService, Owner, Repository.
    Uses jdtls workspace symbol search for semantic results (classes, interfaces, enums).
    """
    project_dir = os.path.abspath(project_dir)

    results = query(project_dir, "workspace_symbol", {"query": pattern})

    if not results:
        print(f"No symbols found for: {pattern}", file=sys.stderr)
        print("Note: find searches type names (classes, interfaces, enums).", file=sys.stderr)
        print("For text search, use: java-nav grep", file=sys.stderr)
        return

    for sym in results:
        kind_num = sym.get("kind", 0)
        kind = SYMBOL_KINDS.get(kind_num, f"kind:{kind_num}")
        name = sym.get("name", "?")
        container = sym.get("containerName", "")
        loc = sym.get("location", {})
        uri = loc.get("uri", "")
        line = loc.get("range", {}).get("start", {}).get("line", 0) + 1

        rel_path = uri.replace(f"file://{project_dir}/", "")
        fqn = f"{container}.{name}" if container else name
        print(f"{kind:12s}  {fqn}  ({rel_path}:{line})")
