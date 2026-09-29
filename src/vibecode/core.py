from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

DOCS = [
    "product.md", "prd.md", "architecture.md", "data-model.md", "tasks.md",
    "current-state.md", "decisions.md", "conventions.md", "security.md",
    "api.md", "changelog.md",
]

IGNORED_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", ".next", ".nuxt", "dist", "build", ".pytest_cache", ".mypy_cache", ".ruff_cache", "coverage", ".tox"}
AI_INSTRUCTION_FILES = ["AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules", ".windsurfrules", ".github/copilot-instructions.md"]

@dataclass
class ProjectProfile:
    name: str
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    test_tools: List[str] = field(default_factory=list)
    source_dirs: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    migration_dirs: List[str] = field(default_factory=list)
    instruction_files: List[str] = field(default_factory=list)
    important_files: List[str] = field(default_factory=list)
    readme_summary: str = ""
    entrypoints: List[str] = field(default_factory=list)
    git: bool = False

    @property
    def stack(self) -> str:
        parts = self.languages + self.frameworks + self.databases
        return ", ".join(parts) if parts else "Not detected"


def _read(root: Path, name: str) -> str:
    path = root / name
    try:
        return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    except OSError:
        return ""


def _dedupe(values: List[str]) -> List[str]:
    return list(dict.fromkeys(values))


def _safe_read(root: Path, rel: str, limit: int = 12000) -> str:
    path = root / rel
    try:
        if not path.is_file() or path.stat().st_size > limit:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _dirs(root: Path) -> List[Path]:
    try:
        return [p for p in root.iterdir() if p.is_dir() and p.name not in IGNORED_DIRS and not p.name.startswith(".")]
    except OSError:
        return []


def detect_project(root: Path) -> ProjectProfile:
    profile = ProjectProfile(name=root.name, git=(root / ".git").exists())
    profile.readme_summary = _read(root, "README.md")[:4000]
    try:
        profile.config_files = sorted(p.name for p in root.iterdir() if p.is_file() and (p.suffix in {".toml", ".json", ".yaml", ".yml", ".ini"} or p.name in {"requirements.txt", "Pipfile", "manage.py"}))
    except OSError:
        profile.config_files = []

    pyproject = _read(root, "pyproject.toml")
    requirements = _read(root, "requirements.txt")
    setup_py = _read(root, "setup.py")
    package = _read(root, "package.json")
    lockfiles = {p.name for p in root.iterdir() if p.is_file()} if root.exists() else set()

    python = bool(pyproject or requirements or setup_py or (root / "manage.py").exists() or any(p.suffix == ".py" for p in root.iterdir() if p.is_file()))
    node = bool(package or {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "bun.lock"} & lockfiles)
    if python:
        profile.languages.append("Python")
    if node:
        profile.languages.append("JavaScript/TypeScript")
    if any(p.suffix in {".tsx", ".ts"} for p in root.rglob("*") if p.is_file() and not any(part in IGNORED_DIRS for part in p.parts)):
        if "JavaScript/TypeScript" not in profile.languages:
            profile.languages.append("JavaScript/TypeScript")

    text_py = (pyproject + "\n" + requirements + "\n" + setup_py).lower()
    text_js = package.lower()
    combined = text_py + "\n" + text_js

    framework_rules = [
        ("Django", ["django"]), ("FastAPI", ["fastapi"]), ("Flask", ["flask"]),
        ("Pydantic", ["pydantic"]), ("PyTorch", ["torch", "pytorch"]), ("TensorFlow", ["tensorflow"]),
        ("React", ['"react"']), ("Next.js", ['"next"']), ("Vue", ['"vue"']),
        ("Angular", ['"@angular/core"']), ("Express", ['"express"']), ("NestJS", ['"@nestjs/core"']),
        ("Prisma", ['"prisma"']), ("Tailwind CSS", ['"tailwindcss"']),
    ]
    for name, needles in framework_rules:
        haystack = text_py if name in {"Django", "FastAPI", "Flask", "Pydantic", "PyTorch", "TensorFlow"} else text_js
        if any(n in haystack for n in needles):
            profile.frameworks.append(name)

    db_rules = [("PostgreSQL", ["postgres", "psycopg"]), ("MySQL", ["mysql"]), ("SQLite", ["sqlite"]), ("MongoDB", ["mongo", "pymongo"]), ("Redis", ["redis"])]
    for name, needles in db_rules:
        if any(n in combined for n in needles):
            profile.databases.append(name)
    if (root / "db.sqlite3").exists() and "SQLite" not in profile.databases:
        profile.databases.append("SQLite")

    if (root / "Dockerfile").exists() or (root / "compose.yml").exists() or (root / "docker-compose.yml").exists():
        profile.tools.append("Docker")
    if (root / ".github").exists():
        profile.tools.append("GitHub Actions / GitHub")
    if (root / "manage.py").exists():
        profile.tools.append("Django management")
    if (root / ".env.example").exists() or (root / ".env.template").exists():
        profile.tools.append("Environment configuration")
    if (root / "Makefile").exists():
        profile.tools.append("Make")

    if any((root / n).exists() for n in ["pytest.ini", "tox.ini"]):
        profile.test_tools.append("pytest")
    if "pytest" in text_py:
        profile.test_tools.append("pytest")
    if any(n in text_js for n in ["jest", "vitest"]):
        profile.test_tools.append("Jest/Vitest")
    if any(n in text_js for n in ["playwright", "cypress"]):
        profile.test_tools.append("Playwright/Cypress")

    for p in _dirs(root):
        if p.name in {"src", "app", "apps", "backend", "frontend", "server", "client", "api", "web", "lib", "components", "tests", "test"}:
            profile.source_dirs.append(p.name + "/")
        if p.name in {"migrations", "alembic", "prisma"} or "migrations" in p.name.lower():
            profile.migration_dirs.append(p.name + "/")
    if (root / "manage.py").exists():
        for p in _dirs(root):
            if (p / "migrations").is_dir():
                profile.migration_dirs.append(f"{p.name}/migrations/")

    for rel in AI_INSTRUCTION_FILES:
        if (root / rel).exists():
            profile.instruction_files.append(rel)

    important = [
        "README.md", "pyproject.toml", "requirements.txt", "package.json", "Dockerfile",
        "docker-compose.yml", "compose.yml", ".env.example", "manage.py", "Makefile",
    ]
    profile.important_files = [x for x in important if (root / x).exists()]

    entrypoint_candidates = [
        "manage.py", "main.py", "app.py", "server.py", "index.js", "index.ts",
        "src/main.py", "src/app.py", "src/main.ts", "src/index.ts",
        "app/main.py", "app/main.ts", "app/page.tsx",
    ]
    profile.entrypoints = [x for x in entrypoint_candidates if (root / x).exists()]

    profile.languages = _dedupe(profile.languages)
    profile.frameworks = _dedupe(profile.frameworks)
    profile.databases = _dedupe(profile.databases)
    profile.tools = _dedupe(profile.tools)
    profile.test_tools = _dedupe(profile.test_tools)
    profile.source_dirs = _dedupe(profile.source_dirs)
    profile.migration_dirs = _dedupe(profile.migration_dirs)
    profile.instruction_files = _dedupe(profile.instruction_files)
    return profile


def _bullets(items: List[str], empty: str = "Not detected") -> str:
    return "\n".join(f"- {x}" for x in items) if items else f"- {empty}"


def _render(name: str, project_name: str, profile: ProjectProfile) -> str:
    stack = profile.stack
    if name == "AGENTS.md":
        existing = _bullets(profile.instruction_files, "No existing AI instruction file detected")
        return f"""# AGENTS.md

## Mission

Build **{project_name}** according to the repository's documented product and engineering context.

## Detected Project Context

### Stack
{_bullets(profile.languages + profile.frameworks + profile.databases)}

### Source Areas
{_bullets(profile.source_dirs)}

### Migrations / Schema
{_bullets(profile.migration_dirs)}

### Existing AI Instructions
{existing}

### Entrypoints
{_bullets(profile.entrypoints)}

## Before Coding

1. Read this file.
2. Read `.vibecode/current-state.md` and `.vibecode/tasks.md`.
3. Read the relevant `.vibecode/` context for the requested task.
4. Inspect the existing implementation before changing it.
5. Make the smallest change that solves the requested problem.

## Scope Lock

- Work only on the requested task.
- Do not redesign unrelated systems.
- Do not add speculative features.
- Do not introduce dependencies without justification.
- Do not modify unrelated files.
- Record discovered out-of-scope improvements in `.vibecode/tasks.md` instead of implementing them.

## Engineering Rules

- Preserve existing working behavior unless the task requires changing it.
- Never expose or commit secrets.
- Database schema changes require migrations where applicable.
- Reuse existing components and patterns before creating new ones.
- Update project context when architecture or important behavior changes.

## After Coding

- Run the relevant tests/checks.
- Update `.vibecode/current-state.md` when actual project state changes materially.
- Record meaningful architectural decisions in `.vibecode/decisions.md`.
"""
    if name == "README.md":
        return f"# {project_name}\n\n> Project context initialized by VibeCode.\n\nDetected stack: **{stack}**\n\nSee `.vibecode/` for AI-readable project context.\n"

    bodies = {
        "product.md": f"## One Sentence\n\nDescribe what **{project_name}** does in one sentence.\n\n## Users\n\nWho is this for?\n\n## Core Loop\n\nDescribe the primary user journey.\n\n## Product Principles\n\n- Keep the core experience simple.\n- Solve the current user problem before expanding scope.\n\n## Out of Scope\n\nDocument features that must not be built yet.\n",
        "prd.md": "## Feature\n\n### Goal\n\n### Inputs\n\n### Behavior\n\n### States\n\n### Success Criteria\n\n### Failure Cases\n",
        "architecture.md": f"## Detected Stack\n\n{_bullets(profile.languages + profile.frameworks + profile.databases)}\n\n## Source Areas\n\n{_bullets(profile.source_dirs)}\n\n## Migrations / Schema\n\n{_bullets(profile.migration_dirs)}\n\n## Existing README Context\n\n{profile.readme_summary.strip() if profile.readme_summary.strip() else "No README content detected."}\n\n## System Overview\n\nDescribe the major components and how data flows between them.\n\n## Components\n\nDocument the existing application, API, database, storage, jobs, integrations, and clients as applicable.\n\n## Constraints\n\nRecord important architectural constraints here.\n",
        "data-model.md": "## Entities\n\nDocument important models/tables and their relationships. Prefer the actual schema over assumptions.\n\n## Source of Truth\n\nRecord the actual schema location, ORM models, migrations, or database definition here.\n\n```text\nEntity\n  ↓\nRelated Entity\n```\n",
        "tasks.md": "## NOW\n\n- [ ] Define the current task\n\n## NEXT\n\n- [ ]\n\n## LATER\n\n- [ ]\n\n## IDEAS\n\n- [ ]\n\n## NOT NOW\n\n- [ ]\n",
        "current-state.md": f"## Detected Project\n\n### Languages\n{_bullets(profile.languages)}\n\n### Frameworks\n{_bullets(profile.frameworks)}\n\n### Databases\n{_bullets(profile.databases)}\n\n### Tools\n{_bullets(profile.tools)}\n\n### Tests\n{_bullets(profile.test_tools)}\n\n### Source Areas\n{_bullets(profile.source_dirs)}\n\n### Important Files\n{_bullets(profile.important_files)}\n\n### Entrypoints\n{_bullets(profile.entrypoints)}\n\n### Existing AI Instructions\n{_bullets(profile.instruction_files)}\n\n## Working\n\nVerify what is currently working.\n\n## Partially Working\n\n-\n\n## Broken\n\n-\n\n## Current Priority\n\n-\n",
        "decisions.md": "## ADR-001\n\n### Decision\n\n### Context\n\n### Why\n\n### Alternatives Rejected\n\n",
        "conventions.md": "## General\n\n- Reuse existing abstractions before creating new ones.\n- Follow conventions already established in the repository.\n\n## Testing\n\nDocument test commands and expectations.\n\n## Error Handling\n\nDocument project-specific error conventions.\n",
        "security.md": "## Secrets\n\nNever commit credentials, tokens, private keys, or production secrets.\n\n## Authentication\n\nDocument authentication requirements.\n\n## Data Protection\n\nDocument sensitive data handling requirements.\n",
        "api.md": "## API Conventions\n\nDocument endpoints, request/response shapes, authentication, validation, and error formats.\n",
        "changelog.md": f"## {date.today().isoformat()}\n\n- Initialized VibeCode context.\n",
    }
    return f"# {name[:-3].replace('-', ' ').title()}\n\n{bodies[name]}"


def init_project(root: Path, project_name: str | None = None, force: bool = False) -> Tuple[List[str], List[str], ProjectProfile]:
    profile = detect_project(root)
    project_name = project_name or root.name
    created: List[str] = []
    skipped: List[str] = []
    context = root / ".vibecode"
    context.mkdir(exist_ok=True)

    for name in ["AGENTS.md", "README.md"]:
        path = root / name
        if path.exists() and not force:
            skipped.append(name)
        else:
            path.write_text(_render(name, project_name, profile), encoding="utf-8")
            created.append(name)

    for name in DOCS:
        path = context / name
        if path.exists() and not force:
            skipped.append(f".vibecode/{name}")
        else:
            path.write_text(_render(name, project_name, profile), encoding="utf-8")
            created.append(f".vibecode/{name}")

    config = context / "config.toml"
    if not config.exists() or force:
        config.write_text(
            f'project_name = {json.dumps(project_name)}\nversion = "0.3"\n\n'
            f'languages = {json.dumps(profile.languages)}\n'
            f'frameworks = {json.dumps(profile.frameworks)}\n'
            f'databases = {json.dumps(profile.databases)}\n'
            f'source_dirs = {json.dumps(profile.source_dirs)}\n'
            f'migration_dirs = {json.dumps(profile.migration_dirs)}\n'
            f'instruction_files = {json.dumps(profile.instruction_files)}\n',
            encoding="utf-8",
        )
        created.append(".vibecode/config.toml")
    else:
        skipped.append(".vibecode/config.toml")
    return created, skipped, profile


def status(root: Path) -> Dict[str, str]:
    profile = detect_project(root)
    return {
        "Languages": ", ".join(profile.languages) or "not detected",
        "Frameworks": ", ".join(profile.frameworks) or "not detected",
        "Databases": ", ".join(profile.databases) or "not detected",
        "Tools": ", ".join(profile.tools) or "not detected",
        "Tests": ", ".join(profile.test_tools) or "not detected",
        "Source": ", ".join(profile.source_dirs) or "not detected",
        "Migrations": ", ".join(profile.migration_dirs) or "not detected",
        "AI Instructions": ", ".join(profile.instruction_files) or "none",
        "Git": "detected" if profile.git else "not detected",
    }


def doctor(root: Path) -> List[Tuple[bool, str]]:
    checks: List[Tuple[bool, str]] = []
    agents = root / "AGENTS.md"
    context = root / ".vibecode"
    checks.append((agents.exists(), "AGENTS.md exists" if agents.exists() else "AGENTS.md missing"))
    checks.append((context.is_dir(), ".vibecode/ context directory exists" if context.is_dir() else ".vibecode/ context directory missing"))
    if context.is_dir():
        missing = [name for name in DOCS if not (context / name).exists()]
        checks.append((not missing, "All core context files present" if not missing else f"Missing context: {', '.join(missing)}"))
    gitignore = root / ".gitignore"
    if gitignore.exists():
        ignored = any(line.strip() in {".vibecode", ".vibecode/"} for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines())
        checks.append((not ignored, ".vibecode/ is tracked by Git" if not ignored else "`.vibecode/` is ignored by Git; decide if project context should be committed"))
    return checks
