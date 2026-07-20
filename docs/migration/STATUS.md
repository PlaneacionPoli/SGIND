# Estado de Migración — SGIND v2

**Última actualización:** 2026-06-19

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
cd sgind-v2 && docker compose up -d
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
python sgind-v2/scripts/uat_verify.py --api-url http://localhost:8000 --anio 2025

# Con reporte JSON:
python sgind-v2/scripts/uat_verify.py --api-url http://localhost:8000 --output-json uat_results.json
```

## Fase 12 — Cutover

| Artefacto | Ruta | Propósito |
|-----------|------|-----------|
| Runbook de cutover | `docs/migration/CUTOVER_RUNBOOK.md` | Playbook T-7d → T+30d |
| Comunicación usuarios | `docs/migration/COMUNICACION_USUARIOS.md` | Plantillas A/B/C/D |
| Script modo mantenimiento | `scripts/set_streamlit_readonly.py` | On/off Streamlit |
| app.py (modificado) | `app.py` (raíz repo) | Soporte `SGIND_MAINTENANCE_MODE` |

```bash
# Activar modo mantenimiento en Streamlit (durante cutover):
python sgind-v2/scripts/set_streamlit_readonly.py --enable --v2-url https://sgind-v2.poli.edu.co

# Estado actual:
python sgind-v2/scripts/set_streamlit_readonly.py --status

# Desactivar (rollback):
python sgind-v2/scripts/set_streamlit_readonly.py --disable
```

## Comandos

```bash
# Frontend
cd sgind-v2/frontend && npm run build

# Backend tests
cd sgind-v2/backend && SGIND_DATA_PATH=../../data PYTHONPATH=. pytest tests/ -q
```
