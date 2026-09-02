# Project Context

> High-level context for AI agents and contributors. Read on-demand when deep domain knowledge is needed.

## Project Name

Intelligent System for the Detection and Assessment of Potentially Abandoned Infrastructure using AI, PNOA and LiDAR

## Goal

Develop a modular platform capable of automatically detecting, analysing and assessing potentially abandoned infrastructure using historical orthophotos (PNOA), LiDAR data and Artificial Intelligence techniques. The system is built incrementally through a functional MVP and successive iterations.

## Scope

**MVP Scope (v1.0):**

- Automatic download and processing of PNOA orthophotos and LiDAR point clouds for a given bounding box.
- Infrastructure detection via object detection models (YOLO11, RT-DETR) and classical CV methods.
- Abandonment assessment through a composite index based on vegetation, roof condition, debris, accessibility, temporal changes, and LiDAR-derived features.
- Comparative experimentation: pre-trained pipeline vs. fine-tuned model vs. expert system.
- Web platform (FastAPI + React + MapLibre) for interactive map-based exploration.
- Automated report generation with LLM assistance.
- MLOps infrastructure (MLflow, DVC) for reproducibility established from the beginning.

**Extended Version Scope (v2.0):**

- Agentic orchestration of the entire pipeline using LangGraph.
- Retrieval-Augmented Generation (RAG) with LlamaIndex for context-enriched reports incorporating technical and urbanistic documentation.

**Out of scope:**

- Real-time video analysis or drone imagery.
- Legal or cadastral ownership verification.
- Structural engineering assessments.

## Key Concepts

| Term | Definition |
|---|---|
| **PNOA** | Plan Nacional de Ortofotografía Aérea — Spain's national programme providing high-resolution orthophotos. |
| **LiDAR** | Light Detection and Ranging — remote sensing providing 3D point cloud data of terrain and structures. |
| **Tile** | A fixed-size spatial subdivision of the study area used to parallelise processing and detection. |
| **Abandonment Index** | A composite score (0–1) estimating the probability that a detected infrastructure is abandoned. |
| **Bounding Box** | A geographic rectangle (min/max lat/lon) defining the area of interest for analysis. |
| **ADR** | Architecture Decision Record — a short document capturing a significant technical decision. |

## Repository Structure

```
TFM_Project/
├── .agents/          # AI agent rules (AGENTS.md, ANTIGRAVITY.md, CLAUDE.md)
├── docs/             # All project documentation (Obsidian vault)
│   ├── architecture/ # System design, stack, ADRs
│   ├── experiments/  # ML/GIS experiment logs
│   ├── research/     # Literature reviews
│   ├── sprints/      # Sprint logs
│   ├── prompts/      # Agent handoff prompts
│   └── tfm/          # Thesis-specific documents
├── src/              # Source code (to be created in Sprint 1)
├── tests/            # Test suite (to be created in Sprint 1)
└── docker-compose.yml # (to be created in Sprint 1)
```

## Related Documents

- [Architecture](architecture/architecture.md)
- [Technology Stack](architecture/stack.md)
- [Current State](current_state.md)
- [Next Tasks](next_tasks.md)
