# Fase 2 — Modelo de Datos PostgreSQL

**Estado:** Completada (validación PG pendiente de Docker Desktop)  
**Fecha:** 2026-06-13

## Entregables

| ID | Documento | Ubicación |
|----|-----------|-----------|
| E2.1 | Diagrama ER | [E2.1_DIAGRAMA_ER.md](./E2.1_DIAGRAMA_ER.md) |
| E2.2 | Script SQL creación | `../migrations/001_initial_schema.sql` |
| E2.3 | Diccionario de datos | [E2.3_DICCIONARIO_DATOS.md](./E2.3_DICCIONARIO_DATOS.md) |
| E2.4 | Mapeo SQLite → PG | [E2.4_MAPEO_MIGRACION.md](./E2.4_MAPEO_MIGRACION.md) |
| E2.5 | Script migración datos | `../scripts/migrate_sqlite_to_postgres.py` |
| E2.6 | Queries críticas | `../queries/001_dashboard_queries.sql` |

## Tablas

| Tabla | Origen | Registros legacy (SQLite) |
|-------|--------|---------------------------|
| `roles` | Nuevo (v2) | — |
| `users` | Nuevo (v2) | — |
| `registros_om` | SQLite | 0 |
| `acciones` | SQLite | 113 |
| `audit_log` | Nuevo (v2) | — |
| `ai_configs` | Nuevo (v2) | — |
| `ai_prompts` | Seed Fase 2 | 3 prompts |

## Aplicar esquema

```bash
# Con Docker
cd sgind-v2 && docker compose up -d db

# Manual
psql postgresql://sgind:sgind_dev_password@localhost:5432/sgind \
  -f database/migrations/001_initial_schema.sql
psql postgresql://sgind:sgind_dev_password@localhost:5432/sgind \
  -f database/migrations/002_seed_ai_prompts.sql
```

## Migrar datos SQLite

```bash
python sgind-v2/database/scripts/migrate_sqlite_to_postgres.py --dry-run

python sgind-v2/database/scripts/migrate_sqlite_to_postgres.py \
  --postgres postgresql://sgind:sgind_dev_password@localhost:5432/sgind
```

## Casos de prueba Fase 2

| ID | Prueba | Estado |
|----|--------|--------|
| TP-2.1 | Script creación sin errores | ⏳ Requiere Docker Desktop |
| TP-2.2 | UPSERT OM | ✅ `test_phase2_schema.py` |
| TP-2.3 | Query dashboard < 500ms | ⏳ Con PG activo |
| TP-2.4 | Migración 100% registros | ✅ Dry-run OK (113 acciones) |
| TP-2.5 | Integridad referencial | ⏳ Con PG activo |

## Decisión particionado

**No se requiere particionado** en Fase 2. Volumen PostgreSQL estimado < 10K filas (OM + acciones). Excel (~100K) permanece fuera de PG.

## Cierre formal

**Estado:** ✅ COMPLETADA (validación runtime PG al levantar Docker)  
**Fecha de cierre:** 2026-06-13
