"""Maven classpath resolution — shared foundation for all tiers."""

import os
import subprocess
import sys
import zipfile

CACHE_DIR = "target/java-nav"
CLASSPATH_CACHE = "classpath.txt"
DEP_SOURCES_DIR = "dep-sources"

SRC_DIRS = ["src/main/java", "src/main/kotlin", "src/main/scala"]
TEST_DIRS = ["src/test/java", "src/test/kotlin", "src/test/scala"]


def find_source_roots(project_dir: str, include_test: bool = False) -> list[str]:
    """Find all Java/Kotlin/Scala source roots in a project, including submodules.

    Handles both single-module and multi-module Maven layouts.
    """
    project_dir = os.path.abspath(project_dir)
    candidates = SRC_DIRS + TEST_DIRS if include_test else SRC_DIRS
    roots = []

    # Check project root
    for src in candidates:
        path = os.path.join(project_dir, src)
        if os.path.isdir(path):
            roots.append(path)

    # Check submodules (one level deep: each dir with a pom.xml)
    if not roots or _has_modules(project_dir):
        for entry in os.listdir(project_dir):
            subdir = os.path.join(project_dir, entry)
            if not os.path.isdir(subdir) or entry.startswith(".") or entry == "target":
                continue
            if os.path.isfile(os.path.join(subdir, "pom.xml")):
                for src in candidates:
                    path = os.path.join(subdir, src)
                    if os.path.isdir(path):
                        roots.append(path)

    return roots


def _has_modules(project_dir: str) -> bool:
    """Quick check if pom.xml declares <modules>."""
    pom = os.path.join(project_dir, "pom.xml")
    if not os.path.isfile(pom):
        return False
    with open(pom) as f:
        # Simple text check — avoids XML parsing dependency
        return "<modules>" in f.read()


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
        with open(cache_file) as f:
            return f.read().strip()

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


def _find_source_jar(jar_path: str) -> str | None:
    """Derive the -sources.jar path from a regular JAR path in ~/.m2."""
    if not jar_path.endswith(".jar"):
        return None
    sources_jar = jar_path[:-4] + "-sources.jar"
    if os.path.isfile(sources_jar):
        return sources_jar
    return None


def find_dep_source(classname: str, project_dir: str = ".") -> str | None:
    """Find and extract the source file for a dependency class.

    Looks up the class in the classpath JARs, finds the corresponding -sources.jar,
    extracts only that JAR (cached per-artifact), and returns the .java file path.
    """
    project_dir = os.path.abspath(project_dir)
    classpath = resolve_classpath(project_dir)
    if classpath is None:
        return None

    class_file = classname.replace(".", "/") + ".class"
    source_file = classname.replace(".", "/") + ".java"
    dep_sources = os.path.join(_cache_dir(project_dir), DEP_SOURCES_DIR)

    # Check if already extracted
    cached = os.path.join(dep_sources, source_file)
    if os.path.isfile(cached):
        return cached

    # Search each JAR on the classpath for the class
    for entry in classpath.split(":"):
        if not entry.endswith(".jar") or not os.path.isfile(entry):
            continue

        # Quick check: does this JAR contain the class?
        try:
            with zipfile.ZipFile(entry) as zf:
                if class_file not in zf.namelist():
                    continue
        except (zipfile.BadZipFile, OSError):
            continue

        # Found the JAR — look for its -sources.jar
        sources_jar = _find_source_jar(entry)
        if sources_jar is None:
            return None  # No source JAR available for this dependency

        # Extract the sources JAR (just this one artifact)
        try:
            with zipfile.ZipFile(sources_jar) as zf:
                zf.extractall(dep_sources)
        except (zipfile.BadZipFile, OSError):
            return None

        if os.path.isfile(cached):
            return cached
        return None

    return None


def ensure_all_dep_sources(project_dir: str = ".") -> str | None:
    """Unpack ALL dependency source JARs into target/java-nav/dep-sources/.

    Use find_dep_source() for single-class lookups (faster).
    This is for bulk search (grep --deps) where all sources are needed.
    """
    project_dir = os.path.abspath(project_dir)
    pom = os.path.join(project_dir, "pom.xml")
    if not os.path.isfile(pom):
        return None

    dep_sources = os.path.join(_cache_dir(project_dir), DEP_SOURCES_DIR)
    marker = os.path.join(_cache_dir(project_dir), "dep-sources-all.marker")

    if not _is_stale(marker, project_dir):
        return dep_sources

    print("Unpacking all dependency sources for search (may take a moment)...", file=sys.stderr)
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

    # Write marker so we know all sources are unpacked
    os.makedirs(os.path.dirname(marker), exist_ok=True)
    with open(marker, "w") as f:
        f.write("done")

    return dep_sources
