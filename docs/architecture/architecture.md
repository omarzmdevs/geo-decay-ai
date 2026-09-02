# System Architecture

> High-level architecture of the system. Updated whenever architectural changes are made.

## Overview

<!-- Describe the overall system architecture -->

## Component Diagram

### MVP (v1.0) Architecture

```mermaid
graph TD
    User([User]) --> Frontend[Frontend React + MapLibre]
    Frontend --> API[API FastAPI]
    API --> Download[PNOA & LiDAR Download]
    API --> GIS[GIS Processing & Tiles]
    API --> Detect[Infrastructure Detection]
    API --> Assess[Abandonment Assessment]
    API --> DB[(PostGIS)]
    API --> Report[LLM Report Gen]
    
    %% MLOps affects training/experimentation tracking mostly, but is foundational
    MLOps[MLOps: MLflow + DVC] -.-> Detect
    MLOps -.-> Assess
```

### Extended Version (v2.0) Architecture

```mermaid
graph TD
    User([User]) --> Frontend[Frontend React + MapLibre]
    Frontend --> API[API FastAPI]
    API --> Agent[LangGraph AI Agent]
    
    Agent --> Download[PNOA & LiDAR Download]
    Agent --> GIS[GIS Processing & Tiles]
    Agent --> Detect[Infrastructure Detection]
    Agent --> Assess[Abandonment Assessment]
    Agent --> DB[(PostGIS)]
    Agent --> RAG[LlamaIndex RAG]
    Agent --> Report[LLM Report Gen]
    
    RAG -.-> Docs[(Technical Docs & Urban Law)]
```

## Data Flow

<!-- Describe how data moves through the system -->

## Key Design Decisions

<!-- Reference relevant ADRs from architecture/adr/ -->

## Deployment Architecture

<!-- Describe the deployment model (Docker, Docker Compose, etc.) -->

## Related Documents

- [Technology Stack](stack.md)
- [ADR Index](adr/README.md)
- [Project Context](../project_context.md)
