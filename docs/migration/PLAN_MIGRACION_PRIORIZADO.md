# Plan de Migración Priorizado — Lógica, Módulos, Visuales y Filtros

> **⚠ Superado (2026-09-20).** Este documento se conserva como referencia
> histórica, no como fuente de verdad vigente. Fue verificado contra código
> el 2026-09-18, pero ya quedó parcialmente desactualizado dos días
> después (su hallazgo sobre el módulo Plan de Mejoramiento — "sin ningún
> equivalente en SGING" — ya no era cierto para el 2026-09-20; ver G-09 en
> `docs/tecnico/09-gaps-y-riesgos.md`). El plan de transformación vigente,
> con auditoría de código más reciente y priorizado por oleadas, es
> `docs/migration/PROMPT_AUDITORIA_ACTUAL.md` y la documentación en
> `docs/tecnico/` + `docs/funcional/`.

**Fecha:** 2026-09-18
**Origen:** auditoría de código independiente sobre `Sistema_Indicadores_Poli/` (Streamlit legacy) y este repositorio (SGING v2), verificando cada afirmación de [`STATUS.md`](STATUS.md) y [`ROADMAP.md`](ROADMAP.md) directamente contra el código fuente, no contra lo que esos documentos dicen. Complementa (no reemplaza) [`PLAN_CIERRE_HALLAZGOS.md`](PLAN_CIERRE_HALLAZGOS.md), del que retoma varias fases reclasificándolas por prioridad real.

## Alcance

Este documento cubre exclusivamente **lógica de negocio, módulos (nuevos o a reactivar), visuales/gráficos, opciones y filtros**. La autenticación y el modelo de seguridad actuales se mantienen tal como están configurados hoy — no se proponen cambios ahí; queda fuera de este documento por decisión explícita.

## Principios transversales

Aplican a todos los ítems de este plan, no son tareas aparte:

- **DDD (Domain-Driven Design)**: las reglas de negocio (categorización de cumplimiento, cálculo de cumplimiento faltante, bandas Kawak, clasificación de tendencia, estado de un indicador del plan, etc.) viven exclusivamente en la capa de dominio (`backend/app/domain/`), como funciones puras sin dependencia de framework/infraestructura. `categorization.py` ya sigue este patrón — es la referencia a imitar en cualquier módulo de reglas nuevo o portado.
- **Arquitectura Limpia / Hexagonal**: separación disciplinada dominio (reglas puras) → aplicación/servicios (orquestación, ej. `pdi_service.py`) → infraestructura (lectura de Excel/Postgres) → presentación (endpoints/UI). Al reactivar o construir un módulo (ver Prioridad Alta ítem 0, y Media ítems 8-10), estructurarlo así desde el inicio en vez de replicar el patrón de "builder monolítico" ya señalado como problema (`informe_por_procesos.py` 1211 líneas y `resumen_por_proceso.py` 4210 líneas en el legacy; builders de dominio igual de largos ya en SGING).
- **Refactorización constante**: cualquier ítem que toque un archivo con código muerto, duplicación, o una función de más de 150-200 líneas incluye su descomposición como parte del mismo cambio — no como tarea aparte que nunca se prioriza. Ejemplo: al consolidar la paleta de semáforo (ítem 1) se elimina la duplicación, no se agrega una cuarta fuente "por si acaso".

---

## Prioridad Crítica — bloquea el cutover (Fase 12), no solo la paridad funcional

### -1. Migrar el pipeline ETL que produce los datos — hoy vive exclusivamente en `scripts/` del legacy, sin ningún equivalente en SGING

**Hallazgo (2026-09-18, a partir de una pregunta directa del usuario):** toda la migración hasta ahora portó el **lado de lectura** (dashboards/API) asumiendo que los archivos Excel consolidados (`Resultados Consolidados.xlsx`, `Resultados_Consolidados_CNA.xlsx`, etc.) ya existen. Nadie migró el proceso que **produce** esos archivos. Confirmado en código: `backend/app/services/etl_pipeline.py` (nombre engañoso, "ETLPipelineService") no extrae ni consolida nada — solo lee el Excel ya generado y renombra columnas para el dashboard.

**Por qué no se migró (causa raíz, no un descuido puntual):** decisión de alcance documentada desde el inicio en `ROADMAP.md`: *"Ejecución paralela. Streamlit permanece activo en producción hasta el cutover (Fase 12). Los datos Excel en `data/` se montan como volumen read-only en el nuevo backend."* SGING fue diseñado desde el ADR-001 como consumidor de solo lectura. Ninguna fase del roadmap (0-12) contempla portar el pipeline de producción de datos — la Fase 8 "Migración de Datos" solo migró datos *ya producidos* (SQLite→Postgres), no el proceso que los genera.

**Consecuencia si se ejecuta el cutover tal como está planeado:** SGING se queda sin forma de refrescar los datos institucionales. Los indicadores se congelan en el último Excel que exista al apagar Streamlit. Esto no es un hallazgo de paridad — es un bloqueante de viabilidad del cutover.

**Alcance real, auditado archivo por archivo (~130 scripts en `Sistema_Indicadores_Poli/scripts/`):**

**a) Ruta de producción real — lo que hay que portar primero.** Confirmado por `.github/workflows/pipeline_automatico.yml` (cron día 5 de cada mes) y `config/settings.toml`:
- `scripts/agent_runner.py` → `scripts/run_pipeline.py` orquestan, en orden: `consolidar_api.py` → `actualizar_consolidado.py` → `generar_reporte.py`.
- `consolidar_api.py`: lee `data/raw/Kawak/{año}.xlsx` (catálogo maestro) + `data/raw/API/{año}.xlsx` (extracción API Kawak) → produce `Indicadores Kawak.xlsx` + `Consolidado_API_Kawak.xlsx`.
- `actualizar_consolidado.py` (el archivo más reciente de todo el pipeline, modificado 2026-08-18): orquestador monolítico — carga fuente, valida contrato (Gate 1), carga catálogo/metadatos, purga filas inválidas, construye registros (histórico/semestral/cierres) vía `scripts/etl/builders.py`, expande sub-indicadores y cronogramas de proyectos, aplica **correcciones AGENT5** (reglas de negocio sobre Ejecución>1.3 y Meta=0/NULL), valida (Gate 2/3), escribe, repara, deduplica, actualiza catálogo, guarda con backup + rollback automático si falla. Produce `data/output/Resultados Consolidados.xlsx`.
- `scripts/etl/*.py` (23 módulos: `normalizacion`, `fuentes`, `catalogo`, `builders`, `agent5_corrections`, `escritura`, `purga`, `signos`, `formulas_excel`, `versioning`, `audit`, `retry_handler`, `notifications`, `validation_gate`, etc.) — toda la lógica de negocio del ETL real, importada por `actualizar_consolidado.py`.
- `generar_reporte.py`: calcula métricas de calidad del run (filas, IDs únicos, cumplimiento promedio, nulos).

**b) `scripts/cna_extraction/` (creado 2026-09-17, la semana del rediseño de Plan de Mejoramiento) — el mejor candidato para portar primero.** Pipeline en 2 fases con límites de escritura explícitos (Fase 1 solo diagnóstico, Fase 2 escritura incremental), produce `data/output/Resultados_Consolidados_CNA.xlsx`. Es el más nuevo, el mejor diseñado, y el que menos deuda técnica acumulada tiene — sin cron/automatización todavía, ejecución manual.

**c) `scripts/pipeline_steps/` (13 pasos + `runner_server.py`, un servidor HTTP local con UI web para correr el pipeline paso a paso) — NO está en la ruta de producción real** (confirmado por grep: ningún workflow/Dockerfile lo referencia), es una reimplementación más nueva (2026-07-15) de la misma lógica de `actualizar_consolidado.py`, pensada para debug manual. Útil como **referencia de diseño de boundaries** para los endpoints del nuevo pipeline (los 13 pasos ya son una descomposición natural), pero el comportamiento de negocio a portar es el de `actualizar_consolidado.py` (el que realmente corre).

**d) `scripts/consolidation/` (paquete "v8 modular" completo, con orquestador/extractores/workers propios) — OBSOLETO/EXPERIMENTAL NO ADOPTADO.** Apunta al mismo archivo de salida que `actualizar_consolidado.py`, pero no está referenciado por ningún workflow ni por el pipeline real; sus fechas de modificación son anteriores al último cambio de `actualizar_consolidado.py`. No usar como base de lógica de negocio — a lo sumo, su idea de paralelización/workers puede inspirar el diseño del nuevo backend.

**e) ~40 scripts de diagnóstico/auditoría puntual y migraciones de una sola pasada** (`scripts/diagnostics/*`, `scripts/agent1-9_*.py` salvo `agent5_corrections` que sí es de producción, `scripts/_archived/*`, `scripts/_patch_*`, `scripts/migrar_*`, `scripts/validar_*` sueltos, etc.) — **no migrar**: son herramientas de un solo uso o ya ejecutadas, varias con rutas hardcodeadas al computador de un desarrollador específico, confirmadas por evidencia (no por nombre) como no importadas por el core activo.

**f) Estado incierto, requiere confirmación con el equipo antes de descartar:** `scripts/backup_sqlite.py` (¿corre vía Windows Task Scheduler en algún servidor real?), `scripts/panel_monitoreo.py` / `scripts/ingesta_plantillas.py` (¿siguen enlazados a la app Streamlit activa?), `scripts/analytics/{data_preparator,predictor}.py` (sin imports encontrados en el resto del repo, posible funcionalidad en desarrollo nunca integrada).

**Acción propuesta:** este ítem requiere su propio diseño de arquitectura (¿el pipeline corre como job programado del backend FastAPI, como función serverless separada, o se mantiene como script operado manualmente contra Postgres?) — no es una tarea de "portar código", es una decisión de infraestructura de datos que aún no se ha tomado. Orden recomendado: (1) decidir la arquitectura del pipeline en el nuevo stack, (2) portar `cna_extraction/` primero (menor deuda, ya aislado en 2 fases), (3) portar la cadena `consolidar_api → actualizar_consolidado → generar_reporte` completa incluyendo las reglas de negocio de `scripts/etl/*` (esto es, en volumen de lógica, comparable o mayor a todo lo demás migrado hasta ahora), (4) confirmar con el equipo el estado incierto de (f) antes de dar el pipeline por completo.

---

## Prioridad Alta — regresiones funcionales, inconsistencias de lógica de negocio, o bloqueantes de paridad frente a Streamlit

### 0. Portar el módulo completo de Plan de Mejoramiento tal como existe HOY en Streamlit

SGING tiene una **versión anterior y distinta** del módulo, no una versión parcial de la actual — el código legacy fue **rediseñado por completo este mes** (`streamlit_app/pages/plan_mejoramiento.py` línea 7: *"2 pestañas planas — Indicadores / Métricas — ... Sin drilldown Factor→Característica→Indicador (reemplazado por completo)"*; commits `03751a4`, `d69978e`, `157f10d`, `daa2395`, 10–17 sep 2026). Lo que hay hoy en SGING (`PlanMejoramientoService.get_dashboard`, basado en `preparar_cna_con_cierre`/`apply_cna_filters`/`build_tabla_cna`, tabla plana única "Indicadores CNA" + Acciones, sin pestañas) corresponde al **diseño anterior ya reemplazado**, no a una versión incompleta del actual. Hay que portar el módulo completo, no solo el delta.

**a) Pestaña "Indicadores"** — fuente: `services/plan_mejoramiento_loader.py::load_plan_indicadores()`, Excel `Indicadores Plan de Mejoramiento.xlsx` hoja "Indicadores Plan de Mejor". **Sin lectura alguna en SGING hoy**: cero referencias a `load_plan_indicadores`, `Meta_num_2025` o `Indicadores Plan de Mejor` en `backend/`.

- 4 KPIs: Indicadores del plan (total), Con meta 2026–2030, Con cumplimiento histórico, Aprobados (con %).
- Sub-vista (`st.segmented_control`): **"Metas 2026–2030"** vs **"Cumplimiento histórico"**, cada una con su gráfico propio (`chart_indicadores_metas_por_factor` / `chart_indicadores_cumplimiento`, en `streamlit_app/components/plan_mejoramiento_charts.py`) y su propia vista de tabla.
- Filtros: Factor (12 factores CNA), Tipo (Indicador y métrica / Solo indicadores / Solo métricas / Sin clasificar), búsqueda de texto libre sobre Indicador+Característica+Acción de mejora.
- Tabla clickable → modal de detalle (`_open_indicador_modal`) con Factor, Característica, Acción de mejora, Tipo, Estado/Aprobación, Responsable, Fuente, Periodicidad, Fórmula, Observación de desempeño, texto combinado Meta/Ejecución/%Cump 2025-2026, y Metas 2026-2030.
- Exportación a Excel (`_render_export_button`), dos variantes según la sub-vista activa.
- Reglas de negocio: cumplimiento = `Ejecución/Meta` (clip a 1.3, solo si Meta≠0 y ambos numéricos); estado `Activo`/`Aprobado`/`Pendiente` vía `_classify_plan_estado` (Activo requiere aprobado + tipo Indicador + medición 2025/2026; Aprobado = aprobado sin medición; si no, Pendiente).
- **Cambio de esta semana** (commit `daa2395`, 17-sep): catálogo nuevo `Catalogo_Indicadores_Plan_Mejoramiento.xlsx` (generado por `scripts/plan_mejoramiento/build_catalogo_indicadores.py`) que clasifica cada indicador con `Signo` (`%FRAC`|`%`|`ENT`|`DEC`|`Sin reporte`) y `Decimales`/`Decimales_Cump`, porque el Excel fuente no es consistente en si un indicador porcentual guarda su valor como fracción 0–1 o como número 0–100; `fmt_valor_plan()` usa ese catálogo para formatear Meta/Ejecución correctamente. **El propio script documenta que es un borrador heurístico de primera pasada, pendiente de revisión manual fila por fila** — coordinar con el negocio el momento en que se considere estable antes de portarlo como definitivo. No confundir con `Meta_Signo`/`Decimales_Meta`/`Decimales_Ejecucion`, ya existentes en `plan_mejoramiento_builders.py::build_tabla_cna` — esquema de formateo distinto y anterior, propio de la tabla CNA por cierre; no mezclar con el nuevo catálogo `Signo`/`Decimales`/`Decimales_Cump`.

**b) Pestaña "Métricas"** — fuente: `services/plan_mejoramiento_loader.py::build_metricas_historico()`, hoja "Metricas" de `data/output/Resultados_Consolidados_CNA.xlsx`. **También sin equivalente confirmado en SGING**: cero referencias a `Subindicador`, a clasificación de tendencia Creciente/Decreciente/Estable, o a columnas tipo sparkline en `plan_mejoramiento_builders.py`.

- 4 KPIs: Métricas con histórico, Factores cubiertos (de 12), % en tendencia creciente, % en tendencia decreciente.
- Gráfico interactivo por factor (`chart_metricas_por_factor`); clic en un punto filtra la tabla por ese factor (`on_select="rerun"`, vía `customdata`).
- Filtros: Factor (pills), Tendencia (Toda/Creciente/Decreciente/Estable), búsqueda de texto.
- Tabla con columna **"Serie" tipo sparkline** (`st.column_config.LineChartColumn`) — sin equivalente nativo hoy en el frontend de SGING (Plotly/Recharts no traen una celda de tabla con mini-gráfico embebido; requiere componente custom).
- Selección de fila → modal (`_open_metrica_modal`) con `chart_metrica_detalle` (resultado vs. meta), Proceso, Sentido/Periodicidad, Variación último año y Variación promedio anual.
- Regla de negocio: tendencia histórica por variación interanual promedio (`_classify_tendencia_historico`): `>+3%` Creciente, `<-3%` Decreciente, si no Estable, "Sin suficiente historia" si hay menos de 2 años con dato — **distinta** de `classify_trend` (compara solo los dos últimos periodos), que el loader conserva pero que ya no usa la vista plana actual; verificar en la migración si `compute_trend_table`/`aggregate_trend_by`/`compute_evolucion_agregada`/`compute_evolucion_por_segmento` siguen vivas en otro lugar (tests u otra página) o son ya código muerto a excluir.
- Métricas y Plan de Indicadores siguen siendo **fuentes independientes sin cruce a nivel indicador** (`docs/metodologia_plan_cna.md`), solo conviven en la misma página por pestaña — no diseñar el backend de SGING asumiendo un join que no existe en el legacy.

**c) Nueva fuente de datos de Métricas CNA** (commit `157f10d`, mismo día): el legacy reemplazó la lectura directa de `Resultados_Consolidados_CNA_actualizado.xlsx` por un pipeline propio `scripts/cna_extraction/` que genera `data/output/Resultados_Consolidados_CNA.xlsx` a partir del Anexo Estadístico oficial (detección de estructura, normalización y diagnóstico propios). El esquema de la hoja "Metricas" se mantuvo compatible, pero conviene verificar que `StrategicLoaders`/`load_cna_catalog()` en SGING apunte a esta misma fuente de verdad y no a una copia congelada más antigua.

**Acción**: tratarlo como rediseño de módulo, no como ajuste — añadir en `backend/app/domain/plan_mejoramiento_builders.py` las funciones de dominio para ambas pestañas (separadas de `build_tabla_cna`, que queda obsoleta o se reduce a fuente interna si ya no refleja la UI real), exponerlas en `PlanMejoramientoService`, y reconstruir `frontend/.../plan-mejoramiento/page.tsx` con las 2 vistas, sus KPIs, gráficos, filtros, modales y exportación — siguiendo el patrón dominio→servicio→endpoint tipado→UI ya usado en el resto del backend.

### 1. Consolidar la paleta de semáforo en una sola fuente de verdad
Persisten 3 definiciones hex distintas en frontend (`design-tokens.ts` vs `cmiChartColors.ts` vs `nivelUtils.tsx`/`CmiProcesosBarPlotly.tsx`); solo backend + `cmiChartColors.ts` coinciden. Retoma `PLAN_CIERRE_HALLAZGOS.md` Fase 1: eliminar las fuentes duplicadas, no agregar una cuarta.

### 2. Paginar las tablas de alertas en Seguimiento Operativo
`AlertTable` sigue truncada a 20 filas sin total visible. La tabla principal de detalle ya quedó resuelta con paginación real server-side; falta este componente secundario.

### 3. Exponer `DELETE` de OM en la UI de Gestión OM
El backend ya lo soporta (`require_admin`); completa el CRUD que hoy solo tiene crear/editar/cerrar en pantalla.

### 4. Reconciliar la discrepancia entre `STATUS.md` y `ROADMAP.md`
Sobre si Seguimiento Operativo/Informe por Procesos ya están conectados a la API real o siguen pendientes — verificar en código cuál documento está desactualizado y corregirlo. (Plan de Mejoramiento ya se resolvió con evidencia concreta en el ítem 0: la parte "Métricas CNA" sí está conectada; la parte "Indicadores" nunca lo estuvo.)

### 5. Cascada de filtros compartida + persistencia en URL
`PLAN_CIERRE_HALLAZGOS.md` Fase 4: `cmi-procesos` e `informe-procesos` duplican la lógica de cascada Unidad→Proceso→Subproceso carácter por carácter, con una divergencia real (reset de mes al cambiar año). Extraer a un hook compartido y aprovechar para persistir filtros en la URL en todos los módulos (hoy solo `?cmi_linea=` lo hace).

### 6. Decisión de producto sobre módulos huérfanos del legacy
El Tablero Operativo (Kanban/QC/Trazabilidad, ~1300 líneas en 3 archivos) no tiene equivalente en SGING y su estado "en scope o descontinuado" nunca se confirmó con negocio. Resolver explícitamente si se migra como módulo nuevo o se documenta como descontinuado, antes de dar por cerrada la paridad funcional.

### 7. Ejecutar `scripts/uat_verify.py` contra datos reales
Es el paso que valida numéricamente que los cálculos de negocio dan el mismo resultado en ambos sistemas; el script existe pero no hay evidencia de que se haya corrido.

---

## Prioridad Media — módulos nuevos/formalización, paridad visual, y consistencia de dominio

### 8. Panel de administración de usuarios/roles
`PLAN_CIERRE_HALLAZGOS.md` Fase 7 — RBAC ya existe en BD, falta exposición HTTP + UI. Diseñar como módulo de aplicación separado del dominio de indicadores, coherente con Arquitectura Limpia.

### 9. Comparativos multi-año
Fase 8 del plan existente — extender `/dashboard/yoy` a un rango de 3-5 años en vez de comparación puntual; verificar que reutiliza la misma capa de dominio de cálculo, no una nueva paralela.

### 10. Evaluar paridad de visualizaciones no confirmadas en SGING
Heatmap Proceso×Periodo, radar comparativo, gauge/indicator, bullet chart, treemap Factor→Característica, sparklines de tendencia. Legacy los tiene disponibles en `heatmap_chart.py`/`renderers.py`; SGING no los tiene confirmados. **Antes de migrarlos, confirmar con negocio cuáles estaban realmente en uso** (no solo disponibles como librería).

### 11. Tipar los endpoints backend restantes
Sin `response_model`: `/sunburst`, `/yoy`, `/procesos/export`, `/seguimiento/export`, `om.py:/plan-accion`. El contrato de datos que cruza la frontera debe estar declarado, no ser `dict[str, Any]`.

### 12. Limpieza de código muerto confirmado en Streamlit
No se migra, se documenta como descartado: `dashboard_config.py` + `dashboard_modules/` (100% mock), páginas no enrutadas (`resumen_general_real.py`, `cmi_estrategico.py`, `cmi_por_procesos_resumen.py`), entrypoint alterno `streamlit_app/app.py`.

---

## Prioridad Baja — mejoras de UX/paridad visual menor, post-cutover

### 13. Habilitar exportación de imagen en gráficos Plotly
11 ubicaciones con `displayModeBar:false` en SGING — hoy es peor que el legacy en este punto puntual.

### 14. Consolidar las 3 librerías de gráficos (Plotly/Recharts/SVG manual) en un wrapper único
Mejora de mantenibilidad y consistencia de interacción (tooltips, zoom), sin impacto funcional inmediato.

### 15. Reforzar jerarquía visual Macro→Meso→Micro
En los módulos que aún no la validaron explícitamente (regla ya definida en `ROADMAP.md`, pendiente en Fase 3 UX/UI).

---

## Tabla resumen

| # | Prioridad | Ítem | Origen | Estado verificado | Principio transversal |
|---|---|---|---|---|---|
| -1 | **Crítica** | Migrar el pipeline ETL de producción de datos (`scripts/`, ~130 archivos auditados) | Hallazgo nuevo (pregunta directa del usuario, 2026-09-18) | Sin ningún equivalente en SGING — confirmado archivo por archivo | Arq. Limpia (decisión de infraestructura pendiente) |
| 0 | Alta | Portar módulo completo Plan de Mejoramiento (Indicadores + Métricas + catálogo Signo) | Hallazgo nuevo (código legacy rediseñado 10-17 sep 2026) | Sin ningún equivalente en SGING — confirmado por grep | DDD, Arq. Limpia |
| 1 | Alta | Consolidar paleta de semáforo | `PLAN_CIERRE_HALLAZGOS.md` Fase 1 | Vigente — 3 paletas hex distintas | Refactor constante |
| 2 | Alta | Paginar tablas de alertas (Seguimiento Operativo) | Comparativo jul-2026 + verificación esta auditoría | Parcial — tabla principal ya paginada, alertas no | — |
| 3 | Alta | Exponer `DELETE` de OM en UI | `STATUS.md` Fase 5 extra | Parcial — create/update/cerrar sí, delete no | — |
| 4 | Alta | Reconciliar discrepancia STATUS.md vs ROADMAP.md (Seguimiento/Informe) | Discrepancia de documentación | Pendiente de verificar | Documentación viva |
| 5 | Alta | Hook `useCascadingProcessFilters` + URL | `PLAN_CIERRE_HALLAZGOS.md` Fase 4 | Vigente | Refactor constante |
| 6 | Alta | Decisión de negocio: Tablero Operativo Kanban | Comparativo jul-2026 | Confirmado inexistente en SGING | — |
| 7 | Alta | Ejecutar `uat_verify.py` con datos reales | `STATUS.md` Fase 11 | Script listo, no ejecutado | — |
| 8 | Media | Panel admin usuarios/roles | `PLAN_CIERRE_HALLAZGOS.md` Fase 7 | Confirmado inexistente | Arq. Limpia |
| 9 | Media | Comparativos multi-año | `PLAN_CIERRE_HALLAZGOS.md` Fase 8 | No implementado | DDD |
| 10 | Media | Paridad de visualizaciones (heatmap/radar/gauge/bullet/treemap/sparklines) | Comparativo jul-2026 | No confirmado en SGING | — |
| 11 | Media | Tipar endpoints restantes | `PLAN_CIERRE_HALLAZGOS.md` Fase 2 | Vigente | Arq. Limpia |
| 12 | Media | Limpieza de código muerto Streamlit | Auditoría Fase 1 (esta conversación) | Confirmado | Refactor constante |
| 13 | Baja | Exportación de imagen en gráficos Plotly | `PLAN_CIERRE_HALLAZGOS.md` Fase 5.1 | Vigente | — |
| 14 | Baja | Wrapper único de librería de gráficos | Comparativo jul-2026 | Vigente | Refactor constante |
| 15 | Baja | Jerarquía visual Macro→Meso→Micro | `ROADMAP.md` Fase 3 | Pendiente de validar | — |
