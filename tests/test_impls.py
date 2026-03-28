from click.testing import CliRunner

from java_nav.cli import main

runner = CliRunner()


def test_impls_finds_implementations(playground_dir):
    result = runner.invoke(main, ["impls", "-d", playground_dir, "com.example.repository.Repository"])
    assert result.exit_code == 0
    assert "InMemoryUserRepository" in result.output
    assert "FileUserRepository" in result.output


def test_subtypes_finds_subclasses(playground_dir):
    result = runner.invoke(main, ["subtypes", "-d", playground_dir, "com.example.processor.AbstractProcessor"])
    assert result.exit_code == 0
    assert "EmailProcessor" in result.output
    assert "SmsProcessor" in result.output


def test_impls_no_implementations(playground_dir):
    result = runner.invoke(main, ["impls", "-d", playground_dir, "com.example.model.User"])
    assert result.exit_code == 0
    assert "No impls found" in result.output
