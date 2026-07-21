# Guía de Actualización — Resultados_Consolidados.xlsx

**Versión:** 2.0 · **Fecha:** Junio 2026  
**Archivo objetivo:** `data/output/Resultados Consolidados.xlsx`

---

## Tabla de contenidos

1. [Visión general](#1-visión-general)
2. [Prerrequisitos y fuentes de datos](#2-prerrequisitos-y-fuentes-de-datos)
3. [Estructura del archivo](#3-estructura-del-archivo)
4. [Proceso de actualización paso a paso](#4-proceso-de-actualización-paso-a-paso)
5. [Lógica de periodicidad y fechas](#5-lógica-de-periodicidad-y-fechas)
6. [Lógica de extracción de Meta y Ejecución](#6-lógica-de-extracción-de-meta-y-ejecución)
7. [Manejo de "No Aplica"](#7-manejo-de-no-aplica)
8. [Reglas de consolidación por hoja](#8-reglas-de-consolidación-por-hoja)
9. [Cálculo de cumplimiento](#9-cálculo-de-cumplimiento)
10. [Campos calculados vs. campos crudos](#10-campos-calculados-vs-campos-crudos)
11. [Deduplicación y control de duplicados](#11-deduplicación-y-control-de-duplicados)
12. [Correcciones automáticas (AGENT5)](#12-correcciones-automáticas-agent5)
13. [Validaciones y contratos de datos](#13-validaciones-y-contratos-de-datos)
14. [Versionado y respaldo](#14-versionado-y-respaldo)
15. [Configuración y parámetros clave](#15-configuración-y-parámetros-clave)
16. [Casos especiales](#16-casos-especiales)
17. [Diagnóstico de errores frecuentes](#17-diagnóstico-de-errores-frecuentes)
18. [Archivos y módulos de referencia](#18-archivos-y-módulos-de-referencia)

---

## 1. Visión general

`Resultados Consolidados.xlsx` es el **archivo de salida principal** del sistema de indicadores. Consolida datos provenientes de la API Kawak, aplica lógica de extracción multi-nivel, calcula cumplimientos y los agrega en tres vistas temporales: histórica (nivel mes), semestral y de cierres anuales.

### Flujo de alto nivel

```
API Kawak (raw)
      │
      ▼
consolidar_api.py        ← Paso obligatorio previo
      │
      ▼
Consolidado_API_Kawak.xlsx
      │
      ▼
actualizar_consolidado.py  ← Actualización principal
      │
      ├─▶ Consolidado Historico
      ├─▶ Consolidado Semestral
      ├─▶ Consolidado Cierres
      └─▶ Catalogo Indicadores (regenerado)
```

---

## 2. Prerrequisitos y fuentes de datos

### 2.1 Archivos requeridos antes de ejecutar

| Archivo | Ruta | Descripción |
|---|---|---|
| `Consolidado_API_Kawak.xlsx` | `data/raw/Fuentes Consolidadas/` | Datos crudos de API (Meta, Ejecución, variables, series) |
| `Resultados_Consolidados_Fuente.xlsx` | `data/raw/` | Base histórica inicial y estructura de hojas |
| `Indicadores Kawak.xlsx` | `data/raw/Fuentes Consolidadas/` | Catálogo maestro de indicadores válidos |
| `Indicadores por CMI.xlsx` | `data/raw/` | Mapeo de procesos/CMI |
| `Ficha_Tecnica.xlsx` | `data/raw/` | Definiciones de indicadores |
| `lmi_reporte.xlsx` | `data/raw/` | Clasificación de tipo de métrica |
| `settings.toml` | `config/` | Parámetros de negocio (año, IDs especiales, topes) |
| `data_contracts.yaml` | `config/` | Reglas de validación de columnas |

### 2.2 Cómo obtener el Consolidado_API_Kawak actualizado

```bash
# Paso 1: Descargar/actualizar datos de la API
python scripts/consolidar_api.py

# Verificar que el archivo fue generado correctamente
# data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx
```

> **Importante:** `actualizar_consolidado.py` **no ejecuta** `consolidar_api.py` automáticamente. Ambos deben correr en secuencia.

---

## 3. Estructura del archivo

### 3.1 Hojas principales

| Hoja | Nivel de detalle | Descripción |
|---|---|---|
| `Consolidado Historico` | Mensual | Un registro por indicador × período válido |
| `Consolidado Semestral` | Semestral | Agregación o cierre de cada semestre |
| `Consolidado Cierres` | Anual | Cierre o agregación anual (diciembre o acumulado) |
| `Catalogo Indicadores` | N/A | Metadatos, reglas de extracción y tipo de cálculo |
| `Logica` | N/A | Documentación de reglas de negocio |
| `Variables` | N/A | Mapeo Símbolo → Campo para indicadores Tipo 2 |
| `Desglose Series` | N/A | Reglas de desglose de series por indicador |

### 3.2 Columnas estándar (hojas Consolidado)

| Columna | Tipo | Origen | Descripción |
|---|---|---|---|
| `Id` | string | API | Identificador único del indicador |
| `Indicador` | string | Kawak | Nombre del indicador |
| `Proceso` | string | API/CMI | Proceso o dependencia |
| `Periodicidad` | string | Catálogo | Frecuencia: Mensual / Trimestral / Semestral / Anual / Bimestral |
| `Sentido` | string | Catálogo | Positivo (más = mejor) / Negativo (menos = mejor) |
| `Fecha` | date | API | Último día del período reportado |
| `Año` | integer | **Fórmula** | `=YEAR(Fecha)` |
| `Mes` | string | **Fórmula** | `=NOMPROPIO(TEXTO(Fecha;"mmmm"))` |
| `Semestre` | string | **Fórmula** | `=SI(MES(Fecha)<=6, AÑO&"-1", AÑO&"-2")` |
| `Meta` | float | API/Catálogo | Valor objetivo del período |
| `Ejecucion` | float | Extracción multi-nivel | Valor real ejecutado |
| `Cumplimiento` | float | **Fórmula** | `=MIN(IFERROR(...), TOPE)` — con tope |
| `Cumplimiento Real` | float | **Fórmula** | `=IFERROR(Ejec/Meta, 0)` — sin tope |
| `Meta_Signo` | string | Catálogo | Formato: `%`, `ENT`, `DEC`, `$` |
| `Ejecucion_Signo` | string | Catálogo | Formato o `"No Aplica"` |
| `Decimales_Meta` | integer | Catálogo | Decimales para visualización de Meta |
| `Decimales_Ejecucion` | integer | Catálogo | Decimales para visualización de Ejecución |
| `LLAVE` | string | **Fórmula** | `=Id&"-"&AÑO&"-"&MES&"-"&DIA` — clave única |
| `Tipo_Registro` | string | Clasificación | Vacío / `"Metrica"` / `"No Aplica"` |

---

## 4. Proceso de actualización paso a paso

### Ejecución del script principal

```bash
python scripts/actualizar_consolidado.py
```

### Pasos internos del pipeline (15 etapas)

```
Paso  1 — CARGAR FUENTE
         Lee Consolidado_API_Kawak.xlsx
         Normaliza IDs, columnas y tipos de dato

Paso  2 — VALIDAR CONTRATO (Capa 1)
         Verifica columnas requeridas y tipos
         ➜ Bloquea si falla

Paso  3 — CARGAR CATÁLOGO
         Lee Extraccion_map, TipoCalculo_map, TipoIndicador_map, Variables_Campo_map

Paso  4 — CARGAR METADATOS
         Consolida Kawak, CMI, Ficha Técnica, LMI

Paso  5 — ABRIR WORKBOOK EXISTENTE
         Carga hojas actuales para comparar LLAVEs y preservar signos

Paso  6 — CONSTRUIR REGISTROS (paralelo)
         ├─ construir_registros_historico()
         ├─ construir_registros_semestral()
         └─ construir_registros_cierres()

Paso  7 — APLICAR CORRECCIONES (AGENT5)
         Topa Ejecución > 1.3 → 1.3
         Marca Meta = 0 para revisión

Paso  8 — VALIDACIÓN INTERMEDIA
         Valida registros post-construcción

Paso  9 — ESCRIBIR FILAS en hojas de Excel

Paso 10 — REPARAR VALORES
         Completa metas faltantes desde lookup
         Recalcula agregaciones multi-serie

Paso 11 — DEDUPLICAR Y REESCRIBIR FÓRMULAS
         Elimina duplicados por LLAVE
         Reescribe fórmulas con número de fila correcto

Paso 12 — ACTUALIZAR CATÁLOGO
         Regenera la hoja Catalogo Indicadores

Paso 13 — GUARDAR
         Escribe Resultados Consolidados.xlsx
         Escribe Resultados Consolidados VALORES.xlsx (sin fórmulas)

Paso 14 — REGISTRO DE AUDITORÍA
         Guarda artifacts/audit/[timestamp].json

Paso 15 — RESPALDO
         Crea .versions/[timestamp]_pre_consolidacion.xlsx
```

---

## 5. Lógica de periodicidad y fechas

### 5.1 Meses válidos por periodicidad

| Periodicidad | Meses válidos |
|---|---|
| `Mensual` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 |
| `Bimestral` | 2, 4, 6, 8, 10, 12 |
| `Trimestral` | 3, 6, 9, 12 |
| `Semestral` | 6, 12 |
| `Anual` | 12 |

### 5.2 Regla de fecha válida

Una fecha es válida **solo si**:
1. El mes está dentro de los meses válidos para la periodicidad del indicador, **Y**
2. La fecha es el **último día** de ese mes.

```
✅ 2025-06-30  →  válido para Semestral, Trimestral, Mensual, Bimestral
❌ 2025-06-29  →  inválido (no es último día)
❌ 2025-07-31  →  inválido para Semestral (julio no está en [6,12])
```

### 5.3 Lógica de Semestre

La columna `Semestre` se genera con la fórmula:

```excel
=SI(MES(Fecha)<=6, AÑO(Fecha)&"-1", AÑO(Fecha)&"-2")
```

| Fecha | Semestre |
|---|---|
| 2025-06-30 | 2025-1 |
| 2025-12-31 | 2025-2 |
| 2024-03-31 | 2024-1 |

---

## 6. Lógica de extracción de Meta y Ejecución

La extracción usa una estrategia de **5 niveles de prioridad**, aplicados en orden. El primer nivel que produce un valor válido detiene la búsqueda.

### Nivel 1 — Detección de "No Aplica"
Ver sección 7.

### Nivel 2 — Tipos de extracción de series (columna `Extraccion` del Catálogo)

| Valor en catálogo | Lógica |
|---|---|
| `"Sumar variables de series y luego aplicar fórmula"` | Suma los valores de variables por serie, luego aplica fórmula |
| `"Promediar variables y luego aplicar fórmula"` | Promedia las variables por serie, luego suma series |
| `"Aplicar fórmula a cada serie y luego promediar"` | Aplica fórmula a cada serie, luego promedia resultados |
| `"Aplicar fórmula a cada serie y luego sumar"` | Aplica fórmula a cada serie, luego suma resultados |

### Nivel 3 — Desglose de Series (Indicadores con lookup)
Extrae directamente del JSON de series → busca en tabla `api_kawak_lookup[(id, fecha)]`.

### Nivel 4 — Desglose de Variables (Indicadores Tipo 2)
Usa el mapeo `Variables/Campo` para encontrar Ejecución/Meta por **símbolos específicos** definidos en la hoja `Variables`.

### Nivel 5 — Heurísticas de respaldo

```
Patrones de configuración (Config_Patrones):
  LAST     → toma el último valor disponible
  VARIABLES → extrae de campo variables
  SUM_SER  → suma todas las series
  AVG      → promedio de valores
  SUM      → suma directa

Palabras clave para Ejecución (KW_EJEC):
  "real", "ejecutado", "logrado", "alcanzado", "obtenido"

Palabras clave para Meta (KW_META):
  "planeado", "objetivo", "programado", "esperado"

Fallback final:
  → Campo "resultado" directo de la API
```

---

## 7. Manejo de "No Aplica"

Un registro se clasifica como **"No Aplica"** cuando se cumple alguna de estas condiciones:

| Condición | Descripción |
|---|---|
| **Explícita** | El campo `analisis` contiene el texto `"no aplica"` (sin distinguir mayúsculas) |
| **Inherente** | No existe valor numérico en `resultado` Y no hay datos en `variables` ni en `series` |

### Comportamiento cuando es "No Aplica"

```
Ejecucion     → NULL (celda vacía)
Ejecucion_Signo → "No Aplica"
Tipo_Registro → "No Aplica"
Meta          → Se preserva si existe
Cumplimiento  → Fórmula retorna "" (cadena vacía)
```

---

## 8. Reglas de consolidación por hoja

### 8.1 Consolidado Historico

- **Fuente:** Todos los registros de la API que cumplan la regla de fecha válida para su periodicidad.
- **Deduplicación:** Por `LLAVE` (`Id-YYYY-MM-DD`). Si existe duplicado, se conserva el registro con mejor ejecución (no nulo, no cero).
- **Incorporación:** Solo se insertan filas cuya `LLAVE` no exista ya en la hoja.

### 8.2 Consolidado Semestral

Funciona con **dos ramas paralelas** según el tipo de cálculo del indicador:

#### Rama A — Indicadores de Cierre (`TipoCalculo = "Cierre"`)
- Filtra registros cuyo mes ∈ {6, 12} (fin de semestre).
- Toma el último día del mes: 30 de junio o 31 de diciembre.
- Usa directamente los valores de Meta y Ejecución de ese mes.

#### Rama B — Indicadores Agregados (`TipoCalculo = "Promedio"` o `"Acumulado"`)
- Agrupa por `(Id, Semestre)` todos los meses del período.

| TipoCalculo | Meta semestral | Ejecución semestral |
|---|---|---|
| `Promedio` | `PROMEDIO(metas del semestre)` | `PROMEDIO(ejecuciones del semestre)` |
| `Acumulado` | `SUMA(metas del semestre)` | `SUMA(ejecuciones del semestre)` |

### 8.3 Consolidado Cierres

- Filtra registros de **diciembre** (mes=12, día=31).
- Un único registro por indicador por año.

| TipoCalculo | Meta anual | Ejecución anual |
|---|---|---|
| `Cierre` | Valor de diciembre | Valor de diciembre |
| `Promedio` | `PROMEDIO(12 meses)` | `PROMEDIO(12 meses)` |
| `Acumulado` | `SUMA(12 meses)` | `SUMA(12 meses)` |

---

## 9. Cálculo de cumplimiento

### 9.1 Fórmula general

```
Si Meta=0 Y Ejec=0:
  Cumplimiento = 1.0  (100% — ambos cero se considera éxito)

Si Sentido="Negativo" Y Ejec=0 Y Meta>0:
  Cumplimiento = 1.0  (100% — cero es perfecto para indicadores negativos)

Si Sentido="Positivo":
  raw = Ejecucion / Meta

Si Sentido="Negativo":
  raw = Meta / Ejecucion

Cumplimiento      = MIN(raw, TOPE)   ← con tope (columna L del Excel)
Cumplimiento Real = raw              ← sin tope (columna M del Excel)
```

### 9.2 Topes dinámicos por indicador

El valor del tope depende de la categoría del indicador:

| Categoría | TOPE | Indicadores |
|---|---|---|
| `IDS_PLAN_ANUAL` | 1.0 (100%) | IDs: 373, 390, 414, 415, 416, 417, 418, 420, 469, 470, 471 (año 2025) |
| `IDS_TOPE_100` | 1.0 (100%) | IDs: 208, 218 |
| Resto de indicadores | 1.3 (130%) | Permite sobre-ejecución hasta 130% |

> **Nota:** Los IDs de `IDS_PLAN_ANUAL` se actualizan anualmente en `config/settings.toml`.

### 9.3 Fórmula Excel generada

```excel
=MIN(IFERROR(
  SI(
    Y(Meta=0, Ejec=0), 1,
    SI(Y(Sentido="Negativo", Ejec=0, Meta>0), 1,
      SI(Sentido="Positivo", Ejec/Meta, Meta/Ejec)
    )
  ), 0), TOPE)
```

---

## 10. Campos calculados vs. campos crudos

| Campo | Naturaleza | Cálculo / Origen |
|---|---|---|
| `Meta` | Crudo | Extraído de API o Catálogo |
| `Ejecucion` | Crudo (post-extracción) | Estrategia multi-nivel (secciones 6 y 7) |
| `Año` | Calculado | `=YEAR(Fecha)` |
| `Mes` | Calculado | `=NOMPROPIO(TEXTO(Fecha,"mmmm"))` |
| `Semestre` | Calculado | `=SI(MES(Fecha)<=6, AÑO&"-1", AÑO&"-2")` |
| `Cumplimiento` | Calculado | `=MIN(IFERROR(...), TOPE)` |
| `Cumplimiento Real` | Calculado | `=IFERROR(Ejec/Meta, 0)` |
| `LLAVE` | Calculado | `=Id&"-"&AÑO(Fecha)&"-"&MES(Fecha)&"-"&DIA(Fecha)` |
| `Tipo_Registro` | Asignado | Clasificación automática: `"Metrica"` / `"No Aplica"` |

---

## 11. Deduplicación y control de duplicados

El sistema garantiza que no haya registros duplicados usando la columna **`LLAVE`**:

```
LLAVE = Id + "-" + Año + "-" + Mes(número) + "-" + Día

Ejemplo: "150-2025-6-30"
```

### Proceso de deduplicación

1. Al construir nuevos registros, se compara cada LLAVE nueva contra las existentes en la hoja.
2. Si la LLAVE ya existe → el registro es ignorado (no se sobreescribe).
3. Si hay duplicados internos en el batch nuevo → se conserva el que tiene mejor ejecución (no nulo, no cero).
4. Después de insertar, se hace una pasada final de deduplicación sobre toda la hoja.
5. Las fórmulas se reescriben con los números de fila correctos tras la limpieza.

---

## 12. Correcciones automáticas (AGENT5)

El módulo AGENT5 aplica correcciones automáticas antes de escribir al Excel:

| Corrección | Condición | Acción |
|---|---|---|
| **Tope de ejecución** | `Ejecucion > 1.3` | Se recorta a `1.3` y se genera alerta de revisión |
| **Meta cero** | `Meta = 0` | Se marca para revisión manual (puede ser error o "cero defectos") |

---

## 13. Validaciones y contratos de datos

### Capa 1 — Validación de entrada (`data_contracts.yaml`)

```
Columnas requeridas en Consolidado_API_Kawak:
  ✓ ID o Id
  ✓ fecha
  ✓ resultado
  ✓ meta
  ✓ variables
  ✓ series

Tipos: fecha → datetime, resultado/meta → numeric
→ El pipeline se bloquea si esta validación falla
```

### Capa 2 — Validación post-construcción

```
✓ Todos los campos requeridos están completos
✓ Fechas válidas para la periodicidad del indicador
✓ Sin NaN en Meta/Ejecucion (excepto "No Aplica")
✓ Sentido ∈ {"Positivo", "Negativo"}
```

### Capa 3 — Validación pre-escritura

```
✓ LLAVE única en el batch
✓ Sin referencias circulares en fórmulas
✓ Alineación de columnas correcta
```

---

## 14. Versionado y respaldo

### Respaldo automático (pre-ejecución)

Antes de cada actualización se crea:

```
.versions/
  Resultados Consolidados_v20250622_143000_pre_consolidacion.xlsx
```

### Archivos de salida

| Archivo | Descripción |
|---|---|
| `data/output/Resultados Consolidados.xlsx` | Archivo principal con fórmulas Excel |
| `data/output/Resultados Consolidados VALORES.xlsx` | Copia con fórmulas materializadas (solo valores) |
| `data/output/Resultados Consolidados.bak.xlsx` | Versión anterior del run previo |

### Auditoría

```
artifacts/audit/20250622_143000.json
  └─ inicio, fin, registros procesados,
     correcciones aplicadas, errores encontrados
```

### Rollback

Si el script falla, restaura automáticamente el respaldo:
```bash
# Manual si se requiere:
cp ".versions/Resultados Consolidados_v[TIMESTAMP].xlsx" \
   "data/output/Resultados Consolidados.xlsx"
```

---

## 15. Configuración y parámetros clave

### `config/settings.toml`

| Parámetro | Tipo | Descripción | Cuándo actualizar |
|---|---|---|---|
| `año_cierre` | integer | Año fiscal activo (ej. `2025`) | Cada enero |
| `ids_plan_anual` | list[int] | IDs con tope 100% por plan anual | Cada planificación anual |
| `ids_tope_100` | list[int] | IDs fijos con tope 100% (`[208, 218]`) | Al agregar/quitar indicadores especiales |

### `Catalogo Indicadores` (hoja del Excel)

| Campo | Valores posibles | Descripción |
|---|---|---|
| `Extraccion` | 4 opciones o vacío | Tipo de extracción de series |
| `TipoCalculo` | `Promedio` / `Acumulado` / `Cierre` | Tipo de agregación para semestral/cierres |
| `Tipo de indicador` | `Tipo 1` / `Tipo 2` | Tipo 1: variables / Tipo 2: series |

### `Variables` (hoja del Excel)

Mapeo de `Símbolo → Campo` para indicadores Tipo 2. Editar cuando se agregan o cambian variables de un indicador.

### `Config_Patrones` (hoja del Excel de salida)

Overrides de patrones de extracción por indicador. Permite ajustar comportamiento sin modificar código.

---

## 16. Casos especiales

### Indicador con múltiples series

```
Ejemplo — Id: 200
  series: [{meta: 50, resultado: 45}, {meta: 50, resultado: 55}]
  Extraccion: "Sumar variables de series..."

  Meta_semestral     = 50 + 50 = 100
  Ejecucion_semestral = 45 + 55 = 100
  Cumplimiento       = MIN(100/100, 1.3) = 1.0  → 100%
```

### Indicador Negativo con Ejecución = 0

```
Sentido = "Negativo"
Ejecucion = 0
Meta = 5

→ Cumplimiento = 1.0  (cero accidentes es perfecto)
```

### Indicador de Plan Anual con sobre-ejecución

```
Id: 373  (está en IDS_PLAN_ANUAL)
Ejecucion = 1.5, Meta = 1.0

→ raw = 1.5
→ TOPE = 1.0  (por ser Plan Anual)
→ Cumplimiento = MIN(1.5, 1.0) = 1.0  → 100%
→ Cumplimiento Real = 1.5            → 150%
```

### Indicador sin Meta disponible

```
Meta = NULL

→ No se puede calcular Cumplimiento
→ AGENT5 lo marca para revisión
→ Paso 10 intenta completar Meta desde lookup del catálogo
```

---

## 17. Diagnóstico de errores frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ValidationError` al inicio | Columnas faltantes en `Consolidado_API_Kawak.xlsx` | Verificar que `consolidar_api.py` corrió correctamente |
| Fechas rechazadas | Fecha no es último día del mes / mes no válido para periodicidad | Revisar datos crudos de la API; corregir en fuente |
| `Meta = 0` en muchos indicadores | Datos de API incompletos o error de extracción | Revisar manualmente los registros marcados en el audit log |
| Ejecución recortada a 1.3 | Valor de ejecución extraído es mayor a 1.3 | Revisar la lógica de extracción del indicador en cuestión; puede requerir ajuste en `Config_Patrones` |
| Duplicados no eliminados | LLAVE mal construida (Id con espacios o formato distinto) | Verificar normalización de IDs en la carga de la API |
| Hoja vacía tras actualización | Todos los registros ya existían (sin datos nuevos) | Confirmar que hay datos nuevos en el período; verificar `año_cierre` en `settings.toml` |
| Fórmulas con `#REF!` | Filas eliminadas durante deduplicación pero fórmulas no actualizadas | El paso 11 debería resolverlo automáticamente; si persiste, re-ejecutar el script |

---

## 18. Archivos y módulos de referencia

| Archivo | Función |
|---|---|
| `scripts/actualizar_consolidado.py` | Orquestador principal del ETL (15 pasos) |
| `scripts/consolidar_api.py` | Prerrequisito: consolida datos de la API |
| `scripts/etl/builders.py` | Construye registros para cada hoja |
| `scripts/etl/extraccion.py` | Estrategia de extracción Meta/Ejecución (5 niveles) |
| `scripts/etl/periodos.py` | Validación de periodicidad y fechas |
| `scripts/etl/cumplimiento.py` | Cálculo de cumplimiento con topes dinámicos |
| `scripts/etl/no_aplica.py` | Detección de registros "No Aplica" |
| `scripts/etl/catalogo.py` | Carga unificada del catálogo |
| `scripts/etl/escritura.py` | Escritura en Excel, deduplicación, fórmulas |
| `scripts/etl/formulas_excel.py` | Generación y materialización de fórmulas |
| `scripts/consolidation/pipeline/orchestrator.py` | Arquitectura modular v8 |
| `config/settings.toml` | Parámetros de negocio (año, IDs, topes) |
| `config/data_contracts.yaml` | Contratos de validación de datos |

---

## Resumen ejecutivo del proceso de actualización

```
MENSUAL (día 5 aprox.):
  1. Ejecutar: python scripts/consolidar_api.py
  2. Ejecutar: python scripts/actualizar_consolidado.py
  3. Revisar: artifacts/audit/[timestamp].json
  4. Verificar: registros con Meta=0 o Ejecucion recortada
  5. Distribuir: Resultados Consolidados.xlsx a usuarios

ANUAL (enero):
  1. Actualizar año_cierre en config/settings.toml
  2. Actualizar ids_plan_anual en config/settings.toml
  3. Revisar y actualizar Catalogo Indicadores (TipoCalculo, Extraccion)
  4. Verificar hoja Variables para indicadores Tipo 2 nuevos
```
