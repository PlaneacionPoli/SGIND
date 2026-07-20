# ADR-003: Backend — FastAPI

**Estado:** Aceptado  
**Fecha:** 2026-06-13

## Decisión

FastAPI async + SQLAlchemy 2.0 + Pydantic v2 + asyncpg.

## Consecuencias

- OpenAPI automático en `/docs`
- Portar lógica de `core/` y `services/` de forma incremental
