# AGENTS.md

## Mission

Build **Demo Farm** according to the repository's documented product and engineering context.

## Detected Stack

- Python

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
