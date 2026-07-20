# Fase 0 — Levantamiento y Auditoría del Sistema Actual

**Proyecto:** SGIND — Sistema de Gestión de Indicadores Institucionales  
**Institución:** Politécnico Grancolombiano  
**Fecha de auditoría:** 13 de junio de 2026  
**Estado:** Implementación completada (pendiente validación stakeholders)

## Entregables

| ID | Documento | Archivo |
|----|-----------|---------|
| E0.1 | Documento Funcional | [E0.1_DOCUMENTO_FUNCIONAL.md](./E0.1_DOCUMENTO_FUNCIONAL.md) |
| E0.2 | Documento Técnico | [E0.2_DOCUMENTO_TECNICO.md](./E0.2_DOCUMENTO_TECNICO.md) |
| E0.3 | Mapa de Procesos y Flujos | [E0.3_MAPA_PROCESOS.md](./E0.3_MAPA_PROCESOS.md) |
| E0.4 | Inventario de Componentes | [E0.4_INVENTARIO_COMPONENTES.md](./E0.4_INVENTARIO_COMPONENTES.md) |
| E0.5 | Catálogo de Fuentes de Datos | [E0.5_CATALOGO_FUENTES_DATOS.md](./E0.5_CATALOGO_FUENTES_DATOS.md) |
| E0.6 | Catálogo de Prompts IA | [E0.6_CATALOGO_PROMPTS_IA.md](./E0.6_CATALOGO_PROMPTS_IA.md) |
| E0.7 | Matriz de Tests | [E0.7_MATRIZ_TESTS.md](./E0.7_MATRIZ_TESTS.md) |
| E0.8 | Lista de Deuda Técnica | [E0.8_DEUDA_TECNICA.md](./E0.8_DEUDA_TECNICA.md) |

## Resumen ejecutivo de hallazgos

| Métrica | Plan | Real (verificado) |
|---------|------|-------------------|
| Líneas Python (áreas clave) | ~22,900 | **74,163** en 270 archivos auditados |
| Páginas activas en sidebar | 9 | **7** enrutadas |
| Páginas Beta | 2 | **3** fuera de sidebar + 2 marcadas en docs |
| Archivos Excel raw | 33 | **27** |
| Archivos Excel output | 15 | **8** (+ versiones en `.versiones/`) |
| Módulos ETL | 25 | **25** en `scripts/etl/` |
| Prompts IA | 3 | **3** en `services/ai_analysis.py` |
| Tests | 696 passing | **699/699 passing** (DT-04 corregido) |
| Roles RBAC | 3 | **No implementados** — solo whitelist de emails |

## Checklist de cierre

- [x] 9 páginas activas documentadas (incluye fuera de sidebar)
- [x] 2+ páginas Beta documentadas
- [x] 21 componentes documentados
- [x] ~75 funciones de `services/` documentadas
- [x] ~45 funciones de `core/` documentadas
- [x] 25 módulos ETL documentados
- [x] 3 prompts IA extraídos
- [x] 35 fuentes Excel mapeadas (27 raw + 8 output)
- [x] Flujos ETL y auth documentados
- [x] 699 tests inventariados, suite ejecutada
- [x] 20 dependencias producción documentadas
- [x] Deuda técnica priorizada
- [ ] Aprobación formal por stakeholders

## Cierre formal

**Estado:** ⏳ PENDIENTE APROBACIÓN  
**Fecha de cierre:** ___________  
**Aprobada por:** ___________
