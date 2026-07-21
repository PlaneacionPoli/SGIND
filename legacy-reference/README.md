# legacy-reference/

Este directorio contiene documentación y código **de referencia** copiados desde el
proyecto original en Streamlit (`Sistema_Indicadores_Poli`), que era el sistema
del cual SGIND v2 (este repo: `backend/` + `frontend/`) es la migración.

**No forma parte de la aplicación activa.** Nada aquí se importa desde
`backend/` ni `frontend/`, no tiene tests, no corre en CI/CD y no se despliega.
Se mantiene fuera de esas carpetas a propósito para que ninguna herramienta de
build, lint o testing lo recoja por accidente.

## Por qué existe

Durante la auditoría de paridad Streamlit-vs-SGIND-v2 se detectó que, al migrar
la app, se copiaron los datos (`data/`) pero **no** la documentación funcional/
técnica ni los scripts de ETL/auditoría del proyecto original. Esto dejaba sin
contexto accesible reglas de negocio no triviales (p. ej. los umbrales de
cumplimiento que varían por tipo de indicador, documentados en
`docs/LOGICA_INDICADORES_ESPECIALES.md`) que sí quedaron portadas al código
(`backend/app/domain/categorization.py`, `calculos.py`) pero sin su explicación
original al lado.

## Contenido

- **`docs/`** — Documentación funcional, técnica y de gobernanza del proyecto
  original: lógica de indicadores especiales, guía de actualización de
  consolidados, arquitectura (`docs/core/00-11`), diagramas ER, SQL de ajustes,
  y el informe ejecutivo. Incluye también `docs/archive/` (decisiones e
  inventarios históricos de fases anteriores del proyecto original).
- **`scripts/`** — Los ~40 scripts de ETL, consolidación y auditoría
  (`scripts/etl/`, `scripts/pipeline_steps/` — runner de 14 pasos que genera
  `Resultados Consolidados.xlsx` desde las fuentes crudas, y los `agentN_*.py`
  de auditoría de calidad/deuda técnica).
- **`core/`** — El paquete `core/` original completo (`calculos.py`,
  `semantica.py`, `db_manager.py`, `domain/`, `modelo_datos/`,
  `presentation/`, `proceso_types.py`). `calculos.py` ya tiene un equivalente
  activo en `backend/app/domain/calculos.py`; el resto se conserva como
  referencia de la lógica que aún no tiene contraparte 1:1 en el backend.
- **`config/`** — `data_contract.yaml`, `data_contracts.yaml`,
  `mapeos_procesos.yaml`, `series_subindicadores.toml`, `settings.toml`: la
  configuración declarativa (contratos de datos, mapeo subproceso→proceso,
  etc.) que gobernaba el pipeline original.
- **`tools/`**, **`notebooks/`** — Utilidades puntuales (`compute_advances.py`)
  y el notebook de análisis exploratorio.
- **`CMI_STRATEGIC/`** — Prototipos HTML y prompts de diseño originales del
  CMI Estratégico, usados como referencia visual durante el diseño.

## Punto importante sin resolver

**El pipeline ETL de 14 pasos (`scripts/pipeline_steps/`) que genera los
Excel consolidados (`Resultados Consolidados.xlsx`, `Seguimiento_Reporte.xlsx`,
etc.) NO corre dentro de SGIND v2.** El backend de SGIND v2
(`backend/app/services/excel_reader.py`) solo **lee** esos Excel ya generados;
no los regenera. Actualmente esa regeneración sigue dependiendo del proyecto
original (`Sistema_Indicadores_Poli`) o de un proceso manual/externo.

Esto es una decisión de arquitectura razonable para una migración por fases
(ver `docs/migration/DATA_SYNC_STRATEGY.md` y `docs/migration/ROADMAP.md` en
`SGING/docs/`), pero **debe decidirse explícitamente** si:
1. El pipeline seguirá viviendo permanentemente en el proyecto Streamlit
   (y este repo solo consume su salida), o
2. Se debe portar/reescribir como un servicio propio de `backend/` en algún
   momento del roadmap de migración.

`backend/app/services/etl_pipeline.py` existe como un servicio parcial, pero
no es un port 1:1 del runner de 14 pasos — no se debe asumir que reemplaza a
`scripts/pipeline_steps/` sin verificarlo paso a paso.
