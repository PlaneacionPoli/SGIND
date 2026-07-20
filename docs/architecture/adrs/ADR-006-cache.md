# ADR-006: Caché — React Query + memoria FastAPI

**Estado:** Aceptado | **Fecha:** 2026-06-13

## Decisión
- Frontend: TanStack React Query (`staleTime: 60s`)
- Backend: caché en memoria Excel TTL 300s (`EXCEL_CACHE_TTL_SECONDS`)

## Consecuencias
- Invalidación manual post-ETL en Fase 7
- Redis opcional en producción (Fase 11)
