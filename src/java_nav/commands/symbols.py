"""Tier 3: list all symbols in a Java file."""

import os
import sys

import click

from java_nav.lsp.client import SYMBOL_KINDS, _flatten_symbols, query


@click.command()
@click.argument("file")
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Maven project root.",
)
def symbols(file: str, project_dir: str) -> None:
    """List all symbols defined in a Java file.

    FILE is a path relative to the project root,
    e.g. src/main/java/com/example/service/UserService.java.
    Shows classes, methods, fields, and constructors with line numbers.
    """
    project_dir = os.path.abspath(project_dir)

    abs_path = os.path.join(project_dir, file)
    if not os.path.isfile(abs_path):
        print(f"File not found: {file}", file=sys.stderr)
        print(
            "Path must be relative to the project root, "
            "e.g. src/main/java/com/example/MyClass.java",
            file=sys.stderr,
        )
        sys.exit(1)

    result = query(project_dir, "document_symbols", {"file": file})
    flat = _flatten_symbols(result)

    if not flat:
        print(f"No symbols found in {file}.", file=sys.stderr)
        print("Ensure jdtls has finished indexing (try java-nav lsp start first).", file=sys.stderr)
        return

    for sym in flat:
        kind_num = sym.get("kind", 0)
        kind = SYMBOL_KINDS.get(kind_num, f"kind:{kind_num}")
        name = sym.get("name", "?")
        line = sym.get("selectionRange", sym.get("range", {})).get("start", {}).get("line", 0) + 1
        detail = sym.get("detail", "")
        suffix = f"  {detail}" if detail else ""
        print(f"{line:4d}  {kind:12s}  {name}{suffix}")
