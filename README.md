# GeoDecay AI — Detección de Infraestructuras Potencialmente Abandonadas

[English version below](#english-version)

> Estado: **en desarrollo**. 
Este proyecto es un Trabajo de Fin de Máster (TFM) con fines académicos y de investigación.

## Estado actual del proyecto

Para el detalle del estado y las próximas tareas, consulta:

- [docs/current_state.md](docs/current_state.md)
- [docs/next_tasks.md](docs/next_tasks.md)
- [docs/project_context.md](docs/project_context.md)

## Idea del proyecto

Este proyecto explora el desarrollo de un sistema capaz de detectar, analizar y evaluar infraestructuras potencialmente abandonadas (naves, edificaciones, instalaciones, etc.) combinando:

- Ortofotos históricas del Plan Nacional de Ortofotografía Aérea (PNOA).
- Datos LiDAR (nubes de puntos 3D) para caracterizar el terreno y las estructuras.
- Técnicas de Inteligencia Artificial y visión por computador para la detección de infraestructuras.

A partir de estas fuentes, el sistema calcula un **índice de abandono**: una puntuación compuesta que estima la probabilidad de que una infraestructura detectada esté abandonada, considerando factores como vegetación, estado del tejado, escombros, accesibilidad y cambios temporales.

## Propósito académico

El proyecto se desarrolla de forma incremental, comenzando por un producto mínimo viable (MVP) y avanzando mediante iteraciones sucesivas conforme al plan de trabajo del TFM. El objetivo es explorar y comparar distintos enfoques (modelos preentrenados, modelos ajustados y sistemas expertos basados en reglas) para la detección y evaluación de abandono, dentro de un contexto de investigación y aprendizaje.

## Metodología de trabajo

El desarrollo sigue prácticas cercanas a un entorno de producción:

- **Agentes de IA**: implementación asistida mediante un agente orquestador (planificación, sprints) y un agente de código (implementación, tests), con *handoffs* documentados y verificación de cada cambio.
- **MLOps**: seguimiento de experimentos y versionado de datos desde el inicio, no como añadido posterior.
- **Calidad automatizada**: linting, tipado y tests integrados vía *pre-commit* e integración continua.
- **Trazabilidad**: decisiones técnicas como ADRs y experimentos documentados en [docs/experiments/](docs/experiments/).

## Nota sobre el stack tecnológico

Las herramientas, librerías y versiones concretas todavía se están evaluando y pueden cambiar a medida que avanza el proyecto. Para no anticipar decisiones que aún están en discusión, este README no detalla el stack técnico; la información más actualizada (siempre sujeta a revisión) puede consultarse en [docs/architecture/stack.md](docs/architecture/stack.md).

## Documentación

Toda la documentación del proyecto vive en la carpeta [docs/](docs/), organizada como un índice navegable. Punto de entrada: [docs/README.md](docs/README.md).

---

Este repositorio corresponde a un trabajo académico individual y no constituye un producto final ni un servicio en producción.

---

# English Version

> Status: **in development**. 
This project is a Master's Thesis (TFM) for academic and research purposes.

## Project Overview

This project explores the development of a system capable of detecting, analyzing and assessing potentially abandoned infrastructure (industrial buildings, structures, facilities, etc.) by combining:

- Historical orthophotos from Spain's National Aerial Orthophotography Plan (PNOA).
- LiDAR data (3D point clouds) to characterize terrain and structures.
- Artificial Intelligence and computer vision techniques for infrastructure detection.

The system computes an **abandonment index**: a composite score estimating the likelihood that detected infrastructure is abandoned, considering factors such as vegetation, roof condition, debris, accessibility and temporal changes.

## Working Methodology

Development follows production-grade practices:

- **AI-assisted development**: implementation combines an orchestration agent (planning, sprints) and a code agent (implementation, tests), with documented handoffs and verification of each change.
- **MLOps from day one**: experiment tracking and data versioning from the start, not as an afterthought.
- **Automated quality**: linting, type checking and tests integrated via pre-commit hooks and CI/CD.
- **Full traceability**: architectural decisions documented as ADRs and experiments logged in [docs/experiments/](docs/experiments/).

## Current Status

The repository is in its initial phases: documentation, architecture and base project structure are being defined. Source code and tests have not yet been developed.

For details: [docs/current_state.md](docs/current_state.md) | [docs/next_tasks.md](docs/next_tasks.md)

## Documentation

All project documentation lives in [docs/](docs/). Entry point: [docs/README.md](docs/README.md).
