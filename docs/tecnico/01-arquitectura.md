# Arquitectura real de SGING v2

> Basado en lectura directa de código el 2026-09-20. Reemplaza las partes de
> `docs/migration/STATUS.md` y `docs/migration/ROADMAP.md` que describen una
> estructura `sgind-v2/backend`, `sgind-v2/frontend` — **esa carpeta no
> existe**; el repo real tiene `backend/` y `frontend/` en la raíz.

## Dos sistemas de datos desacoplados

SGING v2 no es una sola aplicación con un único flujo de datos. Son **dos
sistemas independientes que conviven en el mismo repositorio**:

1. **Sistema de indicadores (lectura de Excel).** El dashboard de
   indicadores, CMI, Plan de Mejoramiento, Seguimiento e Informe por
   Procesos lee archivos `.xlsx` en `data/output/` y `data/raw/`. Esos
   archivos los produce un pipeline de scripts en `scripts/` que **el
   backend nunca ejecuta** — son dos procesos separados, uno en Python
   suelto y otro en FastAPI, sin llamada entre ellos.
2. **Sistema de gestión (Postgres).** Autenticación, usuarios/roles y el
   módulo de Gestión OM (Oportunidades de Mejora) sí usan una base de datos
   PostgreSQL real vía SQLAlchemy async, con su propio esquema en
   `database/migrations/001_initial_schema.sql`.

No hay integración entre ambos: un cambio en Postgres no afecta a los
indicadores, y viceversa.

## Backend (`backend/`)

- **Framework:** FastAPI 0.115.6, Pydantic 2.13.5 / pydantic-settings 2.7.0,
  SQLAlchemy 2.0.36 (async, `asyncpg` 0.30.0), autenticación JWT
  (`python-jose`) + MSAL 1.31.1 para Azure AD.
- **IA:** el backend usa **`google-genai` (Gemini)**, no Anthropic/Claude —
  contradice a `docs/architecture/adrs/ADR-007` si ese ADR dice "Claude API
  integración" (verificar y corregir el ADR si aplica).
- Estructura real: `backend/app/api/v1/endpoints/` (routers), `backend/app/domain/`
  (reglas de negocio puras), `backend/app/services/` (orquestación, lectura de
  Excel/Postgres), `backend/app/models/` (ORM), `backend/app/schemas/`
  (Pydantic), `backend/app/core/` (config, seguridad).
- Dependencias reales viven solo en `backend/requirements.txt` — el
  `pyproject.toml` del backend únicamente configura `ruff`, no declara
  dependencias de runtime.

## Frontend (`frontend/`)

- Next.js **14.2.35** (App Router), TypeScript 5, Tailwind, Zustand 5 (con
  `persist` en `localStorage`), TanStack Query 5, Axios 1.17.
- Gráficos: **dos librerías en paralelo**, Plotly (`plotly.js-dist-min` +
  `react-plotly.js`) para la mayoría de vistas, y Recharts 3.8.1 usado solo
  en `CmiLineaAnalisis.tsx` — sin una convención documentada de cuándo usar
  cada una.
- 9 páginas bajo `frontend/src/app/(dashboard)/`, todas conectadas a la API
  real (ninguna usa datos mock como sustituto de producción). Detalle en
  [`02-core-del-sistema.md`](02-core-del-sistema.md).

## Pipeline de datos (`scripts/`)

Vive completamente fuera de `backend/` y `frontend/`. Produce los `.xlsx`
que el backend lee. Detalle completo en
[`03-modelo-de-datos.md`](03-modelo-de-datos.md) y
[`06-flujos-end-to-end.md`](06-flujos-end-to-end.md).

**No tiene automatización real.** `.github/workflows/` solo contiene
`backend-lint.yml` (ruff en CI) y `keep-alive.yml` (ping de salud cada 10
min a Render). La sección `[schedule]` de `config/settings.toml` (cron
mensual día 5) está declarada pero **ningún workflow la implementa** — el
pipeline de indicadores es 100% manual hoy.

## Base de datos (`database/`)

Una sola migración de esquema (`001_initial_schema.sql`, SQL plano, sin
Alembic ni herramienta de migraciones): `roles`, `users`, `registros_om`,
`acciones`, `audit_log`, `ai_configs`, `ai_prompts`. De estas 7 tablas, el
backend usa activamente 4 (`roles`, `users`, `registros_om`, `acciones`);
las otras 3 existen en la BD pero no tienen ningún consumidor verificado en
`backend/app` — ver [`03-modelo-de-datos.md`](03-modelo-de-datos.md).

## Documentación previa a tener en cuenta con cautela

- `docs/migration/STATUS.md` y `ROADMAP.md`: describen fases como
  "Completada" que no siempre se sostienen contra el código (ver
  [`09-gaps-y-riesgos.md`](09-gaps-y-riesgos.md)): rutas `sgind-v2/*`
  inexistentes, "lint ✅" cuando `ruff` da 2 errores hoy, cifras de tests que
  no se pueden verificar porque el entorno de pruebas está roto.
- `docs/migration/PLAN_MIGRACION_PRIORIZADO.md` (2026-09-18): auditoría de
  código previa, más rigurosa que STATUS/ROADMAP, pero **ya parcialmente
  desactualizada** dos días después — su hallazgo sobre el módulo Plan de
  Mejoramiento ("sin ningún equivalente en SGING") ya no es cierto: el
  backend implementó `load_plan_indicadores`/`build_metricas_historico` y
  sus endpoints después de esa fecha. Su hallazgo crítico sobre el pipeline
  ETL sin migrar **sigue vigente** (confirmado de forma independiente en
  esta auditoría).
- `docs/architecture/RBAC_MATRIX.md`: documenta endpoints (`POST
  /api/v1/etl/run`, `GET /api/v1/export/*`) que no existen en el código.
- Hay **9 ADRs** en `docs/architecture/adrs/`, no 8 como dice `ROADMAP.md`.
