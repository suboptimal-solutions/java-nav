"""Tier 1: jdeps wrapper for class-level dependency analysis."""

import os
import subprocess
import sys

import click

from java_nav.classpath import resolve_classpath


def _find_class_file(classname: str, project_dir: str) -> str | None:
    """Find .class file in project target/ or submodule targets."""
    rel_class = classname.replace(".", "/") + ".class"

    # Check project root
    candidate = os.path.join(project_dir, "target", "classes", rel_class)
    if os.path.isfile(candidate):
        return candidate

    # Check submodules
    for entry in os.listdir(project_dir):
        subdir = os.path.join(project_dir, entry)
        if not os.path.isdir(subdir) or entry.startswith(".") or entry == "target":
            continue
        candidate = os.path.join(subdir, "target", "classes", rel_class)
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
    "--package",
    "package_level",
    is_flag=True,
    help="Show package-level summary instead of class-level detail.",
)
def deps(classname: str, project_dir: str, package_level: bool) -> None:
    """Show class-level dependencies using jdeps.

    CLASSNAME is the fully qualified class name, e.g. com.example.UserService.
    """
    project_dir = os.path.abspath(project_dir)
    classpath = resolve_classpath(project_dir)

    if classpath is None:
        print("No Maven project found. Try -d <project-dir>.", file=sys.stderr)
        sys.exit(1)

    class_file = _find_class_file(classname, project_dir)
    if class_file is None:
        print(f"Class file not found for {classname}", file=sys.stderr)
        print(
            "Make sure the project is compiled (mvn compile). "
            "For multi-module projects, try -d <submodule-dir>.",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = ["jdeps", "--multi-release", "base", "-cp", classpath]
    if package_level:
        cmd.append("-s")
    else:
        cmd.extend(["-verbose:class"])
    cmd.append(class_file)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"jdeps failed for {classname}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print(result.stdout)
