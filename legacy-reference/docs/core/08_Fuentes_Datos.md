# 08 - FUENTES DE DATOS

**Documento:** 08_Fuentes_Datos.md  
**Versión:** 1.0  
**Fecha:** 17 de junio de 2026  
**Status:** ✅ Activo

---

## 1. Resumen

| Categoría | Archivos | Frecuencia de carga |
|-----------|----------|---------------------|
| Excel de entrada (`data/raw/`) | 27 | Manual / post-descarga Kawak |
| Excel de salida (`data/output/`) | 1 workbook (3 hojas) | Tras ejecutar pipeline ETL |
| Bases de datos | 2 (SQLite + PostgreSQL) | Tiempo real / sync |
| Artefactos pipeline | JSON/CSV en `artifacts/` | Post-paso-3 |

---

## 2. Fuentes de Entrada — `data/raw/`

### 2.1 API Kawak (datos de ejecución)

| Ruta | Consumidor | Contenido |
|------|------------|-----------|
| `data/raw/API/2022.xlsx` | `consolidar_api.py` → `Consolidado_API_Kawak.xlsx` | Resultados mensuales 2022 |
| `data/raw/API/2023.xlsx` | `consolidar_api.py` | Resultados mensuales 2023 |
| `data/raw/API/2024.xlsx` | `consolidar_api.py` | Resultados mensuales 2024 |
| `data/raw/API/2025.xlsx` | `consolidar_api.py` | Resultados mensuales 2025 |
| `data/raw/API/2026.xlsx` | `consolidar_api.py` | Resultados mensuales 2026 |

**Estructura típica de columnas API:**
```
ID | nombre | proceso | frecuencia | sentido | fecha | meta | resultado | analisis | variables | series
```

**Notas:**
- La columna `analisis` contiene el texto "no aplica" cuando el indicador no se mide ese período.
- `variables` y `series` son JSON serializados como strings.
- Fuente: descarga manual desde el sistema Kawak del Politécnico Grancolombiano.

---

### 2.2 Catálogo Kawak (metadata de indicadores)

| Ruta | Consumidor | Contenido |
|------|------------|-----------|
| `data/raw/Kawak/2022.xlsx` | `consolidar_api.py` → `Indicadores Kawak.xlsx` | Metadatos indicadores 2022 |
| `data/raw/Kawak/2023.xlsx` | `consolidar_api.py` | Metadatos indicadores 2023 |
| `data/raw/Kawak/2024.xlsx` | `consolidar_api.py` | Metadatos indicadores 2024 |
| `data/raw/Kawak/2025.xlsx` | `consolidar_api.py` + `fuentes.cargar_kawak_2025()` | Metadatos + datos 2025 (con Periodo cols) |
| `data/raw/Kawak/2026.xlsx` | `consolidar_api.py` | Metadatos indicadores 2026 |

**Columnas catálogo (subset canónico):**
```
Año | Id | Indicador | Clasificacion | Proceso | Tipo | Tipo de variable | Periodicidad | Sentido
```

---

### 2.3 Consolidados Intermedios (`Fuentes Consolidadas/`)

> **Generados por `consolidar_api.py`.** No editar manualmente.

| Ruta | Generado por | Consumido por |
|------|-------------|---------------|
| `Fuentes Consolidadas/Consolidado_API_Kawak.xlsx` | `consolidar_api.py` | `actualizar_consolidado.py`, dashboards Streamlit |
| `Fuentes Consolidadas/Indicadores Kawak.xlsx` | `consolidar_api.py` | `catalogo.py`, filtros CMI, `fuentes.cargar_kawak_validos()` |
| `Fuentes Consolidadas/Consolidado_API_Kawak_REV.xlsx` | Manual (revisión) | Auditoría |

---

### 2.4 Maestros y Configuración

| Ruta | Función que lo carga | Contenido |
|------|---------------------|-----------|
| `data/raw/Indicadores por CMI.xlsx` | `fuentes.cargar_metadatos_cmi()` | Indicadores por CMI con clasificación y subproceso |
| `data/raw/Subproceso-Proceso-Area.xlsx` | `fuentes.cargar_mapa_procesos()` | Mapeo subproceso → proceso → área |
| `data/raw/Ficha_Tecnica_Indicadores.xlsx` | `data_loader.cargar_ficha_tecnica()` | Fichas técnicas de indicadores |
| `data/raw/OM.xlsx` | `data_loader.cargar_om()` | Objetivos de Mejora |
| `data/raw/Dataset_Unificado.xlsx` | Legacy/exploratorio | Dataset histórico unificado |

---

### 2.5 Plan de Acción y Seguimiento

| Ruta | Función que lo carga | Contenido |
|------|---------------------|-----------|
| `data/raw/Plan de accion/PA_1.xlsx` | `data_loader.cargar_plan_accion()` | Plan de acción semestre 1 |
| `data/raw/Plan de accion/PA_2.xlsx` | `data_loader.cargar_plan_accion()` | Plan de acción semestre 2 |
| `data/raw/acciones_mejora.xlsx` | `data_loader.cargar_acciones_mejora()` | Acciones de mejora registradas |
| `data/raw/salidas_no_conformes.xlsx` | Módulo Calidad | No conformidades |
| `data/raw/Monitoreo/Monitoreo_Informacion_Procesos 2025.xlsx` | Monitoreo procesos | Seguimiento 2025 |

---

### 2.6 CMI y Estrategia

| Ruta | Función | Contenido |
|------|---------|-----------|
| `data/raw/Indicadores por CMI.xlsx` | `fuentes.cargar_metadatos_cmi()` | Indicadores estratégicos por perspectiva CMI |
| `data/raw/Retos/Plan de retos.xlsx` | `data_loader.cargar_retos()` | Plan de retos institucionales |
| `data/raw/Propuesta Indicadores/Indicadores Propuestos.xlsx` | `informe_por_procesos` | Propuestas de nuevos indicadores |
| `data/raw/Auditoria/auditoria_resultado.xlsx` | ETL Auditoría | Resultados de auditoría ETL |

---

## 3. Salidas del Pipeline — `data/output/`

### 3.1 Workbook Principal

| Archivo | Generado por | Hojas |
|---------|-------------|-------|
| `data/output/Resultados_Consolidados.xlsx` | `actualizar_consolidado.py` | Histórico, Semestral, Cierres |

**Hoja `Consolidado Historico`:**
- Un registro por indicador-periodo (mensual/trimestral/semestral según periodicidad)
- ~30+ columnas: Id, Indicador, Proceso, Fecha, Meta, Ejecucion, Cumplimiento, LLAVE, signos, etc.
- Acumulativo (solo se añaden nuevos registros, no se borran)

**Hoja `Consolidado Semestral`:**
- Registros por indicador-semestre (jun/dic)
- Para indicadores Promedio/Acumulado: agrega meses del semestre
- Para indicadores Cierre: usa el último período de jun o dic

**Hoja `Consolidado Cierres`:**
- Un registro por indicador-año (cierre anual)
- Para años históricos (≤ `AÑO_CIERRE_ACTUAL`): conserva solo diciembre si existe
- Para años futuros: usa último mes disponible

---

### 3.2 Artefactos del Pipeline

| Ruta | Generado por | Contenido |
|------|-------------|-----------|
| `artifacts/reporte_YYYYMMDD.json` | `generar_reporte.py` | Métricas post-ETL por hoja |
| `artifacts/reporte_YYYYMMDD.csv` | `generar_reporte.py` | Tabla plana para revisión |
| `artifacts/pipeline_metrics_YYYY-MM-DD.json` | `MetricsCollector` | Duración, filas procesadas por fase |
| `artifacts/audit_trail.jsonl` | `AuditTrail` | Log de cambios con timestamp |

---

## 4. Bases de Datos

### 4.1 SQLite — `registros_om.db`

| Tabla | Contenido | Módulo |
|-------|-----------|--------|
| `registros_om` | Registros OM (Objetivos de Mejora) | `core/db_manager.py` |
| Otras tablas | Según `core/db/schema_manager.py` | `core/db/operations.py` |

**Uso:** Persistencia de registros OM creados desde el formulario Streamlit. Es la fuente para la página "Gestión OM".

### 4.2 PostgreSQL — Supabase (opcional)

- Usado en SGIND v2 (`sgind-v2/backend/`)
- Configurado vía `DATABASE_URL` en `.env`
- Esquema gestionado por el backend FastAPI
- En Streamlit legacy: modo dual SQLite/PostgreSQL en `core/db_manager.py`

---

## 5. SGIND v2 — Fuentes

En la versión Next.js 14 + FastAPI, las fuentes de datos son:

| Fuente | Ruta | Nota |
|--------|------|------|
| Excel consolidados | Mismos que Streamlit, leídos por `services/excel_reader.py` | Compartidos |
| PostgreSQL | `DATABASE_URL` (Supabase) | Exclusivo v2 |
| API REST interna | `sgind-v2/backend/app/api/` | Para consumo del frontend Next.js |

---

## 6. Contratos de Datos

Los contratos de entrada están documentados en `config/data_contracts.yaml`. Validados en el pipeline por `validation_gate.validar_consolidado_api_entrada()` antes de procesar.

**Campos requeridos en Consolidado_API_Kawak:**
```yaml
columnas_requeridas:
  - ID
  - fecha
  - meta
  - resultado
tipos:
  ID: string|numeric
  fecha: datetime
  meta: float|null
  resultado: float|null
```

---

## 7. Flujo de Datos Simplificado

```
Kawak (manual)
    │
    ├─ API/*.xlsx ──────────┐
    └─ Kawak/*.xlsx ────────┤
                            ▼
                    consolidar_api.py
                            │
            ┌───────────────┤
            ▼               ▼
    Consolidado_API_Kawak   Indicadores Kawak
    (datos con fecha)       (catálogo)
            │               │
            └───────────────┤
                            ▼
                actualizar_consolidado.py
                            │
                    Resultados_Consolidados.xlsx
                            │
                ┌───────────┼───────────────────┐
                ▼           ▼                   ▼
          Streamlit      generar_reporte.py   SGIND v2
          dashboards     (JSON/CSV)           (via API)
```

---

## 8. Referencias

- **Pipeline ETL:** [`09_ETL_Pipeline.md`](09_ETL_Pipeline.md)
- **Catálogo Kawak v2:** [`sgind-v2/docs/phase-0/E0.5_CATALOGO_FUENTES_DATOS.md`](../../sgind-v2/docs/phase-0/E0.5_CATALOGO_FUENTES_DATOS.md)
- **Fuentes en código:** [`scripts/etl/fuentes.py`](../../scripts/etl/fuentes.py)
- **Contrato de datos:** [`config/data_contracts.yaml`](../../config/data_contracts.yaml)
