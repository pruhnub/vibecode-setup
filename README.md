# VibeCode Setup

Project context infrastructure for AI coding agents.

VibeCode scans an existing repository, detects its stack and structure, and creates a small, persistent context layer that coding agents can read.

## Install

```bash
pip install vibecode-setup
```

Or, for isolated CLI installation:

```bash
pipx install vibecode-setup
```

## Initialize a project

```bash
cd your-project
vibecode init
```

VibeCode is local-first and deterministic. It does not require an API key or upload your source code.

## Commands

```bash
vibecode init
vibecode status
vibecode doctor
```

### `init`

Detects languages, frameworks, databases, source areas, migrations, tests, common tooling, existing AI instruction files, and likely entrypoints. It then creates:

```text
AGENTS.md
.vibecode/
  product.md
  prd.md
  architecture.md
  data-model.md
  tasks.md
  current-state.md
  decisions.md
  conventions.md
  security.md
  api.md
  changelog.md
  config.toml
```

Existing files are preserved unless `--force` is explicitly used.

## Roadmap

- Project-aware initialization
- Context health checks
- Git-aware drift detection
- Context synchronization
- Agent-specific context adapters

## Development

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e .
pytest
```

## License

MIT
