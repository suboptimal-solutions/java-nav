"""Install java-nav skill instructions into a Java project."""

import os
import sys
from importlib.resources import files

import click

SKILL_FILE = files("java_nav").joinpath("java-nav", "SKILL.md")


@click.command("install-skill")
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Java project root.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing skill.",
)
def install_skill(project_dir: str, force: bool) -> None:
    """Install java-nav skill into a project's .claude/skills/ directory.

    Writes .claude/skills/java-nav/SKILL.md so Claude Code automatically
    discovers java-nav when working in this project.
    """
    project_dir = os.path.abspath(project_dir)
    target_dir = os.path.join(project_dir, ".claude", "skills", "java-nav")
    target = os.path.join(target_dir, "SKILL.md")
    content = SKILL_FILE.read_text()

    if os.path.isfile(target) and not force:
        print(f"java-nav skill already installed at {target}", file=sys.stderr)
        sys.exit(0)

    os.makedirs(target_dir, exist_ok=True)
    with open(target, "w") as f:
        f.write(content)
    print(f"Installed skill to {target}")
