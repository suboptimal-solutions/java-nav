"""Integration tests for Tier 3 LSP commands (jdtls via multilspy).

These are slow (~10-15s per test due to jdtls startup on-demand).
Run with: uv run pytest -m integration -v -k lsp
"""

import os

import pytest
from click.testing import CliRunner

from java_nav.cli import main

PLAYGROUND_DIR = os.path.join(os.path.dirname(__file__), "..", "playground")
PLAYGROUND_DIR = os.path.abspath(PLAYGROUND_DIR)

pytestmark = pytest.mark.integration
runner = CliRunner()


@pytest.fixture
def playground():
    return PLAYGROUND_DIR


def test_find_class(playground):
    result = runner.invoke(main, ["find", "-d", playground, "Repository"])
    assert result.exit_code == 0
    assert "interface" in result.output
    assert "Repository" in result.output


def test_find_no_match(playground):
    result = runner.invoke(main, ["find", "-d", playground, "XyzNonexistent123"])
    assert "No symbols found" in result.output


def test_symbols_lists_methods(playground):
    result = runner.invoke(
        main,
        [
            "symbols",
            "-d",
            playground,
            "src/main/java/com/example/service/UserService.java",
        ],
    )
    assert result.exit_code == 0
    assert "class" in result.output
    assert "UserService" in result.output
    assert "createUser" in result.output
    assert "getUser" in result.output
    assert "deleteUser" in result.output
    assert "method" in result.output
    assert "field" in result.output


def test_refs_finds_callers(playground):
    result = runner.invoke(main, ["refs", "-d", playground, "UserService.createUser"])
    assert result.exit_code == 0
    assert "App.java" in result.output


def test_refs_class_level(playground):
    result = runner.invoke(main, ["refs", "-d", playground, "UserService"])
    assert result.exit_code == 0
    assert "App.java" in result.output


def test_def_shows_source(playground):
    result = runner.invoke(main, ["def", "-d", playground, "UserService.createUser"])
    assert result.exit_code == 0
    assert "createUser" in result.output
    assert "Preconditions" in result.output


def test_def_class_shows_full_file(playground):
    result = runner.invoke(main, ["def", "-d", playground, "UserService"])
    assert result.exit_code == 0
    assert "class UserService" in result.output


def test_refs_nonexistent_symbol(playground):
    result = runner.invoke(main, ["refs", "-d", playground, "NonExistent.method"])
    assert result.exit_code != 0
    assert "Symbol not found" in result.output
