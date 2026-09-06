# Plan de desarrollo del proyecto (Roadmap técnico)

## Proyecto

**Sistema Inteligente para la Detección y Valoración de Infraestructuras Potencialmente Abandonadas mediante IA, PNOA y LiDAR**

---

# Objetivo general

Desarrollar una plataforma modular capaz de detectar, analizar y valorar automáticamente infraestructuras potencialmente abandonadas utilizando ortofotos históricas, datos LiDAR y técnicas de Inteligencia Artificial, construida de forma incremental mediante un MVP funcional y sucesivas iteraciones.

El proyecto deberá estar desarrollado siguiendo principios de ingeniería del software (Clean Architecture, SOLID, CI/CD y MLOps), de forma que cada Sprint produzca una versión estable y funcional.

---

# Estructura general del proyecto

El desarrollo se divide en dos fases principales:

* **MVP (v1.0)** · Bloques 1–7, Sprints 1–23 → Sistema completo y defendible para el TFM.
* **Versión extendida (v2.0)** · Bloque 8, Sprints 24–26 → Orquestación agéntica (LangGraph) y RAG (LlamaIndex).
* **Bloque final** · Optimización general (rendimiento, precisión, escalabilidad).

Cada Sprint debe cumplir tres condiciones:

* Añadir una funcionalidad nueva.
* Mantener el proyecto completamente funcional.
* No romper la arquitectura existente.

---

## Fase 1: MVP (v1.0) — Sprints 1–23

---

# BLOQUE 1 · Arquitectura e infraestructura

## Objetivo

Construir la base técnica del proyecto.

No se desarrollará todavía ninguna funcionalidad relacionada con IA ni con datos.

---

## Sprint 1 · Inicialización

### Objetivo

Crear la estructura profesional del proyecto.

### Requisitos

* Crear repositorio Git.
* Configurar Dev Container.
* Configurar Docker.
* Configurar Docker Compose.
* Crear estructura inicial de carpetas.
* Configurar pyproject.toml.
* Configurar entorno Python.

### Entregable

Proyecto ejecutándose correctamente sin lógica de negocio.

---

## Sprint 2 · Calidad del código

### Objetivo

Preparar el proyecto para un desarrollo mantenible.

### Requisitos

* Ruff.
* Black.
* MyPy.
* Pytest.
* pre-commit.
* Logging.
* Variables de entorno.
* Configuración centralizada.

### Entregable

Proyecto con validación automática del código.

---

## Sprint 3 · CI/CD

### Objetivo

Automatizar el proceso de desarrollo.

### Requisitos

GitHub Actions deberá ejecutar automáticamente:

* Lint.
* Formateo.
* Tipado.
* Tests.
* Build Docker.

### Entregable

Pipeline CI funcionando correctamente.

---

# BLOQUE 2 · MLOps e infraestructura de datos

## Objetivo

Establecer la infraestructura de tracking de experimentos, versionado de datos y reproducibilidad antes de trabajar con datos o modelos.

Esto garantiza que desde el primer dato descargado y el primer modelo evaluado, todo queda registrado, versionado y es reproducible.

---

## Sprint 4 · MLflow

### Objetivo

Configurar el tracking de experimentos.

### Requisitos

Registrar automáticamente:

* Experimentos.
* Modelos.
* Métricas.
* Hiperparámetros.

### Entregable

MLflow integrado y funcional, listo para registrar cualquier experimento posterior.

---

## Sprint 5 · DVC

### Objetivo

Configurar el versionado de datos y artefactos.

### Requisitos

Versionar:

* Datasets.
* Pesos.
* Modelos.
* Resultados.

### Entregable

DVC configurado y funcional, listo para versionar los datos que se descarguen en bloques posteriores.

---

## Sprint 6 · Reproducibilidad

### Objetivo

Garantizar que cualquier experimento pueda repetirse.

### Requisitos

* Seeds determinísticas.
* Configuraciones externalizadas.
* Pipelines DVC reproducibles.
* Documentación de entornos.

### Entregable

Sistema de reproducibilidad verificado end-to-end.

---

# BLOQUE 3 · Núcleo GIS

## Objetivo

Construir la infraestructura geoespacial del sistema.

---

## Sprint 7 · Base de datos espacial

### Objetivo

Integrar PostgreSQL y PostGIS.

### Requisitos

* Conexión.
* ORM.
* Migraciones.
* Primeras tablas.
* Gestión de geometrías.

### Entregable

Base espacial completamente funcional.

---

## Sprint 8 · Descarga de datos

### Objetivo

Obtener automáticamente los datos necesarios.

### Requisitos

Descargar:

* Ortofotos PNOA.
* Datos LiDAR.
* Metadatos.

El sistema deberá recibir únicamente un Bounding Box.

Todos los datos descargados deberán quedar versionados en DVC.

### Entregable

Descarga automática funcionando con versionado integrado.

---

## Sprint 9 · Procesamiento GIS

### Objetivo

Preparar los datos para la IA.

### Requisitos

* Conversión.
* Normalización.
* Gestión CRS.
* Caché.
* Optimización.
* **Depuración visual (QA):** Scripts en Python/Jupyter (con Folium o Matplotlib) para inspeccionar y validar geometrías, solapes de tiles y proyecciones de coordenadas tempranamente, sin depender de la plataforma web.

### Entregable

Datos preparados para análisis y scripts de depuración visual.

---

## Sprint 10 · Sistema de tiles

### Objetivo

Dividir automáticamente el área.

### Requisitos

* Generación de tiles.
* Gestión de solapes.
* Metadatos.
* Paralelización futura.

### Entregable

Sistema completo de generación de tiles.

---

# BLOQUE 4 · Detección de infraestructuras

## Objetivo

Detectar automáticamente infraestructuras.

---

## Sprint 11 · Investigación comparativa

Antes de desarrollar el sistema definitivo se realizará una fase experimental.

Todos los experimentos deberán registrarse en MLflow.

### Objetivo

Comparar distintas metodologías.

### Se evaluarán

Métodos tradicionales:

* OpenCV.
* Detección por contornos.
* Umbralización.
* Morfología matemática.
* Segmentación clásica.

Modelos IA:

* YOLO11.
* YOLOv8.
* RT-DETR.
* Otros modelos relevantes.

### Métricas

* Precisión.
* Recall.
* F1.
* mAP.
* Velocidad.
* Robustez.

### Resultado esperado

Seleccionar el modelo definitivo con evidencia registrada en MLflow.

---

## Sprint 12 · Implementación del detector

### Objetivo

Construir el sistema definitivo.

### Requisitos

* Detectar edificios.
* Detectar otras infraestructuras.
* Exportar Bounding Boxes.
* Exportar confianza.
* **Validación visual:** Exportación de detecciones y bounding boxes a formatos estándar (GeoJSON) para su superposición inmediata sobre ortofotos en herramientas GIS de escritorio (como QGIS) o notebooks.

### Entregable

Detector completamente funcional con capacidad de exportación para validación en QGIS/Jupyter.

---

## Sprint 13 · Extracción individual

### Objetivo

Convertir cada detección en una entidad independiente.

### Requisitos

Cada infraestructura deberá almacenar:

* Coordenadas.
* Recorte.
* Bounding Box.
* Identificador.

### Entregable

Cada detección almacenada como entidad geoespacial independiente.

---

# BLOQUE 5 · Valoración del abandono

Este constituye el núcleo científico del proyecto.

---

## Sprint 14 · Definición de indicadores

### Objetivo

Definir qué variables describen el abandono.

### Ejemplos

* Vegetación.
* Estado del tejado.
* Escombros.
* Accesibilidad.
* Cambios temporales.
* Información LiDAR.

### Entregable

Taxonomía completa de indicadores de abandono documentada.

---

## Sprint 15 · Extracción automática

### Objetivo

Implementar el cálculo automático de los indicadores definidos.

### Entregable

Pipeline de extracción de indicadores funcional.

---

## Sprint 16 · Motor de valoración

### Objetivo

Construir un sistema capaz de generar un índice de abandono.

### Implementación

Inicialmente mediante:

* Reglas heurísticas.
* Ponderaciones.
* Indicadores objetivos.

Posteriormente podrá compararse con un modelo entrenado.

### Entregable

Motor de valoración generando índices de abandono explicables.

---

# BLOQUE 6 · Experimentación con IA

## Objetivo

Comparar distintas aproximaciones para validar la metodología científica.

Todos los experimentos deberán registrarse en MLflow y los artefactos versionarse con DVC.

---

## Sprint 17 · Sistema sin entrenamiento

### Objetivo

Construir un pipeline basado en:

* Modelos preentrenados.
* Análisis GIS.
* Reglas.

### Entregable

Pipeline zero-shot funcional con resultados registrados.

---

## Sprint 18 · Fine-Tuning

### Objetivo

Entrenar la última etapa del modelo.

### Requisitos

* Crear un pequeño dataset propio.
* Entrenar únicamente la última etapa.
* Comparar resultados con el sistema sin entrenamiento.

### Entregable

Modelo fine-tuned con comparativa documentada.

---

## Sprint 19 · Comparativa científica

### Objetivo

Comparar sistema experto vs modelo entrenado.

### Requisitos

* Evaluación cuantitativa con métricas definidas.
* Análisis cualitativo.
* Conclusiones fundamentadas.

### Entregable

Documento de comparativa científica con conclusiones.

---

# BLOQUE 7 · Plataforma

## Objetivo

Construir la interfaz web que expone toda la funcionalidad del sistema.

---

## Sprint 20 · API

### Objetivo

Implementar la API REST del sistema.

### Requisitos

* FastAPI.
* Endpoints.
* Documentación.
* Swagger.

### Entregable

API funcional y documentada.

---

## Sprint 21 · Frontend

### Objetivo

Construir la interfaz web interactiva.

### Requisitos

* Mapa.
* Selección del área.
* Visualización.
* Marcadores.
* Capas.

### Entregable

Frontend funcional conectado a la API.

---

## Sprint 22 · Resultados

### Objetivo

Visualizar los resultados del análisis en la plataforma.

### Requisitos

Mostrar:

* Infraestructura detectada.
* Índice de abandono.
* Confianza.
* Evidencias.

### Entregable

Visualización completa de resultados en la plataforma.

---

## Sprint 23 · Informes

### Objetivo

Generar informes automáticos.

### Requisitos

* Generación automática mediante LLM.
* Resumen técnico.
* Exportación.

### Entregable

Sistema de generación de informes funcional.

---

---

## Hito: MVP (v1.0) Completado (Sprint 23)

El MVP constituye un sistema completo y defendible para el TFM:

* Detección automatizada de infraestructuras con IA.
* Valoración de abandono con índice compuesto explicable.
* Experimentación científica completamente reproducible (MLflow + DVC).
* Plataforma web funcional (FastAPI + React + MapLibre).
* Pipeline CI/CD completo.

---

## Fase 2: Versión Extendida (v2.0) — Sprints 24–26

---

# BLOQUE 8 · Agentes IA y RAG

## Objetivo

Evolucionar el sistema hacia una arquitectura agéntica con orquestación inteligente y generación de informes enriquecida mediante RAG.

---

## Sprint 24 · LangGraph — Orquestador agéntico

### Objetivo

Refactorizar el pipeline como un grafo de agentes.

### Requisitos

* Cada fase del pipeline (descarga, procesamiento, detección, valoración) se convierte en un nodo/herramienta del agente.
* El agente decide dinámicamente el flujo de ejecución.
* Gestión de estado y memoria del agente.

### Entregable

Pipeline orquestado por LangGraph funcional.

---

## Sprint 25 · LlamaIndex — RAG sobre documentación

### Objetivo

Indexar documentación técnica para enriquecer el sistema.

### Requisitos

* Indexar documentación PNOA.
* Indexar documentación LiDAR.
* Indexar normativa urbanística relevante.
* Sistema de retrieval funcional.

### Entregable

Sistema RAG funcional con documentación indexada.

---

## Sprint 26 · Informes inteligentes con RAG

### Objetivo

Combinar el motor de informes con RAG.

### Requisitos

* Integrar el motor de informes (Sprint 23) con el sistema RAG (Sprint 25).
* Generar informes técnicos contextualizados con normativa y documentación relevante.
* Mejorar la calidad y profundidad de los informes generados.

### Entregable

Sistema de informes enriquecido con RAG funcional.

---

---

## Fase 3: Bloque final de optimización

Una vez exista una versión completamente funcional.

---

## Optimización del rendimiento

* Paralelización.
* Caché.
* Optimización de memoria.
* Optimización GPU.

---

## Optimización de precisión

Comparar:

* Tamaño de tile.
* Resolución.
* Overlap.
* Modelos.
* Hiperparámetros.

---

## Escalabilidad

Permitir analizar:

* Municipios.
* Provincias.
* Comunidades autónomas.

---

# Arquitectura

## MVP (v1.0)

```text
Usuario
    │
    ▼
Frontend (React + MapLibre)
    │
    ▼
API (FastAPI)
    │
    ├──────── Descarga PNOA
    ├──────── Descarga LiDAR
    ├──────── Procesamiento GIS
    ├──────── Generación de tiles
    ├──────── Detección
    ├──────── Valoración
    ├──────── Base de datos (PostGIS)
    ├──────── Generación de informes (LLM)
    └──────── MLOps (MLflow + DVC)
```

## Versión extendida (v2.0)

```text
Usuario
    │
    ▼
Frontend (React + MapLibre)
    │
    ▼
API (FastAPI)
    │
    ▼
Agente IA (LangGraph)
    │
    ├──────── Descarga PNOA
    ├──────── Descarga LiDAR
    ├──────── Procesamiento GIS
    ├──────── Generación de tiles
    ├──────── Detección
    ├──────── Valoración
    ├──────── Base de datos (PostGIS)
    ├──────── RAG (LlamaIndex)
    ├──────── Generación de informes (LLM + RAG)
    └──────── MLOps (MLflow + DVC)
```

---

# Stack tecnológico

## Backend

* Python
* FastAPI

## IA

* PyTorch
* YOLO11
* SAM2 *(fase avanzada)*
* DINOv2 *(fase avanzada)*

## GIS

* GeoPandas
* Rasterio
* GDAL
* PDAL
* Shapely

## Base de datos

* PostgreSQL
* PostGIS

## Frontend

* React
* MapLibre

## Infraestructura

* Docker
* Docker Compose
* Dev Containers

## Calidad

* Ruff
* Black
* MyPy
* Pytest
* pre-commit

## CI/CD

* GitHub Actions

## MLOps

* MLflow
* DVC

## v2.0 — Agentes y RAG

* LangGraph
* LlamaIndex

---

# Resultado esperado

## MVP (v1.0)

Al finalizar el Sprint 23 se dispondrá de una plataforma funcional capaz de:

1. Seleccionar un área geográfica de interés.
2. Descargar automáticamente las ortofotos PNOA y los datos LiDAR necesarios.
3. Procesar la información geoespacial y dividirla en tiles.
4. Detectar infraestructuras mediante la metodología seleccionada tras la fase comparativa.
5. Analizar múltiples indicadores objetivos relacionados con el abandono.
6. Calcular un índice de abandono explicable para cada infraestructura detectada.
7. Almacenar y visualizar los resultados en un sistema GIS.
8. Registrar experimentos y modelos para garantizar la reproducibilidad del proyecto.
9. Generar informes automáticos con los resultados obtenidos.

## Versión extendida (v2.0)

Adicionalmente, tras el Sprint 26:

10. Orquestar el pipeline completo mediante un agente inteligente (LangGraph).
11. Enriquecer los informes con documentación técnica y normativa recuperada mediante RAG (LlamaIndex).

---

Este enfoque garantiza una evolución incremental del proyecto, permitiendo validar cada fase antes de avanzar a la siguiente y manteniendo en todo momento una arquitectura limpia, escalable y preparada para futuras ampliaciones. La separación explícita entre MVP y versión extendida asegura que el TFM dispone en todo momento de una versión defendible, mientras que las mejoras posteriores elevan el sistema a un nivel de producción profesional.
