from click.testing import CliRunner

from java_nav.cli import main

runner = CliRunner()


def test_install_creates_skill(tmp_path):
    result = runner.invoke(main, ["install-skill", "-d", str(tmp_path)])
    assert result.exit_code == 0
    assert "Installed" in result.output

    skill = tmp_path / ".claude" / "skills" / "java-nav" / "SKILL.md"
    assert skill.exists()
    content = skill.read_text()
    assert "java-nav api" in content
    assert "java-nav impls" in content
    assert "name: java-nav" in content


def test_install_idempotent(tmp_path):
    runner.invoke(main, ["install-skill", "-d", str(tmp_path)])
    result = runner.invoke(main, ["install-skill", "-d", str(tmp_path)])
    assert result.exit_code == 0
    assert "already installed" in result.output


def test_install_force_overwrites(tmp_path):
    skill_dir = tmp_path / ".claude" / "skills" / "java-nav"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Old content\n")

    result = runner.invoke(main, ["install-skill", "--force", "-d", str(tmp_path)])
    assert result.exit_code == 0
    assert "Installed" in result.output

    content = (skill_dir / "SKILL.md").read_text()
    assert "Old content" not in content
    assert "java-nav api" in content
