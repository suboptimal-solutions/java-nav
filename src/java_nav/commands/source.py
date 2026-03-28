"""Tier 1: locate and display Java source code for a class."""

import os
import subprocess
import sys

import click

from java_nav.classpath import find_dep_source, resolve_classpath


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

    # Fall back to dependency source (extract only the requested JAR)
    return find_dep_source(classname, project_dir)


def _javap_fallback(classname: str, project_dir: str) -> str | None:
    """Fall back to javap when source is not available."""
    classpath = resolve_classpath(project_dir)
    cmd = ["javap", "-public"]
    if classpath:
        cmd += ["-cp", classpath]
    cmd.append(classname)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout
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
    Falls back to javap (public API signatures) if source is not available.
    """
    project_dir = os.path.abspath(project_dir)
    path = _find_source(classname, project_dir)

    if path is None:
        # Fallback: show javap output instead of failing silently
        javap_output = _javap_fallback(classname, project_dir)
        if javap_output:
            print(f"// Source not available, showing javap output for {classname}")
            print(javap_output)
            return
        print(f"Source not found for {classname}", file=sys.stderr)
        sys.exit(1)

    with open(path) as f:
        file_lines = f.readlines()

    total = len(file_lines)
    start, end = 1, total
    if lines:
        parts = lines.split(":")
        start = int(parts[0])
        if len(parts) > 1:
            end = int(parts[1])

    if start == 1 and end == total:
        print(f"// {path}")
    else:
        print(f"// {path} (lines {start}-{end} of {total})")
    for line in file_lines[start - 1 : end]:
        print(line, end="")
