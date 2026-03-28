"""Maven classpath resolution — shared foundation for all tiers."""

import os
import subprocess
import sys


def resolve_classpath(project_dir: str = ".") -> str | None:
    """Resolve the full Maven classpath including target/classes.

    Returns a classpath string usable with javap, jdeps, java -cp, etc.
    Returns None if no Maven project is found.
    """
    project_dir = os.path.abspath(project_dir)
    pom = os.path.join(project_dir, "pom.xml")
    if not os.path.isfile(pom):
        return None

    result = subprocess.run(
        [
            "mvn",
            "-q",
            "dependency:build-classpath",
            "-DincludeScope=compile",
            "-Dmdep.outputFile=/dev/stdout",
        ],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )
    if result.returncode != 0:
        print(f"Error resolving Maven classpath:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    maven_cp = result.stdout.strip()
    target_classes = os.path.join(project_dir, "target", "classes")

    if maven_cp:
        return f"{maven_cp}:{target_classes}"
    return target_classes
