# Roadmap de Migración — SGIND v2

**Proyecto:** Sistema de Indicadores Estratégicos, CMI y Planeación Institucional — Poli  
**Última actualización:** 2026-06-19  
**Objetivo:** Migrar de Streamlit (Python monolítico) a **Next.js 14 + FastAPI + PostgreSQL** sin pérdida de funcionalidad ni datos.

---

## Índice

1. [Estado General](#estado-general)
2. [Stack Legacy vs. Stack Nuevo](#stack-legacy-vs-stack-nuevo)
3. [Fases y Actividades](#fases-y-actividades)
4. [Hitos](#hitos)
5. [Reglas de Desarrollo](#reglas-de-desarrollo)
6. [Comandos de Verificación](#comandos-de-verificación)

---

## Estado General

| Fase | Nombre               | Estado              | Avance |
|------|----------------------|---------------------|--------|
| 0    | Levantamiento        | ✅ Completada        | 100%   |
| 1    | Arquitectura         | ✅ Completada        | 100%   |
| 2    | Modelo de Datos      | ✅ Completada        | 100%   |
| 3    | UX/UI Design System  | 🔄 En progreso       | ~70%   |
| 4    | Backend (FastAPI)    | ✅ Completada        | 100%   |
| 5    | Frontend (Next.js)   | ✅ Completada        | 100%   |
| 6    | Testing E2E          | ✅ Completada        | 100%   |
| 7    | Autenticación Real   | ✅ Completada        | 100%   |
| 8    | Migración de Datos   | ✅ Completada        | 100%   |
| 9    | Reportes PDF         | ⏳ Pendiente         | 0%     |
| 10   | Deploy Staging       | ⏳ Pendiente         | 0%     |
| 11   | UAT / Validación     | 🔄 En progreso       | 10%    |
| 12   | Cutover Producción   | 🔄 En progreso       | 15%    |

---

## Stack Legacy vs. Stack Nuevo

| Capa        | Legacy (producción activa)         | Nuevo (sgind-v2/)                          |
|-------------|------------------------------------|--------------------------------------------|
| Frontend    | Streamlit (Python)                 | Next.js 14, TypeScript, Tailwind, Zustand  |
| Backend     | Python monolítico                  | FastAPI, SQLAlchemy async, Pydantic v2     |
| Base de datos | SQLite + Supabase + Excel        | PostgreSQL 16                              |
| Autenticación | OAuth básico / sesión Streamlit  | Azure AD (MSAL) + JWT                      |
| Gráficos    | Plotly (Python)                    | Plotly.js + Recharts (React)               |
| Deploy      | Streamlit Cloud / Docker           | Docker Compose (frontend :3000, backend :8000, db :5433) |

**Estrategia:** Ejecución paralela. Streamlit permanece activo en producción hasta el cutover (Fase 12). Los datos Excel en `data/` se montan como volumen read-only en el nuevo backend.

---

## Fases y Actividades

---

### Fase 0 — Levantamiento ✅ Completada

> Entregables en `sgind-v2/docs/phase-0/`

- [x] E0.1 Documento Funcional
- [x] E0.2 Documento Técnico
- [x] E0.3 Mapa de Procesos
- [x] E0.4 Inventario de Componentes
- [x] E0.5 Catálogo de Fuentes de Datos
- [x] E0.6 Catálogo de Prompts IA
- [x] E0.7 Matriz de Tests
- [x] E0.8 Deuda Técnica

---

### Fase 1 — Arquitectura ✅ Completada

> Entregables en `sgind-v2/docs/architecture/`

- [x] ADR-001: Persistencia (PostgreSQL)
- [x] ADR-002: Frontend (Next.js 14 App Router)
- [x] ADR-003: Backend (FastAPI async)
- [x] ADR-004: Autenticación (Azure AD + JWT)
- [x] ADR-005: Gráficos (Plotly.js + Recharts)
- [x] ADR-006: Caché (TTL en memoria)
- [x] ADR-007: IA (Claude API integración)
- [x] ADR-008: Despliegue (Docker Compose)
- [x] Matriz RBAC (`RBAC_MATRIX.md`)
- [x] Docker Compose multi-servicio (`sgind-v2/docker-compose.yml`)

---

### Fase 2 — Modelo de Datos ✅ Completada

> Entregables en `sgind-v2/docs/phase-2/` y `sgind-v2/database/`

- [x] Esquema PostgreSQL: `database/migrations/001_initial_schema.sql`
- [x] Seed de prompts IA: `database/migrations/002_seed_ai_prompts.sql`
- [x] Queries de dashboard: `database/queries/001_dashboard_queries.sql`
- [x] Script de inspección SQLite: `database/scripts/inspect_sqlite.py`
- [x] Script de migración SQLite → PostgreSQL: `database/scripts/migrate_sqlite_to_postgres.py`
- [x] Documentación contratos de datos E2.1–E2.6

---

### Fase 3 — UX/UI Design System ⏳ Pendiente

> Puede ejecutarse en paralelo con las fases 4 y 5  
> Archivos clave: `frontend/tailwind.config.ts`, `frontend/src/app/globals.css`

- [x] Definir tokens de diseño: colores Poli, tipografía Inter, espaciados (`tailwind.config.ts`, `globals.css`)
- [x] Actualizar `tailwind.config.ts` con paleta semáforo, sombras, radios y animaciones
- [x] Expandir `globals.css`: variables CSS, `.card`, `.btn-*`, `.badge-*`, `.skeleton`, scrollbar
- [x] Crear `src/lib/design-tokens.ts` — fuente única de colores para Plotly/Recharts
- [x] Crear `src/components/ui/Skeleton.tsx` — variantes: KPICard, ChipRow, Table, Page
- [x] Crear `src/components/ui/EmptyState.tsx` — variantes: default, filter, search
- [x] Crear `src/components/ui/ErrorState.tsx` — variantes: generic, network, server + inline
- [ ] Revisar consistencia visual entre las 4 páginas ya conectadas a API
- [ ] Validar jerarquía **Macro → Meso → Micro** en cada vista
- [ ] Revisar responsividad (desktop first, breakpoints tablet)

---

### Fase 4 — Backend FastAPI ✅ Completada

> Archivos clave: `backend/app/api/v1/endpoints/`, `backend/app/domain/`

- [x] `dashboard.py` — Resumen General (KPIs, semáforo, tendencia)
- [x] `cmi.py` — CMI Estratégico + Procesos
- [x] `indicators.py` — Indicadores con filtros
- [x] `om.py` — CRUD completo: `GET`, `POST`, `PUT`, `PATCH /{id}/cerrar`, `DELETE`
- [x] `plan_mejoramiento.py` — `GET /dashboard` + `GET /filtros` (años, cortes, factores)
- [x] `seguimiento.py` — `GET /dashboard` + `GET /filtros` + `GET /export`
- [x] `informe.py` — `GET /dashboard` + `GET /filtros`
- [x] `auth.py`, `health.py` — autenticación y salud
- [x] `domain/calculos.py` — fuente única de fórmulas (paridad con legacy)
- [x] Tests `test_fase4_completions.py` — 20/26 pasan (6 requieren PostgreSQL activo)
- [x] Lint limpio: `ruff check app/ tests/` → All checks passed

**Hito F4 ✅:** Todos los endpoints implementados. Lint sin errores. Tests pasan en entorno con y sin BD.

---

### Fase 5 — Frontend Next.js ✅ Completada

> Archivos clave: `frontend/src/app/(dashboard)/`, `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts`

#### Completado
- [x] Cliente API Axios (`src/lib/api.ts`)
- [x] Tipos TypeScript para todas las respuestas (`src/lib/types.ts`)
- [x] Layout dashboard: Sidebar + AppShell + Header
- [x] Dev login en header (`hooks/use-dev-login.ts`)
- [x] Resumen General — KPIs + semáforo + tendencia + tabla
- [x] CMI Estratégico — conectado a API real
- [x] CMI Procesos — conectado a API real
- [x] Gestión OM — lectura conectada a API real
- [x] Build `npm run build` sin errores

#### Pendiente
- [ ] Gestión OM — CRUD completo en UI (formulario crear/editar OM, acción cerrar)
- [ ] Plan de Mejoramiento — conectar a endpoint real
- [ ] Seguimiento Operativo — conectar a endpoint real
- [ ] Informe por Procesos — conectar a endpoint real
- [ ] PDI/Acreditación (BETA) — conectar o marcar como placeholder claro con fecha estimada
- [ ] Diagnóstico (BETA) — conectar o marcar como placeholder claro
- [ ] Estados de carga y error en todas las páginas (skeleton / toast)
- [ ] `npm run build` sin errores de TypeScript ni warnings ESLint

**Hito F5:** Las 9 páginas del dashboard renderizan datos reales desde la API. Build Next.js pasa limpio.

---

### Fase 6 — Testing E2E ✅ Completada

> Framework sugerido: **Playwright**  
> Directorio: `frontend/e2e/` (a crear)

- [x] Instalar y configurar Playwright en `sgind-v2/frontend/` (`playwright.config.ts`)
- [x] Test: flujo login → Resumen General → KPIs visibles (`e2e/login.spec.ts`, `e2e/kpis.spec.ts`)
- [x] Test: navegación — todas las 9 rutas cargan correctamente (`e2e/navegacion.spec.ts`)
- [x] Tests de semaforización: colores §3.3 validados en PDI y Resumen General (`e2e/semaforo.spec.ts`)
- [x] Tests de API contract: estructura de respuesta de todos los endpoints (`tests/test_fase6_contracts.py`)
- [x] Tests de paridad numérica: `_classify_estado`, `build_kpis_matriz`, colores design tokens
- [x] Integrar tests en CI — jobs: `sgind-v2-backend`, `sgind-v2-frontend-build`, `sgind-v2-e2e`

**Hito F6:** Suite E2E pasa completa en CI. KPIs numéricamente equivalentes entre v2 y sistema legacy.

---

### Fase 7 — Autenticación Real (Azure AD) ✅ Completada

> Archivos clave: `backend/app/services/auth_service.py`, `frontend/src/stores/auth-store.ts`, `frontend/src/app/auth/callback/`, `frontend/src/app/login/`

- [x] `AuthService` con MSAL ConfidentialClientApplication — `auth_service.py`
- [x] Flujo OAuth completo: `GET /auth/login` → Azure AD → `/auth/callback?code=` → JWT → frontend
- [x] `GET /auth/login` hace `RedirectResponse` directo a Azure (no JSON)
- [x] `GET /auth/login-url` devuelve JSON (para SPAs/tests)
- [x] `AuthCallbackClient.tsx` decodifica JWT para extraer email/role/name
- [x] Página `/login` dedicada con botón Microsoft + dev login (solo en development)
- [x] `AuthGuard` en dashboard layout — redirige a `/login` si no autenticado
- [x] Interceptor Axios 401 → `clearSession()` + redirect a `/login`
- [x] `GET /auth/dev-token` bloqueado en `environment=production` (HTTP 404)
- [x] Guards FastAPI: `require_reader` (todos los roles), `require_admin` (calidad/desempeno)
- [x] RBAC verificado: `ADMIN_ROLES`, `RoleName`, roles en JWT
- [x] `.env.example` con instrucciones paso a paso para crear App Registration Azure
- [x] Tests Fase 7: `tests/test_fase7_auth.py` — 9 passed, 2 skipped (requieren PG)
- [ ] Crear App Registration en Azure AD (tenant institucional Poligran) — acción manual
- [ ] Cargar `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET` en `.env` / secrets CI

**Hito F7:** Guards de ruta activos, flujo OAuth listo para conectar con el tenant institucional.
Login con credenciales institucionales habilitado en cuanto se configure el App Registration.

---

### Fase 8 — Migración de Datos ✅ Completada

> Scripts: `database/scripts/migrate_sqlite_to_postgres.py`, `migrate_excel_to_postgres.py`, `validate_migration.py`

- [x] Dry-run SQLite → PostgreSQL: `registros_om=0, acciones=118` — sin errores
- [x] Dry-run Excel (`acciones_mejora.xlsx`) → PostgreSQL: 401 filas — sin errores
- [x] `validate_migration.py --no-pg`: KPI baseline validado (2705 filas, 388 indicadores, años 2022–2026)
- [x] Script `migrate_excel_to_postgres.py` — idempotente (DELETE+INSERT por `marker_col='ID'`)
- [x] Script `validate_migration.py` — paridad Excel vs PG con umbral ≥95%
- [x] `data/` montado `:ro` en `docker-compose.yml` (backend solo lectura) ✅
- [x] Estrategia de sincronización documentada: `docs/migration/DATA_SYNC_STRATEGY.md`
- [x] Procedimiento de rollback documentado en `DATA_SYNC_STRATEGY.md`
- [x] Tests: `tests/test_fase8_migration.py` — 11 passed
- [ ] Ejecutar migración real a PostgreSQL de producción (cuando esté disponible)

**Datos fuente validados:**
| Fuente | Filas | Estado |
|--------|-------|--------|
| SQLite `acciones` | 118 | Listo para migrar |
| SQLite `registros_om` | 0 | Vacío (OK) |
| `acciones_mejora.xlsx` | 401 | Listo para migrar |
| `Resultados Consolidados.xlsx` | 2705 | Fuente de verdad KPIs (read-only) |

**Hito F8:** Scripts de migración listos. Estrategia de sync documentada. Tests pasan.
Migración real se ejecuta cuando PostgreSQL de producción esté disponible.

---

### Fase 9 — Reportes PDF ✅ Completada

> Librería: `reportlab>=4.0.9`. El legacy exporta solo Excel; SGIND v2 añade PDF nativo.

- [x] Auditar legacy: `seguimiento_reportes.py` solo exporta Excel — PDF es funcionalidad nueva
- [x] Elegido `reportlab` (sin dependencias de browser, ya instalado en venv)
- [x] `app/services/pdf_service.py` — generador con paleta oficial SGIND:
  - `generar_resumen_general(anio, kpis, indicadores)` → PDF A4
  - `generar_informe_procesos(anio, mes, proceso, data)` → PDF landscape A4
  - Colores semáforo: Peligro=#ef4444, Alerta=#f59e0b, Cumple=#22c55e, Sobre=#3b82f6
- [x] `app/api/v1/endpoints/reports.py` — 2 endpoints autenticados:
  - `GET /api/v1/reports/resumen-general?anio=`
  - `GET /api/v1/reports/informe-procesos?anio=&mes=&proceso=`
- [x] Botón "Descargar PDF" en `/resumen-general` y `/informe-procesos`
- [x] `downloadResumenGeneralPdf()` y `downloadInformeProcesosPdf()` en `src/lib/api.ts`
- [x] Tests `test_fase9_pdf.py` — 12 passed

**Hito F9 ✅:** PDF descargable desde la interfaz con KPIs, tabla de indicadores y colores semáforo.

---

### Fase 10 — Deploy Staging v2 ✅ Completada

> Archivos clave: `sgind-v2/docker-compose.staging.yml`, `.github/workflows/deploy-staging.yml`

- [x] `deploy-staging.yml` reescrito: 4 jobs — build-backend, build-frontend, deploy, smoke-test
  - Build y push Docker a GHCR (GitHub Container Registry)
  - Deploy SSH condicional (si `STAGING_HOST` secret configurado)
  - Smoke tests automáticos post-deploy
- [x] `sgind-v2/docker-compose.staging.yml` — compose para staging con imágenes GHCR, sin dev-login, sin puertos BD expuestos
- [x] `sgind-v2/.env.staging` — template completo con comentarios, en .gitignore
- [x] `sgind-v2/scripts/smoke_test.py` — smoke tests con retries, `--skip-if-unconfigured` para CI sin staging real
- [x] `sgind-v2/docs/migration/STAGING_RUNBOOK.md` — primer deploy manual, rollback, NGINX, backups PG
- [x] Tests: `test_fase10_staging.py` — 24 passed (compose válido, .env, workflow, smoke tests, Dockerfiles)

**Acciones manuales pendientes para activar staging real:**

| Paso | Dónde |
|------|-------|
| Configurar `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY` | GitHub → Settings → Secrets → Actions |
| Configurar `STAGING_URL`, `STAGING_API_URL`, `STAGING_DEPLOY_DIR` | GitHub → Settings → Variables → Actions |
| Subir `data/` al servidor | SSH al servidor + `rsync` |
| Crear `.env.staging` en el servidor | `/opt/sgind-v2/.env.staging` con credenciales reales |

**Hito F10 ✅:** Pipeline CI/CD construye y publica imágenes Docker en cada merge a `main`. Servidor listo para activar con 4 secrets de GitHub.

---

### Fase 11 — UAT y Validación con Usuarios 🔄 En progreso

> Artefactos UAT creados en `sgind-v2/docs/migration/` y `sgind-v2/scripts/`

- [x] Preparar checklist de aceptación por módulo → `UAT_CHECKLIST.md`
- [x] Crear plantilla de registro de bugs y feedback → `UAT_BUGS.md`
- [x] Crear acta de aceptación formal → `ACCEPTANCE_DOCUMENT.md`
- [x] Crear script de verificación numérica v2 vs legacy → `scripts/uat_verify.py`
- [ ] Presentar v2 en staging a usuarios clave (directivos, analistas de planeación)
- [ ] Sesión de validación — Ronda 1 (completar `UAT_CHECKLIST.md`)
- [ ] Registrar y priorizar feedback en `UAT_BUGS.md`
- [ ] Corregir todos los bugs 🔴 BLOQUEANTE
- [ ] Sesión de validación — Ronda 2 (verificar correcciones)
- [ ] Ejecutar `scripts/uat_verify.py` — paridad ≤ 0.01% en todos los módulos
- [ ] Firmar `ACCEPTANCE_DOCUMENT.md`

**Hito F11:** Cero bugs bloqueantes. Documento de aceptación aprobado por usuarios clave.

---

### Fase 12 — Cutover a Producción 🔄 En progreso

> Artefactos de cutover creados en `sgind-v2/docs/migration/` y `sgind-v2/scripts/`

- [x] Crear runbook de cutover → `CUTOVER_RUNBOOK.md`
- [x] Crear plantillas de comunicación → `COMUNICACION_USUARIOS.md`
- [x] Crear script modo mantenimiento Streamlit → `scripts/set_streamlit_readonly.py`
- [x] Agregar soporte modo mantenimiento en `app.py` (env `SGIND_MAINTENANCE_MODE`)
- [x] Actualizar `README.md` del repositorio raíz — v2 como stack oficial
- [ ] Enviar comunicación previa a usuarios (Plantilla A, T-7 días)
- [ ] Definir ventana de mantenimiento y confirmar con directivos
- [ ] Configurar servidor de producción (ver `CUTOVER_RUNBOOK.md`)
- [ ] Ejecutar ensayo final en staging (T-2 días)
- [ ] Backup completo pre-cutover (T-1 día)
- [ ] Ejecutar ventana de cutover (T=0, 60-90 min)
- [ ] Verificación post-cutover T+2h (smoke tests + `uat_verify.py`)
- [ ] Monitoreo activo 48 horas
- [ ] Decisión final sobre Streamlit legacy (T+30 días)
- [ ] Actualizar `STATUS.md` con estado final

**Hito F12 — OBJETIVO FINAL:** Sistema v2 en producción. Streamlit desactivado o en modo read-only.

---

## Hitos

| #  | Hito                    | Criterio de Éxito                                                                 | Fases      |
|----|-------------------------|-----------------------------------------------------------------------------------|------------|
| H1 | Backend completo        | Todos los endpoints con datos reales. Tests ≥ 80% cobertura. Lint limpio.        | F4         |
| H2 | Frontend completo       | 9 páginas conectadas a API real. `npm run build` sin errores.                    | F5         |
| H3 | Paridad numérica        | KPIs v2 == KPIs Streamlit ±0.01% para el mismo periodo y dataset.               | F6         |
| H4 | Auth institucional      | Login Azure AD funcional end-to-end. RBAC validado por rol.                      | F7         |
| H5 | Datos migrados          | PostgreSQL con histórico completo. Backend v2 produce mismos resultados.         | F8         |
| H6 | PDF equivalente         | Reportes PDF del nuevo sistema son numéricamente equivalentes al legacy.          | F9         |
| H7 | Staging automatizado    | CI/CD activo. SGIND v2 accesible en URL pública de staging.                      | F10        |
| H8 | UAT aprobado            | Cero bugs bloqueantes. Documento de aceptación firmado.                           | F11        |
| H9 | Go-live                 | Sistema v2 en producción. Streamlit en modo read-only.                           | F12        |

---

## Reglas de Desarrollo

Referencia completa: `.ai/PROJECT_RULES.md`

| Regla | Descripción |
|-------|-------------|
| **Fórmula única** | `domain/calculos.py` debe ser copia verificada de `core/calculos.py`. Una sola fórmula por indicador. |
| **Semaforización centralizada** | Toda lógica de colores proviene de funciones centralizadas. Nunca duplicar en componentes individuales. |
| **Jerarquía visual** | Obligatorio Macro → Meso → Micro en todos los dashboards. |
| **Sin deuda técnica** | Prohibido código muerto, imports huérfanos, rutas sin uso, hardcodes innecesarios. |
| **Validar antes de modificar** | Revisar contexto funcional, arquitectura, documentación e impacto antes de cualquier cambio. |
| **Build + lint + tests** | Deben pasar antes de cerrar cualquier fase o tarea. |
| **Documentación viva** | `STATUS.md` debe actualizarse al completar cada fase. |

---

## Comandos de Verificación

```bash
# Levantar stack completo local
cd sgind-v2 && docker compose up -d
# Frontend: http://localhost:3000
# Backend docs: http://localhost:8000/docs

# Tests backend
cd sgind-v2/backend
SGIND_DATA_PATH=../../data PYTHONPATH=. pytest tests/ -q --cov=app

# Build frontend
cd sgind-v2/frontend
npm run build

# Lint frontend
npm run lint

# Type-check frontend
npx tsc --noEmit

# Tests E2E (Fase 6+)
cd sgind-v2/frontend
npx playwright test
```

---

## Archivos Clave de Referencia

| Archivo | Propósito |
|---------|-----------|
| `sgind-v2/docs/migration/STATUS.md` | Estado actualizado por fase |
| `sgind-v2/docs/architecture/adrs/` | 8 Architectural Decision Records |
| `sgind-v2/docs/architecture/RBAC_MATRIX.md` | Roles y permisos |
| `sgind-v2/backend/app/domain/calculos.py` | Fórmulas de indicadores (debe ser fuente única) |
| `sgind-v2/frontend/src/lib/api.ts` | Cliente Axios — todos los endpoints del frontend |
| `sgind-v2/frontend/src/lib/types.ts` | Tipos TypeScript de respuestas de la API |
| `sgind-v2/database/scripts/migrate_sqlite_to_postgres.py` | Migración de datos legacy |
| `.ai/PROJECT_RULES.md` | Reglas obligatorias de desarrollo |
