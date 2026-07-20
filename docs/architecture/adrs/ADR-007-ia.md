# ADR-007: IA — Claude API

**Estado:** Aceptado | **Fecha:** 2026-06-13

## Decisión
- Proveedor: Anthropic Claude
- Modelo UI: `claude-haiku-4-5-20251001`
- 3 prompts existentes migrados literalmente (ver E0.6)
- Fallbacks heurísticos obligatorios cuando API no disponible

## Consecuencias
- Tabla `ai_prompts` en PostgreSQL para versionado
- Rate limiting en Fase 8
