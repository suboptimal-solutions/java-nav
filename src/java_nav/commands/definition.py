"""Tier 3: go to definition of a symbol — text-based input."""

import os
import sys

import click

from java_nav.lsp.client import query, resolve_symbol_to_position


@click.command("def")
@click.argument("symbol")
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Maven project root.",
)
def definition(symbol: str, project_dir: str) -> None:
    """Go to definition of a Java symbol.

    SYMBOL is a class or class.method name, e.g. UserService or UserService.createUser.
    Shows the source code at the definition location.
    """
    project_dir = os.path.abspath(project_dir)

    parts = symbol.rsplit(".", 1)
    class_name = parts[0]
    method_name = parts[1] if len(parts) > 1 else None

    pos = resolve_symbol_to_position(project_dir, class_name, method_name)
    if pos is None:
        print(f"Symbol not found: {symbol}", file=sys.stderr)
        sys.exit(1)

    rel_path, line, col = pos

    # If just a class, show the file header
    if method_name is None:
        abs_path = os.path.join(project_dir, rel_path)
        if os.path.isfile(abs_path):
            print(f"// {rel_path}")
            with open(abs_path) as f:
                for i, text in enumerate(f, 1):
                    print(f"{i:4d}  {text}", end="")
        return

    # For methods, get definition via LSP to handle cross-file jumps
    results = query(project_dir, "definition", {"file": rel_path, "line": line, "col": col})

    if not results:
        # Fallback: show the method at the resolved position
        results = [{"relativePath": rel_path, "range": {"start": {"line": line}}}]

    for defn in results:
        rp = defn.get("relativePath", "")
        start_line = defn.get("range", {}).get("start", {}).get("line", 0)
        abs_path = os.path.join(project_dir, rp)
        if not os.path.isfile(abs_path):
            continue

        # Show context around the definition (up to 20 lines)
        print(f"// {rp}")
        with open(abs_path) as f:
            lines = f.readlines()
        begin = max(0, start_line)
        end = min(len(lines), start_line + 20)
        for i in range(begin, end):
            print(f"{i + 1:4d}  {lines[i]}", end="")
