# Documentation Index

> Central index for all project documentation. Open this folder as an Obsidian vault for bidirectional links and graph navigation.

## Quick Access

- [Project Context](project_context.md)
- [Current State](current_state.md)
- [Next Tasks](next_tasks.md)

## Architecture

- [System Architecture](architecture/architecture.md)
- [Technology Stack](architecture/stack.md)
- [Architecture Decision Records](architecture/adr/)

## Development

- [Sprints](sprints/)
- [Experiments](experiments/)
- [Research](research/)

## Agents

The agent contract lives outside `docs/`, at the repository root:

- `AGENTS.md` — shared rules, roles, task lifecycle, handoff format, security
- `.agents/roles/` — orchestrator, developer (with tester mode), documenter
- `.agents/policy.yaml` — secrets, protected paths, write scope per role
- `.agents/TOOLING.md` — tool requirements, tier → model mapping, launch commands

## Other

- [Prompts & Handoffs](prompts/)
- [TFM Documents](tfm/)
