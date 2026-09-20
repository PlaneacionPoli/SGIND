# Inventario de reglas de negocio

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
| RN-03 | Categorización canónica de cumplimiento (semáforo) | `domain/categorization.py::categorizar_cumplimiento` (34-82) | cumplimiento decimal, id | Peligro/Alerta/Cumplimiento/Sobrecumplimiento/Sin dato | **Sí — ver RN-04 a RN-07** |
| RN-04 | Semaforización de procesos (2 niveles, sin variantes) | `domain/procesos_builders.py::cumplimiento_semaforo_color`/`cumplimiento_estado` (63-80) | valor % | color/label | Duplicado divergente de RN-03 |
| RN-05 | Estado de línea para cards (2 niveles) | `domain/cmi_builders.py::_estado_linea_card` (208-239) | cumplimiento %, tiene_datos | dict label/color | Duplicado divergente de RN-03 |
| RN-06 | Estado de línea (3 niveles, mismos nombres, cortes distintos) | `domain/cmi_builders.py::_estado_linea` (242-249) | cumplimiento % | (label, color) | Duplicado divergente de RN-03 (95/100 en vez de 100/105) |
| RN-07 | Narrativa heurística por línea | `domain/cmi_builders.py::generate_linea_narrativa_heuristica` (459-481) | cumplimiento promedio, riesgo | texto/color/icon | Duplicado divergente de RN-03, colores propios |
| RN-08 | Clasificación de tendencia histórica (variación interanual) | `domain/plan_mejoramiento_builders.py::_classify_tendencia_historico` (986-996) | variación % promedio, n años con dato | Creciente/Decreciente/Estable/Sin suficiente historia | No |
| RN-09 | Detección de escala porcentual (fracción vs. 0-100) | `domain/plan_mejoramiento_builders.py::_detecta_escala_pct` (999-1007) | signo, lista de valores | bool | No |
| RN-10 | Cierre de OM | `services/om_service.py::OMService.cerrar` (65-77) | registro_id, comentario | RegistroOM actualizado (`tiene_om=0`) | No |
| RN-11 | Cálculo de KPIs agregados | `domain/calculos.py::calcular_kpis` (64-79) | DataFrame con Cumplimiento_norm/Categoria | (total, conteos/%) | No |
| RN-12 | Derivación de Periodo/Mes/Año faltantes | `services/etl_pipeline.py::fase4_fechas` (141-169) | DataFrame con Fecha | DataFrame con Anio/Mes/Periodo completos | No |
| RN-13 (frontend) | Fallback de clasificación de semáforo (2 niveles + sobrecumplimiento) | `frontend/src/components/cmi/CmiProcesosResumenTab.tsx::nivelKeyFallback` (29-46) | pct | nivel | Duplicado divergente de RN-03, no conoce regímenes especiales (Plan Anual, Negativo-Porcentual) |
| RN-14 (frontend, código muerto) | Formateo de % asumiendo fracción 0-1 | `frontend/src/components/tables/IndicatorsTable.tsx::formatPct` (14-17) | valor | "%" | Contradice a RN-15; componente no usado en ninguna página hoy |
| RN-15 (frontend) | Formateo de % asumiendo escala 0-100 | `frontend/src/components/cmi/nivelUtils.tsx::fmtPct` (23-26) | valor | "%" | Usado en casi toda la app; opuesta semánticamente a RN-14 |
| RN-16 | Estado del Indicador dentro de Plan de Mejoramiento (distinto del semáforo de cumplimiento) | `domain/plan_mejoramiento_builders.py::classify_plan_indicador_estado` (526-544) | Estado_Aprobacion, Tipo, medición 2025/2026 | Activo (aprobado + Tipo=Indicador + con medición) / Aprobado (aprobado sin medición) / Pendiente | No — solo aplica a filas de Plan de Mejoramiento, no al indicador general del dashboard |
| RN-17 | Exclusión de "subtotal fantasma" en desglose de Métricas | `domain/plan_mejoramiento_builders.py::_excluye_subtotal_fantasma` (1010-1028) | filas de una Métrica con y sin `Subindicador` | filas sin el subtotal duplicado | No — corrige un caso real de doble conteo detectado en "Matrícula de estudiantes" (5.881 vs. 58.398 real, 2026-09-18) |

## Regla que sí es única y bien centralizada

`domain/categorization.py` (RN-03) es la referencia correcta a seguir para
cualquier regla de semaforización nueva — los servicios que la reutilizan
en vez de reimplementarla (`services/pdi_service.py`,
`domain/resumen_builders.py`, `services/strategic_loaders.py`) no presentan
duplicación.

## Consecuencia práctica de la duplicación (RN-03 a RN-07, RN-13)

El mismo indicador puede mostrarse con un color/estado en Resumen General o
CMI Estratégico (que usan RN-03 correctamente) y con un color/estado
distinto en Informe por Procesos o en las cards de línea estratégica (que
usan RN-04/05/06/07), especialmente para indicadores bajo el régimen "Plan
Anual" o "Negativo-Porcentual", que solo RN-03 conoce.
