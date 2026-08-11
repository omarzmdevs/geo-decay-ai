Aquí tienes un documento técnico sencillo que puede servir como referencia para el proyecto y como guía para cualquier agente (Claude Code, Codex, Antigravity, etc.).

# Arquitectura de desarrollo del proyecto

## Objetivo

Definir una arquitectura de desarrollo que permita trabajar de forma eficiente con múltiples agentes de IA, manteniendo una única fuente de verdad, reduciendo el consumo de contexto y garantizando la trazabilidad de todas las decisiones del proyecto.

---

# Principios

La arquitectura de desarrollo se basa en los siguientes principios:

* Una única fuente de verdad (*Single Source of Truth*).
* Documentación versionada junto al código.
* Compatibilidad con cualquier agente de IA.
* Reducción del consumo de tokens.
* Máxima trazabilidad.
* Separación entre desarrollo y documentación.
* Facilidad para recuperar el contexto del proyecto.

---

# Arquitectura general

```text
                         GitHub
                            │
                            ▼
                  Repositorio del proyecto
                            │
        ┌───────────────────┼────────────────────┐
        │                   │                    │
        ▼                   ▼                    ▼
      src/                docs/               tests/
        │                   │
        │                   ▼
        │        Documentación Markdown
        │
        ▼
 Implementación del sistema
```

---

# Herramientas

## Entorno de desarrollo

* Google Antigravity IDE

Responsabilidades:

* Gestión del proyecto.
* Orquestación del desarrollo.
* Gestión de tareas.
* Coordinación entre agentes.

---

## Agente principal

Claude Code

Responsabilidades:

* Implementación del código.
* Refactorización.
* Explicación técnica.
* Diseño de arquitectura.
* Revisión del código.

Claude Code recibirá tareas específicas desde Antigravity cuando sea necesaria una mayor capacidad de razonamiento o implementación.

---

## Control de versiones

Git + GitHub

Todo el proyecto deberá mantenerse completamente versionado.

Incluye:

* Código.
* Documentación.
* Experimentos.
* Arquitectura.
* Decisiones técnicas.

---

# Documentación

Toda la documentación se almacenará dentro del propio repositorio.

```text
docs/

architecture/

adr/

experiments/

research/

sprints/

prompts/

tfm/

project_context.md

current_state.md

next_tasks.md

README.md
```

El formato utilizado será exclusivamente **Markdown (.md)**.

---

# Fuente única de verdad

Toda la información deberá existir únicamente dentro del repositorio.

No se crearán copias independientes en aplicaciones externas.

Esto garantiza:

* sincronización,
* versionado,
* trazabilidad,
* compatibilidad con cualquier herramienta.

---

# Obsidian

Obsidian no actuará como repositorio independiente.

La carpeta **docs/** del proyecto será abierta directamente como un Vault de Obsidian.

De esta forma:

```text
Repositorio

↓

docs/

↓

Obsidian Vault
```

No existirá duplicación de información.

---

# Uso de Obsidian

Obsidian se utilizará para:

* Navegación rápida.
* Enlaces bidireccionales.
* Graph View.
* Canvas.
* Organización del conocimiento.
* Consulta técnica.

Nunca será la fuente principal del proyecto.

---

# RAG ligero

Se utilizará Obsidian junto con plugins como Smart Connections para proporcionar recuperación semántica sobre la documentación.

Flujo:

```text
Markdown

↓

Embeddings

↓

Índice vectorial

↓

Búsqueda semántica

↓

LLM
```

Esto permitirá recuperar automáticamente la documentación más relevante para cada consulta sin necesidad de cargar todo el proyecto en el contexto.

---

# Gestión del contexto para agentes

Los agentes no deberán leer el proyecto completo en cada sesión.

Se apoyarán en documentos de contexto específicos.

Documentos principales:

```text
project_context.md

architecture.md

current_state.md

next_tasks.md

stack.md
```

Estos archivos resumen el estado actual del proyecto y permiten reducir el consumo de contexto.

---

# Flujo de trabajo

```text
Usuario

↓

Antigravity IDE

↓

Planificación de tareas

↓

Claude Code

↓

Implementación

↓

Tests

↓

Git Commit

↓

GitHub

↓

Actualización documentación

↓

Obsidian
```

---

# Organización del desarrollo

El proyecto se desarrollará mediante una metodología iterativa e incremental.

La estructura será:

```text
Épica

↓

Sprint

↓

Tareas

↓

Commit

↓

Revisión
```

Cada Sprint deberá producir una versión funcional del sistema.

---

# Gestión de la documentación

Cada Sprint actualizará como mínimo:

* current_state.md
* next_tasks.md
* experiments.md (si procede)
* architecture.md (si existen cambios)
* ADR correspondiente (si se toma una decisión arquitectónica)

---

# Beneficios de esta arquitectura

* Una única fuente de verdad.
* Compatibilidad con Claude Code, Codex y futuros agentes.
* Reducción del consumo de tokens.
* Mejor recuperación del contexto.
* Trazabilidad completa mediante Git.
* Documentación sincronizada con el código.
* Navegación avanzada mediante Obsidian.
* Posibilidad de incorporar capacidades RAG sin modificar la estructura del proyecto.
* Arquitectura preparada para proyectos de larga duración y trabajo colaborativo.

---

# Resumen

La arquitectura de desarrollo se basa en mantener **todo el conocimiento del proyecto dentro del propio repositorio**, utilizando Markdown como formato universal de documentación. Antigravity IDE actúa como entorno de orquestación, Claude Code como agente principal de implementación y GitHub como sistema de versionado. Obsidian se emplea únicamente como interfaz de visualización y consulta sobre la carpeta `docs/`, complementado con búsqueda semántica mediante Smart Connections. Este enfoque garantiza coherencia, trazabilidad, eficiencia en el uso del contexto por parte de los agentes y una evolución ordenada del proyecto.
