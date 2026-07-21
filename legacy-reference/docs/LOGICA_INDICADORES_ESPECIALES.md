# Lógica de cálculo — Indicadores especiales

> **Alcance:** este documento describe cómo el pipeline ETL obtiene, transforma y escribe
> los valores de tres grupos de indicadores que requieren lógica especial:
> matrículas nuevos (379, 381-384), estudiantes antiguos (274) y Plan de Retos (373, 390, 414-418, 420, 469-471 y sub-series).

---

## 1. Conceptos base

### Fuente de datos

| Artefacto | Ruta | Descripción |
|-----------|------|-------------|
| API consolidada | `data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx` | Todos los períodos de todos los años, generado por `consolidar_api.py` |
| Catálogo | `data/raw/Resultados_Consolidados_Fuente.xlsx` (hoja `Catalogo Indicadores`) | `Extraccion`, `TipoCalculo`, `Tipo de indicador` por ID |
| Variables | `data/raw/Resultados_Consolidados_Fuente.xlsx` (hoja `Variables`) | Mapeo símbolo → columna de ejecución/meta por indicador |
| Sub-series | `config/series_subindicadores.toml` | Mapeo nombre de serie → ID decimal (ej. `420.1 = "SGC"`) |

### Campos clave de la API

| Campo | Tipo | Uso |
|-------|------|-----|
| `ID` | int | Identificador del indicador |
| `fecha` | datetime | Período de reporte |
| `resultado` | float | Valor global de ejecución (calculado en Kawak) |
| `meta` | float | Meta global del período |
| `variables` | texto (lista Python) | Lista de `{valor, nombre, simbolo}` — desgloses de ejecución/meta |
| `series` | texto (lista Python) | Lista de sub-series `{nombre, resultado, meta, variables}` |

Los campos `variables` y `series` son **cadenas que contienen literales Python**, parseadas con `ast.literal_eval()` en [`scripts/etl/normalizacion.py:parse_json_safe()`](../scripts/etl/normalizacion.py).

---

## 2. Grupo A — Matrículas nuevos (379, 381-384)

### Indicadores

| ID | Nombre | Símbolo Ejecución | Símbolo Meta |
|----|--------|-------------------|--------------|
| 379 | Total estudiantes nuevos | `NENTM` | `NTENMP` |
| 381 | Cumplimiento matrículas pregrado presencial nuevos | `ENMPP` | `TENPPP` |
| 382 | Cumplimiento matrículas pregrado virtual nuevos | `ENMPV` | `TENPPV` |
| 383 | Cumplimiento matrículas posgrado virtual nuevos | `NENMPV` | `TEMPVP` |
| 384 | Cumplimiento matrículas posgrado presencial nuevos | `NENMPP` | `TENPPPR` |

### Frecuencia y estructura en la API

- **Periodicidad:** Trimestral
- **Períodos con datos:** 2 por año — `YYYY-06-30` y `YYYY-12-31`
- **Campo `series`:** VACÍO — no se usa
- **Campo `variables`:** SÍ tiene contenido; siempre 2 variables (una de ejecución, una de meta)

**Ejemplo de `variables` para ID 379 (`2025-12-31`):**
```python
[
  {"valor": 11285, "nombre": "N estudiantes nuevos total matriculados",              "simbolo": "NENTM"},
  {"valor": 11019, "nombre": "N total de estudiantes nuevos matriculados presupuestados", "simbolo": "NTENMP"}
]
```

### Lógica de extracción

1. **Tipo de extracción en catálogo:** `Desglose Variables`
2. El ETL llama a [`extraer_por_simbolo()`](../scripts/etl/extraccion.py) con los símbolos configurados en la hoja `Variables` del catálogo.
3. La función itera la lista de `variables` buscando por `simbolo` (case-insensitive).
4. El símbolo de ejecución da el numerador; el símbolo de meta da el denominador.
5. El **resultado consolidado** (`Ejecucion`) es el valor directo del símbolo, no un cociente — Kawak ya entrega el porcentaje calculado como `(ejec/meta)*100`.

### Dónde queda configurado

```toml
# config/settings.toml — no requiere nada especial para estos IDs
```

```xlsx
# data/raw/Resultados_Consolidados_Fuente.xlsx → hoja "Variables"
# Columnas: Id | Simbolo_Ejecucion | Simbolo_Meta
379 | NENTM  | NTENMP
381 | ENMPP  | TENPPP
382 | ENMPV  | TENPPV
383 | NENMPV | TEMPVP
384 | NENMPP | TENPPPR
```

### Relación con el indicador 14 (Total Población)

El indicador 14 agrega los resultados de estos sub-indicadores usando la columna `Fuente` del catálogo:
```
14.1 = ENMPP + NENMPP  (presencial)
14.2 = ENMPV + NENMPV  (virtual)
14.3 = ENMPP + ENMPV   (pregrado)
14.4 = NENMPP + NENMPV (posgrado)
```
Esta lógica es independiente del ETL y se resuelve en la hoja `Catalogo Indicadores` del consolidado.

---

## 3. Grupo B — Estudiantes antiguos (274) con desglose por modalidad

### Indicador

| ID | Nombre | Extracción | TipoCalculo |
|----|--------|-----------|-------------|
| 274 | Cumplimiento total estudiantes antiguos | Directo de fuente | Acumulado |

### Frecuencia y estructura en la API

- **Periodicidad:** Trimestral
- **Períodos con datos:** `YYYY-06-30` y `YYYY-12-31`
- **Campo `resultado`:** Valor global (ej. 102.03 en dic-2025)
- **Campo `series`:** 4 sub-series, una por modalidad académica

**Estructura de `series` para ID 274:**
```python
[
  {"nombre": "Posgrado Presencial", "meta": 100, "resultado": 110.61,
   "variables": [{"simbolo": "TEMS", "valor": 396}, {"simbolo": "TEP", "valor": 358}]},
  {"nombre": "Pregrado Presencial", "meta": 100, "resultado": 98.87,
   "variables": [{"simbolo": "TEMS", "valor": 23497}, {"simbolo": "TEP", "valor": 23764}]},
  {"nombre": "Pregrado Virtual",    "meta": 100, "resultado": 101.94, ...},
  {"nombre": "Posgrado Virtual",    "meta": 100, "resultado": 100.84, ...}
]
```

### Sub-indicadores generados por el ETL

El pipeline expande automáticamente las series en registros de sub-indicadores mediante `expandir_series_como_subindicadores()`:

| Sub-ID | Serie en API | Descripción |
|--------|-------------|-------------|
| 274.1 | `"Posgrado Presencial"` | Cumplimiento estudiantes antiguos posgrado presencial |
| 274.2 | `"Pregrado Presencial"` | Cumplimiento estudiantes antiguos pregrado presencial |
| 274.3 | `"Pregrado Virtual"` | Cumplimiento estudiantes antiguos pregrado virtual |
| 274.4 | `"Posgrado Virtual"` | Cumplimiento estudiantes antiguos posgrado virtual |

Cada sub-indicador hereda `Proceso`, `Periodicidad` y `Sentido` del padre (274).

### Variables dentro de cada serie

| Símbolo | Significado |
|---------|-------------|
| `TEMS` | Total Estudiantes Matriculados por Semestre (ejecución) |
| `TEP` | Total Estudiantes Presupuestados (meta) |

La fórmula aplicada en Kawak es: `resultado = (TEMS / TEP) × 100`

---

## 4. Grupo C — Plan de Retos (373, 390, 414-418, 420, 469-471)

### Contexto

Los indicadores de Plan de Retos miden el cumplimiento del plan anual de actividades de cada vicerrectoría/gerencia. Están listados en `IDS_PLAN_ANUAL` (`config/settings.toml`) y tienen umbrales especiales:
- **Alerta:** cumplimiento < 95% (vs. 80% del resto)
- **Tope:** cumplimiento máximo reportado = 100%

### Indicadores padre

| ID | Nombre | N sub-series |
|----|--------|-------------|
| 373 | Cumplimiento de planes anuales por líneas estratégicas | 6 |
| 390 | Cumplimiento Plan Anual por escuela | 12 |
| 414 | Cumplimiento Plan Anual Rectoría | 9 |
| 415 | Cumplimiento Plan Anual Vicerrectoría del Estudiante | 14 |
| 416 | Cumplimiento Plan Anual Vicerrectoría de Crecimiento | 6 |
| 417 | Cumplimiento Plan Anual Vicerrectoría Financiera | 6 |
| 418 | Cumplimiento Plan Anual Vicerrectoría Académica | 9 |
| 420 | Cumplimiento Plan Anual Gerencia de Estrategia | 6 |
| 469 | Cumplimiento Plan Anual Áreas sede Medellín | 9 |
| 470 | Cumplimiento plan anual Secretaria académica y de extensión | 5 |
| 471 | Cumplimiento plan anual Gerencia de Talento Humano | 7 |

### Frecuencia y estructura en la API

- **Periodicidad:** Semestral (datos disponibles en marzo, junio, septiembre y diciembre)
- **Campo `resultado`:** Promedio global calculado en Kawak
- **Campo `series`:** N sub-series, una por gerencia/dirección/facultad

**Variables dentro de cada serie (símbolos varían por indicador padre).**
Cada serie trae exactamente dos variables: una de "% avance" (ejecución real) y
otra de "% esperado" (meta / avance esperado). El par de símbolos es fijo por
indicador padre y se aplica igual a todas sus sub-series. Verificados contra
`data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx` (la tabla anterior
tenía 415 y 416 incorrectos — corregidos aquí):

| Indicador | Símbolo Avance (ejecución) | Símbolo Esperado (meta) |
|-----------|---------------|-----------------|
| 373 | `PAVAN` | `PEAVAN` |
| 390 | `PAPRE` | `PEPRE` |
| 414 | `PAVR`  | `PERE` |
| 415 | `PAVE`  | `PESVE` |
| 416 | `PAVC`  | `PEVE` |
| 417 | `PAVF`  | `PEVF` |
| 418 | `PAVA`  | `PEVA` |
| 420 | `PAGE`  | `PEGE` |
| 469 | `PARM`  | `PAEM` |
| 470 | `PASAE` | `PESAE` |
| 471 | `PAGTH` | `PEGTH` |

Este mapa vive como `_SIMBOLOS_PLAN_ANUAL` en
[`scripts/etl/builders.py`](../scripts/etl/builders.py).

### Mapeo completo de sub-indicadores

#### ID 373 — Planes anuales por líneas estratégicas

| Sub-ID | Serie en API |
|--------|-------------|
| 373.1 | Expansión |
| 373.2 | Educación para toda la vida |
| 373.3 | Trasformación Organizacional |
| 373.4 | Experiencia |
| 373.5 | Sostenibilidad |
| 373.6 | Calidad |

#### ID 390 — Plan Anual por escuela

| Sub-ID | Serie en API |
|--------|-------------|
| 390.1 | ESCUELA DE CIENCIAS BÁSICAS |
| 390.2 | ESCUELA DE  DISEÑO |
| 390.3 | ESCUELA DE OPTIMIZACIÓN, INFRA Y AUTO |
| 390.4 | ESCUELA TIC |
| 390.5 | ESCUELA DE ADMINISTRACIÓN Y COMPETITIVIDAD |
| 390.6 | ESCUELA DE CONTABILIDAD INTERNACIONAL |
| 390.7 | ESCUELA DE NEGOCIOS Y DESARROLLO INTERNACIONAL |
| 390.8 | ESCUELA DE COMUNICACIÓN ARTES VISUALES Y DIGITALES |
| 390.9 | ESCUELA DE DERECHO Y GOBIERNO |
| 390.10 | ESCUELA DE MARKETING Y BRANDING |
| 390.11 | ESCUELA DE PSIC, TALENTO HUM Y SOC |
| 390.12 | ESCUELA DE EDUCACIÓN E INNOVACIÓN |

#### ID 414 — Rectoría

| Sub-ID | Serie en API |
|--------|-------------|
| 414.1 | Vicerrectoría de crecimiento |
| 414.2 | Vicerrectoría del estudiante |
| 414.3 | Vicerrectoría financiera |
| 414.4 | Gerencia de estrategia |
| 414.5 | Gerencia de  talento humano y desarrollo |
| 414.6 | Gerencia sede Medellín |
| 414.7 | Secretaria general |
| 414.8 | Gerencia de educación virtual |
| 414.9 | Vicerrectoría académica |

#### ID 415 — Vicerrectoría del Estudiante

| Sub-ID | Serie en API |
|--------|-------------|
| 415.1 | Gerencia de operaciones |
| 415.2 | Gerencia de servicio y permanencia |
| 415.3 | Gerencia de tecnología e innovación digital |
| 415.4 | BI y analítica |
| 415.5 | Dirección nacional de registro y control |
| 415.6 | Dirección de Experiencia E Inclusion |
| 415.7 | Director de gobierno digital |
| 415.8 | Gerente de innovación y producto |
| 415.9 | Dirección de desarrollo e innovación |
| 415.10 | Director de operaciones IT |
| 415.11 | Director de operaciones integrales |
| 415.12 | Director de permanencia |
| 415.13 | Director de servicio |
| 415.14 | Direccion bienestar universitario y huella grancolombiana |

#### ID 416 — Vicerrectoría de Crecimiento

| Sub-ID | Serie en API |
|--------|-------------|
| 416.1 | Gerencia de matriculas |
| 416.2 | Gerencia de mercadeo |
| 416.3 | Gerencia de servicios corporativos |
| 416.4 | Director B2B y B2C |
| 416.5 | Director de producto |
| 416.6 | Director de estrategia marca |

#### ID 417 — Vicerrectoría Financiera

| Sub-ID | Serie en API |
|--------|-------------|
| 417.1 | Dirección de contabilidad |
| 417.2 | Dirección de infraestructura |
| 417.3 | Dirección planeación financiera y tesorería |
| 417.4 | Dirección de servicios administrativos |
| 417.5 | Dirección de compras y abastecimiento |
| 417.6 | Dirección de relacionamiento de CSU |

#### ID 418 — Vicerrectoría Académica

| Sub-ID | Serie en API |
|--------|-------------|
| 418.1 | Dirección aseguramiento de la calidad |
| 418.2 | Dirección relaciones nacionales e internacionales |
| 418.3 | Secretaria académica y de extensión |
| 418.4 | Dirección de docencia |
| 418.5 | Dirección de currículo presencial y virtual |
| 418.6 | Facultad ingeniería diseño e innovación |
| 418.7 | Facultad negocios gestión y sostenibilidad |
| 418.8 | Facultad sociedad cultura y creatividad |
| 418.9 | Dirección investigación innovación y creación |

#### ID 420 — Gerencia de Estrategia

| Sub-ID | Serie en API |
|--------|-------------|
| 420.1 | SGC |
| 420.2 | SGA |
| 420.3 | Riesgos |
| 420.4 | Auditoría |
| 420.5 | Planeación estratégica |
| 420.6 | Estudios Internos |

#### ID 469 — Plan Anual Áreas sede Medellín

| Sub-ID | Serie en API |
|--------|-------------|
| 469.1 | FSCC- DERECHO Y GOBIERNO-DERECHO |
| 469.2 | FIDI-TIC -INGENIERIA DE SISTEMAS |
| 469.3 | FIDI-OPINA-INGENIERIA INDUSTRIAL |
| 469.4 | FNGS-NEG Y DLLO INTER-NEGOCIOS INTERNACIONALES |
| 469.5 | FSCC- EST.PSIC,TH Y SOC- PSICOLOGIA |
| 469.6 | FIDI-CIENCIAS BÁSICAS MED |
| 469.7 | ADMON DE EMPRESAS |
| 469.8 | FSCC - MARKETING MED |
| 469.9 | FIDI-DISEÑO-DISEÑO GRAFICO |

#### ID 470 — Plan Anual Secretaria académica y de extensión

| Sub-ID | Serie en API |
|--------|-------------|
| 470.1 | DIRECTOR EDITORIAL |
| 470.2 | DIRECTOR CENTRO MEDIOS AUDIOVISUALES |
| 470.3 | DIRECTOR AGENCIA TROMPO |
| 470.4 | DIRECTOR DE GRADUADOS Y PROYECCION EMP. |
| 470.5 | DIRECTOR SISTEMA NACIONAL DE BIBLIOTECAS |

#### ID 471 — Plan Anual Gerencia de Talento Humano

| Sub-ID | Serie en API |
|--------|-------------|
| 471.1 | DIRECTOR DE BIENESTAR Y RELAC. LABORALES |
| 471.2 | DIRECTOR DE FORMACION Y DESARROLLO |
| 471.3 | DIRECTOR DE RELACIONES PUBLICAS Y PROTOC |
| 471.4 | DIRECTOR DE COMUNICACIONES |
| 471.5 | DIRECTOR DE ADMON LABORAL Y COMPENSACION |
| 471.6 | DIRECTOR DE GESTION DE TALENTO |
| 471.7 | DIRECTOR DE COMUN. EXTERNAS SED MEDELLIN |

### Lógica de extracción del consolidado global (indicador padre)

1. **Extracción en catálogo:** `Extraer Meta y ejecución directamente de fuente`
2. El ETL toma `resultado` y `meta` directamente del registro API (valor global ya calculado por Kawak).
3. **TipoCalculo:** `Cierre` — en Consolidado Cierres, se usa el período de diciembre; si no existe, el último disponible del año.
4. El indicador padre (ej. `420`) permanece como consolidado global en todas las hojas.

### Lógica de extracción de sub-indicadores

Los sub-indicadores (ej. `420.1`, `420.2`) **no existen como filas independientes en la API**. Están embebidos en el campo `series` del indicador padre. El ETL los extrae mediante la función `expandir_series_como_subindicadores()` en [`scripts/etl/builders.py`](../scripts/etl/builders.py).

**Flujo de extracción para sub-indicadores:**

⚠️ **Importante:** `serie["resultado"]` NO es la ejecución/avance real — es un
% de cumplimiento ya pre-calculado por Kawak (`avance / esperado × 100`). Y
`serie["meta"]` viene **hardcodeado a 100** en la fuente, no es el avance
esperado real del período. La ejecución (Meta) y el avance (Ejecución) deben
tomarse de las variables `variables[].simbolo` de la serie, usando el par
`(símbolo avance, símbolo esperado)` de la tabla anterior para el indicador
padre correspondiente — NO de `resultado`/`meta`.

```
Registro API: ID=420, fecha=2025-06-30
  series: [
    {"nombre": "SGC", "resultado": 93.10, "meta": 100,
     "variables": [{"simbolo": "PAGE", "valor": 54}, {"simbolo": "PEGE", "valor": 58}]},
    ...
  ]

Expansión (config/series_subindicadores.toml + _SIMBOLOS_PLAN_ANUAL["420"] = (PAGE, PEGE)):
  "SGC" → 420.1 → Ejecucion=PAGE=54, Meta=PEGE=58, fecha=2025-06-30
```

Nótese que `54/58 × 100 = 93.10`, exactamente el `resultado` reportado por
Kawak — confirmando que `resultado` es un cumplimiento, no una ejecución.
Si las variables no estuvieran presentes en una serie puntual, el ETL cae
como último recurso a `resultado`/`meta` (comportamiento defensivo, no el
camino esperado).

**Meta en el corte de diciembre:** al leer el símbolo "esperado" real (en vez
de `meta=100` hardcodeado), el corte de diciembre muestra Meta≈100 de forma
**natural** — la planificación anual está completa al cierre de año — sin
necesidad de ninguna regla especial de negocio en el código. En meses
intermedios la Meta refleja el avance esperado parcial correcto (ej. PEGE=58
en junio).

**Coincidencia de nombres:** la búsqueda de sub-serie → sub-ID es case-insensitive y normaliza espacios múltiples, por lo que variaciones menores de escritura en el API no rompen el mapeo.

---

---

## 4. Grupo D — Cronograma de proyectos estratégicos (1-13, 10.1, 13.1, 900-928)

### Contexto

Los proyectos estratégicos institucionales se reportan mes a mes en Kawak, pero **no tienen filas propias** en el catálogo Kawak. Sus valores de ejecución y meta están embebidos en el campo `series` del indicador padre que varía por año:

| Año de vigencia | ID padre | Nombre del indicador padre |
|-----------------|----------|---------------------------|
| 2024 | 441 | Cumplimiento a cronograma de proyectos 2024 |
| 2025 | 509 | Cumplimiento a cronograma de proyectos 2025 |
| 2026 | 603 | Cumplimiento a cronograma de proyectos 2026 |

> ⚠️ El indicador padre (509, 603…) puede contener datos de varios años en la API; el ETL filtra por `fecha.year == año_del_padre` para extraer solo el año correcto.

### Estructura en la API

El campo `series` del padre contiene una entrada por proyecto activo ese año:

```python
# ID 509, fecha 2025-06-30
series = [
  {"nombre": "Ecosistema E3",   "resultado": 99.0,  "meta": 90.0, "variables": [...]},
  {"nombre": "ADN POLI",        "resultado": 100.0, "meta": 90.0, "variables": [...]},
  {"nombre": "SER PRO Fase II", "resultado": 0,     "meta": 90.0, "variables": [...]},
  ...  # 18 proyectos en 2025
]
```

### Mapeo completo de proyectos por año

#### Proyectos activos en 2025 (ID 509 — 18 series)

| ID indicador | Nombre en el listado | Nombre de la serie en API |
|-------------|---------------------|--------------------------|
| 909 | Acreditación Institucional Fase III - Etapa de evaluación externa | Acreditación Institucional fase III Etapa de evaluación externa o evaluación por pares |
| 913 | Actualización de TRD y creación del Plan de gestión documental | Actualización de TRD y creación del Plan de Gestión documental |
| 904 | Ecosistema E3 | Ecosistema E3 |
| 910 | Fortalecimiento de la investigacion, la innovación y la creación | Fortalecimiento de la investigación, la innovación y la creación |
| 911 | Fortalecimiento de planta docente | Fortalecimiento de planta docente |
| 915 | Gobierno de datos | Gobierno de datos |
| 916 | Herramientas de Gestión para el mejoramiento continuo | Herramientas de Gestión para el mejoramiento continuo |
| 922 | Proyecto de permanencia institucional | Proyecto de Permanencia institucional |
| 918 | Reingeniería de aplicaciones | Reingenieria de aplicaciones |
| 919 | SOPHIA Sistema de optimización y programación horaria institucional | SOPHIA Sistema de Optimización y Programación Horaria Institucional Académica I Fase |
| 924 | Modelo de seguimiento al graduado | Modelo de seguimiento al graduado |
| 906 | Ser PRO | SER PRO Fase II |
| 901 | Centro de Idiomas Fase I - Stand By | Centro de Idiomas POLI |
| 12 | Creación del colegio de educación media virtual - Stand By | Colegio Virtual |
| 11 | Creación del Instituto de Educación para el trabajo y el desarrollo humano - Stand By | Institución de educación para el trabajo y desarrollo humano IETDH |
| 912 | Plataforma de gestión de la información curricular Fase I | Plataforma Tecnologica de Gestión de información Curricular |
| 927 | Sistema de medición de resultados de aprendizaje | Sistema de medición de resultados de aprendizaje |
| 914 | ADN Poli | ADN POLI |

#### Proyectos activos en 2026 (ID 603 — 20 series)

Los proyectos continuos de 2025 aparecen con el **mismo nombre** de serie en 2026; los nuevos proyectos o con nombre cambiado se listan a continuación:

| ID indicador | Nombre en el listado | Nombre de la serie en API (2026) |
|-------------|---------------------|----------------------------------|
| 910 | Fortalecimiento de la investigación… | Fortalecimiento de la investigación, la innovación y la creación |
| 911 | Fortalecimiento de planta docente | Fortalecimiento de planta docente |
| 915 | Gobierno de datos | Gobierno de datos |
| 916 | Herramientas de Gestión… | Herramientas de Gestión para el mejoramiento continuo |
| 914 | ADN Poli | ADN POLI / ADN POLI FASE II |
| 912 | Plataforma de gestión información curricular Fase I | Plataforma de gestión de información curricular Fase 1 |
| 924 | Modelo de seguimiento al graduado | Redefinición de Modelo de seguimiento y acompañamiento al Graduado |
| 920 | Hubspot CRM | Implementación de Hubspot Eduvida |
| 926 | Titulación Autogestionada | Titulación Autogestionada |

**Series 2026 sin ID asignado aún** (proyectos nuevos no en el listado actual):

| Serie en API | Estado |
|-------------|--------|
| Portal de Talento Humano | Sin ID — requiere asignación |
| Proyecto E2E - ILUMNO | Sin ID — requiere asignación |
| Homologaciones IA - ILUMNO | Sin ID — requiere asignación |
| Modelo Predictivo de deserción basado en Scoring | Sin ID — requiere asignación |
| Voice IA - Recupero | Sin ID — requiere asignación |
| Whatsapp IA | Sin ID — requiere asignación |
| Adecuaciones campus principal | Sin ID — requiere asignación |
| Implementación reforma Curricular | Sin ID — requiere asignación |
| Optimización SEO AEO Captación | Sin ID — requiere asignación |
| Sistematización proceso de la ORII | Sin ID — requiere asignación |

> Para añadir un nuevo proyecto: asignar ID en el consolidado y agregar la entrada en `config/series_subindicadores.toml` bajo `[cronograma_proyectos.series]`.

#### Proyectos en 2024 (ID 441)

El indicador 441 no tiene sub-series disponibles en el API actual (0 filas en el consolidado). Los proyectos del listado que no aparecen en 2025 ni 2026 (IDs 1-10, 13, 10.1, 13.1, 900, 902, 903, 905, 907, 908, 917, 921, 923, 925, 928) corresponden probablemente al año 2024 y deben verificarse en el archivo Kawak 2024 o en la API actualizada.

### Lógica de extracción en el ETL

La función `extraer_cronograma_proyectos()` en `scripts/etl/builders.py`:

1. Lee `CRONOGRAMA_PADRES` → `{2024: "441", 2025: "509", 2026: "603"}`
2. Lee `_CRONOGRAMA_SERIES_FLAT` → `{nombre_serie_norm → id_proyecto}`
3. Filtra `df_api` para filas donde `Id` sea uno de los padres
4. Para cada fila, verifica que `fecha.year == año_correspondiente_al_padre`
5. Parsea el JSON `series` de esa fila
6. Para cada serie, normaliza el nombre y busca en `_CRONOGRAMA_SERIES_FLAT`
7. Genera un registro con `Id = id_proyecto`, `Ejecucion = serie.resultado`, `Meta = serie.meta`

```
Ejemplo de expansión (ID 509, 2025-06-30):
  serie: {"nombre": "Ecosistema E3", "resultado": 99.0, "meta": 90.0}
    → nombre_norm = "ecosistema e3"
    → proj_id    = "904"
    → Registro: Id=904, Ejecucion=99.0, Meta=90.0, fecha=2025-06-30
                 LLAVE="904-2025-06-30"
```

**Normalización resistente a encoding:** el nombre de la serie en el API puede contener entidades HTML (`&oacute;`) o caracteres de reemplazo UTF-8 (`U+FFFD`). La función `_normalizar_nombre_serie()` decodifica HTML, elimina reemplazos Unicode y descarta acentos (ASCII-only) antes de comparar. Las entradas en el TOML se guardan en español correcto; ambos lados quedan normalizados de la misma forma.

### Integración en el pipeline

**Paso 10.45** (en `scripts/actualizar_consolidado.py`, entre paso 10.4 y 10.5):

```python
regs_proy = extraer_cronograma_proyectos(df_api, llaves_hist)
regs_hist += regs_proy
```

> Solo se generan registros para `Consolidado Histórico`. No hay versiones semestral/cierres independientes porque los proyectos son mensuales y el consolidado semestral/cierres hereda desde el histórico.

### Configuración (`config/series_subindicadores.toml`)

```toml
[cronograma_proyectos.padres]
"2024" = 441
"2025" = 509
"2026" = 603

[cronograma_proyectos.series]
"Ecosistema E3"                 = "904"
"Gobierno de datos"             = "915"
"ADN POLI"                      = "914"
# ... (23 entradas en total)
```

Para agregar un nuevo proyecto: una línea en `[cronograma_proyectos.series]`, sin modificar Python.

---

## 5. Mecanismo de expansión de sub-series

### Configuración (`config/series_subindicadores.toml`)

```toml
[subindicadores]
"274.1" = "Posgrado Presencial"
"420.1" = "SGC"
"420.2" = "SGA"
# ... etc.
```

Para **agregar nuevos sub-indicadores** en el futuro: añadir una línea en el archivo TOML y reiniciar el pipeline. No se requiere modificar código Python.

### Función ETL (`expandir_series_como_subindicadores`)

La función opera en 3 modos según la hoja destino:

| Modo | Filtro de fechas | Hoja destino |
|------|-----------------|-------------|
| `historico` | Todos los períodos | Consolidado Histórico |
| `semestral` | Solo `mes ∈ {6, 12}` | Consolidado Semestral |
| `cierres` | Un registro por año: diciembre si existe, si no el último | Consolidado Cierres |

### Integración en el pipeline (paso 10.4)

```python
# scripts/actualizar_consolidado.py — paso 10.4
regs_sub_hist    = expandir_series_como_subindicadores(df_api, llaves_hist,    modo="historico")
regs_sub_sem     = expandir_series_como_subindicadores(df_api, llaves_sem,     modo="semestral")
regs_sub_cierres = expandir_series_como_subindicadores(df_api, llaves_cierres, modo="cierres")
regs_hist    += regs_sub_hist
regs_sem     += regs_sub_sem
regs_cierres += regs_sub_cierres
```

### LLAVE de deduplicación

Los sub-indicadores usan la misma fórmula que el resto:
```
LLAVE = sub_id + "-" + YYYY + "-" + MM + "-" + DD
# Ejemplo: "420.1-2025-06-30"
```

---

## 6. Identificación de indicadores Plan de Retos en la base API

### Filtrar por ID

```python
import pandas as pd, ast

ids_plan_retos = {414, 415, 416, 417, 418, 420}

df_api = pd.read_excel("data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx")
df_retos = df_api[df_api["ID"].isin(ids_plan_retos)].dropna(subset=["series"])
df_retos = df_retos[df_retos["series"].astype(str).str.strip() != ""]
```

### Listar sub-series disponibles

```python
for _, row in df_retos.iterrows():
    series_list = ast.literal_eval(row["series"])
    print(f"ID {row['ID']} | {row['fecha'].date()}")
    for s in series_list:
        print(f"  - {s['nombre']:50s}  resultado={s.get('resultado', 'N/A')}")
```

### Identificar en Kawak (`data/raw/Kawak/YYYY.xlsx`)

En los archivos Kawak, los indicadores Plan de Retos aparecen como **múltiples filas** con el mismo `Id` y distintos nombres en la columna `Serie`:

```
Id=420  Serie="Consolidado Global"            → valor agregado
Id=420  Serie="SGC"                           → 420.1
Id=420  Serie="SGA"                           → 420.2
Id=420  Serie="Riesgos"                       → 420.3
Id=420  Serie="Auditoría"                     → 420.4
Id=420  Serie="Planeación estratégica"        → 420.5
Id=420  Serie="Estudios Internos"             → 420.6
```

El tipo de cálculo Kawak para estos indicadores es `"Aplicar la fórmula a cada serie y luego promediar los resultados"`.

---

## 7. Resumen de reglas por grupo

| Grupo | IDs | Fuente de Ejecución | Fuente de Meta | Mecanismo ETL |
|-------|-----|--------------------|--------------|--------------------|
| Matrículas nuevos | 379, 381-384 | `variables[simbolo]` | `variables[simbolo_meta]` | Desglose Variables |
| Estudiantes antiguos | 274 | `resultado` (global) | `meta` (global) | Directo de fuente |
| Estudiantes antiguos (sub) | 274.1-274.4 | `series[i].resultado` | `series[i].meta` | `expandir_series_como_subindicadores()` |
| Plan de Retos — líneas | 373 | `resultado` (global) | `meta` (global) | Directo de fuente |
| Plan de Retos — líneas (sub) | 373.1-373.6 | `series[i].resultado` | `series[i].meta` | `expandir_series_como_subindicadores()` |
| Plan de Retos — escuelas | 390 | `resultado` (global) | `meta` (global) | Directo de fuente |
| Plan de Retos — escuelas (sub) | 390.1-390.12 | `series[i].resultado` | `series[i].meta` | `expandir_series_como_subindicadores()` |
| Plan de Retos — vicerrectorías | 414-418, 420 | `resultado` (global) | `meta` (global) | Directo de fuente |
| Plan de Retos — VR (sub) | 414.x-420.x | `series[i].resultado` | `series[i].meta` | `expandir_series_como_subindicadores()` |
| Plan de Retos — sede / áreas | 469-471 | `resultado` (global) | `meta` (global) | Directo de fuente |
| Plan de Retos — sede (sub) | 469.x-471.x | `series[i].resultado` | `series[i].meta` | `expandir_series_como_subindicadores()` |
| Proyectos cronograma | 11, 12, 901-927 | `series[i].resultado` del padre | `series[i].meta` del padre | `extraer_cronograma_proyectos()` |

---

## 8. Actualizaciones periódicas

### Qué hacer al inicio de un nuevo año

1. Verificar en el archivo API (`data/raw/API/YYYY.xlsx`) que los IDs del plan de retos tienen datos en el campo `series`.
2. Si hay nuevas sub-series en el API que no existen en `config/series_subindicadores.toml`, añadirlas con el siguiente sub-ID disponible.
3. Ejecutar `python scripts/consolidar_api.py` para regenerar el consolidado.
4. Ejecutar `python scripts/actualizar_consolidado.py`.

### Cómo verificar que los sub-indicadores se generaron

```python
import pandas as pd
df = pd.read_excel("data/output/Resultados Consolidados.xlsx",
                   sheet_name="Consolidado Historico")
sub_ids = df[df["Id"].astype(str).str.contains(r"\.", na=False)]["Id"].unique()
print(sorted(sub_ids))
# Debe incluir: 274.1, 274.2, 274.3, 274.4, 420.1, 420.2, ... etc.
```
