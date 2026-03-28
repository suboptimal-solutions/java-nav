from click.testing import CliRunner

from java_nav.cli import main

runner = CliRunner()


def test_grep_finds_pattern(playground_dir):
    result = runner.invoke(main, ["grep", "-d", playground_dir, "createUser"])
    assert result.exit_code == 0
    assert "UserService.java" in result.output


def test_grep_no_match(playground_dir):
    result = runner.invoke(main, ["grep", "-d", playground_dir, "xyzNonexistentPattern123"])
    # grep returns exit code 1 for no matches
    assert result.exit_code == 1


def test_grep_deps(playground_dir):
    result = runner.invoke(main, ["grep", "-d", playground_dir, "--deps", "checkArgument"])
    assert result.exit_code == 0
    # Should find usages in both project and Guava sources
    assert "UserService.java" in result.output
    assert "Preconditions.java" in result.output
