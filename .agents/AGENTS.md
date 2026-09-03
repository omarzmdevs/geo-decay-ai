# Project Rules

> These rules apply to all AI agents (Antigravity, Claude Code, Codex, etc.) working on this project.

---

## General Principles

- **Single Source of Truth**: All project knowledge lives inside this repository. Never create copies in external applications.
- **Documentation language**: All documentation, comments, commit messages, and code identifiers must be written in **English**.
- **Documentation format**: Use **Markdown (.md)** exclusively for all documentation.
- **Documentation is versioned**: Documentation is part of the repository and is committed alongside code.

---

## Context Management & Token Efficiency

- **Single Entry Point**: Do NOT read the entire project or multiple docs at the start of a session.
- **Primary Context**: Only read `docs/current_state.md` and `docs/next_tasks.md` to understand current priorities.
- **On-Demand Reading**: Read `docs/project_context.md`, `docs/architecture/architecture.md`, and `docs/architecture/stack.md` ONLY if the specific task requires deep architectural or domain knowledge.
- **Stop and Ask**: If the user's request is ambiguous or lacks specific details, STOP and ask the user for clarification. Do NOT make assumptions that could lead to wasted tokens or incorrect implementations.

---

## Development Workflow & Traceability

- The project follows an **iterative and incremental** methodology organised in Blocks, Sprints, and Tasks.
- Every Sprint must:
  - Add new functionality.
  - Keep the project fully functional.
  - Not break the existing architecture.
  - Be aware of potential future blocks and tasks and plan accordingly to not break them.
- After completing a Sprint, update at minimum:
  - `docs/current_state.md`
  - `docs/next_tasks.md`
  - `docs/experiments/` (if experiments were conducted)
  - `docs/architecture/architecture.md` (if architectural changes were made)
  - The corresponding ADR (if an architectural decision was taken)

---

## Code Quality & Security

- Follow **Clean Architecture** and **SOLID** principles.
- All code must pass linting (Ruff), formatting (Black), type checking (MyPy), and tests (Pytest) before committing.
- **Security First**: Never run destructive bash commands (e.g., recursive deletions) or modify environment configurations without explicit user approval.
- Use **pre-commit** hooks to enforce quality automatically.
- Write meaningful commit messages.

---

## Architecture Decision Records (ADR)

- Create a new ADR in `docs/architecture/adr/` whenever a significant technical or architectural decision is made.
- Use the template at `docs/architecture/adr/adr-template.md`.
- Name ADRs sequentially: `adr-001-short-title.md`, `adr-002-short-title.md`, etc.

---

## Experiments

- Log every experiment in `docs/experiments/`.
- Use the template at `docs/experiments/experiment-template.md`.
- Name experiments sequentially: `exp-001-short-title.md`, `exp-002-short-title.md`, etc.
- Always record: objective, methodology, configuration, results, analysis, and conclusion.

---

## Sprint Logs

- Create a sprint log in `docs/sprints/` at the start of each sprint.
- Use the template at `docs/sprints/sprint-template.md`.
- Name sprint logs as: `sprint-01-short-title.md`, `sprint-02-short-title.md`, etc.

---

## Git Conventions

- Commit frequently with atomic, descriptive commits.
- Keep the repository fully versioned: code, documentation, experiments, architecture, and decisions.

---

## Agent Coordination & Orchestration

- **Antigravity IDE** is the orchestration environment (project management, task planning, decision-making, and agent coordination).
- **Claude Code** is the primary implementation agent (coding, refactoring, architecture design, test execution).
- **Delegation & Handoffs**:
  - Antigravity decides when and how to delegate implementation to Claude Code, selecting the optimal model (`--model haiku` or `--model sonnet`) to minimize token consumption.
  - **Autonomous execution**: Antigravity can invoke Claude Code programmatically via CLI when automatic execution is desired.
  - **Documented handoffs**: Antigravity maintains documented handoff prompts in `docs/prompts/` (with recommended model, exact command, target files, and acceptance criteria), giving the user full visibility and the option to run/inspect tasks in terminal.
- The user provides high-level goals; Antigravity handles orchestration, handoff preparation, and execution verification seamlessly.

---

## File Structure Reference

```
docs/
├── README.md
├── project_context.md
├── current_state.md
├── next_tasks.md
├── architecture/
│   ├── architecture.md
│   ├── stack.md
│   └── adr/
│       ├── README.md
│       └── adr-template.md
├── experiments/
│   ├── README.md
│   └── experiment-template.md
├── research/
│   └── README.md
├── sprints/
│   ├── README.md
│   └── sprint-template.md
├── prompts/
│   └── README.md
└── tfm/
    └── README.md
```
