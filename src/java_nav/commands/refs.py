"""Tier 3: find all references to a symbol — text-based input."""

import os
import sys

import click

from java_nav.lsp.client import query, resolve_symbol_to_position


@click.command()
@click.argument("symbol")
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Maven project root.",
)
def refs(symbol: str, project_dir: str) -> None:
    """Find all references to a Java symbol.

    SYMBOL is a class or class.method name, e.g. UserService or UserService.createUser.
    Uses jdtls for compiler-accurate results. Starts jdtls on-demand if no daemon is running.
    """
    project_dir = os.path.abspath(project_dir)

    # Split into class and optional method: "com.example.UserService.createUser"
    # The class name may contain dots, so find the split point by looking for
    # a lowercase-to-uppercase transition (method names start lowercase)
    parts = symbol.rsplit(".", 1)
    class_name = parts[0]
    method_name = parts[1] if len(parts) > 1 else None

    pos = resolve_symbol_to_position(project_dir, class_name, method_name)
    if pos is None:
        print(f"Symbol not found: {symbol}", file=sys.stderr)
        print(
            "Use fully qualified name: java-nav refs com.example.UserService.methodName",
            file=sys.stderr,
        )
        sys.exit(1)

    rel_path, line, col = pos
    results = query(project_dir, "references", {"file": rel_path, "line": line, "col": col})

    if not results:
        print(f"No references found for {symbol}.", file=sys.stderr)
        print("The symbol exists but is not referenced anywhere in the project.", file=sys.stderr)
        return

    for ref in results:
        rp = ref.get("relativePath", ref.get("uri", "?"))
        start = ref.get("range", {}).get("start", {})
        ln = start.get("line", 0) + 1  # 0-indexed → 1-indexed
        print(f"{rp}:{ln}")
