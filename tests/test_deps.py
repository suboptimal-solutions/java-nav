from click.testing import CliRunner

from java_nav.cli import main

runner = CliRunner()


def test_deps_shows_class_dependencies(playground_dir):
    result = runner.invoke(main, ["deps", "-d", playground_dir, "com.example.service.UserService"])
    assert result.exit_code == 0
    assert "com.example.model.User" in result.output
    assert "com.example.repository.Repository" in result.output
    assert "com.google.common.base.Preconditions" in result.output


def test_deps_package_level(playground_dir):
    result = runner.invoke(main, ["deps", "-d", playground_dir, "--package", "com.example.service.UserService"])
    assert result.exit_code == 0
    assert "UserService" in result.output


def test_deps_nonexistent_class(playground_dir):
    result = runner.invoke(main, ["deps", "-d", playground_dir, "com.example.DoesNotExist"])
    assert result.exit_code != 0
    assert "Class file not found" in result.output
