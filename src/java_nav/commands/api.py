"""Tier 1: javap wrapper — extract public API surface of a Java class."""

import subprocess
import sys

import click

from java_nav.classpath import resolve_classpath


@click.command()
@click.argument("classname")
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Maven project root.",
)
@click.option(
    "--private",
    "access_level",
    flag_value="-private",
    help="Show all members (public, protected, package, private).",
)
@click.option(
    "--protected",
    "access_level",
    flag_value="-protected",
    help="Show protected and public members.",
)
def api(classname: str, project_dir: str, access_level: str | None) -> None:
    """Show the public API surface of a Java class using javap.

    CLASSNAME is the fully qualified class name, e.g. com.example.UserService.
    Works for project classes, dependency JARs, and JDK standard library classes.
    """
    classpath = resolve_classpath(project_dir)
    flag = access_level or "-public"

    cmd = ["javap", flag]
    if classpath:
        cmd += ["-cp", classpath]
    cmd.append(classname)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Class not found: {classname}", file=sys.stderr)
        if classpath:
            print("The class is not on the project classpath.", file=sys.stderr)
        else:
            print("No Maven project found. Try -d <project-dir>.", file=sys.stderr)
        sys.exit(1)

    print(result.stdout)
