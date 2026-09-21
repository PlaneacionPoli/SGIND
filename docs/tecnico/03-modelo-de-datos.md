# Modelo de datos real

## PostgreSQL (`database/migrations/`)

Tres migraciones SQL planas (sin Alembic): `001_initial_schema.sql`,
`002_seed_ai_prompts.sql` y `003_drop_unused_ai_tables.sql` (Oleada 4).
`/docker-entrypoint-initdb.d` solo corre en una BD nueva: en bases ya
desplegadas la 003 se aplica a mano con `psql -f`.

| Tabla | Uso real en backend | Notas |
|---|---|---|
| `roles` | Sí (`users.role_id`) | Seed: `procesos`, `calidad`, `desempeno` |
| `users` | Sí (`auth_service.py`, `security.py`) | `azure_oid` único, soporta login Azure AD y dev/email login |
| `registros_om` | Sí (`om_service.py`, endpoint `om.py`) | Único FK-less pero con `UNIQUE(id_indicador, periodo, anio)` usado como clave de upsert; checks `tiene_om IN (0,1)`, `anio BETWEEN 2018 AND 2035` |
| `acciones` | **No** — sin modelo ORM ni SQL directo en `backend/app` (desde Oleada 4) | El modelo ORM `Accion` se eliminó (código muerto: las acciones se leen del Excel vía `domain/om_builders.py`/`plan_mejoramiento_builders.py`). La tabla sigue en el esquema (`payload JSONB`, `marker_col`/`marker_value`) como destino de una migración Excel→BD que no se ejecutó; su destino queda pendiente de decisión. Esta doc decía antes que `plan_mejoramiento_service.py` la usaba — era incorrecto |
| `audit_log` | Intencionalmente **sin lectura desde la app** | Se llena por trigger en cada cambio de `registros_om` y se consulta manualmente en auditorías (decisión de negocio, Oleada 4). Crece sin purga; una política de retención queda como mejora futura |
| ~~`ai_configs`~~, ~~`ai_prompts`~~ | **Eliminadas en Oleada 4** (migración 003) | Vestigios del diseño original con Anthropic; la IA real usa `google-genai` con config en entorno (G-10, G-20) |

Relaciones: `users.role_id → roles.id`, `audit_log.user_id → users.id (ON
DELETE SET NULL)`. `registros_om` y `acciones` no tienen FK entrantes ni
salientes — son destino de migración desde Excel/SQLite, no un modelo
relacional normalizado.

## Modelo Excel (fuente de los indicadores)

El dashboard de indicadores **no lee Postgres**, lee archivos `.xlsx` en
`data/`.

| Archivo | Estado | Quién lo produce | Quién lo lee |
|---|---|---|---|
| `data/output/Resultados Consolidados.xlsx` (hojas: Consolidado Semestral, Consolidado Historico, Consolidado Cierres, Catalogo Indicadores) | **Fuente de verdad activa** | `scripts/actualizar_consolidado.py` | `backend/app/services/etl_pipeline.py`, `excel_reader.py`, `strategic_loaders.py` |
| `data/output/Resultados Consolidados VALORES.xlsx` | Fuente de verdad secundaria (fallback, fórmulas materializadas) | mismo pipeline | mismo backend, como 2º candidato |
| `data/output/Resultados Consolidados.bak.xlsx` | Respaldo automático | `actualizar_consolidado.py` (`shutil.copy2`) | Nadie (solo respaldo) |
| `data/output/Resultados_Consolidados_CNA.xlsx` | Fuente de verdad activa (subsistema CNA) | `scripts/cna_extraction/writer.py` | `domain/plan_mejoramiento_builders.py` |
| `data/output/Seguimiento_Reporte.xlsx` | Fuente de verdad activa | Proceso no cubierto por `run_pipeline.py` (fecha de modificación más antigua que el resto — posible desactualización silenciosa) | `services/seguimiento_service.py` |
| `data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx` / `Indicadores Kawak.xlsx` | Fuente intermedia activa | `scripts/consolidar_api.py` | Entrada de `actualizar_consolidado.py` |
| `Resultados Consolidados - copia.xlsx`, `Resultados Consolidadoss - copia - copia.xlsx`, `Metricas CNA.xlsx`, `Metricas CNA - copia.xlsx`, `Resultados_Consolidados_CNA - copia.xlsx`, `revvv.xlsx` | **Obsoletos/residuales** | Copias manuales | Ninguno — no referenciados en código |
| `.versiones/` | Infraestructura de respaldo activa | `scripts/etl/versioning.py::VersionManager` (rota 5 versiones) | — |

### Discrepancia de ruta detectada

`backend/app/services/excel_reader.py` declara como archivo primario
`output/Consolidado_API_Kawak.xlsx`, pero ese archivo **no existe en
`data/output/`** — el real está en
`data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx`. Cualquier
lectura de esa ruta declarada fallará o devolverá vacío. Corregir la ruta
en `excel_reader.py` (ver [`09-gaps-y-riesgos.md`](09-gaps-y-riesgos.md)).

## Conclusión

Hay dos modelos de datos completamente separados en el mismo repositorio:
uno relacional (Postgres, 4 de 7 tablas realmente usadas) para
autenticación y OM, y uno documental (Excel, con fuentes de verdad claras
pero mezcladas con archivos residuales sin limpieza automatizada) para
indicadores/CMI/Plan de Mejoramiento/Seguimiento/Informe.
