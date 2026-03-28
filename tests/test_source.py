from click.testing import CliRunner

from java_nav.cli import main

runner = CliRunner()


def test_source_project_class(playground_dir):
    result = runner.invoke(main, ["source", "-d", playground_dir, "com.example.service.UserService"])
    assert result.exit_code == 0
    assert "public class UserService" in result.output
    assert "createUser" in result.output


def test_source_with_line_range(playground_dir):
    result = runner.invoke(main, ["source", "-d", playground_dir, "com.example.service.UserService", "-l", "12:17"])
    assert result.exit_code == 0
    assert "public class UserService" in result.output
    # Should not contain content outside the range
    lines = [l for l in result.output.strip().splitlines() if not l.startswith("//")]
    assert len(lines) == 6


def test_source_dependency_class(playground_dir):
    result = runner.invoke(main, ["source", "-d", playground_dir, "com.google.common.base.Strings"])
    assert result.exit_code == 0
    assert "package com.google.common.base" in result.output


def test_source_nonexistent_class(playground_dir):
    result = runner.invoke(main, ["source", "-d", playground_dir, "com.example.DoesNotExist"])
    assert result.exit_code != 0
    assert "Source not found" in result.output
