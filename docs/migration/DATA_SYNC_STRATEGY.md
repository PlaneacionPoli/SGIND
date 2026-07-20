# Estrategia de Sincronización de Datos — SGIND v2 Fase 8

**Última actualización:** 2026-06-19

---

## Contexto

Durante el período de coexistencia (Fases 8–11), los dos sistemas operan en paralelo:

| Aspecto | Streamlit (Legacy) | SGIND v2 (Nuevo) |
|---------|-------------------|------------------|
| URL producción | Streamlit Cloud | Docker / staging |
| Fuente KPIs | Excel directo | Excel vía ETL cache |
| CRUD OM | SQLite local | PostgreSQL |
| Acciones mejora | Excel `acciones_mejora.xlsx` | PostgreSQL `acciones` |

---

## Fuentes de datos y sus propietarios

### Excel (fuente de verdad para KPIs — read-only en SGIND v2)

| Archivo | Propietario de escritura | Qué contiene |
|---------|--------------------------|--------------|
| `data/output/Resultados Consolidados.xlsx` | ETL pipeline (scripts/) | Histórico de indicadores 2022–2026 |
| `data/raw/Kawak/*.xlsx` | Sistema Kawak (automático) | Datos de gestión |
| `data/raw/API/*.xlsx` | Sistema API Poli | Resultados académicos |
| `data/raw/acciones_mejora.xlsx` | Kawak (export manual) | Acciones de mejora |
| `data/raw/Indicadores por CMI.xlsx` | Equipo calidad | Catálogo CMI |
| `data/raw/Ficha_Tecnica_Indicadores.xlsx` | Equipo calidad | Fichas técnicas |

**Regla:** SGIND v2 monta `data/` como **solo lectura** (`:ro` en docker-compose). Nunca escribe en estos archivos.

### PostgreSQL (fuente de verdad para datos mutables)

| Tabla | Origen inicial | Fuente de escritura en producción |
|-------|---------------|-----------------------------------|
| `registros_om` | Vacío (SQLite vacío) | CRUD vía API SGIND v2 |
| `acciones` | `acciones_mejora.xlsx` (118 SQLite + 401 Excel) | Kawak export + CRUD v2 |
| `users` | Vacío | Login OIDC / dev-token |
| `audit_log` | Vacío | Triggers automáticos |

---

## Flujo de sincronización durante coexistencia

```
┌──────────────────────────────────────────────────────────┐
│  EXCEL (read-only para SGIND v2)                         │
│  ┌─────────────────────────────────┐                     │
│  │ Resultados Consolidados.xlsx    │ ← ETL scripts       │
│  │ Kawak/*.xlsx, API/*.xlsx        │ ← Sistemas externos │
│  │ acciones_mejora.xlsx            │ ← Export Kawak      │
│  └────────────────────┬────────────┘                     │
│                       │ read (cache TTL=5min)            │
└───────────────────────┼──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  SGIND v2 Backend (FastAPI + ETL pipeline)               │
│  • KPI dashboards: Excel → ETL → API response           │
│  • OM CRUD: PostgreSQL                                   │
│  • Acciones: PostgreSQL (seed desde Excel)               │
└──────────────────────────────────────────────────────────┘
```

---

## Procedimiento de sincronización incremental (acciones_mejora.xlsx)

Cuando el equipo exporta una nueva versión de `acciones_mejora.xlsx` desde Kawak:

```bash
# 1. Reemplazar el archivo
cp /ruta/nueva/acciones_mejora.xlsx data/raw/acciones_mejora.xlsx

# 2. Dry-run para verificar diferencias
python sgind-v2/database/scripts/migrate_excel_to_postgres.py --dry-run

# 3. Migración real (re-inserción idempotente: DELETE WHERE marker_col='ID' + INSERT)
python sgind-v2/database/scripts/migrate_excel_to_postgres.py \
    --postgres "postgresql://sgind:pass@localhost:5433/sgind"

# 4. Validar integridad
python sgind-v2/database/scripts/validate_migration.py \
    --postgres "postgresql://sgind:pass@localhost:5433/sgind"
```

**Frecuencia recomendada:** Mensual (o cuando se exporte un nuevo reporte de Kawak).

---

## KPI Cache (sin sincronización requerida)

Los KPIs se leen del Excel en tiempo real con caché en memoria (TTL=5 minutos, configurable via `EXCEL_CACHE_TTL_SECONDS`). No hay proceso de sincronización activa — el ETL se re-ejecuta automáticamente al expirar el cache.

---

## Plan de migración completa (Cutover — Fase 12)

Cuando SGIND v2 sea la única fuente:

1. `acciones_mejora.xlsx` → migración final completa a `acciones`
2. Desactivar montaje `:ro` de `data/` si el Excel ya no es necesario
3. Todos los KPIs se calculan desde PostgreSQL (requiere migrar histórico Excel → PG)
4. Apagar Streamlit

**Nota:** La migración completa de histórico KPI a PG es opcional si se mantiene el Excel como fuente. El ETL pipeline puede coexistir indefinidamente con PostgreSQL.

---

## Rollback

En caso de problema post-migración:

```bash
# 1. Revertir tabla acciones a estado anterior
psql "postgresql://sgind:pass@localhost:5433/sgind" \
    -c "DELETE FROM acciones WHERE marker_col = 'ID';"

# 2. Restaurar desde SQLite legacy (118 acciones)
python sgind-v2/database/scripts/migrate_sqlite_to_postgres.py \
    --sqlite data/db/registros_om.db \
    --postgres "postgresql://sgind:pass@localhost:5433/sgind"

# 3. Verificar
python sgind-v2/database/scripts/validate_migration.py \
    --postgres "postgresql://sgind:pass@localhost:5433/sgind"
```

La tabla `audit_log` registra automáticamente todas las inserciones/actualizaciones/borrados vía trigger.

---

## Verificación de integridad post-migración

| Check | Valor esperado | Comando |
|-------|---------------|---------|
| Acciones en PG desde Excel | 401 filas | `validate_migration.py --postgres ...` |
| Paridad acciones | ≥ 95% | idem |
| `registros_om` OM | ≥ 0 filas | idem |
| KPI Resultados Consolidados | 2705 filas | `validate_migration.py --no-pg` |
| Indicadores únicos | 388 | idem |
