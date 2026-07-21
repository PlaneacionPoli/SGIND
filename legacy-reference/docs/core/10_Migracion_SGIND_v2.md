# 10 - MIGRACIÓN SGIND v2

**Documento:** 10_Migracion_SGIND_v2.md  
**Versión:** 1.0  
**Fecha:** 17 de junio de 2026  
**Status:** ✅ Activo — En Progreso

---

## 1. Contexto

SGIND v2 es la reescritura del sistema de indicadores Streamlit en un stack moderno:

| Aspecto | Streamlit (Producción) | SGIND v2 (Migración) |
|---------|------------------------|----------------------|
| Frontend | Streamlit (Python) | Next.js 14 (App Router, TypeScript, Tailwind) |
| Backend | n/a (monolítico) | FastAPI (async, SQLAlchemy 2.0, Pydantic v2) |
| Base de datos | SQLite + Excel | PostgreSQL (Supabase) + Excel |
| Auth | OIDC Microsoft (Streamlit-auth) | MSAL / OIDC Microsoft (FastAPI) |
| Deploy | Streamlit Community Cloud | Docker / Render / VPS |
| Entorno local | `streamlit run app.py` | `docker compose up --build` |

---

## 2. Estado por Componente

### 2.1 Backend — FastAPI

| Módulo | Estado | Notas |
|--------|--------|-------|
| `app/main.py` | ✅ Completo | Entrypoint con CORS, routers, lifespan |
| `app/api/v1/endpoints/auth.py` | ✅ Completo | OIDC Microsoft |
| `app/api/v1/endpoints/dashboard.py` | ✅ Completo | KPIs principales |
| `app/api/v1/endpoints/indicators.py` | 🟡 Parcial | Algunos endpoints con TODO en `indicator_service.py` |
| `app/api/v1/endpoints/cmi.py` | ✅ Completo | CMI estratégico |
| `app/api/v1/endpoints/om.py` | ✅ Completo | Objetivos de Mejora |
| `app/api/v1/endpoints/informe.py` | 🟡 Parcial | `informe_builders.py` tiene TODOs |
| `app/api/v1/endpoints/plan_mejoramiento.py` | ✅ Scaffold | Estructura completa, lógica básica |
| `app/api/v1/endpoints/seguimiento.py` | ✅ Completo | Seguimiento de indicadores |
| `app/api/v1/endpoints/health.py` | ✅ Completo | Health check |
| `app/services/etl_pipeline.py` | 🟡 Parcial | Integra con pipeline Streamlit, algunos stubs |
| `app/services/excel_reader.py` | ✅ Completo | Lector de archivos Excel compartidos |
| `app/services/strategic_loaders.py` | ✅ Completo | Indicadores estratégicos |
| `app/services/tracking_cache.py` | ✅ Completo | Cache de seguimiento |
| `app/domain/` (14 builders) | 🟡 Parcial | `informe_builders.py` tiene stubs; resto completo |
| `app/core/database.py` | 🟡 Parcial | TODO: connection pooling config |

### 2.2 Frontend — Next.js 14

| Módulo | Estado | Notas |
|--------|--------|-------|
| `src/app/layout.tsx` | ✅ Completo | Root layout, Providers |
| `src/app/page.tsx` | ✅ Completo | Redirect a dashboard |
| `src/app/auth/` | ✅ Completo | Login/logout flow MSAL |
| `src/app/(dashboard)/` | 🟡 Scaffold | Layout con nav, contenido parcial |
| `src/components/ui/KPICard.tsx` | ✅ Completo | Tarjeta KPI institucional |
| `src/components/ui/FilterBar.tsx` | ✅ Completo | Filtros dinámicos |
| `src/components/ui/VistaSelector.tsx` | ✅ Completo | Selector de vista |
| `src/components/ui/ExecutiveNarrative.tsx` | ✅ Completo | Narrativa IA |
| `src/components/charts/TrendChart.tsx` | ✅ Completo | Gráfico de tendencia |
| `src/components/charts/SemaphoreChart.tsx` | ✅ Completo | Semáforo de cumplimiento |
| `src/components/charts/SunburstChart.tsx` | ✅ Completo | Sunburst (composición) |
| `src/components/charts/ProyectosGanttChart.tsx` | ✅ Completo | Gantt de proyectos |
| `src/components/PagePlaceholder.tsx` | ⚠️ Existe | Usado en páginas aún no implementadas |
| `src/hooks/` | ✅ Completo | Data fetching hooks con SWR/TanStack |
| `src/stores/` | ✅ Completo | Estado global (Zustand) |
| `src/lib/` | ✅ Completo | API client, utils |

---

## 3. Fases de Migración

Las fases están documentadas en `sgind-v2/docs/`:

| Fase | Carpeta | Estado | Contenido |
|------|---------|--------|-----------|
| Fase 0 | `docs/phase-0/` | ✅ Completo | Inventario, funcional, técnico, fuentes de datos, prompts IA |
| Fase 2 | `docs/phase-2/` | ✅ Completo | Arquitectura de migración |
| Fase 4 | `docs/phase-4/` | ✅ Completo | Diseño de dominio y API |
| Fase 5 | `docs/phase-5/` | 🟡 En progreso | Tests y calidad v2 |

---

## 4. Diferencias de Dominio vs Streamlit

| Concepto | Streamlit | SGIND v2 |
|----------|-----------|----------|
| Cálculo cumplimiento | `scripts/etl/cumplimiento.py` | `app/domain/calculos.py` (misma lógica) |
| Categorización | `core/domain/categorization.py` | `app/domain/categorization.py` (idéntica, 3 regímenes: Regular/Plan Anual/Negativo-Porcentual) |
| Umbrales semaforización | `core/config.py` | `app/domain/constants.py` |
| IDs Plan Anual | Dinámico desde Excel | Mismo origen, configurado vía `settings.py` |
| IDs Negativo-Porcentual (jul-2026) | `IDS_NEGATIVO_PCT` en `core/config.py` (lista curada fija) | `IDS_NEGATIVO_PCT` en `app/domain/constants.py` (misma lista, mantenida en sincronía manual — no hay import compartido entre ambos codebases) |
| Auth | OIDC Streamlit-auth library | MSAL / OAuth2 propio en FastAPI |
| Plan Mejoramiento | Manual/editorial (no en código) | `plan_mejoramiento_service.py` + endpoint REST |
| Predicciones | `scripts/analytics/predictor.py` (no integrado) | No migrado aún |

---

## 5. Vacíos de Migración (FASE 6)

> Ver [`00_INVENTARIO.md` sección Vacíos Tecnológicos](00_INVENTARIO.md#vacíos-tecnológicos-fase-6) para el detalle completo.

| Funcionalidad | Estado Streamlit | Estado v2 | Gap |
|---------------|-----------------|-----------|-----|
| Dashboard CMI | ✅ Completo | ✅ Endpoint y UI básica | Parity alcanzada |
| Gestión OM | ✅ Completo | ✅ Endpoint completo | Parity alcanzada |
| Resumen por proceso | ✅ Completo | 🟡 Parcial | Página no finalizada |
| Plan Mejoramiento | 📄 Editorial | ✅ CRUD REST | v2 supera a Streamlit |
| Informes por proceso | ✅ Completo | 🟡 Partial stubs | Falta completar builders |
| Predicciones/Analytics | ❌ No integrado | ❌ No migrado | Gap en ambas versiones |
| Ficha PDF | ✅ `services/ficha_pdf/` | ❌ No implementado | Pendiente v2 |
| Notificaciones SMTP | ✅ Código existe | ❌ No en v2 | Pendiente v2 |

---

## 6. Criterio de Cutover

Para migrar el tráfico de producción de Streamlit → SGIND v2 se deben cumplir:

| Criterio | Estado |
|----------|--------|
| Parity funcional en dashboards principales (CMI, OM, Resumen, Indicadores Riesgo) | 🟡 En progreso |
| Auth MSAL funcionando con allowlist de emails institucionales | ✅ Completo |
| Pipeline ETL generando datos compatibles (mismo Excel de entrada) | ✅ Completo |
| Tests E2E de las páginas principales | ❌ Pendiente |
| Deploy CI/CD configurado | 🟡 docker-compose listo, sin pipeline CI |
| Documentación de usuario final | ❌ Pendiente |

**Estimado de cutover:** No hay fecha definida. Prioritizar completar stubs de `informe_builders.py` e implementar páginas con `PagePlaceholder`.

---

## 7. Inicio Local

```bash
# 1. Variables de entorno
cp sgind-v2/.env.example sgind-v2/.env
# Editar .env: DATABASE_URL, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET

# 2. Docker (recomendado)
cd sgind-v2
docker compose up --build

# 3. Sin Docker
# Backend:
cd sgind-v2/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend:
cd sgind-v2/frontend
npm install
npm run dev
```

| Servicio | URL local |
|----------|-----------|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

---

## 8. Referencias

- **Inventario completo:** [`00_INVENTARIO.md`](00_INVENTARIO.md)
- **Arquitectura:** [`01_Arquitectura.md`](01_Arquitectura.md)
- **Lógica de cálculo (compartida):** [`02_Logica_Indicadores.md`](02_Logica_Indicadores.md)
- **Vacíos tecnológicos:** Sección 5 de este documento + [`00_INVENTARIO.md`](00_INVENTARIO.md)
- **Docs fase-0 SGIND v2:** [`sgind-v2/docs/phase-0/`](../../sgind-v2/docs/phase-0/)
