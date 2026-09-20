# Estado de Migración — SGIND v2

**Última actualización:** 2026-09-20 (Oleada 1 de `docs/tecnico/`)

> **Corrección de estructura (2026-09-20):** este documento y `ROADMAP.md`
> describían una carpeta `sgind-v2/` (`sgind-v2/backend`, `sgind-v2/frontend`,
> etc.) que **no existe en este repositorio**. La estructura real tiene
> `backend/`, `frontend/`, `database/`, `scripts/`, `docs/` directamente en
> la raíz del repo. Todos los comandos de abajo ya se corrigieron a las
> rutas reales — ver `docs/tecnico/01-arquitectura.md` para el detalle
> completo verificado contra el código.

## Resumen

| Fase | Nombre              | Estado      | Notas                                      |
|------|---------------------|-------------|--------------------------------------------|
| 0    | Levantamiento       | **Completada** | 8 entregables en `docs/phase-0/`        |
| 1    | Arquitectura        | **Completada**| 8 ADRs, RBAC, dominio portado, docker-compose |
| 2    | Modelo de Datos     | **Completada**| Esquema PG, migración, docs E2.1–E2.6     |
| 3    | UX/UI Design System | **En progreso**| Tokens, globals.css, componentes de estado |
| 4    | Backend             | **Completada** | CRUD OM, filtros plan/seguimiento/informe, lint ✅ |
| 5    | Frontend            | **Completada** | 9 páginas conectadas a API real ✅         |
| 6    | Testing E2E         | **Completada** | Playwright E2E + contratos API + CI ✅  |
| 7    | Auth Real (Azure AD)| **Completada** | /login, AuthGuard, JWT, MSAL, RBAC ✅   |
| 8    | Migración de Datos  | **Completada** | Scripts migración + validación + sync ✅  |
| 9    | Reportes PDF        | **Completada** | reportlab, 2 endpoints, botón frontend ✅ |
| 10   | Deploy Staging v2   | **Completada** | GHCR, docker-compose.staging, smoke tests ✅ |
| 11   | UAT / Validación    | **En progreso** | Artefactos UAT listos. Pendiente sesiones con usuarios. |
| 11.5 | Cierre de Hallazgos del Comparativo | **En progreso** | Plan de 8 fases en `PLAN_CIERRE_HALLAZGOS.md`, 0/8 completadas |
| 12   | Cutover Producción  | **En progreso** | Artefactos listos. Pendiente ventana de mantenimiento. |

## Fase 5 — Avance

- [x] Cliente API Axios (`src/lib/api.ts`)
- [x] Resumen General: KPIs + semáforo + tendencia + tabla
- [x] CMI Estratégico y CMI Procesos
- [x] Gestión OM (lectura)
- [x] Dev login en header
- [x] Build Next.js OK
- [x] Plan de Mejoramiento — filtros, KPIs, gráficos, tablas CNA y acciones
- [x] Seguimiento Operativo — filtros, alertas, barras apiladas, tabla detalle, export Excel
- [x] Informe por Procesos — 6 tabs: resumen, indicadores, calidad, auditoría, propuestas, IA
- [x] PDI / Acreditación — filtros, KPIs, treemap, benchmark, evolución brechas, tabla
- [x] Diagnóstico — panel de salud: checks API, datos, módulos
- [ ] CRUD OM en UI (Fase 5 extra)

## Docker

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend  | http://localhost:8000/docs |
| PostgreSQL | localhost:5433 |

```bash
docker compose up -d
```

## Uso rápido

1. Abrir http://localhost:3000
2. Clic en **Dev login** (desarrollo)
3. Ir a **Resumen General** — ver KPIs y gráficos

## Fase 11 — UAT

| Artefacto | Ruta | Propósito |
|-----------|------|-----------|
| Checklist de aceptación | `docs/migration/UAT_CHECKLIST.md` | 8 módulos, 80+ criterios |
| Registro de bugs | `docs/migration/UAT_BUGS.md` | Severidad BLOQUEANTE/MAYOR/MENOR |
| Acta de aceptación | `docs/migration/ACCEPTANCE_DOCUMENT.md` | Firma formal go-live |
| Script verificación | `scripts/uat_verify.py` | Paridad numérica v2 vs legacy |

```bash
# Ejecutar verificación numérica UAT (backend corriendo):
python scripts/uat_verify.py --api-url http://localhost:8000 --anio 2025

# Con reporte JSON:
python scripts/uat_verify.py --api-url http://localhost:8000 --output-json uat_results.json
```

## Fase 11.5 — Cierre de Hallazgos del Comparativo

| Artefacto | Ruta | Propósito |
|-----------|------|-----------|
| Plan de implementación | `docs/migration/PLAN_CIERRE_HALLAZGOS.md` | 8 fases: paleta de semáforo, tipado de endpoints, paginación, filtros compartidos, visuales, reactivación de menú, admin usuarios, comparativos multi-año |
| **Plan priorizado vigente** | [`docs/migration/PLAN_MIGRACION_PRIORIZADO.md`](PLAN_MIGRACION_PRIORIZADO.md) | Fuente de verdad de priorización funcional/visual (2026-09-18), verificada contra código real (no contra este STATUS.md). **Hallazgo crítico (ítem -1):** el pipeline ETL que produce los datos (`scripts/` del legacy, ~130 archivos) nunca se migró — SGING solo lee Excel ya producidos, sin ningún equivalente que los genere; bloquea el cutover de Fase 12 tal como está planeado. También incluye que el módulo Plan de Mejoramiento fue rediseñado en Streamlit esta semana y SGING tiene una versión anterior, no una parcial de la actual. |

## Fase 12 — Cutover

| Artefacto | Ruta | Propósito |
|-----------|------|-----------|
| Runbook de cutover | `docs/migration/CUTOVER_RUNBOOK.md` | Playbook T-7d → T+30d |
| Comunicación usuarios | `docs/migration/COMUNICACION_USUARIOS.md` | Plantillas A/B/C/D |
| Script modo mantenimiento | `scripts/set_streamlit_readonly.py` | On/off Streamlit |
| app.py (modificado) | `app.py` (raíz repo) | Soporte `SGIND_MAINTENANCE_MODE` |

```bash
# Activar modo mantenimiento en Streamlit (durante cutover):
python scripts/set_streamlit_readonly.py --enable --v2-url https://sgind-v2.poli.edu.co

# Estado actual:
python scripts/set_streamlit_readonly.py --status

# Desactivar (rollback):
python scripts/set_streamlit_readonly.py --disable
```

## Comandos

```bash
# Frontend
cd frontend && npm run build

# Backend tests (usar el venv correcto, ver backend/README.md — G-02)
cd backend && SGIND_DATA_PATH=../data PYTHONPATH=. .venv312/Scripts/python.exe -m pytest tests/ -q
```
