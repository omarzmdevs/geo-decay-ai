# Informe 01 · Muestra de datos reales y viabilidad inicial

**Fecha:** 2026-11-04 · **Experimento:** EXP-001 · **Instrumento:**
`notebooks/exp-001/` · **Auditoría:** `notebooks/exp-001/out/manifest.csv`

> Todo lo que aquí se marca como **medido** procede de una petición real a un
> servicio, con su MD5 registrado en el manifiesto y el documento crudo guardado
> en el repositorio. Lo que no está medido se marca como **pendiente** o como
> **hipótesis**, y no se presenta como resultado.

## Estado de los cuatro encargos

| | Encargo | Estado |
|---|---|---|
| 1 | Muestra de datos reales | 🟡 **servicios y catálogo medidos**; imágenes y huellas aún no descargadas |
| 2 | Análisis exploratorio (EDA) | 🟡 **notebook operativo**; auditoría del catálogo hecha, visualizaciones pendientes |
| 3 | Valoración de viabilidad | 🟢 **esta sección**, con el alcance mínimo propuesto |
| 4 | Infraestructura CI/CD y MLOps | 🟢 **en pie y verde**, documentada abajo |

---

## 1 · Muestra de datos reales

### La zona

| | |
|---|---|
| Extent elegido | `469120, 4482944, 470464, 4483840` en **EPSG:25830** (UTM 30N) |
| En grados | `-3.364126, 40.497182` → `-3.348985, 40.504393` (noreste de Madrid) |
| Tamaño | **1344 × 896 m** · 1,20 km² |
| A 0,25 m/px | 5376 × 3584 px · **21 × 14 = 294 teselas** de 256 px |
| Registro | `out/extent.json` y `out/drawing.json` |

Se elige dibujando un rectángulo sobre un mapa interactivo, y el notebook lo
reproyecta, lo ajusta a teselas enteras y lo registra en disco. **No hay ninguna
coordenada escrita en el código**: cambiar de zona no toca ni una línea.

Si la zona es *representativa* todavía no puede afirmarse: no se ha descargado
ninguna imagen sobre ella. Eso es el paso siguiente.

### Los servicios: 4 de 4 responden

Medido el 2026-11-04. Cinco peticiones, cinco respuestas `200`.

| Servicio | Tipo | Bytes | Anuncia |
|---|---|---|---|
| PNOA máxima actualidad | WMS | 27 902 | 3 capas, 20 CRS |
| PNOA histórico | WMS | 113 091 | **37 capas**, 18 CRS |
| Catastro cartografía | WMS | 28 799 | 13 capas, 17 CRS |
| Catastro INSPIRE edificios | WFS | 16 182 | 3 tipos de entidad, 11 CRS |
| Catastro INSPIRE · consultas | WFS | 1 770 | 5 stored queries |

**Formatos.** Imagen por WMS (`GetMap`, JPEG/PNG) y vectorial por WFS (GML).
Ambos son protocolos OGC estándar, consultables por bounding box, sin registro ni
clave de API.

**Sistemas de referencia.** 26 códigos distintos entre los cuatro servicios. Los
cuatro que el proyecto necesita —`EPSG:25829/25830/25831` y `EPSG:4326`— están
anunciados, y el CRS de nuestras peticiones (`EPSG:25830`) también. La
portabilidad entre husos UTM españoles está cubierta.

### Profundidad temporal: bastante más de lo esperado

El servicio histórico anuncia **21 épocas PNOA contiguas, 2004 → 2024**
(`PNOA2025` todavía no existe). Pero además sirve, como capas con nombre propio,
series anteriores:

| Serie | Periodo |
|---|---|
| Americano (Serie B) | 1956-1957 |
| Interministerial | 1973-1986 |
| Nacional | 1981-1986 |
| OLISTAT | 1997-1998 |
| SIGPAC | 1997-2003 |
| PNOA10 (regional) | 2007-2018, por comunidad |
| Orto Expedita LIDAR | 2023, 2024 |

Es decir: **una serie temporal potencial de unos 70 años por el mismo
protocolo**, no los 20 que se asumían. Para detectar abandono —un proceso
lento— esto cambia el planteamiento. *Pendiente:* comprobar qué series cubren
realmente este extent y a qué resolución; el servicio ofrece una capa de consulta
(`infoVuelos`) para averiguarlo.

### Limitaciones encontradas

| Limitación | Estado | Consecuencia |
|---|---|---|
| **La resolución no se declara** en ningún campo legible por máquina; los títulos son «PNOA 2024», sin metros | medido | los 0,25 m/px son un **supuesto** del proyecto, no un dato del servicio: hay que medirlo comparando píxeles pedidos contra metros de suelo |
| **Sin banda infrarroja**: ninguna de las 56 capas anunciadas es IR ni falso color | medido | **no hay NDVI**. La vegetación habrá que estimarla con índices sobre RGB (ExG, VARI), que confunden planta con cubierta verde y sombra |
| **Sin servicio de elevación** en la configuración actual | medido | MDT, MDS y LiDAR sin sondear. El portal de descargas del CNIG no tiene interfaz OGC, así que no se puede consultar por programa |
| **El WFS no tiene consulta por bounding box**: sus 5 stored queries son todas por parcela | medido | pedir huellas por extent exigirá `TYPENAMES` + `BBOX`, sin confirmar todavía |
| **Cobertura por época** desconocida | pendiente | que una capa se anuncie no significa que cubra esta zona |
| **Atributos del catastro** sin confirmar | pendiente | llegan con las entidades, no con el catálogo |

Tres valores de la configuración resultaron equivocados al contrastarlos con los
servicios, y es exactamente para eso que la sección existe: el nombre de la capa
de edificios, el año final del rango y la consulta del WFS.

---

## 2 · Análisis exploratorio

### Qué hay construido

Un notebook autocontenido en `notebooks/exp-001/`: el notebook, su módulo de
funciones y la carpeta de salidas, todo junto y movible. Cada celda de código va
precedida de una explicación de qué hace y qué mirar en su resultado.

| Sección | Estado |
|---|---|
| 1-2 · Propósito y parámetros | ✅ |
| 3 · Elegir el extent en un mapa | ✅ |
| 4 · Contraste del catálogo contra la configuración | ✅ |
| 5-6 · Disponibilidad por época y calidad de imagen | ⏳ siguiente |
| 7 · Comprobación espectral | ⏳ |
| 8 · Huellas catastrales y sus atributos | ⏳ |
| 9 · Elevación | ⏳ |
| 10-11 · Edificios de ejemplo y tabla de etiquetado | ⏳ |
| 12 · Hallazgos | ⏳ |

Dos decisiones de método que ya están dando resultado:

- **Toda petición deja una fila en el manifiesto**, con URL, estado, bytes, MD5 y
  el error si lo hubo. Una cifra sin su fila no es una medición.
- **La ausencia es un resultado legible, no un fallo.** Sin red, el notebook llega
  hasta el final e imprime `ABSENT:` con el motivo en cada sección. Eso es lo que
  permite distinguir «el dato no existe» de «no pude pedirlo».

### Qué información se puede extraer

**Confirmado:** una serie de ortofotos multi-época sobre la misma zona, en un CRS
proyectado métrico, troceable en teselas de 256 px; y una capa vectorial de
construcciones del catastro (`bu:Building`, `bu:BuildingPart`,
`bu:OtherConstruction`).

**Pendiente de confirmar:** los atributos que el catastro acompaña a cada
construcción —identificador, estado de la construcción, año, uso y número de
plantas—. Si el estado de construcción está poblado, es la vía más barata a
etiquetas débiles.

### Problemas encontrados

1. **No hay infrarrojo.** Es la limitación de fondo: el indicador más estándar de
   vegetación queda descartado.
2. **La elevación no es accesible por servicio.** Sin modelo de superficie no hay
   diferencia de altura de cubierta, que es uno de los indicios más fiables de
   ruina.
3. **La resolución es un supuesto**, no un dato declarado.
4. **Fragilidad del selector interactivo.** El rectángulo dibujado se perdía al
   reiniciar el kernel. Se resolvió persistiéndolo en disco en el instante del
   dibujo y resolviéndolo después desde cinco fuentes en orden. Es un detalle de
   ingeniería, pero costó tres intentos y conviene dejarlo escrito.

### Variables candidatas para detectar abandono

**Hipótesis de trabajo, ninguna medida todavía.** Se validan en los pasos 5 a 11.

| Familia | Variable | Depende de |
|---|---|---|
| Cambio multi-época | varianza del gradiente y de la textura de la cubierta entre años | épocas comparables |
| Cambio multi-época | aparición de huecos o discontinuidades en la cubierta | resolución real |
| Vegetación | ExG / VARI sobre RGB como sustituto del NDVI | sin NIR, es lo que queda |
| Vegetación | invasión vegetal del perímetro de la parcela | huellas catastrales |
| Radiometría | caída de contraste y homogeneización del tejado | calidad por época |
| Geometría | altura y volumen de la cubierta | **bloqueado**: sin elevación |
| Etiqueta débil | estado de construcción del catastro | atributos por confirmar |
| Contexto | antigüedad, uso y número de plantas | atributos por confirmar |

---

## 3 · Valoración inicial de viabilidad

### Lo descubierto, en tres frases

Los datos existen, son abiertos, estándar y accesibles por programa sin clave:
cuatro servicios responden y ofrecen una serie temporal mucho más larga de lo
previsto. La limitación real no es el acceso, sino **el contenido espectral y la
elevación**: sin infrarrojo y sin modelo de superficie, los indicios de abandono
habrá que buscarlos en el cambio temporal de la imagen RGB y en la geometría de la
parcela. Y la resolución efectiva, que condiciona todo lo demás, es todavía un
supuesto que hay que medir.

### Cómo conseguir ejemplos etiquetados

Una estrategia en dos niveles, ya instrumentada en el notebook:

1. **Etiqueta débil, automática.** El estado de construcción del catastro marca
   candidatos sin coste humano. Es ruidosa —el catastro se actualiza por trámite
   administrativo, no por inspección— pero sirve para *priorizar* qué mirar.
2. **Etiqueta fuerte, manual y medida.** Para N edificios, el notebook genera una
   tira de recortes de la misma construcción a lo largo de los años y una tabla
   vacía con columnas de etiqueta, evidencia, notas y **minutos empleados**.
   Cronometrar el etiquetado es lo que convierte «¿se pueden etiquetar
   suficientes?» en un número en lugar de una impresión.

### Dificultades que anticipo

| Dificultad | Por qué importa |
|---|---|
| Señal visual débil | el abandono rara vez es evidente en una sola foto aérea: es un cambio lento |
| Desbalanceo de clases | los edificios abandonados son una fracción pequeña del total |
| Ruido en la etiqueta débil | el catastro puede ir años por detrás de la realidad física |
| Comparabilidad entre épocas | distinta cámara, distinta estación, distinta hora: cambios radiométricos que no son cambios físicos |
| Sin NIR y sin elevación | obliga a renunciar a los dos indicadores más directos |
| Coste de la verdad de campo | sin visita a terreno, la etiqueta fuerte es interpretación de un humano sobre una imagen |

### Enfoque más razonable para continuar

Empezar por **una zona y muchas épocas** antes que por muchas zonas: el eje
temporal es donde está la señal, y donde este proyecto tiene ventaja gracias a las
series de 1956 en adelante. Construir primero un conjunto pequeño y bien
etiquetado a mano, usar la etiqueta débil del catastro solo para priorizar, y
comparar un modelo tabular sencillo sobre variables explícitas contra un modelo de
visión sobre los recortes. Mantener el proveedor **descrito como datos** —ya lo
está— para que cubrir otra comunidad o otro país no sea reescribir código.

### Alcance mínimo viable

| | Propuesta |
|---|---|
| **Zona** | el extent actual, 1,2 km² |
| **Épocas** | 3, separadas en el tiempo, de las que cubran la zona |
| **Muestra** | 30-50 construcciones etiquetadas a mano, con minutos registrados |
| **Variables** | cambio temporal RGB + ExG/VARI + atributos del catastro |
| **Modelos** | una base tabular interpretable contra un clasificador de visión sobre los recortes |
| **Métrica** | precisión y exhaustividad sobre la clase minoritaria, no exactitud global |
| **Entregable** | el experimento reproducible de una sola carpeta, con su manifiesto |
| **Fuera de alcance** | elevación, LiDAR, inferencia nacional, servicio en producción |

---

## 4 · Estado de la infraestructura

Cuatro sprints cerrados antes de tocar un solo dato. La base está en pie y en
verde; lo que falta está deliberadamente aparcado.

### Lo que funciona

| Pieza | Estado |
|---|---|
| **Puerta de calidad local** (`pre-commit`) | ✅ 6 hooks: Ruff (lint y formato), MyPy estricto, import-linter, Pytest y guardia de secretos |
| **CI/CD** (GitHub Actions) | ✅ la misma puerta en cada push, verde desde 2026-10-25 |
| **Arquitectura por capas** | ✅ contratos de import verificados por import-linter: el dominio no depende de infraestructura |
| **Entorno reproducible** | ✅ `uv` con dependencias bloqueadas; grupo `eda` opcional, que un `uv sync` normal no instala |
| **Contenedor de referencia** | ✅ `debian:trixie` con GDAL a nivel de sistema |
| **Configuración validada** | ✅ `Settings` y `BoundingBox` por variables de entorno; el extent ya era configuración, solo faltaba su valor |
| **Logging** | ✅ configurado una vez por proceso |
| **Seguimiento de experimentos** | ✅ puerto en el dominio, adaptador MLflow confinado a la capa de datos, adaptador nulo, y `geo-decay tracking-smoke` registrando una ejecución |
| **Gobierno del trabajo con agentes** | ✅ tres roles con ámbitos de escritura, encargos con registro de ejecución y verificación independiente, y el usuario como único que commitea |

### Lo que falta, y por qué

| Pieza | Motivo |
|---|---|
| **DVC** (versionado de datos) | aplazado: todavía no hay un dataset estable que versionar |
| **ADR-004** (decisión de arquitectura de datos) | es *la salida* de este experimento, no una entrada |
| **PDAL** (nubes de puntos) | depende de ADR-004: si la vía es ráster, basta GDAL |
| **Entrenamiento de modelos** | fuera del objetivo de esta fase |

El ámbito de escritura por rol no se comprueba en el commit: lo verifica el
orquestador durante la revisión. Está documentado como deuda conocida.

---

## Qué falta medir, en orden

1. **Disponibilidad y calidad por época** sobre este extent: qué años cubren de
   verdad, con qué resolución efectiva y si la imagen es legible. Responde a la
   pregunta de la resolución, que es la que condiciona todo lo demás.
2. **Comprobación espectral** definitiva: cerrar si existe alguna vía a
   infrarrojo.
3. **Huellas y atributos del catastro**: confirmar la consulta por bounding box y
   si el estado de construcción está poblado. De aquí sale la etiqueta débil.
4. **Elevación**: decidir si se añade un servicio de MDT a la configuración.
5. **Edificios de ejemplo y etiquetado cronometrado**: el número que cierra la
   viabilidad.

Cada punto es un paso del encargo 015: se ejecuta y se valida contra el servicio
real antes de escribir el siguiente, y deja su registro en el propio encargo.
