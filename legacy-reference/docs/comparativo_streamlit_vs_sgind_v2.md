# Comparativo funcional y visual: Streamlit (legacy) vs. SGIND-v2

**Fecha del análisis:** 2026-07-11
**Alcance:** revisión de código fuente completa de `streamlit_app/` (+ `app.py`, `core/`, `services/` raíz) vs. `sgind-v2/frontend/` (Next.js 14) y `sgind-v2/backend/` (FastAPI), más documentación de migración en `sgind-v2/docs/`.
**Metodología:** exploración de código por tres agentes independientes (uno por sistema), sin ejecutar las apps en navegador. Toda observación cita archivo:línea de origen.

---

## 1. Resumen ejecutivo

SGIND-v2 replica con **alta fidelidad funcional** los 7 módulos activos del menú de Streamlit, reorganizados en 9 rutas Next.js consumiendo una API FastAPI de 46 endpoints. La lógica de negocio (fórmulas de cumplimiento, umbrales de semáforo, régimen "Plan Anual" vs. regular) fue portada explícitamente 1:1 desde `core/domain/categorization.py` del legacy — hay comentarios en el código v2 que lo confirman literalmente.

**Hallazgo principal**: la migración está funcionalmente **~85-90% completa** sobre el alcance enrutado del legacy, pero con tres categorías de riesgo:

1. **Funcionalidades no migradas o de estado incierto**: análisis con IA generativa real (Claude) en fichas de indicador (v2 solo tiene heurísticas basadas en reglas, mal etiquetadas como "IA"), generación de PDF por ficha individual, exportación de imágenes de gráficos, motor ECharts de respaldo, sparklines, y 4 módulos "huérfanos" del legacy (Tablero Operativo Nivel 3 con Kanban/QC/Trazabilidad, Gestión y Acreditación Nivel 2) cuyo estado de "en scope o descontinuado" no está confirmado en el código.
2. **Deuda técnica trasladada, no eliminada**: v2 sigue leyendo Excel en cada request (sin ETL a base de datos analítica), mantiene módulos de dominio de 700-1000+ líneas (el problema de "páginas monolíticas" del legacy reaparece como "builders monolíticos"), y tiene inconsistencias internas (3 definiciones distintas de colores de semáforo en frontend, umbrales de PDI reimplementados fuera del módulo central de categorización).
3. **Brechas de UX**: v2 no persiste filtros en URL (excepto un caso puntual), no tiene paginación real en tablas grandes (trunca a 200 filas en cliente), y mezcla tres librerías de gráficos (Plotly/Recharts/SVG manual) sin wrapper único, generando inconsistencia de interacción.

**Mejoras claras de v2 sobre legacy**: RBAC real con 3 roles (vs. whitelist plana sin roles), CRUD completo de Gestión OM sobre PostgreSQL (vs. solo lectura+formulario simple en legacy), separación arquitectónica routers/servicios/dominio, tests E2E con Playwright, y generación de PDF de reportes completos (Resumen General, Informe por Procesos) que el legacy no tenía.

**Estimación de equivalencia funcional: ~85%** sobre el alcance enrutado (7 módulos activos), **~65-70%** si se incluyen los 4 módulos huérfanos del legacy como parte del alcance. Ver sección 15 para el desglose.

---

## 2. Inventario y matriz comparativa de módulos

| # | Módulo Streamlit | Estado en Streamlit | Módulo SGIND-v2 | Estado en v2 | Veredicto |
|---|---|---|---|---|---|
| 1 | Resumen General (`pages/resumen_general.py`, 3141 líneas) | Activo, enrutado | Resumen General (`/resumen-general`) | Activo | **Existe en ambos** — ver §2.1 |
| 2 | CMI Estratégico (`cmi_estrategico_tabulado.py`) | Activo, enrutado | CMI Estratégico (`/cmi-estrategico`) | Activo | **Existe en ambos** — ver §2.2 |
| 3 | CMI por Procesos (`resumen_por_proceso.py`, 4207 líneas) | Activo, enrutado | CMI por Procesos (`/cmi-procesos`) | Activo | **Existe en ambos** — ver §2.3 |
| 4 | Informe por Procesos (`informe_por_procesos.py`) | Activo, enrutado | Informe por Procesos (`/informe-procesos`) | Activo | **Existe en ambos, mejorado** — ver §2.4 |
| 5 | Plan de Mejoramiento / CNA (`plan_mejoramiento.py`) | Activo, enrutado | Plan de Mejoramiento (`/plan-mejoramiento`) | Activo | **Existe en ambos** — ver §2.5 |
| 6 | Seguimiento Operativo (`seguimiento_reportes.py`) | Activo, enrutado | Seguimiento Operativo (`/seguimiento-operativo`) | Activo, con limitación de tabla | **Existe parcialmente** — ver §2.6 |
| 7 | Gestión OM (`gestion_om.py`, 1640 líneas) | Activo, enrutado | Gestión OM (`/gestion-om`) | Activo, CRUD mejorado | **Existe y mejora** — ver §2.7 |
| 8 | Tablero Operativo Nivel 3 (`tablero_operativo.py`, 1001 líneas) — Kanban, QC, Trazabilidad | **No enrutado** en menú (huérfano) | Sin equivalente directo | — | **Solo existe (parcialmente) en Streamlit** — requiere confirmación de negocio |
| 9 | Gestión y Acreditación Nivel 2 (`pdi_acreditacion.py`) | **No enrutado** (huérfano) | PDI / Acreditación (`/pdi-acreditacion`, Beta) | Activo (Beta) | **Existe en ambos** — v2 lo formalizó pese a no estar en el menú legacy |
| 10 | Diagnóstico técnico de despliegue (`pages/diagnostico.py`) | No enrutado, utilitario | Diagnóstico (`/diagnostico`, Beta) | Activo, autochequeo de sistema | **Existe en ambos**, con propósito distinto (v2: healthcheck de API/auth/datos) |
| 11 | Administración de usuarios/roles | **No existe** (whitelist en `st.secrets`) | **No existe** (RBAC vía BD pero sin panel UI) | — | **No existe en ninguno** — oportunidad de mejora |
| 12 | Configuración de umbrales/parámetros | **No existe** (solo editando Excel/código) | **No existe** | — | **No existe en ninguno** |

### 2.1 Resumen General
- **Streamlit**: 4 "vistas" (Indicadores/Proyectos/Plan de Retos/Consolidado) con sunburst Línea→Objetivo, fusión fuzzy de etiquetas casi-duplicadas (`difflib`, umbral 0.92), sin exportación visible al usuario.
- **v2**: mismas 4 vistas (`VistaSelector`), `SunburstPlotlyChart`, `ExecutiveNarrative`, `ProyectosGanttChart` (nuevo — el legacy no tenía Gantt), tablas de tendencia/variación, **exportación PDF** (mejora sobre legacy, que no exportaba nada en este módulo).
- **Brecha**: no se confirmó si v2 replica la fusión fuzzy de etiquetas casi-duplicadas del sunburst; el componente `ExecutiveNarrative` en v2 usa HTML de un backend heurístico, análogo al narrativo del legacy, no verificado como generación por IA real en ninguno de los dos.

### 2.2 CMI Estratégico
- **Streamlit**: 4 secciones (Resumen Desglosado, Líneas Estratégicas con análisis IA real vía Claude, Listado con exportación Excel, Alertas) + modal de ficha con **análisis IA real, exportación PDF individual y gráfico de pastel + barra/línea combinada**.
- **v2**: 4 pestañas equivalentes (Resumen, Líneas, Listado, Alertas), modal de ficha (`CmiFichaModal`) con histórico Recharts, deep-link por URL (`?cmi_linea=`, único caso de persistencia de filtro en v2).
- **Brecha crítica**: el análisis con IA generativa real (Claude Haiku) de fichas y líneas estratégicas en Streamlit **no tiene equivalente confirmado como IA real en v2** — el backend v2 solo tiene "narrativa heurística" basada en reglas (`generate_ficha_narrativa_heuristica`), no una llamada a un LLM. Tampoco se confirmó exportación PDF de ficha individual en v2 (solo hay PDF de reporte completo a nivel de módulo, no por indicador).

### 2.3 CMI por Procesos
- **Streamlit**: 5 pestañas, con un catálogo extenso de visualizaciones reutilizables (`heatmap_chart.py`): heatmap, sunburst, radar, timeline, treemap, gauge, bullet chart — no todas necesariamente en uso activo.
- **v2**: 5 pestañas equivalentes, con exportación real CSV/Excel (`downloadCMIProcesosExport`), narrativa IA heurística en ficha de indicador, análisis avanzado con ranking vs. año base.
- **Brecha**: el catálogo de visualizaciones tipo radar/heatmap/gauge/bullet del legacy no tiene presencia confirmada en v2 (que usa principalmente barras horizontales, dona, y barras comparativas superpuestas). Si esos tipos de gráfico estaban realmente en uso en producción (no solo disponibles como librería), representan una posible regresión visual.

### 2.4 Informe por Procesos
- **Streamlit**: módulo de Calidad de Datos (QC) con gauge tipo dona, radar de dimensiones, alertas automáticas por umbral de score (90%/70%).
- **v2**: 6 pestañas incluyendo "Calidad de Datos" y **"Análisis IA"** (heurístico) — v2 añade una pestaña de Auditoría y Propuestas que el legacy no tenía explícitamente como sección propia. **Mejora clara** en cuanto a estructura (más pestañas, más organizado) aunque el radar de dimensiones de calidad no está confirmado en v2.

### 2.5 Plan de Mejoramiento
- Ambos sistemas cubren KPIs CNA por Factor/Característica, cumplimiento, distribución de niveles, y acciones de mejora asociadas. v2 usa barras horizontales + donut; Streamlit usa barras, pastel, barras apiladas Factor×Nivel, y **treemap Factor→Característica** que no está confirmado en v2 — posible brecha visual menor.

### 2.6 Seguimiento Operativo
- **Streamlit**: doble motor de gráficos (Plotly + fallback ECharts), sin límite de filas visible en la tabla de detalle, exportación Excel.
- **v2**: gráfico de barras apiladas Plotly (sin ECharts), exportación Excel, pero **la tabla de detalle trunca a 200 filas en cliente sin paginación real** (`seguimiento-operativo/page.tsx:188`) — regresión funcional frente al legacy si este mostraba el detalle completo.

### 2.7 Gestión OM
- **Streamlit**: formulario simple de asociación de OM (`st.form`), sin edición/cierre posterior, sin roles diferenciados (cualquier usuario autorizado podía usar el formulario).
- **v2**: **CRUD completo** (crear/actualizar/cerrar/eliminar) sobre PostgreSQL, **restringido por rol** (`calidad`/`desempeno`) — mejora clara en control de acceso y en completitud de la gestión del ciclo de vida de una OM. Documentación de v2 (`STATUS.md:36`) señala explícitamente que falta exponer el CRUD completo en la UI (el backend lo soporta, pero el frontend solo mostraría lectura + creación) — **pendiente conocido, no brecha oculta**.

### 2.8 Módulos huérfanos del legacy — decisión pendiente
El **Tablero Operativo Nivel 3** (Kanban, QC de datos, Trazabilidad — 1001 líneas de código funcional) no está enrutado en el menú de Streamlit ni tiene equivalente identificado en v2. Debe confirmarse con el equipo de negocio si:
(a) fue descontinuado intencionalmente antes de la migración (en cuyo caso no es una brecha), o
(b) sigue siendo necesario y quedó fuera del alcance de la migración por omisión.
Dado que consume ~1300 líneas de código en tres archivos y funcionalidad de Kanban no presente en ningún otro módulo de ninguno de los dos sistemas, es el hallazgo de mayor incertidumbre del análisis.

---

## 3. Matriz comparativa de gráficas

| Visualización | Streamlit | SGIND-v2 | Veredicto |
|---|---|---|---|
| Sunburst Línea→Objetivo | `go.Sunburst`, colores institucionales, hovertemplate custom | `SunburstPlotlyChart` (Plotly) | Migrada correctamente |
| Gantt de proyectos PDI | No existe | `ProyectosGanttChart` (Plotly) | **Mejora nueva en v2** |
| Barras por línea/proceso | `px.bar` | `CmiBarLineasPlotly`, `CmiCumplimientoHorizBarPlotly` | Migrada, rediseñada como horizontal con línea de referencia "Meta 100%" |
| Pastel/Donut de niveles | `go.Pie` | `CmiDonutNivelPlotly` (**SVG manual, no Plotly**) | Migrada pero con implementación técnica distinta (posible inconsistencia de estilo/tooltip vs. resto de gráficas Plotly) |
| Barras comparativas vs. año base | No existe explícitamente así | `CmiProcesosBarPlotly` (**CSS/HTML manual**) | **Nueva en v2**, pero no usa librería de gráficos (riesgo de mantenimiento) |
| Heatmap Proceso×Periodo | `heatmap_chart.py` (`px.imshow`) | No confirmado | Posible pérdida — verificar uso real en legacy |
| Radar comparativo | `go.Scatterpolar` | No confirmado | Posible pérdida — verificar uso real en legacy |
| Gauge/Indicator | `go.Indicator`, usado en hero section y QC | No confirmado como componente reutilizable en v2 | Posible pérdida |
| Bullet chart | `go.Bar`+`go.Scatter` | No confirmado | Posible pérdida |
| Treemap Proceso→Subproceso / Factor→Característica | `px.treemap` (CMI Procesos, Plan Mejoramiento) | Treemap solo confirmado en PDI/Acreditación (`pdi-acreditacion/page.tsx`) | Parcial — treemap existe en v2 pero no en los mismos módulos que legacy |
| Histórico de indicador (línea) | `go.Scatter`/`px.line`, combinado con barras Meta/Ejecución | `Recharts LineChart` (ficha), `Plotly line+markers` (análisis avanzado) | Migrada, con doble implementación (Recharts en modal, Plotly en tab de análisis) — inconsistencia de librería dentro de v2 mismo |
| Barras apiladas Estado×Proceso | `px.bar` stacked + fallback ECharts | Plotly `barmode:"stack"` | Migrada, sin fallback ECharts |
| Sparklines de tendencia | `generate_sparkline_counts/agg` (`renderers.py`) | No confirmado | Posible pérdida menor |
| Exportación de imagen de gráfico | No confirmada explícita (solo toolbar nativo de Plotly) | **Deshabilitada explícitamente** (`displayModeBar:false` en todas las Plotly de v2) | v2 es **peor** en este punto: si el legacy dejaba el toolbar de Plotly activo por defecto, el usuario podía descargar PNG; v2 lo bloquea activamente |

**Código muerto en v2** (componentes de gráficos creados pero nunca importados): `SemaphoreChart.tsx`, `TrendChart.tsx`, `SunburstChart.tsx` (Recharts) — sugiere iteraciones de diseño abandonadas, no afecta al usuario pero es deuda de limpieza.

**Inconsistencia de librería en v2**: coexisten Plotly, Recharts y SVG/CSS manual sin wrapper único — genera comportamiento de tooltip/interacción distinto entre gráficas dentro de la misma pantalla (p.ej. donut con `title` HTML nativo junto a barras Plotly con tooltip enriquecido).

---

## 4. Comparativo de indicadores, KPIs y semáforos

| Aspecto | Streamlit | SGIND-v2 |
|---|---|---|
| Umbrales régimen Regular | Peligro <80%, Alerta 80-99%, Cumplimiento 100-104%, Sobrecumplimiento ≥105% (`core/config.py:62-64`) | `UMBRAL_PELIGRO=0.80`, `UMBRAL_ALERTA=1.00`, `UMBRAL_SOBRECUMPLIMIENTO=1.05` (`domain/categorization.py`, `constants.py:5-9`) — **coincide** |
| Umbrales régimen Plan Anual | Peligro <80%, Alerta 80-94%, Cumplimiento 95-100% (techo, sin sobrecumplimiento) | `UMBRAL_ALERTA_PA=0.95`, `UMBRAL_SOBRECUMPLIMIENTO_PA=1.00` — **coincide** |
| Umbrales régimen Negativo-Porcentual (jul-2026) | Peligro >110%, Alerta 102-110%, Cumplimiento <102%; lista curada fija `IDS_NEGATIVO_PCT={"121","207","377","561"}` (`core/config.py`) | `UMBRAL_ALERTA_NEG_PCT=1.02`, `UMBRAL_PELIGRO_NEG_PCT=1.10`, `IDS_NEGATIVO_PCT` (`constants.py`) — **coincide**, ambos puertos actualizados en la misma sesión |
| Función central de categorización | `core/domain/categorization.py::categorizar_cumplimiento(cumplimiento, id_indicador=None)`, única fuente oficial, precedencia Plan Anual > Negativo-Porcentual > Regular | `domain/categorization.py::categorizar_cumplimiento()` — **portada 1:1**, implementación independiente (no importa de `core/`) pero mantenida en sincronía manual |
| **Excepción: PDI/Acreditación** | Sin confirmar si usa la función central | `PDIService._classify_estado` (pdi_service.py:31-41) **reimplementa umbrales en escala de porcentaje entero (75/100/105) en vez de decimal, sin reutilizar `categorizar_cumplimiento`** | **Riesgo real de inconsistencia**, ahora mayor: además de no coincidir 75/100/105 (%) con 0.80/1.00/1.05 (decimal), tampoco contempla el régimen Negativo-Porcentual — si algún indicador PDI/Acreditación cae en `IDS_NEGATIVO_PCT`, se categorizará distinto que en el resto del sistema |
| KPIs de tarjetas/resumen | `st.metric`, `kpi_card` (renderers.py) | `KPICard`, `StrategyCard`, `CmiMetricCard`, `ChipRow` — mayor variedad de componentes visuales |
| Semáforo visual (colores) | `NIVELES_COLORS` centralizado, regla de proyecto explícita de no duplicar (`dashboard_components.py:13-16`) | **3 definiciones distintas** de los mismos colores de nivel en frontend (`CmiResumenTab.tsx`, `nivelUtils.tsx`, `cmiChartColors.ts`) — v2 **retrocede** respecto a la disciplina de "fuente única" que sí tenía el legacy |
| Tendencias (↑↓→) | `_detect_trend` (dashboard_components.py:109) | `trend` prop en `KPICard`, `TrendVariationTables` | Migrado |
| Series históricas | Tabla últimos 10 periodos (modal ficha) | Histórico completo vía `/indicators/{id}` e `/cmi/indicador/{id}` | Equivalente o mejor (backend expone histórico completo, no limitado a 10) |

**Conclusión de esta sección**: la paridad de cifras entre ambos sistemas depende críticamente de que **PDI/Acreditación en v2 use exactamente los mismos umbrales** que el resto — este es el hallazgo de mayor riesgo de "números distintos entre pantallas" detectado en todo el análisis, y debería verificarse con datos reales antes de considerar el módulo equivalente. Con la incorporación del régimen Negativo-Porcentual (jul-2026), este riesgo se amplía: cualquier código que reimplemente umbrales fuera de `categorizar_cumplimiento()` (como `PDIService._classify_estado`) queda automáticamente desactualizado respecto al tercer régimen.

---

## 5. Comparativo de filtros

| Filtro | Streamlit | SGIND-v2 | Observación |
|---|---|---|---|
| Año | Todos los módulos, `segmented_control`/`pills` | Todos los módulos, `YearSegmentedControl` | Equivalente |
| Corte semestral (Jun/Dic) | CMI Estratégico, Plan Mejoramiento | Igual | Equivalente |
| Mes | CMI Procesos, Informe Procesos, Seguimiento, Gestión OM | Igual | Equivalente |
| Unidad → Proceso → Subproceso (cascada) | Cascada completa en CMI Procesos e Informe Procesos | Cascada Proceso→Subproceso confirmada en CMI Procesos; **Informe Procesos no filtra Subproceso dinámicamente** (usa lista completa) | **Regresión en v2**: Informe por Procesos pierde la dependencia cascada que sí tiene en Streamlit y en el propio CMI Procesos de v2 — inconsistencia entre módulos hermanos dentro de v2 |
| Clasificación, Frecuencia | CMI Procesos, Informe Procesos | Igual | Equivalente |
| Línea/Objetivo estratégico | Filtro dedicado en CMI Estratégico legacy (no enrutado) | Filtro de tabla en cliente (no enviado a backend) | Cambia de filtro server-side a client-side; funcionalmente similar pero no escalará igual con datasets grandes |
| Factor/Característica CNA (cascada) | Sí | Sí, con mismo comportamiento de reseteo | Equivalente |
| Estado/Macrolínea/Horizonte (PDI) | Sí (módulo huérfano) | Sí | Equivalente |
| **Persistencia de filtros en URL** | No confirmada explícitamente (pero sí hay deep-link `?cmi_linea=` a nivel de navegación general) | Solo `?cmi_linea=` en CMI Estratégico; **el resto de filtros (año, mes, proceso, etc.) se pierden al recargar o compartir enlace** | v2 no mejora este punto respecto al legacy; ambos son débiles aquí, oportunidad de mejora compartida |
| Rendimiento de filtrado | Sobre DataFrame en memoria de proceso Streamlit (por sesión) | Sobre DataFrame cacheado con TTL en backend (compartido entre usuarios, no por sesión) | v2 es potencialmente más eficiente (caché compartida) pero también más sensible a invalidación cruzada en despliegues multi-worker |

---

## 6. Comparativo visual (UX/UI)

| Criterio | Streamlit | SGIND-v2 |
|---|---|---|
| Identidad institucional | CSS custom inyectado, paleta y colores por línea estratégica definidos (`LINEA_COLORS`) | `design-tokens.ts` centralizado (colores marca Poli, semáforo, paleta líneas, tema Plotly) — mejor intención de sistema de diseño, aunque no todos los componentes lo usan consistentemente (ver duplicación de colores en §4) |
| Navegación | Sidebar de Streamlit nativo, con separador visual entre grupos de módulos | `Sidebar.tsx` con `NAV_ITEMS`/`BETA_ITEMS`, etiqueta visual "Beta" para módulos en evaluación (PDI, Diagnóstico) — más claro sobre qué está en producción vs. en prueba |
| Componentización | Reutilización vía funciones Python en `components/` (no componentes de UI verdaderos, son funciones que renderizan) | Componentes React reutilizables reales (`KPICard`, `NivelBadge`, etc.) — arquitectura de UI más madura y mantenible |
| Responsive | Limitado por el motor de Streamlit (adaptación automática básica) | Tailwind + `useResizeHandler`/`responsive:true` en gráficos Plotly — control más fino, pero no verificado en dispositivo real (sin prueba en navegador) |
| Accesibilidad | No evaluada en el código (Streamlit tiene soporte base limitado) | No evaluada explícitamente en el código explorado; recomendación: auditar contraste de badges de semáforo y navegación por teclado |
| Consistencia visual | Alta dentro de cada módulo (mismo framework, mismo sistema de colores centralizado) | Media — mezcla de 3 librerías de gráficos y 3 definiciones de colores de nivel reduce la consistencia lograda por el design-tokens central |

**Nota metodológica**: esta sección se basa en análisis de código, no en captura de pantalla ni prueba interactiva en navegador — se recomienda una validación visual real (screenshots lado a lado) antes de dar por cerrada la comparación de UX/UI, ya que el código no revela con precisión espaciados, tipografía renderizada ni fluidez percibida.

---

## 7. Experiencia de usuario (UX) — calificación estimada (1-5)

*Calificación basada en evidencia de código; requiere validación con usuarios reales para ser definitiva.*

| Criterio | Streamlit | SGIND-v2 | Justificación |
|---|---|---|---|
| Flujo de navegación | 3 | 4 | v2 tiene rutas URL reales navegables/compartibles (excepto filtros); Streamlit depende de `session_state` y reruns completos de página |
| Cantidad de clics para tareas comunes | 3 | 3 | Similar número de pasos; v2 pierde puntos por no persistir filtros (hay que re-filtrar tras recargar) |
| Claridad de la información | 4 | 4 | Ambos usan semáforos, badges y KPIs de forma clara; empate |
| Organización del contenido | 3 | 4 | v2 organiza mejor con pestañas + componentes separados; Streamlit tiene archivos de página gigantes que sugieren UI menos modular |
| Velocidad de acceso / carga | No medida (requiere prueba real) | No medida (requiere prueba real) | **No se puede calificar sin ejecutar ambas apps** — recomendación explícita: medir con herramientas de performance reales |
| Curva de aprendizaje | 4 (interfaz Streamlit muy estándar) | 4 (interfaz web convencional) | Empate, ambas son interfaces de dashboard convencionales |

---

## 8. Rendimiento

**No se pudo evaluar con evidencia empírica** (no se ejecutaron ambas aplicaciones ni se hicieron mediciones de tiempo de carga/memoria). Observaciones basadas en arquitectura:

- **Streamlit**: cachea DataFrames por sesión de usuario (`@st.cache_data`), recarga completa de script en cada interacción (patrón "rerun"), consumo de memoria por sesión activa.
- **SGIND-v2**: cachea DataFrames en memoria de proceso backend con TTL (300s default), compartido entre todos los usuarios — más eficiente en agregado, pero cada worker Uvicorn mantiene su propia copia de caché (sin invalidación cruzada en despliegue multi-worker), y **ningún sistema tiene ETL hacia una base de datos analítica** — ambos recalculan sobre Excel en cada ciclo de refresco de caché, por lo que el cuello de botella estructural (lectura de Excel) persiste en la migración.
- **Recomendación**: ejecutar ambas apps con el mismo dataset y medir tiempo de primera carga, tiempo de cambio de filtro, y uso de memoria en reposo antes de concluir sobre rendimiento.

---

## 9-10. Arquitectura y calidad del código

| Aspecto | Streamlit | SGIND-v2 |
|---|---|---|
| Organización de capas | Páginas (`pages/`) → componentes (`components/`) → servicios (`services/`) → núcleo de dominio (`core/`) — capas presentes pero páginas muy grandes (hasta 4207 líneas) | Routers (`api/v1/endpoints`) → servicios (`services/`) → dominio puro (`domain/`) → I/O Excel/DB — separación más limpia en el backend, pero módulos de dominio igual de grandes (hasta 1072 líneas) |
| Frontend/presentación | Funciones Python que renderizan Streamlit widgets — no hay componentes de UI verdaderamente reutilizables/testeables de forma aislada | Componentes React con props tipadas, testeables — mejora arquitectónica real |
| Modularidad | Media — mucha lógica de negocio y presentación mezclada dentro de archivos de página | Alta en frontend (buena separación de componentes); media en backend (domain builders extensos) |
| Duplicación de lógica | Baja en el núcleo de cumplimiento (centralizado en `core/domain/categorization.py`, con regla de proyecto explícita anti-duplicación) | Media — 3 definiciones de colores de semáforo en frontend, umbrales PDI reimplementados fuera del módulo central, filtro "Todos" repetido en ~10 builders sin helper compartido |
| Contratos de API | N/A (monolito, no hay API separada) | **Débil**: la mayoría de endpoints de negocio (PDI, plan-mejoramiento, informe, seguimiento, fichas CMI) devuelven `dict` sin `response_model` Pydantic — frontend y backend acoplados por convención, no por schema validado |
| Tests | No se relevó cobertura de tests del legacy en este análisis | 21 archivos de test backend (~2554 líneas) organizados por fase de migración + tests E2E Playwright en frontend — **mejor cobertura documentada** que el legacy |
| Documentación de arquitectura | No hay ADRs ni documentos de arquitectura formal identificados | 8 ADRs, matriz RBAC, runbooks de cutover — **mucho mejor documentado**, aunque con inconsistencias entre documentos (ver §11) |
| Deuda técnica dejada en producción | Artefactos de diagnóstico escritos a disco en cada carga de Resumen General (`artifacts/*.xlsx`), instrumentación de debug no removida | Formato de archivo irregular en `dashboard.py` (líneas dobles, sugiere generación automática sin `black`/`ruff`), modelo `Accion` definido sin uso | Ambos tienen señales de "trabajo en progreso" dejado en el código |

---

## 11. Funcionalidades faltantes (priorizadas)

| Funcionalidad | Prioridad | Impacto |
|---|---|---|
| Confirmar destino de **Tablero Operativo Nivel 3** (Kanban, QC, Trazabilidad) | **Crítica** | Si estaba en uso real por el equipo operativo, su ausencia en v2 es una pérdida funcional mayor no documentada como decisión consciente |
| **Análisis con IA generativa real** (Claude) en fichas CMI Estratégico y por Procesos | **Alta** | El legacy ofrece narrativa generada por LLM real; v2 solo tiene heurísticas de reglas — degradación de una funcionalidad diferenciadora visible al usuario final |
| **Exportación PDF de ficha individual de indicador** | **Alta** | Presente en legacy (modal de ficha CMI Estratégico), no confirmada en v2 (solo hay PDF de reporte completo por módulo) |
| **Verificar umbrales PDI/Acreditación** (`PDIService._classify_estado` vs. `categorizar_cumplimiento`) | **Alta** | Riesgo de que el mismo indicador muestre semáforo distinto entre módulos — riesgo de confianza en los datos |
| **Cascada Subproceso dependiente de Proceso en Informe por Procesos (v2)** | **Media** | Inconsistencia entre módulos hermanos dentro del propio v2, y regresión frente al comportamiento del legacy |
| **Paginación real en Seguimiento Operativo (v2)** (actualmente trunca a 200 filas en cliente) | **Media** | Pérdida de visibilidad de datos si el dataset supera 200 filas |
| Gráficas tipo heatmap, radar, gauge, bullet chart (catálogo `heatmap_chart.py` del legacy) | **Media** | Depende de si estaban realmente en uso en producción — requiere confirmación |
| Treemap Factor→Característica (Plan de Mejoramiento) | **Baja** | Visualización secundaria, no crítica para la toma de decisiones |
| Sparklines de tendencia en tarjetas | **Baja** | Detalle visual menor |
| Motor de respaldo ECharts (Seguimiento Operativo) | **Baja** | Redundancia técnica del legacy, no necesariamente deseable de replicar |
| Persistencia de filtros en URL (todos los módulos salvo `cmi_linea`) | **Media** | Afecta a ambos sistemas por igual — no es una regresión de v2, pero sí una oportunidad de mejora conjunta |
| Panel de administración de usuarios/roles | **Media** | No existe en ninguno de los dos — v2 tiene mejor base (RBAC real en BD) para construirlo a futuro |

---

## 12. Mejoras implementadas en SGIND-v2

| Mejora | Qué cambió | Beneficio |
|---|---|---|
| RBAC real (3 roles: procesos/calidad/desempeno) vía JWT + Azure AD OIDC | Reemplaza whitelist plana de correos sin diferenciación de roles | Control de acceso granular; solo `calidad`/`desempeno` pueden mutar OM |
| CRUD completo de Gestión OM sobre PostgreSQL | Legacy solo tenía formulario de creación simple sin actualización/cierre/eliminación estructurados | Ciclo de vida completo de una Oportunidad de Mejora gestionable desde la app |
| Exportación PDF de reportes completos (Resumen General, Informe por Procesos) | El legacy solo exportaba PDF de una ficha individual | Reportes ejecutivos completos descargables, no existentes en el legacy |
| Arquitectura de componentes React reutilizables y tipados | Reemplaza funciones Python de renderizado ad-hoc | Mayor mantenibilidad y testabilidad del frontend |
| Tests E2E con Playwright + 21 archivos de test backend por fase | No se identificó suite de tests equivalente en el legacy | Mayor confianza en no-regresión durante desarrollo futuro |
| Documentación de arquitectura (8 ADRs, matriz RBAC, runbook de cutover) | El legacy no tenía documentación de arquitectura formal | Facilita onboarding y decisiones futuras (aunque con inconsistencias a corregir, §11 de hallazgos backend) |
| Gantt de proyectos PDI (Resumen General) | No existía en el legacy | Nueva capacidad de visualización de vigencia de proyectos institucionales |
| Módulo "Diagnóstico" de autochequeo de sistema (Beta) | El legacy tenía un diagnóstico de despliegue técnico distinto (imports/sys.path), no de salud de API/datos | Mejor observabilidad operativa para el equipo técnico |

---

## 13. Oportunidades de mejora (no presentes en ninguno de los dos sistemas)

- **IA generativa real aplicada de forma consistente**: unificar y potenciar el uso de Claude (ya probado en el legacy) en v2 para narrativas, detección de anomalías y recomendaciones — actualmente v2 solo tiene heurísticas etiquetadas engañosamente como "IA".
- **Predicciones y análisis de tendencia**: proyección de cumplimiento futuro por indicador (ninguno de los dos sistemas lo tiene, aunque el repo raíz sí tiene `scripts/analytics/predictor.py` — verificar si es reutilizable).
- **Alertas proactivas** (notificaciones push/email cuando un indicador cruza a Peligro), no presente en ningún sistema.
- **Comparativos históricos multi-año** más allá de año-contra-año (YoY) — series de 3-5 años con tendencia.
- **Benchmarking externo** (comparación contra otras instituciones), mencionado como campo en PDI/Acreditación pero sin fuente de datos externa confirmada.
- **Simulación de metas** ("¿qué pasaría si la meta fuera X?") — no existe en ninguno.
- **Panel de administración de catálogos** (procesos, líneas, indicadores) desde la UI — actualmente ambos requieren editar Excel fuera de la aplicación.
- **ETL hacia base de datos analítica real**, eliminando la dependencia de lectura de Excel en cada request/sesión — mejora estructural compartida pendiente en ambos sistemas.

---

## 14. Backlog priorizado para completar la migración

| # | Ítem | Prioridad | Complejidad | Riesgo | Recomendación |
|---|---|---|---|---|---|
| 1 | Confirmar con negocio el destino del Tablero Operativo Nivel 3 (Kanban/QC/Trazabilidad) | Crítica | — (decisión, no desarrollo) | Alto si se descubre tarde que era necesario | Reunión de validación de alcance antes de cutover |
| 2 | Verificar y unificar umbrales de PDI/Acreditación con `categorizar_cumplimiento` central | Alta | Baja | Alto (inconsistencia de cifras visibles al usuario) | Refactor de `PDIService._classify_estado` para reutilizar la función central |
| 3 | Decidir si se replica el análisis IA real (Claude) en v2 o se documenta como decisión de producto | Alta | Media | Medio (percepción de regresión funcional) | Si es valorado por usuarios, portar `services/ai_analysis.py` del legacy al backend v2 |
| 4 | Corregir cascada Subproceso en Informe por Procesos (v2) para que dependa de Proceso, igual que en CMI Procesos | Media | Baja | Bajo | Ajuste de frontend, reutilizar patrón ya existente en `cmi-procesos/page.tsx` |
| 5 | Implementar paginación real en tabla de Seguimiento Operativo (v2) | Media | Baja-Media | Medio si el dataset crece | Paginación server-side vía backend, igual que en `indicators` |
| 6 | Unificar librería de gráficos en v2 (elegir Plotly como estándar y migrar el donut SVG y las barras CSS manuales) | Media | Media | Bajo | Reduce deuda visual y de mantenimiento a mediano plazo |
| 7 | Unificar definición de colores de nivel de semáforo en frontend v2 (una sola fuente, hoy hay 3) | Media | Baja | Medio (drift visual entre módulos) | Consolidar en `design-tokens.ts` y eliminar duplicados |
| 8 | Añadir `response_model` Pydantic a endpoints de negocio que hoy devuelven `dict` sin tipar | Media | Media | Medio (contratos frágiles frente a cambios de frontend) | Definir schemas para PDI, plan-mejoramiento, informe, seguimiento, fichas |
| 9 | Exportación PDF de ficha individual de indicador en v2 | Media | Baja-Media | Bajo | Reutilizar `pdf_service.py` existente, extender a nivel de ficha |
| 10 | Actualizar documentación de fases (`docs/phase-4/README.md`, `RBAC_MATRIX.md`) para reflejar el estado real del código | Baja | Baja | Bajo (solo confusión interna) | Sesión de limpieza documental antes del cutover |
| 11 | Completar sesiones de UAT reales y registrar bugs en `UAT_BUGS.md` (actualmente solo tiene la plantilla de ejemplo) | Alta | — (proceso, no desarrollo) | Alto (cutover sin validación de usuarios reales) | Ejecutar el plan ya documentado en `CUTOVER_RUNBOOK.md` antes de apagar el legacy |
| 12 | Validación visual real (screenshots side-by-side) de ambos sistemas | Alta | Baja | Medio (esta comparación se basó solo en código) | Complementar este informe con capturas de pantalla y prueba interactiva |

---

## 15. Conclusión — equivalencia funcional estimada

| Alcance considerado | % de equivalencia estimado |
|---|---|
| Solo los 7 módulos activos del menú Streamlit | **~85-90%** |
| Incluyendo los módulos huérfanos (Tablero Operativo N3, Acreditación N2) | **~65-70%** |
| Ponderado por criticidad de negocio (asumiendo que Tablero Operativo N3 es de uso real) | **~70-75%** |

**No se alcanza el 100% de equivalencia funcional** principalmente por: (1) el estado no confirmado del Tablero Operativo Nivel 3, (2) la ausencia de IA generativa real en las narrativas de v2, y (3) brechas puntuales de exportación PDF por ficha. Ninguna de estas tres es, sin embargo, un bloqueante estructural: son ítems acotados y accionables (ver backlog, §14).

**Limitación explícita de este informe**: todo el análisis se hizo por revisión de código estático, sin ejecutar ninguna de las dos aplicaciones en navegador ni comparar datos calculados en vivo. Antes de dar por cerrada la migración se recomienda: (a) ejecutar ambos sistemas con el mismo Excel de origen y comparar cifras de cumplimiento indicador por indicador, especialmente en PDI/Acreditación (§4), y (b) una sesión de UAT real con los usuarios finales del sistema legacy, tal como ya está planificado en `docs/migration/CUTOVER_RUNBOOK.md` pero pendiente de ejecución según `UAT_BUGS.md`.
