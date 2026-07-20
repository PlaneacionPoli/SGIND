# ADR-009: Decisiones bloqueantes del Plan Maestro (Bloque 11.A/11.B)

**Estado:** Aceptado | **Fecha:** 2026-07-12
**Fuente:** [Plan Maestro de Implementación](../../plan_maestro_implementacion_sgind_v2.md) — historias B-01 y C-01

## Contexto

El Plan Maestro de cierre de brechas (Fase 11 — UAT/Validación) identificó dos decisiones de producto que bloqueaban el backlog:

- **B-01**: alcance no confirmado del Tablero Operativo Nivel 3 (Kanban/QC/Trazabilidad), presente en el legacy pero no enrutado en v2.
- **C-01**: si se porta la narrativa con IA generativa real (Claude) del legacy, o se mantienen las heurísticas de reglas ya implementadas en v2.

## Decisión B-01 — Tablero Operativo N3

**Migrar.** El Tablero Operativo N3 sigue en uso activo por el equipo operativo (Calidad/Procesos) y debe implementarse en SGIND-v2 con paridad funcional frente a `tablero_operativo.py` del legacy.

### Consecuencias
- Se activa la historia **B-02** (Alta prioridad, condicional → ahora confirmada): diseño e implementación del módulo Kanban/QC/Trazabilidad en Next.js/FastAPI.
- Estimación original del backlog: 80-120h (10-15 días). Esto **ajusta el cronograma de Fase 11**; se ejecuta como Sprint 6 (condicional) según §10 del Plan Maestro, o se replantea el orden de sprints si el volumen de trabajo lo amerita.
- Antes de implementar, se requiere una fase de exploración del módulo legacy (`tablero_operativo.py` y páginas asociadas) para levantar los requisitos funcionales exactos (columnas Kanban, criterios de QC, trazabilidad) — no se asume el diseño, se releva del código fuente existente.
- No bloquea el resto del Bloque 11.A/11.B, que puede cerrarse en paralelo.

## Decisión C-01 — IA generativa real (Claude)

**Integrar Claude real.** Se porta la integración con la API de Claude del legacy (`services/ai_analysis.py`) al backend de v2, reemplazando la narrativa puramente heurística de fichas CMI (Estratégico y Procesos) por narrativa generada por LLM cuando `ANTHROPIC_API_KEY` esté configurada, con el heurístico existente como fallback obligatorio.

### Consecuencias
- Se activa la historia **C-02** (Alta prioridad, condicional → ahora confirmada): integración en `narrativa_ia` / `generate_ficha_narrativa_heuristica`.
- Reutiliza la decisión previa de **ADR-007** (modelo `claude-haiku-4-5-20251001`, prompts existentes, fallback heurístico obligatorio) — este ADR confirma su implementación efectiva, que estaba pendiente.
- Costo operativo de API: a validar en Bloque 11.C con datos reales de volumen de fichas consultadas/mes antes de habilitar en producción sin límites; mientras tanto se implementa con manejo de errores que degrada a heurística ante fallo o cuota agotada (mismo patrón del legacy), evitando exposición a costos no controlados.
- No introduce cambios de esquema de datos obligatorios; ADR-007 ya contemplaba tabla `ai_prompts` opcional para versionado de prompts (fuera de alcance de este ciclo si no se requiere versionado inmediato).

## Referencias
- Backlog: B-01, B-02, C-01, C-02 en el Plan Maestro §4.
- ADR-007-ia.md (decisión previa de proveedor/modelo).
