"""Maven classpath resolution — shared foundation for all tiers."""

import os
import subprocess
import sys

CACHE_DIR = "target/java-nav"
CLASSPATH_CACHE = "classpath.txt"
DEP_SOURCES_DIR = "dep-sources"


def _cache_dir(project_dir: str) -> str:
    return os.path.join(project_dir, CACHE_DIR)


def _is_stale(cache_file: str, project_dir: str) -> bool:
    """Check if cache is stale by comparing mtime against pom.xml."""
    if not os.path.isfile(cache_file):
        return True
    cache_mtime = os.path.getmtime(cache_file)
    pom_mtime = os.path.getmtime(os.path.join(project_dir, "pom.xml"))
    return pom_mtime > cache_mtime


def resolve_classpath(project_dir: str = ".") -> str | None:
    """Resolve the full Maven classpath including target/classes.

    Results are cached in target/java-nav/classpath.txt and invalidated
    when pom.xml is newer than the cache.

    Returns a classpath string usable with javap, jdeps, java -cp, etc.
    Returns None if no Maven project is found.
    """
    project_dir = os.path.abspath(project_dir)
    pom = os.path.join(project_dir, "pom.xml")
    if not os.path.isfile(pom):
        return None

    cache_file = os.path.join(_cache_dir(project_dir), CLASSPATH_CACHE)

    if not _is_stale(cache_file, project_dir):
        return open(cache_file).read().strip()

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
    classpath = f"{maven_cp}:{target_classes}" if maven_cp else target_classes

    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w") as f:
        f.write(classpath)

    return classpath


def ensure_dep_sources(project_dir: str = ".") -> str | None:
    """Unpack dependency source JARs into target/java-nav/dep-sources/.

    Lazy: only runs mvn if the cache is missing or pom.xml changed.
    Returns the path to the unpacked sources directory, or None if no Maven project.
    """
    project_dir = os.path.abspath(project_dir)
    pom = os.path.join(project_dir, "pom.xml")
    if not os.path.isfile(pom):
        return None

    dep_sources = os.path.join(_cache_dir(project_dir), DEP_SOURCES_DIR)

    if not _is_stale(dep_sources, project_dir):
        return dep_sources

    result = subprocess.run(
        [
            "mvn",
            "-q",
            "dependency:unpack-dependencies",
            "-Dclassifier=sources",
            f"-DoutputDirectory={dep_sources}",
            "-Dmdep.failOnMissingClassifierArtifact=false",
        ],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )
    if result.returncode != 0:
        print(f"Error unpacking dependency sources:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Touch the directory so mtime comparison works
    os.utime(dep_sources, None)

    return dep_sources
