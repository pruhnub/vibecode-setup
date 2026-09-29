from pathlib import Path
from vibecode.core import detect_project, init_project, doctor


def test_detect_python_django(tmp_path: Path):
    (tmp_path / "manage.py").write_text("", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("Django==5.2\npsycopg2-binary\npytest\n", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.13\n", encoding="utf-8")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "migrations").mkdir()
    profile = detect_project(tmp_path)
    assert "Python" in profile.languages
    assert "Django" in profile.frameworks
    assert "PostgreSQL" in profile.databases
    assert "Docker" in profile.tools
    assert "pytest" in profile.test_tools
    assert "app/" in profile.source_dirs
    assert "app/migrations/" in profile.migration_dirs


def test_detect_next_prisma(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"dependencies":{"next":"latest","react":"latest","prisma":"latest","tailwindcss":"latest"}}', encoding="utf-8")
    (tmp_path / "src").mkdir()
    profile = detect_project(tmp_path)
    assert "JavaScript/TypeScript" in profile.languages
    assert "Next.js" in profile.frameworks
    assert "React" in profile.frameworks
    assert "Prisma" in profile.frameworks
    assert "src/" in profile.source_dirs


def test_detect_existing_agent_instructions(tmp_path: Path):
    (tmp_path / "CLAUDE.md").write_text("rules", encoding="utf-8")
    profile = detect_project(tmp_path)
    assert "CLAUDE.md" in profile.instruction_files


def test_init_uses_detection(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    created, skipped, profile = init_project(tmp_path, "Demo")
    assert "AGENTS.md" in created
    assert not skipped
    assert "FastAPI" in profile.frameworks
    assert "FastAPI" in (tmp_path / ".vibecode" / "architecture.md").read_text(encoding="utf-8")
    assert (tmp_path / ".vibecode" / "config.toml").exists()


def test_init_is_safe(tmp_path: Path):
    init_project(tmp_path, "Demo")
    (tmp_path / "AGENTS.md").write_text("custom", encoding="utf-8")
    _, skipped, _ = init_project(tmp_path, "Demo")
    assert "AGENTS.md" in skipped
    assert (tmp_path / "AGENTS.md").read_text() == "custom"


def test_doctor(tmp_path: Path):
    init_project(tmp_path, "Demo")
    checks = doctor(tmp_path)
    assert all(ok for ok, _ in checks)


def test_cli_version(capsys):
    from vibecode.cli import main
    import sys
    old = sys.argv
    sys.argv = ["vibecode", "--version"]
    try:
        try:
            main()
        except SystemExit as exc:
            assert exc.code == 0
    finally:
        sys.argv = old
    assert "0.4.2" in capsys.readouterr().out
