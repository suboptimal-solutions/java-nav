"""Tier 1: search Java source code using ripgrep or grep fallback."""

import os
import shutil
import subprocess
import sys

import click

from java_nav.classpath import ensure_all_dep_sources, find_source_roots


def _build_cmd(pattern: str, paths: list[str]) -> list[str]:
    """Build search command, preferring rg over grep."""
    if shutil.which("rg"):
        return ["rg", "-n", "--type", "java", pattern] + paths
    return [
        "grep",
        "-rn",
        "--include=*.java",
        pattern,
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
    Automatically discovers source directories in multi-module Maven projects.
    """
    project_dir = os.path.abspath(project_dir)
    paths = find_source_roots(project_dir, include_test=include_test)

    if deps:
        dep_sources = ensure_all_dep_sources(project_dir)
        if dep_sources and os.path.isdir(dep_sources):
            paths.append(dep_sources)

    if not paths:
        print(
            f"No source directories found in {project_dir}.\n"
            "For multi-module projects, run from the root directory containing pom.xml.",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = _build_cmd(pattern, paths)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    # grep/rg exit code 1 = no matches (not an error)
    if result.returncode == 1 and not result.stdout:
        searched = ", ".join(
            os.path.basename(os.path.dirname(p)) + "/" + os.path.basename(p) for p in paths
        )
        print(f'No matches for "{pattern}" in: {searched}', file=sys.stderr)
        hint = ""
        if not include_test:
            hint += " Try --test to include test sources."
        if not deps:
            hint += " Try --deps to include dependency sources."
        if hint:
            print(hint.strip(), file=sys.stderr)

    sys.exit(result.returncode)
