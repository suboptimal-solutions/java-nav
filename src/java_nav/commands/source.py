"""Tier 1: locate and display Java source code for a class."""

import os
import sys

import click

from java_nav.classpath import ensure_dep_sources


def _class_to_path(classname: str) -> str:
    """Convert com.example.Foo to com/example/Foo.java."""
    return classname.replace(".", "/") + ".java"


def _find_source(classname: str, project_dir: str) -> str | None:
    """Find source file in project src/ or unpacked dependency sources."""
    rel_path = _class_to_path(classname)

    # Search project sources first
    for src_root in ["src/main/java", "src/test/java"]:
        candidate = os.path.join(project_dir, src_root, rel_path)
        if os.path.isfile(candidate):
            return candidate

    # Fall back to dependency sources (lazy unpack)
    dep_sources = ensure_dep_sources(project_dir)
    if dep_sources:
        candidate = os.path.join(dep_sources, rel_path)
        if os.path.isfile(candidate):
            return candidate

    return None


@click.command()
@click.argument("classname")
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Maven project root.",
)
@click.option(
    "--lines",
    "-l",
    default=None,
    help="Line range to display, e.g. 10:30.",
)
def source(classname: str, project_dir: str, lines: str | None) -> None:
    """Show source code of a Java class.

    CLASSNAME is the fully qualified class name, e.g. com.example.UserService.
    Searches project sources first, then unpacked dependency sources.
    """
    project_dir = os.path.abspath(project_dir)
    path = _find_source(classname, project_dir)

    if path is None:
        print(f"Source not found for {classname}", file=sys.stderr)
        sys.exit(1)

    with open(path) as f:
        file_lines = f.readlines()

    start, end = 1, len(file_lines)
    if lines:
        parts = lines.split(":")
        start = int(parts[0])
        if len(parts) > 1:
            end = int(parts[1])

    print(f"// {path}")
    for i, line in enumerate(file_lines[start - 1 : end], start=start):
        print(f"{i:4d}  {line}", end="")
