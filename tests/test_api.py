from click.testing import CliRunner

from java_nav.cli import main

runner = CliRunner()


def test_api_project_class(playground_dir):
    result = runner.invoke(main, ["api", "-d", playground_dir, "com.example.service.UserService"])
    assert result.exit_code == 0
    assert "public class com.example.service.UserService" in result.output
    assert "createUser" in result.output
    assert "getUser" in result.output
    assert "listUsers" in result.output
    assert "deleteUser" in result.output


def test_api_interface(playground_dir):
    result = runner.invoke(main, ["api", "-d", playground_dir, "com.example.repository.Repository"])
    assert result.exit_code == 0
    assert "public interface com.example.repository.Repository<T>" in result.output
    assert "findById" in result.output
    assert "save" in result.output


def test_api_dependency_class(playground_dir):
    result = runner.invoke(
        main, ["api", "-d", playground_dir, "com.google.common.base.Preconditions"]
    )
    assert result.exit_code == 0
    assert "checkArgument" in result.output


def test_api_jdk_class():
    result = runner.invoke(main, ["api", "java.util.List"])
    assert result.exit_code == 0
    assert "public interface java.util.List<E>" in result.output
    assert "size" in result.output


def test_api_nonexistent_class(playground_dir):
    result = runner.invoke(main, ["api", "-d", playground_dir, "com.example.DoesNotExist"])
    assert result.exit_code != 0
