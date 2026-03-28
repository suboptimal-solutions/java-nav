import os
import time

from java_nav.classpath import resolve_classpath


def test_resolve_classpath_returns_jars_and_target(playground_dir):
    cp = resolve_classpath(playground_dir)
    assert cp is not None
    assert "target/classes" in cp
    assert "guava" in cp


def test_resolve_classpath_returns_none_without_pom(tmp_path):
    cp = resolve_classpath(str(tmp_path))
    assert cp is None


def test_classpath_is_cached(playground_dir):
    # First call populates cache
    cp1 = resolve_classpath(playground_dir)

    cache_file = os.path.join(playground_dir, "target", "java-nav", "classpath.txt")
    assert os.path.isfile(cache_file)
    with open(cache_file) as f:
        assert f.read().strip() == cp1

    # Second call reads from cache (same result)
    cp2 = resolve_classpath(playground_dir)
    assert cp1 == cp2


def test_cache_invalidated_on_pom_change(playground_dir):
    # Populate cache
    resolve_classpath(playground_dir)
    cache_file = os.path.join(playground_dir, "target", "java-nav", "classpath.txt")
    first_mtime = os.path.getmtime(cache_file)

    # Touch pom.xml to simulate a dependency change
    time.sleep(0.05)
    pom = os.path.join(playground_dir, "pom.xml")
    os.utime(pom, None)

    # Next call should regenerate the cache
    resolve_classpath(playground_dir)
    second_mtime = os.path.getmtime(cache_file)
    assert second_mtime > first_mtime
