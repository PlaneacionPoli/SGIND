# 09 - PIPELINE ETL

**Documento:** 09_ETL_Pipeline.md  
**Versión:** 1.0  
**Fecha:** 17 de junio de 2026  
**Status:** ✅ Activo

---

## 1. Visión General

El pipeline ETL del sistema Streamlit tiene **3 pasos macro** que se ejecutan en secuencia. Cada uno genera un artefacto que el siguiente consume.

```
[data/raw/Kawak/*.xlsx]       [data/raw/API/*.xlsx]
          │                            │
          └─────────── PASO 1 ─────────┘
                  consolidar_api.py
                          │
                          ▼
          [Consolidado_API_Kawak.xlsx]
          [Indicadores Kawak.xlsx]
                          │
                    PASO 2 ────────────────────────────────────────
              actualizar_consolidado.py (Orquestador ETL)
                          │
                          ▼
          [Resultados_Consolidados.xlsx]  ← 3 hojas:
             · Consolidado Historico
             · Consolidado Semestral
             · Consolidado Cierres
                          │
                    PASO 3
              generar_reporte.py
                          │
                          ▼
          [artifacts/reporte_YYYYMMDD.json]
          [artifacts/reporte_YYYYMMDD.csv]
```

---

## 2. Paso 1 — `scripts/consolidar_api.py`

**Propósito:** Consolida los archivos anuales de la API Kawak en dos archivos de salida limpios.

### Entradas
| Fuente | Ruta | Frecuencia |
|--------|------|------------|
| Datos Kawak por año | `data/raw/Kawak/{2022..2026}.xlsx` | Manual (descarga Kawak) |
| API Kawak por año | `data/raw/API/{2022..2026}.xlsx` | Manual (descarga API) |

### Salidas
| Artefacto | Ruta | Descripción |
|-----------|------|-------------|
| Catálogo Kawak | `data/raw/Fuentes Consolidadas/Indicadores Kawak.xlsx` | Metadata maestro de indicadores |
| Consolidado API | `data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx` | Todos los registros con fecha |

### Columnas Catálogo Kawak
```
Año | Id | Indicador | Clasificacion | Proceso | Tipo | Tipo de variable | Periodicidad | Sentido
```

### Ejecución
```bash
python scripts/consolidar_api.py
```

---

## 3. Paso 2 — `scripts/actualizar_consolidado.py`

**Propósito:** Orquestador principal. Añade registros nuevos al workbook Excel de salida (`Resultados_Consolidados.xlsx`). Toda la lógica de negocio vive en `scripts/etl/`.

### Fases Internas (main function)

| # | Fase | Función/módulo | Descripción |
|---|------|----------------|-------------|
| 1 | Cargar fuente | `fuentes.cargar_fuente_consolidada()` | Lee `Consolidado_API_Kawak.xlsx`, normaliza columnas, construye campo `LLAVE` |
| 1.5 | Validar entrada | `validation_gate.validar_consolidado_api_entrada()` | Gate LAYER 1: bloquea pipeline si datos inválidos |
| 2 | Cargar catálogo | `catalogo.cargar_catalogo_completo()` | `extraccion_map`, `tipo_calculo_map`, `tipo_indicador_map`, `variables_campo_map` |
| 3 | Metadatos auxiliares | múltiples en `fuentes.py` | `kawak_validos`, `metadatos_kawak`, `metadatos_cmi`, `mapa_procesos`, `ids_metrica`, `api_kawak_lookup` |
| 4 | Config patrones | `catalogo.cargar_config_patrones()` | Patrones AVG/SUM por indicador |
| 4.5 | Init versionado | `VersionManager`, `AuditTrail`, `EmailNotifier` | Backup pre-modificación, trail de auditoría |
| 5 | Abrir workbook | `workbook_io.workbook_local_copy()` | Copia local segura, abre con openpyxl |
| 5.5 | Backup de versión | `vm.crear_version(tag="pre_consolidacion")` | Guarda hasta 5 versiones anteriores |
| 6 | Leer existentes | `pd.read_excel()` x3 hojas | Obtiene `llaves_existentes` para cada hoja |
| 7 | Construir registros | `builders.*` | Genera registros nuevos para Histórico, Semestral, Cierres |
| 7.5 | Correcciones AGENT5 | `AGENT5Corrections` | Cap ejecución > 1.3, flag Meta=0 |
| 8 | Validar intermedio | `validate_after_build_records()` | Gate LAYER 2: valida integridad de registros construidos |
| 9 | Purgar inválidos | `purga.purgar_filas_invalidas()` | Elimina filas futuras y fuera del catálogo Kawak |
| 10 | Limpiar/dedup | `purga.limpiar_cierres_existentes()`, `_dedup_cierres_por_año()` | Normaliza hoja Cierres |
| 11 | Reparar Meta vacía | `purga.reparar_meta_vacia()`, `reparar_multiserie()`, `reparar_semestral_agregados()` | Rellena celdas vacías con datos del lookup |
| 12 | Calcular signos | `signos.obtener_signos()` | Determina signo (%, ENT, etc.) por indicador |
| 13 | Validar pre-escritura | `validate_before_write()` | Gate LAYER 3: valida filas antes de escribir |
| 14 | Escribir filas | `escritura.escribir_filas()` x3 | Escribe en Histórico, Semestral, Cierres |
| 15 | Ordenar y limpiar | `escritura.limpiar_ordenar_hoja()` x3 | Deduplica, reordena, reescribe fórmulas |
| 16 | Guardar workbook | `wb.save()` | Persiste el workbook con todos los cambios |
| 17 | Métricas finales | `MetricsCollector.finish_pipeline()` | Guarda métricas en `artifacts/` |
| 18 | Notificaciones | `EmailNotifier.send_summary()` | Envía resumen si SMTP configurado |

### Hojas del Workbook de Salida

| Hoja | Rol | Actualización |
|------|-----|---------------|
| `Consolidado Historico` | Todos los registros mensuales | Acumulativo |
| `Consolidado Semestral` | Registros semestrados (jun/dic) | Acumulativo |
| `Consolidado Cierres` | Un registro de cierre por indicador-año | Reemplaza según año |

### Columnas clave (Histórico y Semestral)
```
A: Id  |  B: Indicador  |  C: Clasificacion  |  D: Proceso  |  E: Periodicidad
F: Sentido  |  G: Anio (fórmula)  |  H: Mes (fórmula)  |  I: Semestre (fórmula)
J: Meta  |  K: Ejecucion  |  L: Cumplimiento (fórmula)  |  M: CumplReal (fórmula)
N: TipoRegistro  |  O: Ejecucion_Signo  |  P: Meta_Signo  |  R: LLAVE (fórmula)
```

### Fórmulas Excel materializadas
| Columna | Fórmula origen | Función Python |
|---------|----------------|----------------|
| G (Anio) | `=YEAR(F2)` | `formula_G(row)` |
| H (Mes) | `=MONTH(F2)` | `formula_H(row)` |
| I (Semestre) | `=IF(H2<=6,1,2)` | `formula_I(row)` |
| L (Cumplimiento) | `=IF(J2...,K2/J2,...)` | `formula_L(row)` |
| M (CumplReal) | igual a L con tope PA | `formula_M(row)` |
| R (LLAVE) | `=A2&"-"&TEXT(F2,"YYYY-MM-DD")` | `formula_R(row)` |

### Ejecución
```bash
# Requiere que Paso 1 ya se haya ejecutado
python scripts/actualizar_consolidado.py
```

---

## 4. Paso 3 — `scripts/generar_reporte.py`

**Propósito:** Genera un resumen ejecutivo post-ETL con métricas por hoja.

### Entradas
- `Resultados_Consolidados.xlsx` (salida del Paso 2)

### Salidas
| Artefacto | Descripción |
|-----------|-------------|
| `artifacts/reporte_YYYYMMDD.json` | Métricas por hoja (filas, nulls, por indicador) |
| `artifacts/reporte_YYYYMMDD.csv` | Tabla plana para revisión rápida |

### Ejecución
```bash
python scripts/generar_reporte.py
```

---

## 5. Módulos ETL (`scripts/etl/`)

| Módulo | Rol | Cobertura |
|--------|-----|-----------|
| `cumplimiento.py` | Cálculo puro de cumplimiento | 89% |
| `extraccion.py` | Extrae Meta/Ejecución desde API (variables/series/directo) | ~60% |
| `normalizacion.py` | `COL_ALIASES`, `make_llave()`, helpers de normalización | ~95% |
| `periodos.py` | Fechas por periodicidad, último día de mes | 100% |
| `signos.py` | Obtiene signos (%, ENT, etc.) por indicador | 100% |
| `no_aplica.py` | Detecta registros "No Aplica" | 100% |
| `builders.py` | Construye registros para Histórico/Semestral/Cierres | 88% |
| `fuentes.py` | Carga fuentes externas (Excel, catálogos) | 32% |
| `purga.py` | Limpia, deduplica, repara hojas Excel | 30% |
| `escritura.py` | Escribe filas en openpyxl, deduplica sheet | 29% |
| `formulas_excel.py` | Materializa fórmulas (Anio, Mes, Semestre, LLAVE, Cumplimiento) | n/a |
| `catalogo.py` | Carga catálogo de indicadores | n/a |
| `notifications.py` | EmailNotifier (SMTP) | ~79% |
| `validation_gate.py` | Gates de validación LAYER 1/2/3 | 73% |
| `audit.py` | AuditTrail de cambios | n/a |
| `versioning.py` | VersionManager (backups) | 26% |
| `retry_handler.py` | Reintentos automáticos del pipeline | 89% |
| `pipeline_metrics.py` | MetricsCollector | 0% |
| `workbook_io.py` | Copia local segura del workbook | 0% |
| `config.py` | `AÑO_CIERRE_ACTUAL`, `OUTPUT_FILE`, `BASE_PATH` | n/a |

---

## 6. Flujo de la LLAVE

La `LLAVE` es el identificador único de cada registro: `{Id}-{YYYY-MM-DD}`.

```python
# Construcción en fuentes.py (vectorizada)
id_series + "-" + fecha.dt.year + "-" + fecha.dt.month.str.zfill(2) + "-" + fecha.dt.day.str.zfill(2)

# Cálculo Python (normalizacion.py:make_llave)
def make_llave(id_val, fecha) -> Optional[str]:
    id_s = _id_str(id_val)
    try:
        fecha_ts = pd.to_datetime(fecha)
        return f"{id_s}-{fecha_ts.strftime('%Y-%m-%d')}"
    except Exception:
        return None
```

La hoja Excel tiene la `LLAVE` como fórmula Excel (columna R) **y** como valor materializado durante la escritura.

---

## 7. Detección y escritura de "No Aplica"

Un registro se marca `es_na=True` cuando:
1. El campo `analisis` de la API Kawak contiene el texto "no aplica" (case-insensitive)
2. `resultado=NaN` AND sin datos en `variables` ni `series`

Al escribir en el consolidado:
| Columna | Valor para "No Aplica" |
|---------|----------------------|
| K (Ejecucion) | `None` (celda vacía) |
| O (Ejecucion_Signo) | `"No Aplica"` |
| L (Cumplimiento) | `""` vía fórmula |
| J (Meta) | conserva si existe, `None` si no |

---

## 8. Retry y resiliencia

El pipeline usa `@retry_pipeline(max_attempts=3, initial_wait=2.0, max_wait=60.0)` sobre `main()`. En caso de error transitorio (I/O, red) reintenta con backoff exponencial antes de fallar definitivamente.

---

## 9. Referencias

- **Cálculo cumplimiento:** [`02_Logica_Indicadores.md`](02_Logica_Indicadores.md)
- **Fuentes de datos:** [`08_Fuentes_Datos.md`](08_Fuentes_Datos.md)
- **Tests ETL:** [`06_Testing_Calidad.md`](06_Testing_Calidad.md)
- **Código orquestador:** [`scripts/actualizar_consolidado.py`](../../scripts/actualizar_consolidado.py)
- **Módulos ETL:** [`scripts/etl/`](../../scripts/etl/)
