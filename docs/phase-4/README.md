# Fase 4 — Backend FastAPI

**Estado:** En progreso (núcleo implementado)  
**Fecha:** 2026-06-13

## Entregables implementados

| ID | Componente | Estado |
|----|------------|--------|
| E4.1 | Backend FastAPI funcional | ✅ Núcleo |
| E4.2 | Swagger /docs | ✅ |
| A4.2 | ExcelReader + caché TTL | ✅ |
| A4.4 | Dashboard KPIs, semáforo, tendencia | ✅ |
| A4.4.5 | `GET /indicators` + detalle | ✅ |
| A4.5 | CMI estratégico, procesos, alertas | ✅ |
| A4.6 | OM CRUD | ✅ |
| A4.1 | Pipeline ETL 5 fases | ✅ Portado |
| A4.7 | Endpoints IA | ⏳ Fase 8 |
| A4.8 | Endpoints ETL run/status | ⏳ |
| A4.9 | Export Excel/PDF | ⏳ |
| E4.3–E4.5 | Coverage ≥ 80% | ⏳ 21 tests |

## Endpoints nuevos

| Método | Ruta | Auth |
|--------|------|------|
| GET | `/api/v1/indicators` | reader |
| GET | `/api/v1/indicators/{id}` | reader |
| GET | `/api/v1/cmi/estrategico` | reader |
| GET | `/api/v1/cmi/procesos` | reader |
| GET | `/api/v1/cmi/alertas` | reader |
| GET | `/api/v1/dashboard/semaphore` | reader |
| GET | `/api/v1/dashboard/trend` | reader |

## Servicios

- `ETLPipelineService` — `app/services/etl_pipeline.py`
- `IndicatorService` — `app/services/indicator_service.py`
- `CMIService` — `app/services/cmi_service.py`
- `DashboardService` — actualizado para usar ETL

## Casos de prueba

| ID | Prueba | Estado |
|----|--------|--------|
| TP-4.1 | Health 200 | ✅ |
| TP-4.2 | KPIs sin auth → 401 | ✅ |
| TP-4.3 | POST OM procesos → 403 | ✅ |
| TP-4.4 | GET indicators con auth | ✅ |
| TP-4.5 | Filtro año | ✅ |
| TP-4.6 | IA analyze | ⏳ |
| TP-4.7 | Coverage 80% | ⏳ |

## Verificación

```bash
cd sgind-v2/backend
SGIND_DATA_PATH=../../data PYTHONPATH=. pytest tests/ -q
```
