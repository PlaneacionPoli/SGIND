# Informe de impacto — Soporte multi-PDI (N ciclos) y marcos CNA versionados

> Fase 1 — Descubrimiento. No se modificó código. Fecha: 2026-10-01.
> Alcance: Resumen General, CMI Estratégico, CMI por Procesos, Informe Ejecutivo PDF + narrativa IA, Plan de mejoramiento / OM, ETL.

---

## 0. Resumen ejecutivo

- **El PDI no existe como entidad de datos.** Ninguna tabla de Postgres, ninguna hoja de Excel, ninguna tabla de Power BI ni ningún esquema de la API tiene un `pdi_id`, `ciclo` o `version`. El ciclo 2022-2026 se impone de forma implícita con:
  1. constantes de años (`ANIOS_RANGO = [2022..2025]`);
  2. un corte por número de proyecto (`PRY ≤ 44`);
  3. una hoja con nombre fijo ("Cierre PDI");
  4. nombres de archivo (`pdi_2022_2026.json`, `centroDeProyectos_PMO_2026.xlsx`, `narrativa_estrategica_2022_2025.json`);
  5. constantes de líneas y objetivos repetidas en Python y en TypeScript.
- Las líneas, objetivos y metas estratégicas se relacionan con los indicadores mediante **texto libre** en el catálogo (`Linea_Estrategica`, `Objetivo_Estrategico`, `Meta_Estrategica`). El **CNA** tiene el mismo problema (`Factor`, `Caracteristica`).
- El único "selector de ciclo" de la API es el booleano `rango` ("Cierre PDI 2022-2025") de `/cmi/estrategico-dashboard` y `/dashboard/resumen-completo`.
- **Ninguna clave de caché** (backend TTL ni react-query) incluye el ciclo. Agregar un segundo PDI sin cambiarlas mezclaría datos entre ciclos.
- Existen **dos cálculos distintos del consolidado** (retos + proyectos + indicadores). Ninguno recibe el ciclo como parámetro.

---

## 1. Decisiones de negocio confirmadas

| # | Decisión |
|---|---|
| D1 | **Los Ids de indicador no cambian** entre PDI. Lo que cambia es la **asociación** (línea, objetivo, meta). Las sucesiones (ej. 386 → 523) son casos puntuales que se declaran de forma explícita. |
| D2 | La asociación al PDI 2026-2030 **solo aplica a indicadores activos**. Los inactivos conservan solo su asociación 2022-2026. |
| D3 | Los **datos de 2026 pertenecen solo al PDI 2026-2030**. El 2022-2026 cierra con datos 2022-2025. |
| D4 | **Retos y proyectos PMO**: un archivo por ciclo. |
| D5 | **CNA**: desde 2027 rige una nueva resolución, cuyo listado aún no existe. La resolución actual se toma como versión original. |
| D6 | **Selector de PDI**: se muestra siempre al entrar desde el menú. El PDI va en la URL y dentro del módulo hay un chip para cambiarlo. |
| D7 | **CMI por Procesos**: los filtros muestran las líneas del PDI seleccionado. La **ficha** muestra la línea del PDI anterior **y** la del actual, según la fecha de inicio del indicador. |
| D9 | **Los proyectos que aún no han cerrado continúan en el PDI 2026-2030**, con el mismo Id (D1). Un proyecto cuenta como cerrado si su estado PMO es Cerrado/Finalizado; el resto (Ejecución, Planeación, Stand by) continúa. El cierre del 2022-2026 sigue congelado con su estado a ese corte. |
| D8 | **Alcance**: Informe Ejecutivo PDF + narrativa IA, Plan de mejoramiento y OM. **Fuera de alcance**: Power BI y restricción por rol (quedan como pendientes). |

### 1.1 Avance de implementación (actualizado)
- **Taxonomía 2026-2030**: tomada del skill `contexto-pdi-poli` §3 (4 líneas, 10 objetivos, 22 metas) en `backend/app/data/taxonomia/PDI-2026-2030.json`. La del 2022-2026 (6 líneas, 11 objetivos, 33 metas) se derivó de `pdi_2022_2026.json` en `PDI-2022-2026.json`. Ids: `<linea>`, `<linea>-O<n>`, `<linea>-O<n>-M<k>`.
- **Asociación manual indicador ↔ marco**: nueva hoja `Indicador_Marco` en `data/raw/Catalogo de Indicadores.xlsx` (con `Taxonomia_Marco` y `Listas_Marco` para los desplegables), creada por `scripts/agregar_hojas_marco_catalogo.py`. Precargada para `PDI-2026-2030` con 322 filas: 300 indicadores con `Estado = Activo` (D2), **12 proyectos del ciclo anterior que no han cerrado** (D9: PRY-12, 13, 17 en Stand by; PRY-26, 28, 30, 31, 32, 40, 42 en ejecución; PRY-43, 44 en planeación) y 10 proyectos nuevos (PRY-45 a 54). La columna `Origen` indica de cuál grupo viene cada fila; Planeación elige Línea, Objetivo y Meta. Las hojas originales del catálogo no se modificaron.
- **Validación**: `backend/app/domain/taxonomia.py::resolver_asociaciones` resuelve los textos a ids y rechaza objetivos que no pertenecen a la línea, metas que no pertenecen al objetivo, repetidos y versiones sin taxonomía. Una prueba revisa el catálogo real.
- **Aislamiento por PDI en la API**: `?pdi=<version_id>` se valida en todos los endpoints de `/dashboard` y `/cmi` y en `/reports/informe-ejecutivo` (`app/api/pdi_deps.py`): 404 si no existe, 422 si no es un PDI, **409 si el ciclo aún no tiene datos** (`datos_disponibles = false`), nunca datos de otro ciclo. Sin `pdi` se usa el vigente con datos.
- **Cachés**: las claves de `ResumenService` incluyen el PDI (probado). Los años del ciclo y la hoja de cierre salen del registro (`marco.anios`, `marco.hoja_cierre`) en vez de `ANIOS_RANGO` / "Cierre PDI" fijos; el 2022-2026 da exactamente el valor anterior (prueba de regresión).
- **Frontend**: Resumen, CMI Estratégico y CMI por Procesos envían `pdi` y lo incluyen en sus claves de react-query. Las vistas por línea quedan fijas a `PDI-2022-2026` (`PDI_VISTAS_POR_LINEA`).
- **Pendiente de esta etapa**: leer `Indicador_Marco` para filtrar indicadores por PDI (hoy el membership sigue siendo `FlagPlanEstrategico`), líneas del PDI elegido en los filtros de CMI por Procesos, ficha con ambos PDI, narrativa/plantilla del PDF por ciclo y `get_filtros` (lista blanca de años 2022-2025). `ProyectosOficialesService` (44 proyectos) sigue siendo específico del 2022-2026.
- **Proyectos que continúan (D9)**: en el catálogo ningún proyecto tiene `Estado = Activo` (30 vacíos, 24 históricos), así que el estado sale del PMO vía `ProyectosOficialesService`. Para el 2026-2030 el universo de proyectos pasa a ser el de `Indicador_Marco`, no el corte `PRY ≤ 44`. Los 3 en Stand by se incluyeron por no estar cerrados.
- **Decisiones abiertas de D9**: (a) ¿el avance de un proyecto que continúa se mide acumulado desde su inicio o reinicia en 2026?; (b) ¿Stand by debe continuar o se descarta?; (c) el archivo PMO del ciclo nuevo debe incluir estos proyectos, y su Gantt/ventana (hoy 2021-2025 en `proyectos_pmo_loader.py:205-206`) debe cubrir 2026-2030.
- **Diseño vigente de la asociación (2026-10-06, reemplaza lo anterior sobre `Indicador_Marco`, `Tipo_PDI_*` y los códigos numéricos)**: una **hoja independiente por PDI** en el catálogo (`PDI_2022_2026`, `PDI_2026_2030`), cada una con **una sola columna `PDI`** (**1** = indicador estratégico del PDI, exige meta estratégica; **0** = de proceso, no puede tenerla; vacío = sin definir) y `Linea` / `Objetivo` / `Meta` por nombre con lista desplegable (`Listas_PDI_*`). El backend (`resolver_asociaciones`) reporta errores de asociación con su fila y la regla de meta en `incumplimientos`, sin descartar filas. El 2022-2026 se migró una vez desde las columnas de texto del catálogo y queda congelado (683 indicadores; los PRY-45 a 54 son del ciclo nuevo y no entran; 44 metas con redacción distinta a la oficial se conservan tal cual y se toleran con advertencia). El 2026-2030 está precargado con 322 filas (PDI sugerido con la marca actual del plan; Planeación debe revisarlo). Regla de meta en la hoja 2022-2026: 5 estratégicos sin meta (PRY-5, PRY-8, 109, 335, 472) y 66 de proceso con meta.
- **Nota técnica**: guardar el libro con openpyxl (el script y el pipeline) elimina el valor calculado de las celdas con fórmula (p. ej. Ficha Tecnica Detalle ids 203, 215, 328, 430 y las constantes de "Cierre PDI"); el contenido no cambia, pero lectores como pandas ven vacío hasta que Excel recalcule.
- **Taxonomía oficial 2026-2030 (2026-10-08)**: `data/raw/PDI_2026-2030_Lineas_Objetivos_Metas.xlsx` es la fuente (4 líneas, 10 objetivos, 22 metas, textos oficiales sin parafrasear). `scripts/importar_taxonomia_pdi.py` la importa: reescribe `backend/app/data/taxonomia/PDI-2026-2030.json` con los códigos del Excel como ids (`L1`, `L1-OI`, `L1-OI-M1`), migra al texto oficial lo ya elegido en la hoja `PDI_2026_2030` (28 celdas, emparejadas por posición) y regenera `Taxonomia_Marco`, `Listas_PDI_2026_2030` y los desplegables. Las 17 asociaciones existentes resuelven sin errores.
- **Supuesto a confirmar**: "activo" = `Estado = Activo` (300). `Ind_Act = 1` da otra cifra (371) y no se usó.

---

## 2. Modelo de datos actual

### 2.1 Arquitectura de almacenamiento
- **Postgres** (`database/migrations/001_initial_schema.sql`, `004_add_rol_administrador.sql`): `roles`, `users`, `registros_om`, `acciones`, `audit_log`, `ai_configs`, `ai_prompts`. No guarda indicadores.
- **Excel**: es la fuente real de indicadores, metas, ejecuciones, retos y proyectos. Se lee con `backend/app/services/excel_reader.py` (raíz `settings.sgind_data_path`).
- **JSON**: `backend/app/data/pdi_2022_2026.json` (contenido oficial del PDI) y `data/derived/narrativa_estrategica_2022_2025.json`.
- **SQLite legado**: `data/db/registros_om.db`.
- **ETL**: `scripts/run_pipeline.py`, `scripts/actualizar_consolidado.py` y `scripts/etl/*`. Se ejecuta cada mes en CI (`.github/workflows/actualizar-datos.yml`).
- **Power BI**: `Tablero BI/…SemanticModel` (16 tablas TMDL que leen los mismos Excel).

### 2.2 Dónde vive hoy el "PDI"

| Mecanismo | Ubicación |
|---|---|
| Años del ciclo | `backend/app/services/resumen_service.py:60` (`ANIOS_RANGO`), `:263` (lista blanca de años); `backend/app/domain/resumen_builders.py:1235,1317,1371` (`anio_min=2022`); `:1632-1633` (Gantt fijado a 2022-2026) |
| Corte de proyectos | `resumen_service.py:66` `PROYECTOS_CICLO_2022_2025_MAX = 44`; lista curada en `services/proyectos_oficiales_service.py:1-66,145`; ventana 2021-2025 en `services/proyectos_pmo_loader.py:205-206` |
| Líneas y objetivos | `resumen_builders.py:48` `STRATEGIC_LINE_DEFS`, `:97-130` `CANONICAL_OBJETIVOS`; `domain/linea_order.py:7` `LINEA_ORDER`; `resumen_service.py:931` `_ORDEN_PDI`; `frontend/src/lib/strategic-lines.ts`; `frontend/src/components/ui/FlorEstrategica.tsx:24-108`; `public/img/pdi/*.png` |
| Contenido oficial | `backend/app/data/pdi_2022_2026.json`, cargado en `services/narrativa_estrategica_service.py:28,114` |
| Hoja de cierre | "Cierre PDI" en `data/output/Resultados Consolidados.xlsx`, leída en `services/strategic_loaders.py:271-336` |
| Sucesión de Ids | `config/series_subindicadores.toml:158`, `scripts/etl/builders.py:193` (386 → 523) |
| Etiquetas en la API | `api/v1/endpoints/cmi.py:41` (`rango`), `reports.py:88,105` (nombre del PDF 2022-2025) |
| Etiquetas en la UI | `resumen-general/page.tsx:114,275`, `cmi-estrategico/page.tsx:111,158`, `components/cmi/CmiFilters.tsx:15,73`, `components/ui/YearSegmentedControl.tsx:62`, `components/charts/PdiMindmap.tsx:17,49,403`, `lib/api.ts:515-519`, `lib/types.ts:344,717,723,787`, plantillas `templates/informe_ejecutivo/report.html` |

**Hoja "Cierre PDI".** El pipeline la procesa:
- `scripts/etl/formulas_excel.py:87-141` recalcula su cumplimiento, porque recorre todas las hojas desde `actualizar_consolidado.py:725-727`. El log `artifacts/pipeline_run_20260920_202029.log:348` lo confirma.
- `scripts/etl/purga.py:773` trata toda hoja cuyo título contenga "Cierre".

**Sin embargo, no encontré en el repo el paso que inserta sus filas.** Hay que confirmar qué script lo hace, por si es externo al repo. La hoja es una sola y no tiene columna de ciclo.

### 2.3 Relación de líneas, objetivos, proyectos y retos con el PDI
- **Indicadores**: la pertenencia al PDI es `FlagPlanEstrategico = 1` en el catálogo, más el año del dato. Línea, objetivo y meta son texto libre.
- **Proyectos**: se identifican por `Proyecto = 1` en el catálogo y por el archivo PMO (columna `4. Líneas estratégicas`, en texto).
- **Retos**: `data/raw/Retos/Plan de retos.xlsx` (columnas `Línea Estratégica`, `Objetivo`, `Año`).
- **No existe un identificador de ciclo en ninguno de ellos.** Hoy se asume un único PDI global.

### 2.4 Inventario de artefactos

Ningún artefacto tiene identificador de ciclo. En la tabla, "No" significa que no tiene.

| Dominio | Artefacto | Consumidores | ¿Tiene ciclo? |
|---|---|---|---|
| Catálogo de indicadores | `data/raw/Catalogo de Indicadores.xlsx` ("Catalogo Indicadores", 702 filas: `Linea_Estrategica`, `Objetivo_Estrategico`, `Meta_Estrategica`, `Proyecto`, `Orden_CMI`, `Factor`, `Caracteristica`…; "Ficha Tecnica Detalle") | `strategic_loaders.py:20-22,137`, ETL, Power BI `Dim_Catalogo` | No |
| Copia del catálogo | "Catalogo Indicadores" en `data/output/Resultados Consolidados.xlsx` (`Años_Activo`, `Activo_Año_Actual`) | API | Solo por años |
| Ficha técnica | `data/raw/Ficha_Tecnica_Indicadores.xlsx` (`Fecha Desde/Hasta`) | ETL (`purga.purgar_filas_antes_fecha_desde`) | No; **su fecha de inicio sirve para D7** |
| Metas y ejecuciones | "Consolidado Historico", "Consolidado Semestral", "Consolidado Cierres", "Desglose Series", "Variables" | `strategic_loaders.py:166`, `etl_pipeline.py`, Power BI `Fact_*` | No (`Año`, `Periodo`) |
| Cierre del PDI | hoja "Cierre PDI" | `strategic_loaders.load_cierre_pdi_final` | Solo por el nombre de la hoja |
| Fuentes crudas | `data/raw/API/2022..2026.xlsx`, `data/raw/Kawak/2022..2026.xlsx`, `Consolidado_API_Kawak.xlsx` | `scripts/etl/fuentes.py`, `extraccion.py`, `consolidar_api.py` | Año en el nombre de archivo |
| Proyectos (fuente) | `data/raw/Resultados_Consolidados_Fuente.xlsx` | `strategic_loaders.py:29-31,338` | No |
| Proyectos PMO | `data/raw/Proyectos/centroDeProyectos_PMO_2026.xlsx` | `proyectos_pmo_loader.py:37,141,211`, `proyectos_oficiales_service.py` | Año en el nombre de archivo |
| Retos | `data/raw/Retos/Plan de retos.xlsx` (hojas Linea, Objetivo, Planes, Areas) | `services/retos_loaders.py:12-120`, Power BI `Dim_Retos_*` | No |
| Plan de mejoramiento / CNA | `data/raw/Plan de mejoramiento/*.xlsx`, `data/output/Resultados_Consolidados_CNA.xlsx`, `scripts/cna_extraction/` | `plan_mejoramiento_service.py` (`:219` "Metas 2026-2030"), `plan_mejoramiento_builders.py:445-1093`, Power BI `Fact_PlanMejoramiento`, `Fact_CNA_Metricas`, `Dim_CNA_FactorCaracteristica` | Solo una etiqueta |
| OM / Plan de acción | `data/raw/OM.xlsx`, `data/raw/Plan de accion/PA_*.xlsx`; Postgres `registros_om`, `acciones` (`models/om.py:9`) | `om_service.py`, `om_matriz_service.py`, `endpoints/om.py` | No (`anio`, `periodo`) |
| Usuarios, roles y permisos | Postgres `users`, `roles` (`models/user.py`); `core/security.py:18,83-106`; `auth_service.py:92-121`; `frontend/src/config/navigation.ts:32-46` | Todos los módulos | No |
| Auditoría e IA | Postgres `audit_log`, `ai_configs`, `ai_prompts`; `narrativa_*_service.py`; `backend/scripts/generar_narrativa_estrategica.py`; `data/derived/narrativa_estrategica_2022_2025.json`, `narrativas_ia_procesos.json` | Resumen, PDF | Solo en el nombre de archivo |
| Reportes PDF | `endpoints/reports.py:37,86,113,157`; `pdf_service.py`; `report_html_service.py`; `templates/informe_ejecutivo/*` | Resumen, Informe | Fijo en el código |
| Exportables Excel | `cmi.py:145` (`/procesos/export`), `plan_mejoramiento.py:82`, `seguimiento.py:52`, `data/output/Seguimiento_Reporte.xlsx`, `scripts/generar_reporte.py` | Usuarios | No |
| Dashboards (API) | `endpoints/dashboard.py:34-152`, `cmi.py`, `informe.py`, `seguimiento.py`, `indicators.py` | Frontend | Solo el booleano `rango` |
| Alertas | `cmi.py:185` `/alertas`; `CmiAlertasTab.tsx`, `CmiProcesosAlertasTab.tsx`; umbrales en `domain/constants.py:5-26`; `scripts/etl/notifications.py` | CMI | No |
| Validación | `services/data_validation/*`, `domain/pdi_validation.py`, `scripts/etl/validation_gate.py`, `validacion_historica.py` | ETL, PDF | No |
| Power BI *(fuera de alcance)* | `Tablero BI/.../tables/*.tmdl`, `relationships.tmdl`, `expressions.tmdl` | Gerencia | No (`Dim_Calendario` solo por años) |
| Dashboards guardados | No existen como entidad persistida | — | — |

---

## 3. Código que asume un único PDI implícito

### 3.1 Navegación (frontend, Next.js App Router)
- `frontend/src/config/navigation.ts:7-15` define `NAV_ITEMS`, que llevan directo a `/resumen-general`, `/cmi-estrategico` y `/cmi-procesos`.
- Estos ítems se muestran en `components/layout/Sidebar.tsx:78` y en el lanzador `/menu` (`LauncherScreen.tsx`, `OrbitNode.tsx:72,86`, `OrbitWaveRow.tsx:182,202`).
- `(dashboard)/layout.tsx` aplica `AuthGuard` y `AppShell`. Los permisos se resuelven con `canAccessPath` por prefijo; probado en `navigation.test.ts`.

### 3.2 Resumen General
- **Frontend**
  - `resumen-general/page.tsx`: por defecto `anio=2025` y `rango=true` (`:37-39`); clave `["resumen-completo", anio, vista, rango]` (`:63`); años de respaldo `[2022..2025]` (`:70`).
  - `consolidado-por-linea/page.tsx:14-16` hace una llamada fija con `anio: 2025, rango: true`.
  - `linea/[key]/page.tsx:17,26,29`; `LineaFichaGeneral.tsx:23`.
  - `ProyectosPmoTimeline.tsx:8-15` (`SCALE_START = 2022`).
- **Backend**
  - Endpoints en `endpoints/dashboard.py`: `/kpis`, `/semaphore`, `/trend`, `/filtros`, `/lineas`, `/sunburst`, `/yoy`, `/narrativa`, `/resumen-completo` (`:126-136`) y `/resumen-linea/{key}` (`:139-149`).
  - `services/resumen_service.py`:
    - `get_resumen_completo` (`:555-569`, con caché) y `_get_resumen_completo_uncached` (`:571-816`), que según la vista llama a `preparar_pdi_cierre_final()`, `preparar_pdi_con_cierre(anio, 12)`, `build_proyectos_oficiales_gantt(anios=ANIOS_RANGO)` o `_retos_multi_anio(ANIOS_RANGO)`.
    - La narrativa y `TARJETAS_CONSOLIDADO` solo aparecen con `rango` (`:779-783`).
    - `get_resumen_linea` (`:818-865`) y `get_informe_ejecutivo` (`:904-1007`) están fijos en 2022-2025.

### 3.3 CMI Estratégico
- **Frontend**: `cmi-estrategico/page.tsx:36-38,45,68,74,158`; `CmiFilters.tsx`; pestañas `CmiResumenTab`, `CmiLineasTab`, `CmiListadoTab`, `CmiAlertasTab`, `CmiFichaModal`.
- **Backend**
  - Endpoints en `cmi.py`: `/cmi/filtros` (`:28`), `/cmi/estrategico-dashboard` (`:36-47`), `/cmi/indicador/{id}` (`:50`), `/cmi/estrategico` (`:69`), `/cmi/alertas` (`:185`).
  - `cmi_service.get_dashboard` (`:180-245`) y `_prepare_df_cierre_pdi` (`:161-164`); `MAX_ANIO_FILTROS = 2026` (`:84`).
  - `domain/strategic_processors.py:89-189` (`preparar_pdi_con_cierre`, `preparar_pdi_cierre_final`).
  - `domain/cmi_builders.py:49-54` (`default_anio` prefiere 2025).
- **Pertenencia**: `FlagPlanEstrategico` más el año, sin asociación por ciclo.

### 3.4 CMI por Procesos
- **Frontend**: `cmi-procesos/page.tsx:42-106`; componentes `CmiProcesos*`; `/informe-procesos` usa el mismo servicio.
- **Backend**
  - Endpoints en `cmi.py`: `:82` filtros, `:94-117` dashboard, `:120` ficha, `:145` export, `:176`.
  - `cmi_service.get_procesos_filtros` (`:360-381`), `get_procesos_dashboard` (`:412-451`, con caché), `_get_year_prepared` (`:312-338`).
  - `domain/procesos_builders.py:958-965` (`default_anio_procesos` prefiere 2026).
- **Fuentes**: `output/Seguimiento_Reporte.xlsx` (vía `tracking_cache.py`), `raw/Subproceso-Proceso-Area.xlsx`, el catálogo y Kawak (`domain/cmi_filters.py:16,75,144`).
- **Estado actual**: filtra solo por año y mes, sin relación con el PDI.
- **Cambio requerido (D7)**: el filtro de línea debe mostrar la taxonomía del PDI seleccionado, y la ficha debe mostrar la asociación de cada PDI cuya vigencia se cruce con la del indicador (desde `Fecha Desde` de la ficha técnica).

### 3.5 Consolidado y % global

| Implementación | Ubicación | Regla |
|---|---|---|
| Vista "consolidado" del Resumen | `resumen_builders.py::merge_consolidado_summaries` (`:919-1014`); `get_chip_config_consolidado` (`:1043-1055`) | Promedio simple (skipna) de Indicadores, Proyectos y Retos por línea; `fillna(0)`; **sin topes** |
| Informe Ejecutivo y detalle de línea | `resumen_builders.py::build_informe_ejecutivo_lineas` (`:1565-~1720`); global en `resumen_service.py:962-969` | Topes 100 (proyecto) y 130 (indicador), excluye "Stand by", Gantt fijado a 2022-2026 |
| Reglas canónicas | `domain/pdi_measurement.py` (`TOPE_*`, `FORMULA_GLOBAL`, `calcular_consolidado_linea`, `calcular_global`) | Solo las usan `pdi_validation.py` y los tests |

- **Ninguna recibe el ciclo como parámetro.** El ciclo se decide antes de llamarlas, con `ANIOS_RANGO`, la hoja "Cierre PDI" y `PRY ≤ 44`.
- **Riesgo**: el % global de la vista consolidado y el del PDF pueden diferir para el mismo ciclo.

### 3.6 Cachés y vistas precalculadas

Ninguna clave de caché incluye el ciclo.

| Caché | Clave actual |
|---|---|
| `resumen_service._RESUMEN_COMPLETO_CACHE` (`:54,563,825`) | `(id(excel), anio, vista, rango)` |
| `cmi_service._YEAR_PREPARED_CACHE` (`:78,321`), `_PROCESOS_DASHBOARD_CACHE` (`:79,428`) | año/mes/filtros |
| `etl_pipeline._LEER_CIERRES_CACHE`, `cmi_filters._*_CACHE` (`:19-22`), `procesos_loaders._PROCESS_MAP_CACHE`, `tracking_cache._TRACKING_CACHE` | ruta/hoja |
| `ExcelReaderService` (singleton, `api/deps.py:10-21`), `StrategicLoaders._cached` | ruta + hoja |
| Precarga al arranque, `main.py:17-47` | fija: `anio=2025`, `rango=True` |
| react-query (`Providers.tsx:55`, staleTime 60 s) | ver §3.2–3.4 |

- **Precalculados**: `narrativa_estrategica_2022_2025.json`, `narrativas_ia_procesos.json` y los Excel de `data/output`. No hay vistas SQL.

### 3.7 PDF, IA, Plan de mejoramiento y OM
- **PDF**: `reports.py:86-105` y `report_html_service.py`, con títulos y textos fijos en `report.html` (`:5,42,124,134,374-471`, que mezclan "2022-2025", "2022–2026" y "2026-2030").
- **IA**: la narrativa estratégica se genera por ciclo, pero la ruta está fija (`narrativa_estrategica_service.py:28,42`); prompts en `ai_prompts`.
- **Plan de mejoramiento**: `plan_mejoramiento.py:59` (subvista "metas 2026-2030"); usa factor y característica CNA sin versión.
- **OM**: `registros_om` y `acciones` no tienen línea ni factor versionado. Si se registra la línea, depende del ciclo.

### 3.8 Pruebas afectadas
- **Backend**: `test_cmi_estrategico.py`, `test_cmi_procesos.py`, `test_resumen_linea.py`, `test_pdi_measurement.py`, `test_performance_cache.py`, `test_fase6_contracts.py`, `test_fase9_pdf.py`, `test_api_phase4.py`, `test_fase4_completions.py`, `test_domain.py`.
- **Frontend**: `navigation.test.ts`, e2e `navegacion.spec.ts`, `kpis.spec.ts`, `semaforo.spec.ts`.

---

## 4. Diseño propuesto (para validar antes de la Fase 2)

### 4.1 Marcos de referencia versionados (PDI y CNA)
Se usa un mismo concepto para los dos tipos de marco y así se evita codificar "actual vs. anterior".

**Registro `config/marcos.toml`**
```toml
[[marco]]
tipo = "PDI"
version_id = "PDI-2022-2026"
nombre = "PDI 2022-2026"
anio_datos_desde = 2022
anio_datos_hasta = 2025         # D3
estado = "cerrado"
imagen = "img/pdi/2022-2026.png"
taxonomia = "data/marcos/PDI-2022-2026/taxonomia.xlsx"
hoja_cierre = "Cierre PDI 2022-2026"
retos = "data/raw/Retos/2022-2026/Plan de retos.xlsx"         # D4
pmo = "data/raw/Proyectos/2022-2026/centroDeProyectos_PMO.xlsx"
narrativa = "data/derived/narrativa_estrategica_PDI-2022-2026.json"

[[marco]]
tipo = "PDI"
version_id = "PDI-2026-2030"
anio_datos_desde = 2026
anio_datos_hasta = 2030
estado = "activo"
# …

[[marco]]
tipo = "CNA"
version_id = "CNA-vigente"         # resolución actual = versión original
vigencia_hasta = 2026
[[marco]]
tipo = "CNA"
version_id = "CNA-2027"            # se carga cuando exista (D5)
vigencia_desde = 2027
```

**Taxonomía por versión** (una hoja por nivel)
- PDI: `Lineas` (linea_id, nombre, orden, color, imagen), `Objetivos` (objetivo_id, linea_id, nombre), `Metas_Estrategicas` (meta_id, objetivo_id, descripción, meta, unidad).
- CNA: `Factores`, `Caracteristicas` (y `Aspectos` si aplican).
- Reemplaza a `pdi_2022_2026.json`, `STRATEGIC_LINE_DEFS`, `CANONICAL_OBJETIVOS`, `LINEA_ORDER`, `_ORDEN_PDI`, `strategic-lines.ts` y los colores e imágenes fijos. **No se debe suponer un número fijo de líneas.**

**Asociación en la base original** (catálogo; hoja nueva `Indicador_Marco`)
- Columnas: `Id` (estable, D1), `tipo`, `version_id`, `nivel1_id`, `nivel2_id`, `nivel3_id`, `FlagPlanEstrategico`, `Orden_CMI`, y meta, fórmula, periodicidad o responsable cuando difieran en esa versión.
- **Migración**: las columnas actuales de texto (`Linea_Estrategica`, `Objetivo_Estrategico`, `Meta_Estrategica`, `Factor`, `Caracteristica`) se convierten en filas de la versión original (`PDI-2022-2026`, `CNA-vigente`). Se genera un reporte con los textos que no se puedan mapear. Las columnas originales se conservan como legado de solo lectura.
- **PDI 2026-2030**: Planeación diligencia la asociación **solo para indicadores activos** (D2). El ETL valida que todo indicador activo con `FlagPlanEstrategico` tenga una fila en el ciclo activo.
- **Sucesiones**: hoja `Sucesion_Indicadores` (`Id_anterior`, `Id_nuevo`, `version_id`, motivo), que generaliza `series_subindicadores.toml:158`.
- **Validación**: los ids de nivel deben existir en la taxonomía de la misma versión.

**Cierres**: una hoja por versión ("Cierre PDI 2022-2026" queda congelada; "Cierre PDI 2026-2030" la produce el pipeline). El script que hoy actualiza "Cierre PDI" debe recibir la versión como parámetro.

### 4.2 Backend
- Nuevo `services/marcos_service.py` que lee el registro y las taxonomías, y nuevo `GET /api/v1/marcos?tipo=PDI` para las tarjetas del selector.
- Parámetro `pdi: str` (por defecto el PDI activo, por compatibilidad) en `/dashboard/*`, `/cmi/*`, `/reports/*` y en la narrativa.
  - `rango` pasa a significar "cierre del PDI seleccionado".
  - `ANIOS_RANGO`, `PRY ≤ 44` y las rutas fijas se derivan de la versión.
- `pdi` se agrega a **todas** las claves de caché y la precarga se hace para cada PDI con estado activo o cerrado.
- Ficha de CMI Procesos y CMI Estratégico: campo `asociaciones: [{tipo, version_id, linea, objetivo, meta | factor, caracteristica}]`, filtrado por cruce de vigencias con la `Fecha Desde` del indicador (D7).
- El consolidado y el % global se unifican sobre `domain/pdi_measurement.py`, con la versión como parámetro.
- Postgres: migración `005_marcos_version.sql`, que agrega `version_id` a las tablas de OM y de plan de mejoramiento que guarden línea o factor.

### 4.3 Frontend
- Rutas `/(dashboard)/pdi/[pdi]/{resumen-general,cmi-estrategico,cmi-procesos}` (el PDI va en la URL, D6).
- Pantalla `/pdi?destino=resumen-general|cmi-estrategico|cmi-procesos` con una tarjeta por PDI (imagen, nombre, estado activo/cerrado), generada desde `/marcos`.
- `NAV_ITEMS`, el lanzador y `canAccessPath` apuntan al selector. Las rutas viejas redirigen al selector.
- Chip "PDI 2026-2030 ▾" en la cabecera de cada módulo para cambiar rápido.
- `pdi` en todas las claves de react-query. Títulos, años y líneas se toman de la API.

### 4.4 ETL
- `normalizacion.py` reconoce la nueva hoja de asociación.
- `actualizar_consolidado.py` y el paso de "Cierre PDI" quedan parametrizados por versión.
- `validation_gate.py` agrega las reglas de asociación y taxonomía.
- CI mensual sin cambios de calendario.

### 4.5 Etapa nueva: generador del cierre del PDI por versión
Se validó en el repo original (`C:\Users\ximen\OneDrive\Proyectos_DS\Sistema_Indicadores_Poli`) y en SGING.

**Ninguno contiene un script que construya las filas de la hoja "Cierre PDI".** En ambos, el pipeline solo recalcula el cumplimiento de la hoja ya existente:
- `formulas_excel._materializar_cumplimiento`, invocado desde `actualizar_consolidado.py:725-727`. Evidencia: `artifacts/agent_run_20260905_102433.json` del repo original y `artifacts/pipeline_run_20260920_202029.log:348` de SGING.
- `purga.py:773`.

Las filas actuales (90 registros) existen en el Excel, pero su generación no está versionada en código. Por eso esta etapa se incluye en el plan.

1. **Ingeniería inversa del cierre 2022-2026:** comparar cada fila de "Cierre PDI" con "Consolidado Cierres", "Consolidado Historico" y la fuente de proyectos para deducir la regla (último cierre del ciclo, valor acumulado o máximo, tratamiento de proyectos con Ids como "10.1", casos resueltos a mano que documenta `proyectos_oficiales_service.py:8-66`). Documentar la regla y las excepciones.
2. **Script nuevo** `scripts/etl/cierre_pdi.py`, con la firma `generar_cierre(version_id)`:
   - toma los indicadores asociados a la versión (`Indicador_Marco`) y los años `anio_datos_desde..hasta` del registro;
   - aplica la regla del paso 1;
   - escribe la hoja `Cierre PDI <version>`.
3. **Prueba de equivalencia:** `generar_cierre("PDI-2022-2026")` debe reproducir la hoja actual fila por fila. Cada diferencia se explica o se declara en una hoja de excepciones (`Cierre_Excepciones`).
4. **Integración en el pipeline:**
   - Se ejecuta en `run_pipeline.py` / `actualizar_consolidado.py` para la versión activa (2026-2030).
   - La de 2022-2026 queda **congelada**: no se regenera salvo de forma explícita.
   - `formulas_excel` y `purga` siguen recalculando por título "Cierre…", y debe verificarse que no alteren la hoja congelada.
5. **Backend:** `strategic_loaders.load_cierre_pdi_final` lee la hoja indicada en `hoja_cierre` del registro de la versión.

---

## 5. Riesgos y preguntas abiertas

| # | Tema | Estado |
|---|---|---|
| R1 | **Generador de "Cierre PDI"**: no existe ni en SGING ni en el repo original (`Sistema_Indicadores_Poli`); solo se recalcula su cumplimiento. | Se incluye como etapa en §4.5 |
| R2 | Taxonomía 2026-2030 con ids (líneas, objetivos, metas): falta definir el responsable y la fecha de entrega. | Abierta |
| R3 | Calidad de `Fecha Desde` en la ficha técnica (nulos, formatos). La regla de la ficha (D7) depende de ella. | Validar en la Fase 2 |
| R4 | Mapear el texto libre actual a ids de la taxonomía 2022-2026 (variantes de escritura). | Reporte de no mapeados |
| R5 | El % global difiere entre la vista consolidado y el PDF; hay que unificarlo antes de comparar PDI. | Decisión técnica |
| R6 | Retos y PMO 2026-2030 deben asociarse a las nuevas líneas; los archivos por ciclo aún no existen. | Abierta |
| R7 | Recursos visuales por ciclo (flor estratégica, mindmap, imágenes). | Diseño |
| R8 | Resolución CNA 2027 aún sin listado; el modelo queda listo, pero sin datos. | Planificada |
| R9 | Power BI sin dimensión de versión. | Fuera de alcance (pendiente) |
| R10 | Restricción del PDI por rol. | Fuera de alcance (pendiente) |
| R11 | Los cambios de URL rompen enlaces guardados y pruebas e2e; se necesitan redirecciones. | Mitigado con redirecciones |
