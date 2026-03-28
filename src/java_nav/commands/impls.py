"""Tier 2: find implementations and subtypes using ClassGraph bytecode scanning."""

import os
import subprocess
import sys
from importlib.resources import files

import click

from java_nav.classpath import resolve_classpath

SCANNER_JAR = str(files("java_nav").joinpath("jars", "classgraph-scanner.jar"))


def _run_scanner(mode: str, project_dir: str, classname: str) -> None:
    classpath = resolve_classpath(project_dir)
    if classpath is None:
        print("No Maven project found.", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        ["java", "-jar", SCANNER_JAR, mode, classpath, classname],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    output = result.stdout.strip()
    if output:
        print(output)
    else:
        print(f"No {mode} found for {classname}", file=sys.stderr)


@click.command()
@click.argument("classname")
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Maven project root.",
)
def impls(classname: str, project_dir: str) -> None:
    """Find all implementations of a Java interface.

    CLASSNAME is the fully qualified interface name, e.g. com.example.Repository.
    Uses ClassGraph bytecode scanning (~2s) for accurate results across the full classpath.
    """
    _run_scanner("impls", os.path.abspath(project_dir), classname)


@click.command()
@click.argument("classname")
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Maven project root.",
)
def subtypes(classname: str, project_dir: str) -> None:
    """Find all subclasses of a Java class.

    CLASSNAME is the fully qualified class name, e.g. com.example.BaseProcessor.
    Uses ClassGraph bytecode scanning (~2s) for accurate results across the full classpath.
    """
    _run_scanner("subtypes", os.path.abspath(project_dir), classname)
