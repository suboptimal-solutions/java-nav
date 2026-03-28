"""Tier 1: jdeps wrapper for class-level dependency analysis."""

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
    "--package",
    "package_level",
    is_flag=True,
    help="Show package-level summary instead of class-level detail.",
)
def deps(classname: str, project_dir: str, package_level: bool) -> None:
    """Show class-level dependencies using jdeps.

    CLASSNAME is the fully qualified class name, e.g. com.example.UserService.
    """
    import os

    project_dir = os.path.abspath(project_dir)
    classpath = resolve_classpath(project_dir)

    if classpath is None:
        print("No Maven project found.", file=sys.stderr)
        sys.exit(1)

    # Find the .class file for the given class
    class_file = os.path.join(
        project_dir, "target", "classes", classname.replace(".", "/") + ".class"
    )
    if not os.path.isfile(class_file):
        print(f"Class file not found: {class_file}", file=sys.stderr)
        print("Make sure the project is compiled (mvn compile).", file=sys.stderr)
        sys.exit(1)

    cmd = ["jdeps", "--multi-release", "base", "-cp", classpath]
    if package_level:
        cmd.append("-s")
    else:
        cmd.extend(["-verbose:class"])
    cmd.append(class_file)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print(result.stdout)
