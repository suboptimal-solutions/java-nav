"""Tier 1: search Java source code using ripgrep or grep fallback."""

import os
import shutil
import subprocess
import sys

import click

from java_nav.classpath import ensure_dep_sources


def _build_cmd(pattern: str, paths: list[str]) -> list[str]:
    """Build search command, preferring rg over grep."""
    if shutil.which("rg"):
        return ["rg", "-n", "--type", "java", pattern] + paths
    return [
        "grep", "-rn", "--include=*.java", pattern,
    ] + paths


@click.command()
@click.argument("pattern")
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Maven project root.",
)
@click.option(
    "--deps",
    is_flag=True,
    help="Also search unpacked dependency sources.",
)
@click.option(
    "--test",
    "include_test",
    is_flag=True,
    help="Also search test sources.",
)
def grep(pattern: str, project_dir: str, deps: bool, include_test: bool) -> None:
    """Search Java source code for a pattern.

    PATTERN is a regex pattern. Uses ripgrep if available, falls back to grep.
    """
    project_dir = os.path.abspath(project_dir)

    paths = [os.path.join(project_dir, "src", "main")]
    if include_test:
        test_dir = os.path.join(project_dir, "src", "test")
        if os.path.isdir(test_dir):
            paths.append(test_dir)

    if deps:
        dep_sources = ensure_dep_sources(project_dir)
        if dep_sources and os.path.isdir(dep_sources):
            paths.append(dep_sources)

    # Filter to paths that actually exist
    paths = [p for p in paths if os.path.isdir(p)]
    if not paths:
        print("No source directories found.", file=sys.stderr)
        sys.exit(1)

    cmd = _build_cmd(pattern, paths)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    sys.exit(result.returncode)
