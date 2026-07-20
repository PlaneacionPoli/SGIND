# ADR-001: Persistencia de Datos

**Estado:** Aceptado  
**Fecha:** 2026-06-13

## Contexto

SGIND actual usa Excel como fuente de verdad (~100K registros) y SQLite/PostgreSQL solo para registros OM y auth.

## Decisión

- **Excel**: fuente de verdad para indicadores (lectura read-only desde `SGIND_DATA_PATH`)
- **PostgreSQL**: OM, usuarios, roles, auditoría, configuración IA

## Alternativas

1. Migrar todo a PostgreSQL — rechazado (alto riesgo, Excel es fuente operativa)
2. Mantener SQLite — rechazado (no escala para multi-usuario concurrente)

## Consecuencias

- Backend necesita `ExcelReaderService` con caché TTL
- Parallel run: ambos sistemas leen los mismos Excel sin modificar el legacy
