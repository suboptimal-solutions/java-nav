import os

from java_nav.classpath import resolve_classpath


def test_resolve_classpath_returns_jars_and_target(playground_dir):
    cp = resolve_classpath(playground_dir)
    assert cp is not None
    assert "target/classes" in cp
    assert "guava" in cp


def test_resolve_classpath_returns_none_without_pom(tmp_path):
    cp = resolve_classpath(str(tmp_path))
    assert cp is None
