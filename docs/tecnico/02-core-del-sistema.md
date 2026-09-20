# CORE del sistema — indicadores, cálculo y consolidación

## Motor de cálculo/semaforización — fuente única desde Oleada 2 (2026-09-20)

`backend/app/domain/calculos.py` reutiliza `categorizar_cumplimiento`
(`domain/categorization.py`) y `recalcular_cumplimiento_faltante`
(`domain/health_metrics.py`) como el motor canónico. Los umbrales oficiales
viven en `domain/constants.py`:

- General: Peligro `<0.80`, Alerta `<1.00`, Cumplimiento `<1.05`,
  Sobrecumplimiento `>=1.05`.
- Plan Anual: Peligro `<0.80`, Alerta `<0.95`, Cumplimiento `<=1.00`,
  Sobrecumplimiento `>1.00` — aplica a 11 IDs fijos **y, de forma
  incondicional por tipo, a todos los subindicadores de Retos y todos los
  Proyectos** (parámetro `regimen="plan_anual"`, confirmado con negocio).
- Negativo-Porcentual: Cumplimiento `<1.02`, Alerta `<=1.10`, Peligro
  `>1.10` — aplica a 4 IDs fijos.

Paleta oficial (`COLOR_CATEGORIA`, debe coincidir con
`frontend/src/lib/design-tokens.ts::SEMAFORO`): Peligro `#D32F2F`, Alerta
`#f59e0b`, Cumplimiento `#22c55e`, Sobrecumplimiento `#3b82f6`, Sin dato
`#BDBDBD`.

**Hasta Oleada 2 había 6 reimplementaciones divergentes** en backend
(`domain/procesos_builders.py`, `domain/cmi_builders.py` x3,
`domain/resumen_builders.py::_retos_category`,
`domain/om_builders.py::CATEGORIA_COLORS`) y 3 copias de paleta en frontend
(`cmiChartColors.ts`, `CmiVistaRapidaCards.tsx`,
`CmiProcesosResumenTab.tsx`) — todas ahora delegan a la fuente única. Ver
el detalle histórico y la evidencia de cada una en
[`05-reglas-de-negocio.md`](05-reglas-de-negocio.md).

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
