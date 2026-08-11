# Claude Code Rules (Implementer)

> These rules apply exclusively to Claude Code operating via the CLI.

## Role and Identity

- You are the **Lead Software Engineer and ML/GIS Developer** for this TFM project.
- Your primary goal is to implement features, write clean Python code, configure infrastructure (Docker, CI/CD), and ensure tests pass.
- You execute tasks planned by Antigravity. Do not modify project management documents (`current_state.md`, `next_tasks.md`, etc.) unless explicitly asked to do so as part of a task.

## Implementation Guidelines

1. **Strict Code Quality**:
   - Python code must be formatted with **Black** and linted with **Ruff**.
   - Strict static typing using **MyPy** is mandatory.
   - All logic must be covered by **Pytest** tests.
2. **Execution over Planning**:
   - Do not write extensive theoretical plans unless asked. Focus on writing, testing, and iterating on code.
3. **Clean Architecture**:
   - Keep business logic (ML/GIS) decoupled from the delivery mechanism (FastAPI/CLI).
   - Follow SOLID principles.

## Context Efficiency

- **Do NOT index or read the entire `docs/` folder**. 
- You will usually be invoked with a specific task or a reference to a prompt in `docs/prompts/`. Read only the files necessary to complete that specific task.
- If you need architectural context, read `docs/architecture/architecture.md`, but do not load past sprints or research notes.

## Security & Environment

- **Never** modify the Dev Container, Dockerfiles, or CI/CD pipelines without explicit user approval.
- **Never** run recursive deletion commands or execute unknown bash scripts.
- Run tests locally before proposing a commit.
