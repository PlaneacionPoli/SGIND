# ADR-007: IA — Claude API

**Estado:** Aceptado | **Fecha:** 2026-06-13

> **Nota de vigencia (2026-09-20, Oleada 1):** esta decisión quedó
> **desactualizada por un cambio posterior no documentado en un nuevo
> ADR**. El código real (`backend/app/core/config.py:39-43`,
> `requirements.txt`) usa `google-genai` (Gemini), no Anthropic Claude — el
> propio comentario del código dice "Reemplaza a Anthropic Claude (de
> pago) por decisión de producto". Ver G-20 en
> `docs/tecnico/09-gaps-y-riesgos.md`. Este documento se conserva como
> registro histórico de la decisión original; para el estado real de la
> integración de IA, ver `docs/tecnico/01-arquitectura.md`. Pendiente:
> crear un ADR-010 que documente formalmente el cambio a Gemini.

## Decisión
- Proveedor: Anthropic Claude
- Modelo UI: `claude-haiku-4-5-20251001`
- 3 prompts existentes migrados literalmente (ver E0.6)
- Fallbacks heurísticos obligatorios cuando API no disponible

## Consecuencias
- Tabla `ai_prompts` en PostgreSQL para versionado
- Rate limiting en Fase 8
