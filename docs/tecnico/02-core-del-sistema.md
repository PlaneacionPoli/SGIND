# CORE del sistema — indicadores, cálculo y consolidación

## Motor de cálculo/semaforización — NO es una fuente única

`backend/app/domain/calculos.py` reutiliza correctamente
`categorizar_cumplimiento` (`domain/categorization.py:34-82`) y
`recalcular_cumplimiento_faltante` (`domain/health_metrics.py:13-63`) como
el motor "canónico". Los umbrales oficiales viven en
`domain/constants.py:5-14`:

- General: Peligro `<0.80`, Alerta `<1.00`, Cumplimiento `<1.05`,
  Sobrecumplimiento `>=1.05`.
- Variante "Plan Anual": alerta `<0.95`, sobrecumplimiento `>=1.00`.
- Variante "Negativo-Porcentual": `1.02`/`1.10`.

**Pero hay 4 reimplementaciones divergentes de la misma regla** en otros
archivos, con umbrales y nombres distintos a los canónicos:

| Ubicación | Umbrales usados | Problema |
|---|---|---|
| `domain/procesos_builders.py:63-80` (`cumplimiento_semaforo_color`/`cumplimiento_estado`) | 2 niveles: `>=100` / `>=80` | Sin tercer nivel "Sobrecumplimiento", sin variantes Plan Anual/Negativo-Porcentual |
| `domain/cmi_builders.py:208-239` (`_estado_linea_card`) | `>=100` / `>=80` | Otro set de 2 niveles distinto al anterior |
| `domain/cmi_builders.py:242-249` (`_estado_linea`) | `>=100` / `>=95` / `>=80` | 3 niveles con los mismos nombres que `CategoriaCumplimiento` pero cortes numéricos distintos (95/100 en vez de 100/105) |
| `domain/cmi_builders.py:459-481` (`generate_linea_narrativa_heuristica`) | `>=100` / `>=95` | Colores propios que no coinciden con `COLOR_CATEGORIA` |

El propio código documenta en un comentario (`domain/pdi_service.py:16-19`)
que ya hubo un intento previo de unificar una paleta divergente — es un
problema conocido y recurrente, no resuelto del todo.

**En el frontend se repite el mismo patrón**: 4 mapas de color distintos
para el mismo dominio semántico (`cmiChartColors.ts`, `nivelUtils.tsx`,
`CmiProcesosResumenTab.tsx`, `CmiVistaRapidaCards.tsx`), y un fallback de
clasificación en `CmiProcesosResumenTab.tsx:29-46` que reimplementa umbrales
80/100/105 sin conocer los regímenes especiales (Plan Anual, etc.) del
backend — si el backend deja de mandar el campo `nivel`, el frontend
clasificaría mal esos casos.

## El pipeline de consolidación (productor real de los datos)

`scripts/actualizar_consolidado.py` es el orquestador real de negocio (no
`backend/app/services/etl_pipeline.py`, pese al nombre de este último).
Combina fuentes (Kawak/API), aplica ~15 pasos (purga, construcción de
registros histórico/semestral/cierres, correcciones AGENT5 sobre
Ejecución>1.3, validaciones en 3 "gates", reparación de metas/signos,
backup con rollback automático) y produce `data/output/Resultados
Consolidados.xlsx`. La lógica de negocio real vive en los 23 módulos de
`scripts/etl/`.

`backend/app/services/etl_pipeline.py` **no es este proceso** — solo:
1. Lee la hoja del Excel ya producido.
2. Hace un `merge` con la hoja "Catalogo Indicadores" para traer
   `Clasificacion`.
3. Hace un segundo `merge` para traer `Subproceso`/`Linea`/`Objetivo`.
4. Deriva `Anio`/`Mes`/`Periodo` si faltan.
5. Llama a `domain/calculos.py::aplicar_calculos_cumplimiento`.

Es decir: enriquece un archivo ya generado, no lo genera. **El backend
nunca ejecuta `scripts/*.py`** (confirmado, sin `subprocess`/`os.system`
hacia esos scripts en `backend/app`).

Subsistema aparte: `scripts/cna_extraction/` (2 fases — diagnóstico y
escritura — deliberadamente separadas) produce
`data/output/Resultados_Consolidados_CNA.xlsx`, consumido por
`domain/plan_mejoramiento_builders.py`. Tampoco está integrado al backend
ni automatizado; se corre manualmente.

## Módulo OM (Gestión de Oportunidades de Mejora) — único con persistencia real en Postgres

`registros_om` (Postgres) es la única entidad de negocio con CRUD real
respaldado por base de datos relacional (no Excel): creación, actualización,
cierre (`tiene_om=0`) y borrado, todos protegidos con `require_admin`
excepto la lectura (`require_reader`). Ver
[`04-api.md`](04-api.md) para el detalle de endpoints.

## Componentes CORE (resumen)

| Componente | Tipo | Archivo | Es CORE porque |
|---|---|---|---|
| `categorizar_cumplimiento` | Regla de dominio | `domain/categorization.py` | Motor canónico de semaforización, reutilizado por la mayoría de servicios |
| `recalcular_cumplimiento_faltante` | Regla de dominio | `domain/health_metrics.py` | Calcula cumplimiento cuando el dato viene incompleto |
| `actualizar_consolidado.py` + `scripts/etl/*` | Pipeline externo | `scripts/` | Produce el archivo fuente de verdad de indicadores; sin él, los datos se congelan |
| `etl_pipeline.py` | Servicio backend | `backend/app/services/` | Puente entre el Excel producido y los endpoints de dashboard |
| `om_service.py` / `models/om.py` | Servicio + modelo | `backend/app/` | Único flujo de datos con escritura transaccional real (Postgres) |
| `plan_mejoramiento_builders.py` | Dominio | `backend/app/domain/` | Reglas de Plan de Mejoramiento (indicadores + métricas + tendencia), ya implementado pese a que la auditoría previa decía lo contrario |
