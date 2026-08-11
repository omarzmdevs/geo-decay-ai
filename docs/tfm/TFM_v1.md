# Plan de desarrollo del proyecto (Roadmap técnico)

## Proyecto

**Sistema Inteligente para la Detección y Valoración de Infraestructuras Potencialmente Abandonadas mediante IA, PNOA y LiDAR**

---

# Objetivo general

Desarrollar una plataforma modular capaz de detectar, analizar y valorar automáticamente infraestructuras potencialmente abandonadas utilizando ortofotos históricas, datos LiDAR y técnicas de Inteligencia Artificial, construida de forma incremental mediante un MVP funcional y sucesivas iteraciones.

El proyecto deberá estar desarrollado siguiendo principios de ingeniería del software (Clean Architecture, SOLID, CI/CD y MLOps), de forma que cada Sprint produzca una versión estable y funcional.

---

# Estructura general del proyecto

El desarrollo se divide en **7 bloques principales**, cada uno compuesto por varios Sprint.

Cada Sprint debe cumplir tres condiciones:

* Añadir una funcionalidad nueva.
* Mantener el proyecto completamente funcional.
* No romper la arquitectura existente.

---

# BLOQUE 1 · Arquitectura e infraestructura

## Objetivo

Construir la base técnica del proyecto.

No se desarrollará todavía ninguna funcionalidad relacionada con IA.

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

# BLOQUE 2 · Núcleo GIS

## Objetivo

Construir la infraestructura geoespacial del sistema.

---

## Sprint 4 · Base de datos espacial

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

## Sprint 5 · Descarga de datos

### Objetivo

Obtener automáticamente los datos necesarios.

### Requisitos

Descargar:

* Ortofotos PNOA.
* Datos LiDAR.
* Metadatos.

El sistema deberá recibir únicamente un Bounding Box.

### Entregable

Descarga automática funcionando.

---

## Sprint 6 · Procesamiento GIS

### Objetivo

Preparar los datos para la IA.

### Requisitos

* Conversión.
* Normalización.
* Gestión CRS.
* Caché.
* Optimización.

### Entregable

Datos preparados para análisis.

---

## Sprint 7 · Sistema de tiles

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

# BLOQUE 3 · Detección de infraestructuras

## Objetivo

Detectar automáticamente infraestructuras.

---

## Sprint 8 · Investigación comparativa

Antes de desarrollar el sistema definitivo se realizará una fase experimental.

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

Seleccionar el modelo definitivo.

---

## Sprint 9 · Implementación del detector

### Objetivo

Construir el sistema definitivo.

### Requisitos

* Detectar edificios.
* Detectar otras infraestructuras.
* Exportar Bounding Boxes.
* Exportar confianza.

### Entregable

Detector completamente funcional.

---

## Sprint 10 · Extracción individual

### Objetivo

Convertir cada detección en una entidad independiente.

### Requisitos

Cada infraestructura deberá almacenar:

* Coordenadas.
* Recorte.
* Bounding Box.
* Identificador.

---

# BLOQUE 4 · Valoración del abandono

Este constituye el núcleo científico del proyecto.

---

## Sprint 11 · Definición de indicadores

Definir qué variables describen el abandono.

Ejemplos:

* Vegetación.
* Estado del tejado.
* Escombros.
* Accesibilidad.
* Cambios temporales.
* Información LiDAR.

---

## Sprint 12 · Extracción automática

Implementar el cálculo automático de dichos indicadores.

---

## Sprint 13 · Motor de valoración

Construir un sistema capaz de generar un índice de abandono.

Inicialmente mediante:

* reglas heurísticas,
* ponderaciones,
* indicadores objetivos.

Posteriormente podrá compararse con un modelo entrenado.

---

# BLOQUE 5 · Experimentación con IA

## Objetivo

Comparar distintas aproximaciones.

---

## Sprint 14 · Sistema sin entrenamiento

Pipeline basado en:

* modelos preentrenados,
* análisis GIS,
* reglas.

---

## Sprint 15 · Fine-Tuning

Crear un pequeño dataset propio.

Entrenar únicamente la última etapa.

Comparar resultados.

---

## Sprint 16 · Comparativa científica

Comparar:

Sistema experto

vs

Modelo entrenado.

Obtener conclusiones.

---

# BLOQUE 6 · Plataforma

## Sprint 17 · API

Implementar FastAPI.

Endpoints.

Documentación.

Swagger.

---

## Sprint 18 · Frontend

Mapa.

Selección del área.

Visualización.

Marcadores.

Capas.

---

## Sprint 19 · Resultados

Mostrar:

* infraestructura,
* índice,
* confianza,
* evidencias.

---

## Sprint 20 · Informes

Generación automática mediante LLM.

Resumen técnico.

Exportación.

---

# BLOQUE 7 · MLOps

## Sprint 21 · MLflow

Registrar automáticamente:

* experimentos,
* modelos,
* métricas,
* hiperparámetros.

---

## Sprint 22 · DVC

Versionar:

* datasets,
* pesos,
* modelos,
* resultados.

---

## Sprint 23 · Reproducibilidad

Garantizar que cualquier experimento pueda repetirse.

---

# Bloque final · Optimización

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

* tamaño de tile,
* resolución,
* overlap,
* modelos,
* hiperparámetros.

---

## Escalabilidad

Permitir analizar:

* municipios,
* provincias,
* comunidades autónomas.

---

# Arquitectura final

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
    ├──────── Base de datos
    └──────── Generación de informes
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
* LangGraph

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

---

# Resultado esperado

Al finalizar todos los Sprint se dispondrá de una plataforma funcional capaz de:

1. Seleccionar un área geográfica de interés.
2. Descargar automáticamente las ortofotos PNOA y los datos LiDAR necesarios.
3. Procesar la información geoespacial y dividirla en tiles.
4. Detectar infraestructuras mediante la metodología seleccionada tras la fase comparativa.
5. Analizar múltiples indicadores objetivos relacionados con el abandono.
6. Calcular un índice de abandono explicable para cada infraestructura detectada.
7. Almacenar y visualizar los resultados en un sistema GIS.
8. Registrar experimentos y modelos para garantizar la reproducibilidad del proyecto.
9. Generar informes automáticos con los resultados obtenidos.

Este enfoque garantiza una evolución incremental del proyecto, permitiendo validar cada fase antes de avanzar a la siguiente y manteniendo en todo momento una arquitectura limpia, escalable y preparada para futuras ampliaciones.
