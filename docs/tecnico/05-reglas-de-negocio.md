# Inventario de reglas de negocio

> **Actualización Oleada 2 (2026-09-20):** las reglas RN-03 a RN-07 y
> RN-13/RN-14/RN-15 (semaforización duplicada) quedaron **consolidadas**.
> Ver el detalle en la tabla de abajo y en
> [`09-gaps-y-riesgos.md`](09-gaps-y-riesgos.md) (G-03). Paleta oficial
> confirmada con negocio: Peligro `#D32F2F`, Alerta `#f59e0b`, Cumplimiento
> `#22c55e`, Sobrecumplimiento `#3b82f6` (fuente única:
> `backend/app/domain/constants.py::COLOR_CATEGORIA` y
> `frontend/src/lib/design-tokens.ts::SEMAFORO`, que deben coincidir
> exactamente). `categorizar_cumplimiento()` ahora acepta un parámetro
> `regimen` explícito ("plan_anual"/"negativo_pct") para clasificar por
> **tipo** de entidad (Retos, Proyectos) en vez de solo por pertenencia a
> una lista de Id — confirmado con negocio que Retos y Proyectos usan
> Plan Anual (95/100) incondicionalmente.

> **Alcance de este inventario — léase antes de usarlo.** Cubre el motor de
> semaforización/cumplimiento (RN-01 a RN-07, RN-13 a RN-15) y las reglas
> propias de Plan de Mejoramiento ya identificadas (RN-08, RN-09, RN-16,
> RN-17). **No es exhaustivo**: el pipeline real de producción de datos
> (`scripts/etl/`, ~15 pasos en `actualizar_consolidado.py` — correcciones
> AGENT5 sobre Ejecución>1.3, gates de validación de entrada/salida, purga
> de filas inválidas, reparación de metas/signos/multiserie, expansión de
> series como subindicadores) codifica más reglas de negocio que aún no se
> extrajeron a nivel de archivo:función individual — solo se documentan por
> nombre en [`06-flujos-end-to-end.md`](06-flujos-end-to-end.md). Completar
> esa extracción requiere una pasada dedicada sobre `scripts/etl/*.py`.

## Indicador vs. Métrica — son conceptos distintos, no sinónimos

Antes de leer la tabla: el sistema maneja **dos entidades de negocio
diferentes** que las reglas siguientes no calculan de la misma forma.

| | **Indicador** | **Métrica** |
|---|---|---|
| Fuente de datos | `Resultados Consolidados.xlsx` (dashboard general) o fila con `Tipo="Indicador"` en `Indicadores Plan de Mejoramiento.xlsx` (Plan de Mejoramiento) | `Resultados_Consolidados_CNA.xlsx`, hoja "Metricas" — **fuente completamente independiente**, sin cruce a nivel de indicador (`docs/metodologia_plan_cna.md`) |
| Qué se calcula | Cumplimiento (`Ejecución/Meta`) + categoría de semáforo (RN-03/RN-04/RN-05/RN-06/RN-07) | Tendencia histórica por variación interanual (RN-08) — **no tiene semáforo de cumplimiento** |
| Identificador | `Id` | `Indicador` + `Subindicador` (puede tener desglose, ej. "Presencial - Universitario") |
| Estado propio (solo dentro de Plan de Mejoramiento) | Activo / Aprobado / Pendiente (RN-16) | No aplica — las métricas no tienen este estado |
| Dónde se ve | Resumen General, CMI Estratégico/Procesos, Informe, Seguimiento, pestaña "Indicadores" de Plan de Mejoramiento | Solo la pestaña "Métricas" de Plan de Mejoramiento |

**Consecuencia práctica:** preguntar "¿cómo se calcula el color de este
indicador?" no tiene la misma respuesta que "¿cómo se calcula la tendencia
de esta métrica?" — son dos reglas distintas sobre dos fuentes de datos
distintas, aunque ambas aparezcan en la misma pantalla de Plan de
Mejoramiento.

### Fuera de Plan de Mejoramiento también hay ítems sin meta — pero sin clasificar como "Métrica"

En **CMI por Procesos** e **Informe por Procesos** (`domain/procesos_builders.py`)
no existe ningún campo `Tipo`/`Clasificacion` que distinga "Indicador" de
"Métrica" — es una clasificación formal exclusiva de Plan de Mejoramiento
(confirmado: la cadena `"Metrica"` como valor de `Tipo` solo aparece en
`backend/app/services/plan_mejoramiento_service.py:130,174`, en ningún
archivo de `procesos_builders.py`/`cmi_builders.py`).

Sin embargo, **sí existen ítems sin meta real** en esas pantallas: cuando
`Meta` es `0` o `NULL` (y el sentido no es "Negativo", donde `Meta=0` es
legítimo), `domain/health_metrics.py::recalcular_cumplimiento_faltante`
devuelve `NaN` y el ítem se muestra como **"Sin dato"** (gris) —
exactamente el mismo color que usa el sistema para un dato que sí tiene
meta pero que nadie reportó todavía. `scripts/etl/agent5_corrections.py`
(líneas 73-85) señala estos casos como "Meta = 0/NULL, requiere revisión
manual" durante el pipeline, pero esa señal no llega al frontend — el
usuario final ve "Sin dato" sin poder distinguir "esto es una métrica de
seguimiento sin meta por diseño" de "falta capturar la ejecución de este
indicador". Ver gap G-19 en
[`09-gaps-y-riesgos.md`](09-gaps-y-riesgos.md).

| ID | Regla | Ubicación (archivo:función) | Entrada | Salida | Duplicada |
|---|---|---|---|---|---|
| RN-01 | Normalización de cumplimiento (string %, coma decimal, escala 0-100→0-1) | `domain/calculos.py::normalizar_cumplimiento` (16-44) | valor crudo | float [0.0, 1.3] o NaN | No |
| RN-02 | Recálculo de cumplimiento faltante (Ejecución/Meta según sentido) | `domain/health_metrics.py::recalcular_cumplimiento_faltante` (13-63) | meta, ejecución, sentido, id | float acotado a 1.0 o 1.3 | No |
| RN-03 | Categorización canónica de cumplimiento (semáforo), con parámetro `regimen` explícito desde Oleada 2 | `domain/categorization.py::categorizar_cumplimiento` (ampliada) | cumplimiento decimal, id, regimen opcional | Peligro/Alerta/Cumplimiento/Sobrecumplimiento/Sin dato | No — única fuente, ver corrección abajo |
| RN-04 | ~~Semaforización de procesos (2 niveles, sin variantes)~~ **Corregido en Oleada 2** — ahora delega a RN-03 | `domain/procesos_builders.py::cumplimiento_semaforo_color`/`cumplimiento_estado` | valor % | color/label (vocabulario canónico) | Ya no duplica |
| RN-05 | ~~Estado de línea para cards (2 niveles)~~ **Corregido en Oleada 2** — el corte de categoría delega a RN-03, se conserva el estilo rico (bg/text) por categoría | `domain/cmi_builders.py::_estado_linea_card` | cumplimiento %, tiene_datos | dict label/color/bg/text | Ya no duplica |
| RN-06 | ~~Estado de línea (3 niveles, cortes distintos)~~ **Corregido en Oleada 2** — ahora delega a RN-03 (100/105 general, ya no 95/100 de Plan Anual aplicado a todas las líneas) | `domain/cmi_builders.py::_estado_linea` | cumplimiento % | (label, color) | Ya no duplica |
| RN-07 | ~~Narrativa heurística por línea~~ **Corregido en Oleada 2** — el corte de categoría delega a RN-03 | `domain/cmi_builders.py::generate_linea_narrativa_heuristica` | cumplimiento promedio, riesgo | texto/color/icon | Ya no duplica |
| RN-18 | ~~Categoría de subindicadores de Retos (régimen general hardcodeado)~~ **Corregido en Oleada 2** — ahora delega a RN-03 con `regimen="plan_anual"` forzado, confirmado con negocio | `domain/resumen_builders.py::_retos_category` | pct | Peligro/Alerta/Cumplimiento/Sobrecumplimiento/Sin dato | Ya no duplica |
| RN-19 | ~~Paleta de colores propia en Gestión OM~~ **Corregido en Oleada 2** — `CATEGORIA_COLORS` es ahora un alias directo de RN-03's `COLOR_CATEGORIA` | `domain/om_builders.py::CATEGORIA_COLORS` | categoría (string) | color hex | Ya no duplica |
| RN-08 | Clasificación de tendencia histórica (variación interanual) | `domain/plan_mejoramiento_builders.py::_classify_tendencia_historico` (986-996) | variación % promedio, n años con dato | Creciente/Decreciente/Estable/Sin suficiente historia | No |
| RN-09 | Detección de escala porcentual (fracción vs. 0-100) | `domain/plan_mejoramiento_builders.py::_detecta_escala_pct` (999-1007) | signo, lista de valores | bool | No |
| RN-10 | Cierre de OM | `services/om_service.py::OMService.cerrar` (65-77) | registro_id, comentario | RegistroOM actualizado (`tiene_om=0`) | No |
| RN-11 | Cálculo de KPIs agregados | `domain/calculos.py::calcular_kpis` (64-79) | DataFrame con Cumplimiento_norm/Categoria | (total, conteos/%) | No |
| RN-12 | Derivación de Periodo/Mes/Año faltantes | `services/etl_pipeline.py::fase4_fechas` (141-169) | DataFrame con Fecha | DataFrame con Anio/Mes/Periodo completos | No |
| RN-13 (frontend) | Fallback de clasificación de semáforo (solo si el backend no envía `nivel`) — **se conserva deliberadamente** como respaldo, ya no es la fuente de color (esa es RN-20) | `frontend/src/components/cmi/CmiProcesosResumenTab.tsx::nivelKeyFallback` | pct | nivel | Fallback defensivo, no divergencia activa (backend ya envía `nivel` siempre que hay `cumplimiento_pct`) |
| RN-14 | ~~Formateo de % asumiendo fracción 0-1~~ **Eliminado en Oleada 1** junto con `IndicatorsTable.tsx` (código muerto con este bug) | — | — | — | Eliminado |
| RN-15 (frontend) | Formateo de % asumiendo escala 0-100 | `frontend/src/components/cmi/nivelUtils.tsx::fmtPct` | valor | "%" | Único ahora que RN-14 se eliminó |
| RN-20 (frontend) | ~~3 copias de paleta de color~~ **Corregido en Oleada 2** — `cmiChartColors.ts`, `CmiVistaRapidaCards.tsx` y `CmiProcesosResumenTab.tsx` ahora importan de `design-tokens.ts::SEMAFORO` (solares) y `nivelUtils.tsx::NIVEL_STYLES` (tonos muted de badge/leyenda) en vez de definir sus propios hex | `frontend/src/lib/design-tokens.ts`, `frontend/src/components/cmi/nivelUtils.tsx` | — | — | Ya no duplica |
| RN-16 | Estado del Indicador dentro de Plan de Mejoramiento (distinto del semáforo de cumplimiento) | `domain/plan_mejoramiento_builders.py::classify_plan_indicador_estado` (526-544) | Estado_Aprobacion, Tipo, medición 2025/2026 | Activo (aprobado + Tipo=Indicador + con medición) / Aprobado (aprobado sin medición) / Pendiente | No — solo aplica a filas de Plan de Mejoramiento, no al indicador general del dashboard |
| RN-17 | Exclusión de "subtotal fantasma" en desglose de Métricas | `domain/plan_mejoramiento_builders.py::_excluye_subtotal_fantasma` (1010-1028) | filas de una Métrica con y sin `Subindicador` | filas sin el subtotal duplicado | No — corrige un caso real de doble conteo detectado en "Matrícula de estudiantes" (5.881 vs. 58.398 real, 2026-09-18) |

## RN-21 · Arrastre del último dato anual: solo en Indicadores POLISIGS

**Regla aparte (confirmada con negocio, 2026-10-08).** Cuando un indicador de
periodicidad anual todavía no tiene reporte en el año en curso (p. ej. Great
Place to Work o «Programas acreditables acreditados Sede Bogotá» en 2026), la
única sección que muestra el último dato anual disponible (p. ej. diciembre
2025) es **Indicadores POLISIGS**. En todas las demás secciones el indicador
se muestra como **«Pendiente de medición»**, sin meta ni ejecución, y nunca con
cifras de un año anterior.

| Sección | Indicador anual sin reporte del año | Dónde se implementa |
|---|---|---|
| Indicadores POLISIGS | Muestra el último dato anual, rotulando el corte real («Diciembre 2025») | `services/polisigs_service.py::_ultimo_fallback_anual` |
| CMI Estratégico (PDI con hoja propia, p. ej. 2026-2030) | «Pendiente de medición» (nivel interno `Pendiente de reporte`); la ficha solo trae histórico de los años del ciclo | `domain/strategic_processors.py::preparar_pdi_marco_con_cierre`, `services/cmi_service.py::get_indicador_ficha` |
| CMI por Procesos (PDI con hoja propia) | Solo ofrece los años del ciclo del PDI | `services/cmi_service.py::get_procesos_filtros` |
| Resto de secciones | No arrastran datos de otro año | — |

Consecuencias de diseño:
- El CMI Estratégico del 2026-2030 solo mide dentro de su ciclo (`Marco.incluye_anio`); los años 2022-2025 se consultan en POLISIGS o en el PDI 2022-2026.
- El filtro general **«Mostrar solo indicadores con reporte»** (CMI Estratégico) oculta los pendientes de medición y recalcula KPIs y gráficas sin ellos (`solo_con_reporte` en `/cmi/estrategico-dashboard`).
- Si se agrega otra sección que deba arrastrar el dato anual, esta regla se debe ampliar de forma explícita; por defecto **no** aplica.

## Reglas del ciclo N-PDI y del catálogo (octubre 2026)

Reglas de negocio confirmadas durante la incorporación del PDI 2026-2030. El diseño
y las decisiones abiertas están en [`impact_report.md`](../../impact_report.md);
aquí queda lo que el sistema **aplica**.

| Id | Regla | Implementada en | Notas |
|---|---|---|---|
| RN-22 | **Coexistencia de PDI.** Cada PDI es un marco versionado en `marcos.toml` (años de datos, módulos habilitados, taxonomía, hoja de cierre). Los dos PDI se mantienen: 2022-2026 (cerrado, consultable) y 2026-2030 (activo). **2026 pertenece solo al 2026-2030**; el 2022-2026 cierra con datos 2022-2025. El Id de un indicador **no cambia** entre PDI: solo cambia su asociación. | `backend/app/data/marcos.toml`, `domain/marcos.py` | Sin `?pdi` se sirve el PDI que atiende todos los módulos (hoy 2022-2026), nunca el 2026-2030 por omisión. |
| RN-23 | **Qué responde la API según el PDI.** `?pdi` inexistente → 404; no es un PDI → 422; sin datos cargados → 409; módulo no habilitado para ese PDI → 409 (hoy el Resumen General del 2026-2030). Nunca se sirven datos de otro ciclo en su lugar; las cachés y las claves del frontend incluyen el PDI. | `api/pdi_deps.py` (`get_pdi_marco`, `pdi_para`) | El selector de PDI se pide siempre al entrar a Resumen, CMI Estratégico y CMI por Procesos, con chip para cambiar. |
| RN-24 | **Una hoja por PDI en el catálogo** (`PDI_2022_2026`, `PDI_2026_2030`). Columnas: contexto del indicador + `PDI` + `Linea` + `Objetivo` + `Meta` + `Observaciones`. Línea, objetivo y meta se eligen **por nombre** con desplegables en cascada (`Listas_PDI_*`), no por códigos. La hoja 2022-2026 es una migración congelada; la del 2026-2030 la diligencia Planeación y los scripts solo agregan lo que falta. | `scripts/agregar_hojas_marco_catalogo.py`, `domain/taxonomia.py::resolver_asociaciones` | Los errores de asociación (texto que no existe en la taxonomía) se reportan con su fila; no se ignoran en silencio. |
| RN-25 | **Marcador `PDI` y regla de meta estratégica.** `PDI = 1` indicador estratégico del PDI: **debe** tener meta estratégica. `PDI = 0` indicador de proceso: **no puede** tenerla. **Vacío = 0** (los indicadores nuevos entran con 0). El incumplimiento se reporta pero **no descarta la fila**. | `domain/taxonomia.py::regla_meta`, `services/strategic_loaders.py::load_indicadores_pdi` | El CMI Estratégico de un PDI con hoja propia solo incluye `PDI = 1`. |
| RN-26 | **Taxonomía oficial por PDI.** Las líneas, objetivos y metas salen del Excel oficial (`data/raw/PDI_2026-2030_Lineas_Objetivos_Metas.xlsx`: 4 líneas, 10 objetivos, 22 metas, textos sin parafrasear). Los ids son los códigos del Excel (`L1`, `L1-OI`, `L1-OI-M1`). | `scripts/importar_taxonomia_pdi.py`, `backend/app/data/taxonomia/*.json` | Al reimportar, lo ya elegido en el catálogo se migra al texto oficial por posición; lo que no se pueda emparejar se informa sin modificarlo. |
| RN-27 | **Proyectos.** Los proyectos del ciclo anterior (PRY ≤ 44) cuyo estado PMO **no** sea Cerrado/Finalizado continúan en el 2026-2030 con el mismo Id (los «Stand by» se consideran abiertos). Los PRY posteriores al 44 son del ciclo nuevo. | `scripts/agregar_hojas_marco_catalogo.py::candidatos_vigente` | Abierto: si el avance de un proyecto que continúa es acumulado o reinicia en 2026. |
| RN-28 | **Indicadores nuevos y «activo».** Un indicador es nuevo si está en el año más reciente de Kawak o en la API y no en el catálogo. «Activo» = Estado `Activo` **o** vigente en Kawak/API (el Estado vacío no lo excluye). Solo los activos se asocian al PDI vigente; los nuevos entran con `PDI = 0` y la línea/objetivo se **solicita** (en terminal) o queda pendiente con `[AVISO]` (en el pipeline). Los vacíos del catálogo se completan desde Kawak/API **sin pisar** valores existentes. | `scripts/sincronizar_directorio_indicadores.py` | Paso del pipeline entre `consolidar_api` y `actualizar_directorio_maestro`. |
| RN-29 | **Asociación preliminar.** La línea y el objetivo propuestos por contenido (nombre, descripción, proceso) son una **propuesta** para revisión: solo llenan celdas vacías, no tocan `PDI` ni `Meta` y marcan la fila en Observaciones. | `scripts/asociar_preliminar_pdi.py` | La decisión final es de Planeación. |
| RN-30 | **CMI por Procesos.** Los filtros muestran las líneas del PDI elegido y los años de su ciclo. La **ficha** del indicador muestra la línea de cada PDI cuya vigencia cruza la del indicador según su fecha de inicio (iniciado en 2023: ambos PDI; iniciado en 2027: solo el vigente). | `services/cmi_service.py::get_procesos_filtros`, `domain/asociaciones.py::asociaciones_ficha` | Faltan fechas de inicio en algunos indicadores (p. ej. 526, 543, 544, 551). |
| RN-31 | **Años y cierre por PDI.** El PDI 2022-2026 ofrece 2022-2025 y su botón «Cierre PDI 2022-2025» (medición consolidada al cierre). El 2026-2030 ofrece solo 2026 y no muestra botón de cierre hasta que exista su hoja «Cierre PDI 2026-2030». Un PDI no muestra mensajes de «sin información» de otro ciclo. | `services/cmi_service.py::get_filtros`, `Marco.etiqueta_cierre` | Ver también RN-21 (pendiente de medición y filtro «solo con reporte»). |
| RN-32 | **ETL: la hoja Variables es obligatoria.** Si hay indicadores con extracción «Desglose Variables» y el mapa de Variables/Campo está vacío, el ETL **se detiene** en lugar de escribir el consolidado (sin ella, ~88 indicadores quedaban con Meta/Ejecución = 100). Todo cambio del ETL se prueba primero en un sandbox. | `scripts/actualizar_consolidado.py`, `scripts/etl/catalogo.py::_leer_variables_campo` | Incidente documentado; ver memoria del proyecto. |
| RN-33 | **ETL: indicadores que suman variables de series.** Meta y Ejecución del 274 (matrículas) y del 203 (ingresos) se calculan sumando variables de sus series (TEMS/TEP y TIEJE/TIPRE), en montos, no como el porcentaje crudo de la API. El promedio de NPS ignora semestres 0/0. | `scripts/etl/extraccion.py::_IDS_SUMA_VARIABLES_SERIES`, `scripts/etl/purga.py` | El texto del catálogo no coincide con las constantes del ETL: se declara por Id. |
| RN-34 | **Unidades de visualización.** El formato (`%`, `$`, `ENT`) sale de `Meta_Signo` en el catálogo; si falta se usa `%`. Por eso las cifras en pesos (Caja, Utilidad, CAPEX, OPEX, EBITDA, Ingresos) y las enteras (GreenMetric) deben tener su signo declarado. | `frontend/src/lib/*` (`fmtValorSigno`), catálogo | |
| RN-35 | **Métricas.** Un registro que es métrica (sin meta por diseño) tiene nivel `Métrica`, **no** «Pendiente de reporte». | `domain/resumen_builders.py::mask_metrica`, `NIVEL_METRICA` | |
| RN-36 | **Lectura con Excel abierto.** Si el catálogo está bloqueado por Excel/OneDrive, el backend lee una copia temporal en lugar de fallar; si tampoco puede copiarlo, propaga el error. | `services/excel_reader.py::_read_excel_via_copy` | Evita que el dashboard quede vacío mientras Planeación diligencia el catálogo. |
| RN-37 | **CNA versionado (diseñado, sin implementar).** Los factores y características pasan a una nueva resolución desde 2027. El mismo modelo de marcos (`tipo = CNA`) los versiona; la resolución vigente queda como versión original. | `marcos.toml` (`CNA-ACTUAL`) | La nueva resolución aún no existe. |

## Regla que sí es única y bien centralizada

`domain/categorization.py` (RN-03) es la única fuente desde Oleada 2 — todos
los builders (`domain/resumen_builders.py`, `domain/cmi_builders.py`,
`domain/procesos_builders.py`, `domain/om_builders.py`,
`services/strategic_loaders.py`) delegan a ella en vez de reimplementarla.

## Estado histórico (antes de Oleada 2) — consecuencia práctica de la duplicación

El mismo indicador podía mostrarse con un color/estado en Resumen General o
CMI Estratégico (que usan RN-03 correctamente) y con un color/estado
distinto en Informe por Procesos o en las cards de línea estratégica (que
usan RN-04/05/06/07), especialmente para indicadores bajo el régimen "Plan
Anual" o "Negativo-Porcentual", que solo RN-03 conoce.
