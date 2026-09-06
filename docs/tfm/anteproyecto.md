# Anteproyecto de Trabajo Fin de Máster (TFM)

---

## 1. Título

**Sistema Inteligente para la Detección y Valoración de Infraestructuras Potencialmente Abandonadas mediante Inteligencia Artificial, Ortofotografía PNOA y Datos LiDAR**

---

## 2. Tipo de Proyecto

**Proyecto de Aplicación Profesional / Desarrollo Tecnológico**

El trabajo plantea el diseño, desarrollo e implantación de una solución técnica integral basada en Inteligencia Artificial y tecnologías geoespaciales para resolver una necesidad práctica del sector público y de la gestión territorial. Aunque incluye una fase empírica y comparativa entre algoritmos, modelos de visión por computador y heurísticas, su foco principal es la entrega de una plataforma de software modular, funcional y evaluable.

Asimismo, el proyecto adopta una metodología de ingeniería de vanguardia basada en el desarrollo asistido y orquestado mediante agentes de Inteligencia Artificial (Antigravity IDE como entorno director y Claude Code como agente principal de implementación), complementado con una rigurosa disciplina de DevOps (containerización con Docker, validaciones automáticas y CI/CD) y MLOps (versionado de datasets geoespaciales con DVC y seguimiento de experimentos con MLflow). De este modo, la propuesta no solo resuelve un reto práctico de dominio territorial, sino que explora y documenta un flujo de trabajo moderno de desarrollo de software acelerado por IA.

---

## 3. Contexto de Negocio y Tecnológico

En España existen miles de construcciones e infraestructuras agrarias, industriales o residenciales en estado de abandono o degradación severa. Esta situación genera múltiples problemas de impacto directo:
* **Riesgo ambiental y forestal:** edificaciones invadidas por masa forestal descontrolada o con acumulación de residuos que actúan como focos de ignición o propagación de incendios.
* **Seguridad ciudadana y salubridad:** derrumbes parciales, presencia de cubiertas degradadas con amianto, vertidos ilegales o riesgo de ocupación no regulada.
* **Gestión municipal ineficiente:** los ayuntamientos y administraciones comarcales suelen carecer de personal suficiente para inspeccionar visualmente todo su término municipal, dependiendo casi siempre de denuncias vecinales o revisiones manuales muy costosas.
* **Herencias sin resolver y propietarios que desconocen serlo:** muchos inmuebles rurales quedan abandonados de forma permanente porque sus herederos nunca completaron los trámites sucesorios o porque, tras generaciones de emigración del campo a la ciudad, los descendientes ni siquiera saben que son propietarios de esas fincas. Esto impide a los ayuntamientos identificar a un responsable legal al que exigir el mantenimiento del inmueble.
* **Construcciones ocultas bajo la vegetación (la ventaja del LiDAR):** con el paso del tiempo, muchas edificaciones y ruinas quedan completamente cubiertas por vegetación. En una foto aérea convencional (como las del PNOA) o en una imagen de satélite óptica, esas estructuras son invisibles: solo se aprecia una mancha de bosque homogénea. El LiDAR aerotransportado resuelve este problema porque no es una cámara, sino un sensor láser: emite pulsos que en su mayoría rebotan en las copas de los árboles, pero una parte logra colarse entre las ramas y llegar hasta el suelo o las estructuras que hay debajo. Registrando por separado esos ecos que llegan más tarde ("últimos retornos"), es posible reconstruir el terreno y las edificaciones ocultas que ninguna imagen óptica puede mostrar.

A nivel tecnológico, España cuenta con una de las infraestructuras de datos espaciales públicos más completas de Europa, gestionada por el Instituto Geográfico Nacional (IGN) a través de su Centro Nacional de Información Geográfica (CNIG):
1. **PNOA (Plan Nacional de Ortofotografía Aérea):** fotografías aéreas de todo el territorio nacional con una resolución de 25 cm por píxel, actualizadas por zonas con un objetivo de revisión de aproximadamente tres años.
2. **PNOA-LiDAR:** nubes de puntos 3D captadas por sensores láser aerotransportados y clasificadas automáticamente en categorías como suelo, vegetación o edificación. El proyecto se ha ejecutado en sucesivas campañas nacionales cada vez más densas: 0,5 puntos por m² en la primera cobertura (2008-2015) y hasta 5 puntos por m² en la más reciente (2022-2025), lo que aporta cada vez más detalle para detectar construcciones pequeñas.

A pesar de disponer de estos datos masivos en abierto, la mayoría de los análisis se siguen realizando de forma manual o con sistemas de información geográfica (SIG) estáticos, sin apoyo de IA. La oportunidad radica en combinar modelos modernos de **visión artificial** (detección y segmentación de objetos en imagen) con el **análisis de nubes de puntos 3D** y una disciplina de **MLOps** que garantice la trazabilidad de los experimentos, automatizando así el rastreo del territorio para detectar edificaciones y calcular un **Índice de Abandono** objetivo para cada inmueble.

---

## 4. Objetivos de Aprendizaje

A lo largo del desarrollo del proyecto se consolidarán y aplicarán los siguientes objetivos competenciales, concebidos desde un enfoque de aprendizaje continuo y descubrimiento progresivo:

1. **Visión por Computador en Teledetección:** entrenar y evaluar modelos de aprendizaje profundo (Deep Learning) para detección de edificaciones sobre ortoimágenes de alta resolución, comprendiendo y resolviendo los desafíos propios de la vista aérea cenital (cambios de escala, sombras acusadas, deformaciones y solapamientos).
2. **Exploración y asimilación de datos geoespaciales y 3D:** familiarizarse y aprender a manipular fuentes territoriales de gran volumen (ortofotos PNOA y nubes de puntos LiDAR en formato LAZ), descubriendo a lo largo del proyecto qué variables geométricas y espaciales (alturas relativas, discontinuidades en cubiertas o densidad de retornos) resultan más significativas para diagnosticar el estado físico de una edificación.
3. **Definición iterativa de indicadores de valoración:** experimentar progresivamente con diferentes técnicas analíticas —desde índices espectrales clásicos (como el NDVI para vigor vegetal) hasta reglas heurísticas y análisis de relieve— para formular de manera evolutiva un Índice de Abandono contrastado con la realidad territorial.
4. **Metodología de ingeniería de software aumentada por IA (Agentic Development):** dominar el flujo de desarrollo colaborativo mediante agentes de Inteligencia Artificial, aprendiendo a orquestar el proyecto (con Antigravity IDE), delegar implementaciones técnicas (con Claude Code) y gestionar contextos, prompts y transferencias de tareas para potenciar la calidad y velocidad de desarrollo.
5. **Cultura y prácticas profesionales de MLOps y DevOps:** adquirir experiencia práctica en la construcción de proyectos reproducibles y robustos, integrando control de versiones de código (Git), versionado de datos pesados (DVC), monitorización y registro de experimentos (MLflow), containerización (Docker) y validación continua (CI/CD).
6. **Diseño de arquitectura limpia y desacoplada:** aplicar principios de ingeniería de software (Clean Architecture y SOLID) para estructurar una solución modular y mantenible, separando con claridad la adquisición de datos, el núcleo analítico de IA, la API de servicios y el visor web interactivo.

---

## 5. Resultados Esperados

El resultado tangible del proyecto constará de los siguientes productos técnicos:

1. **Pipeline de Ingestión y Preprocesamiento Automatizado:** módulo capaz de recibir unas coordenadas geográficas de interés (*Bounding Box*) y descargar, recortar y alinear automáticamente los mosaicos PNOA y los bloques LiDAR correspondientes, dejándolos listos para inferencia.
2. **Modelos de Detección Entrenados y Evaluados:** evaluación comparativa entre un modelo preentrenado de última generación (familia YOLO11 / RT-DETR) y adaptaciones específicas para identificación de cubiertas, presencia de escombros y fracturas visibles, registrando métricas cuantitativas estándar (mAP@0.5, mAP@0.5:0.95, Precision, Recall y F1-score).
3. **Motor de Cálculo del Índice de Abandono:** algoritmo cuantificador que genera una puntuación normalizada de 0 a 1 para cada inmueble localizado, posiblemente ponderando:
   - Cobertura de vegetación sobre y alrededor de la estructura (NDVI).
   - Integridad estructural y desnivel de cubiertas obtenido a partir de LiDAR.
   - Accesibilidad respecto a viales transitables conocidos.
   - Historial de cambios temporales entre coberturas PNOA consecutivas.
4. **Plataforma Web de Consulta Interactiva:** aplicación con interfaz gráfica y mapa interactivo que permita cargar una zona geográfica, visualizar las infraestructuras detectadas marcadas con código de colores según su nivel de abandono, inspeccionar su ficha técnica y descargar informes en formato PDF/GeoJSON.
5. **Entorno Reproducible y Documentación de Calidad:** repositorio de código abierto con contenedores Docker, pruebas unitarias y de integración automáticas, y linaje de datos completamente rastreable para garantizar la reproducibilidad de cada resultado.

---

## 6. Asignaturas y Módulos Relacionados

El proyecto sintetiza y pone en práctica los conocimientos adquiridos en las principales materias del plan de estudios:

| Módulo / Asignatura del Máster | Aplicación Concreta en el TFM |
|---|---|
| **Visión Artificial / Computer Vision** | Detección de edificaciones, segmentación de cubiertas, detección de anomalías y procesado de imágenes multiespectrales (RGB + NIR). |
| **Aprendizaje Profundo (Deep Learning)** | Entrenamiento, ajuste fino (*fine-tuning*) y optimización de redes convolucionales y transformadores de visión (YOLO11, RT-DETR). |
| **Aprendizaje Automático (Machine Learning)** | Modelado del Índice de Abandono mediante algoritmos supervisados de clasificación/regresión y combinación de reglas heurísticas. |
| **Ingeniería de Datos y Big Data** | Ingesta masiva, particionado espacial por teselas (*tiling*), transformaciones de sistemas de coordenadas (ETRS89 / UTM) y almacenamiento en bases de datos relacionales espaciales. |
| **MLOps y Despliegue de Modelos** | Gestión del ciclo de vida de los modelos con MLflow, versionado de datasets de teledetección con DVC, containerización con Docker y despliegue de APIs REST. |
| **Arquitectura de Software y Entornos de Desarrollo** | Aplicación de principios SOLID, Clean Architecture, tipado estricto, pruebas unitarias y automatización con GitHub Actions. |
| **Ética, Legislación y Gobernanza de la IA** | Cumplimiento del Reglamento Europeo de IA (AI Act), respeto a la privacidad territorial y garantía de explicabilidad en las decisiones del sistema. |

---

## 7. Métodos, Materiales y Tecnologías de Uso Potencial

### Metodología de Trabajo
Se seguirá una metodología ágil e incremental organizada en bloques y sprints, orientada a generar entregables funcionales en cada etapa:
* **Ingeniería asistida por agentes de IA:** el desarrollo se estructura mediante un flujo colaborativo donde Antigravity IDE asume el rol de orquestador (planificación, gestión de contexto y control de tareas) y Claude Code actúa como agente principal de implementación de código, asegurando trazabilidad en cada decisión técnica y un control exhaustivo de versiones en Git.
* **Fase 1 (MVP Funcional):** ciclo estructurado en sprints donde se construye primero la base técnica (contenedores, CI/CD, MLOps con DVC y MLflow), después el motor geoespacial de descarga, a continuación el entrenamiento y evaluación de los modelos de visión, y finalmente la API y el visor interactivo.
* **Fase 2 (Ampliaciones avanzadas):** incorporación de orquestación autónoma mediante agentes y generación asistida de informes técnicos contextualizados.

### Orígenes de Datos y Viabilidad del Acceso

Todos los datos seleccionados son públicos y de acceso libre y gratuito, bajo licencias abiertas compatibles con fines académicos y de desarrollo: los productos del IGN/CNIG se distribuyen con una licencia equivalente a Creative Commons Attribution 4.0 (Orden FOM/2807/2015), que solo exige citar la fuente, y la cartografía catastral se ofrece a través de los servicios armonizados que exige la Directiva europea INSPIRE:

1. **PNOA Imagen (IGN / CNIG):**
   - *Origen y descarga:* Centro de Descargas del CNIG ([https://centrodedescargas.cnig.es/CentroDescargas/](https://centrodedescargas.cnig.es/CentroDescargas/)) y servicio web estándar WMS ([https://www.ign.es/wms-inspire/pnoa-ma](https://www.ign.es/wms-inspire/pnoa-ma)).
   - *Características del dato:* ortofotografías aéreas en color verdadero (RGB) e infrarrojo cercano (NIR) de 25 cm de resolución. El recorte y tamaño de las teselas de trabajo se ajustará durante la fase de pruebas técnicas.
2. **PNOA LiDAR (IGN / CNIG):**
   - *Origen y descarga:* catálogo de nubes de puntos del CNIG ([https://centrodedescargas.cnig.es/CentroDescargas/buscadorCatalogo.do?codFamilia=LIDAR](https://centrodedescargas.cnig.es/CentroDescargas/buscadorCatalogo.do?codFamilia=LIDAR)), con ficheros en formato LAZ (versión comprimida del estándar LAS).
   - *Características del dato:* nubes de puntos 3D de las distintas coberturas nacionales, ya clasificadas de forma estándar en categorías como suelo, vegetación o edificación, lo que servirá como base para extraer métricas de altura y de irregularidad de las cubiertas.
3. **Cartografía Catastral Vectorial (Dirección General del Catastro):**
   - *Origen y descarga:* Sede Electrónica del Catastro ([https://www.sedecatastro.gob.es/](https://www.sedecatastro.gob.es/)) y servicios INSPIRE de descarga masiva (WFS/ATOM) ([https://www.catastro.hacienda.gob.es/webinspire/index.html](https://www.catastro.hacienda.gob.es/webinspire/index.html)).
   - *Características del dato:* capas vectoriales (formato GML, convertible a GeoJSON/Shapefile) con las geometrías oficiales de parcelas y construcciones registradas, empleadas para correlación y validación cruzada.
4. **Conjuntos de Datos de Apoyo para Calibración Inicial y Benchmark:**
   - Para acelerar el entrenamiento inicial antes de afinar los modelos sobre PNOA, se recurrirá a datasets abiertos de teledetección ya establecidos en la comunidad investigadora, como *SpaceNet Buildings Dataset* (imágenes satelitales de varias ciudades con cientos de miles de huellas de edificios etiquetadas, alojado en AWS bajo licencia Creative Commons; [https://spacenet.ai/spacenet-buildings-dataset-v2/](https://spacenet.ai/spacenet-buildings-dataset-v2/)) y el *Open Cities AI Challenge Dataset* (imágenes de dron sobre ciudades africanas con más de 790.000 huellas de edificios etiquetadas, publicado por DrivenData; [https://source.coop/open-cities/ai-challenge](https://source.coop/open-cities/ai-challenge)).
5. **Coordenadas de Validación y Muestras de Campo (Google Maps / Exportación KML-GeoJSON):**
   - *Origen y exportación:* coordenadas geográficas y puntos de interés recopilados de forma empírica y exportados mediante herramientas geoespaciales (KML/KMZ desde Google Maps / Google Takeout o GeoJSON).
   - *Características del dato:* conjunto de datos de verdad-terreno (*ground truth*) geoetiquetado que recopila localizaciones reales de edificaciones e infraestructuras abandonadas o en desuso. Servirá como soporte para el entrenamiento supervisado (muestras positivas), calibración fina (*fine-tuning*) del modelo sobre ortofotografías PNOA y validación cruzada cualitativa.

### Tecnologías y Stack Técnico Previsto
El siguiente stack es el previsto a fecha de redacción de este anteproyecto, alineado con la planificación técnica del proyecto; algunas piezas concretas podrán ajustarse durante el desarrollo sin alterar la arquitectura general:
* **Lenguaje principal:** Python 3.11+.
* **Bibliotecas geoespaciales y 3D:** GDAL, Rasterio, Shapely, GeoPandas, PyProj, PDAL y Laspy.
* **Deep Learning y Computer Vision:** PyTorch, Ultralytics (YOLO11), OpenCV, Albumentations y torchvision.
* **MLOps y Reproducibilidad:** MLflow (seguimiento de parámetros y modelos) y DVC (*Data Version Control* para versionado de datos ráster y pesos).
* **Calidad de software y tests:** Ruff, Black, MyPy, Pytest y GitHub Actions.
* **Base de datos espacial:** PostgreSQL 16 con extensión PostGIS, gestionado mediante SQLAlchemy y GeoAlchemy2.
* **Backend de servicios:** FastAPI y Uvicorn para servir las inferencias y datos geoespaciales.
* **Frontend y visualización:** React con TypeScript y MapLibre GL JS para renderizado cartográfico vectorial y visualización de polígonos.
* **Infraestructura:** Docker y Docker Compose para garantizar la ejecución homogénea en cualquier equipo local o servidor.

---

## 8. Análisis de Viabilidad

La viabilidad del proyecto ha sido evaluada desde tres perspectivas fundamentales:

1. **Viabilidad de Datos:**
   El proyecto no depende de acuerdos privados, permisos confidenciales ni APIs de pago de terceros. Los datos de PNOA, LiDAR y Catastro son bienes públicos abiertos gestionados por el Estado español, accesibles de forma continua mediante descarga directa y servicios estándar del sector geoespacial (WMS/WFS), con cobertura territorial completa.
2. **Viabilidad Técnica y Computacional:**
   El procesado geoespacial se planteará mediante técnicas de particionado espacial (*tiling*) dinámico. Esto permite trocear la información masiva en porciones manejables, acotando el consumo de memoria para evitar bloqueos del sistema. De este modo, tanto la preparación de los datos como el entrenamiento de los modelos de visión se podrán ejecutar en equipos con tarjetas gráficas comerciales estándar o instancias de procesamiento en la nube asequibles, sin necesidad de recurrir a supercomputadores.
3. **Viabilidad Temporal y Operativa:**
   El proyecto adopta una estrategia modular: el MVP se centra estrictamente en la detección básica de edificaciones, cálculo inicial de métricas y visualización mínima. Este núcleo es autosuficiente y garantiza que, ante cualquier imprevisto temporal, se dispone de un entregable completo y defendible para el TFM. Las funcionalidades adicionales (orquestación con agentes o análisis avanzado con RAG) se abordan como módulos complementarios una vez asegurada la base principal.
