# EXP-001 · Resumen de la ejecución

- Fecha: 2026-11-15
- Extent: `469120.00 4482944.00 470464.00 4483840.00` en `EPSG:25830`
- Commit: `92da4000776e`

## Medido · 12.1 · Qué se puede extraer

- **5** — ortofoto con imagen sobre el extent en 9 de 21 años sondeados: 2006, 2009, 2011, 2012, 2014, 2015, 2017, 2020, 2023 · _fuente: MEASURED: epochs_
- **10.1** — 7 de 9 años con chip conservado en los 12 edificios de ejemplo (2006, 2009, 2011, 2014, 2017, 2020, 2023); el resto sólo en parte: 2012 en 1 de 12, 2015 en 1 de 12 · _fuente: disco: strips.csv_
- **6** — resolución nativa medida: 0.25 m/px en 6 año(s) (2009, 2011, 2014, 2017, 2020, 2023); sólo cota: 2006 ≥ 0.5 m/px; sin cifra ni cota: 2012, 2015 · _fuente: disco: ladder.csv_
- **6.1** — calidad de 21 épocas juzgadas como imagen: 12 blanca, 0 saturada, 12 bajo contraste · _fuente: MEASURED: quality_
- **7** — ninguna de las 59 capas anunciadas menciona infrarrojo, falso color ni índice espectral — 10 términos buscados en nombre, título y descripción · _fuente: veredicto de la sección 7_
- **7** — 3 bandas de color + alfa en la imagen de 2023 a 2048 px (md5 14b2bfb2) · _fuente: veredicto de la sección 7_
- **8** — 787 huellas catastrales en EPSG:25830, pedidas en 2 teselas bajo un techo de 0.975 km² · _fuente: MEASURED: cadastre_request_
- **8.1** — `conditionOfConstruction` — functional 787; uniforme: no sirve como etiqueta débil · _fuente: MEASURED: cadastre_attributes_
- **8.1** — huella mediana 70.9 m² (cuartiles 64.0–77.9) · _fuente: MEASURED: cadastre_attributes_
- **8.3** — otros tipos del catastro: buildings 787, building_parts 6355, other_constructions 124, addresses 782, parcels 826 · _fuente: MEASURED: feature_types_
- **8.1** — `numberOfFloorsAboveGround` en los edificios, con valor en 0 de 787 (MEASURED: cadastre_attributes); en las partes, con valor en 6355 de 6355 (disco: manifest.csv + vectors/) · _fuente: MEASURED y disco_
- **9** — 4 de 4 productos de elevación sobre el extent — terrain: paso 4.99628 × 5.00559 m, int16, 0.0% sin dato; surface: paso 4.99628 × 5.00559 m, int16, 0.0% sin dato; building_height: paso 2.50279 × 2.50279 m, int16, 0.0% sin dato; vegetation_height: paso 2.50279 × 2.50279 m, int16, 0.0% sin dato · _fuente: MEASURED: elevation_
- **10.1** — 12 tiras de edificios de ejemplo: 86 de 108 chips conservados · _fuente: disco: strips.csv_
- **10.2** — 7 muestras manuales, 3 dentro del extent y 4 fuera o en su borde; 44 de 63 chips conservados · _fuente: disco: manual_samples.csv, strips.csv, extent.json_
- **11** — tabla de etiquetado de 794 filas: 787 cadastre, 7 manual; 18 con tira · _fuente: disco: candidates.csv_

## Medido · 12.2 · Problemas encontrados

- **7** — sin infrarrojo: ninguna de las 59 capas anunciadas menciona infrarrojo, falso color ni índice espectral — 10 términos buscados en nombre, título y descripción; 3 bandas de color + alfa en la imagen de 2023 a 2048 px (md5 14b2bfb2) · _fuente: veredicto de la sección 7_
- **10.1** — 2012: imagen sólo en parte del extent — 1 de 12 edificios de ejemplo con chip conservado · _fuente: disco: strips.csv_
- **10.1** — 2015: imagen sólo en parte del extent — 1 de 12 edificios de ejemplo con chip conservado · _fuente: disco: strips.csv_
- **6.1** — 12 de 21 épocas con defectos como imagen (años 2004, 2005, 2007, 2008, 2010, 2013, 2016, 2018, 2019, 2021, 2022, 2024) · _fuente: MEASURED: quality_
- **6** — 3 año(s) sin cifra de resolución medida: 2006, 2012, 2015 · _fuente: disco: ladder.csv_
- **10** — 26 huella(s) con marco mayor que una tesela (64 m); la mayor, ES.SDGC.BU.9937001VK6893N: 85 partes, 61439 m², marco 801 m · _fuente: MEASURED: examples_
- **9** — 4 de 4 productos entregan un paso distinto del que sugiere su id: terrain 4.99628 × 5.00559 m, surface 4.99628 × 5.00559 m, building_height 2.50279 × 2.50279 m, vegetation_height 2.50279 × 2.50279 m · _fuente: MEASURED: elevation_
- **9** — 4 de 4 productos en enteros (int16): alturas en metros enteros · _fuente: MEASURED: elevation_
- **8** — 2 de 2 teselas sin `numberReturned`/`numberMatched`: la completitud no se puede verificar · _fuente: MEASURED: cadastre_request_
- **10.3** — 1 muestra(s) manual(es) sin imagen en ningún año: M-0007 · _fuente: disco: strips.csv_

## Medido · Las cuatro preguntas de EXP-001

| Pregunta | Estado | Motivo |
|---|---|---|
| 1 · Resolución y años de PNOA | **contestada** | 9 años con imagen; resolución medida en 6 (12.1, secciones 5 y 6) |
| 2 · Productos de elevación | **parcialmente** | 4 de 4 rásters medidos (12.1, sección 9); nube de puntos no perseguida (9.2) |
| 3 · Indicadores computables | **parcialmente** | lo medido está en 12.1 y 12.2; la viabilidad por grupo de indicadores es inferida (12.3) |
| 4 · Etiquetado manual y etiquetas débiles | **no contestada** | pasada manual fuera de este bloque (decisión del usuario, 2026-11-15); estado de la tabla, no resultado: 794 filas, 2 con `label`, 0 minutos anotados |
