# Modelo de datos real

## PostgreSQL (`database/migrations/001_initial_schema.sql`)

Única migración de esquema, SQL plano (sin Alembic).

| Tabla | Uso real en backend | Notas |
|---|---|---|
| `roles` | Sí (`users.role_id`) | Seed: `procesos`, `calidad`, `desempeno` |
| `users` | Sí (`auth_service.py`, `security.py`) | `azure_oid` único, soporta login Azure AD y dev/email login |
| `registros_om` | Sí (`om_service.py`, endpoint `om.py`) | Único FK-less pero con `UNIQUE(id_indicador, periodo, anio)` usado como clave de upsert; checks `tiene_om IN (0,1)`, `anio BETWEEN 2018 AND 2035` |
| `acciones` | Sí (`plan_mejoramiento_service.py`) | `payload JSONB` para columnas no tipadas del Excel origen; `marker_col`/`marker_value` para idempotencia de migración |
| `audit_log` | **No** — sin consumidor en `backend/app` | Se sigue llenando automáticamente vía trigger en cada cambio de `registros_om`, pero nadie la lee ni expone |
| `ai_configs` | **No** — sin consumidor en `backend/app` | Config de proveedor/modelo IA, huérfana |
| `ai_prompts` | **No** — sin consumidor en `backend/app` | 3 prompts sembrados (`002_seed_ai_prompts.sql`) para análisis IA, sin código que los use |

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
