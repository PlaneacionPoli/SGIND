# 07 - DECISIONES Y PROBLEMAS RESUELTOS

**Documento:** 07_Decisiones.md  
**Versión:** 2.0  
**Fecha:** 17 de junio de 2026 (actualizado FASE 3 auditoría)  
**Status:** ✅ Consolidado MDV

---

## 1. Problemas Resueltos

### 1.1 Problema 1: Duplicación de Funciones

**Descripción:** `preparar_pdi_con_cierre()` y `preparar_cna_con_cierre()` eran casi idénticas, violando DRY.

**Impacto:** +65 líneas de código duplicado, difícil mantenimiento.

**Solución:** Extraer lógica común a `_preparar_indicadores_con_cierre()` parametrizada.

```python
# ANTES: 65+65 líneas duplicadas
def preparar_pdi_con_cierre():
    # casi idéntico a preparar_cna_con_cierre
    ...

def preparar_cna_con_cierre():
    # casi idéntico a preparar_pdi_con_cierre
    ...

# DESPUÉS: 70+10+10 líneas
def _preparar_indicadores_con_cierre(flag_col, catalog_fn, merge_cols):
    # lógica genérica
    ...

def preparar_pdi_con_cierre():
    return _preparar_indicadores_con_cierre(
        flag_col="FlagPlanEstrategico",
        catalog_fn=load_pdi_catalog,
        merge_cols=["Linea", "Objetivo"]
    )

def preparar_cna_con_cierre():
    return _preparar_indicadores_con_cierre(
        flag_col="FlagCNA",
        catalog_fn=load_cna_catalog,
        merge_cols=["Factor", "Caracteristica"]
    )
```

**Resultado:** Reducción 85%, código mantenible.

**Archivo:** [`services/strategic_indicators.py`](../../services/strategic_indicators.py)

---

### 1.2 Problema 2: Casos Especiales de Cumplimiento

**Descripción:** Indicadores con Meta=0 o casos negativos requerían lógica especial.

**Casos identificados:**
1. Meta=0 AND Ejec=0 → cumplimiento = 1.0
2. Indicador negativo AND Ejec=0 → cumplimiento = 1.0
3. Indicador sin datos → "Sin dato"

**Solución:** Centralizar en `core/semantica.py` con función dedicada.

```python
def categorizar_cumplimiento(cumplimiento, id_indicador=None):
    # Detectar tipo de indicador (Plan Anual vs Negativo-Porcentual vs Regular)
    # Aplicar lógica especial si aplica
    # Calcular categoría final
    return categoria
```

**Archivo:** [`core/semantica.py`](../../core/semantica.py)

**Actualización (jul-2026):** se agregó un tercer régimen, **Negativo-Porcentual**
(`IDS_NEGATIVO_PCT` en `core/config.py`, lista curada: `121, 207, 377, 561`), con
umbrales < 102% Cumplimiento | 102-110% Alerta | > 110% Peligro. Precedencia:
Plan Anual > Negativo-Porcentual > Regular. Detalle completo en
[`02_Logica_Indicadores.md`](02_Logica_Indicadores.md).

---

## 2. Decisiones Arquitectónicas (Con Issue Tracking)

### 2.1 Decisión ARQ-001: Sin Redis Cloud

| Componente | Valor |
|-----------|-------|
| **ID** | `ARQ-001` |
| **Área** | Infraestructura / Caché |
| **Decisión** | NO implementar Redis Cloud |
| **Razón** | Sin presupuesto de inversión |
| **Alternativa** | Caché local en memoria con TTL configurable |
| **GitHub Issue** | [#INFRA-047](https://github.com/orgs/mi-org/issues/INFRA-047) |
| **Status** | ✅ Implementado |
| **Fecha Decisión** | 2026-03-15 |
| **Implementado** | 2026-04-01 |
| **Impacto** | Bajo - Uso internal only |

**Implementación:**
```python
# core/config.py
CACHE_TTL = 300  # 5 minutos
CACHE_BACKEND = "memory"  # No Redis
```

**Tracking:**
- [x] Decisión tomada por PO
- [x] Aprobación Arquitectura
- [x] Implementación completada
- [x] Tests: 3/3 passing
- [ ] Monitoreo en producción

---

### 2.2 Decisión ARQ-002: Hoja Principal Semestral

| Componente | Valor |
|-----------|-------|
| **ID** | `ARQ-002` |
| **Área** | Modelo Datos |
| **Decisión** | Usar "Consolidado Semestral" como hoja principal |
| **Excepciones** | Gestión OM usa "Consolidado Historico" |
| **Razón** | Separación de concerns, optimización de lectura |
| **GitHub Issue** | [#DATA-023](https://github.com/orgs/mi-org/issues/DATA-023) |
| **Status** | ✅ Implementado |
| **Fecha Decisión** | 2026-03-10 |
| **Impacto** | Medio - Todas las páginas excepto OM |

**Tracking:**
- [x] Decisión tomada
- [x] Integración en ETL
- [x] Validación en servicios
- [x] Tests: 28/28 passing
- [ ] Documentación en 03_Modelo_Datos.md (EN PROGRESO)

---

### 2.3 Decisión ARQ-003: Excel como Persistencia Primaria

| Componente | Valor |
|-----------|-------|
| **ID** | `ARQ-003` |
| **Área** | Persistencia |
| **Decisión** | Usar Excel (.xlsx) como formato principal |
| **Alternativa Futura** | PostgreSQL para producción (Fase 4+) |
| **Razón** | Auditorías manuales, transparencia, facilita migración |
| **GitHub Issue** | [#DB-015](https://github.com/orgs/mi-org/issues/DB-015) |
| **Status** | ✅ Implementado |
| **Fecha Decisión** | 2026-02-20 |
| **Impacto** | Alto - Core del sistema |

**Tracking:**
- [x] Decisión tomada
- [x] Implementación (generar_reporte.py, actualizar_consolidado.py)
- [x] Tests: 15/15 passing
- [ ] PostgreSQL migration plan (Fase 4 - Estimado Julio 2026)

---

### 2.4 Decisión ARQ-004: Granularidad en Datos, Agrupación en UI (CMI Estratégico)

| Componente | Valor |
|-----------|-------|
| **ID** | `ARQ-004` |
| **Área** | CMI Estratégico / Frontend |
| **Problema** | Replicación visual de indicadores en pestaña por Línea/Meta |
| **Decisión** | Mantener granularidad en datos ← → Agrupar solo en UI |
| **Razón** | Evitar pérdida de detalle histórico en catálogo |
| **GitHub Issue** | [#CMI-089](https://github.com/orgs/mi-org/issues/CMI-089) |
| **Status** | ✅ Implementado |
| **Fecha Decisión** | 2026-04-05 |
| **Implementado** | 2026-04-18 |
| **Impacto** | Medio - Solo UI CMI |

**Archivos relacionados:**
- [`streamlit_app/components/cmi_tabs/tab_lineas.py`](../../streamlit_app/components/cmi_tabs/tab_lineas.py)
- [`streamlit_app/components/cmi_tabs/tab_alertas.py`](../../streamlit_app/components/cmi_tabs/tab_alertas.py)
- [`services/ai_analysis.py`](../../services/ai_analysis.py)

**Tracking:**
- [x] Decisión tomada por PO + Arquitecto
- [x] Aprobación de cambios
- [x] Implementación completada
- [x] Tests: 9/9 passing
- [x] QA validation
- [ ] Deploy a producción (Estimado Junio)

---

### 2.5 Decisión ARQ-005: Plan Anual Dinámico (NO Hardcoded)

| Componente | Valor |
|-----------|-------|
| **ID** | `ARQ-005` |
| **Área** | Configuración / Indicadores |
| **Decisión** | Cargar IDs Plan Anual dinámicamente desde Excel |
| **Razón** | Permite cambios sin redeploy, trazabilidad |
| **GitHub Issue** | [#CONFIG-067](https://github.com/orgs/mi-org/issues/CONFIG-067) |
| **Status** | ✅ Implementado |
| **Fecha Decisión** | 2026-04-20 |
| **Implementado** | 2026-04-22 |
| **Impacto** | Alto - Lógica de categorización |

**Tracking:**
- [x] Decisión tomada
- [x] Implementación (core/config.py)
- [x] Tests: 20/20 passing
- [x] AGENT 3 audit completado
- [x] AGENT 4 documentation updated

---

## 3. Matriz de Impacto y Tracking de Decisiones

### 3.1 Resumen de Decisiones

| ID | Área | Decisión | Status | Impacto | GitHub | Tests | Fecha |
|----|----|----------|--------|---------|--------|-------|-------|
| **ARQ-001** | Caché | Sin Redis Cloud | ✅ Implementado | Bajo | #INFRA-047 | 3/3 | 2026-04-01 |
| **ARQ-002** | Datos | Semestral principal | ✅ Implementado | Medio | #DATA-023 | 28/28 | 2026-04-10 |
| **ARQ-003** | Persistencia | Excel primario | ✅ Implementado | Alto | #DB-015 | 15/15 | 2026-04-15 |
| **ARQ-004** | UI/CMI | Granularidad datos | ✅ Implementado | Medio | #CMI-089 | 9/9 | 2026-04-18 |
| **ARQ-005** | Config | Plan Anual dinámico | ✅ Implementado | Alto | #CONFIG-067 | 20/20 | 2026-04-22 |

### 3.2 Matriz de Impacto (por módulo)

| Módulo | ARQ-001 | ARQ-002 | ARQ-003 | ARQ-004 | ARQ-005 | Impacto Total |
|--------|---------|---------|---------|---------|---------|---------------|
| core/ | - | ✅ | ✅ | - | ✅ | ALTO |
| services/ | ✅ | ✅ | ✅ | ✅ | ✅ | CRÍTICO |
| scripts/ | - | ✅ | ✅ | - | ✅ | ALTO |
| streamlit_app/ | - | ✅ | - | ✅ | - | MEDIO |

### 3.3 Timeline de Implementación

```
┌─────────────────────────────────────────────────────────────┐
│                    2026 DECISIONES TIMELINE                 │
├─────────────────────────────────────────────────────────────┤
│ Febrero 2026                                                │
│   └─ ARQ-003: Excel Persistencia (Decisión)                │
│                                                             │
│ Marzo 2026                                                  │
│   ├─ ARQ-001: Sin Redis Cloud (Decisión)                   │
│   └─ ARQ-002: Semestral Principal (Decisión)               │
│                                                             │
│ Abril 2026 🔄 IMPLEMENTACIÓN COMPLETADA                    │
│   ├─ ARQ-001: ✅ Implementado (04-01)                      │
│   ├─ ARQ-002: ✅ Implementado (04-10)                      │
│   ├─ ARQ-003: ✅ Implementado (04-15)                      │
│   ├─ ARQ-004: ✅ Implementado (04-18)                      │
│   └─ ARQ-005: ✅ Implementado (04-22)                      │
│                                                             │
│ Mayo 2026 🟡 VALIDACIÓN EN PRODUCCIÓN                      │
│   ├─ ARQ-001: Monitoreo caché (Estimado 05-20)            │
│   ├─ ARQ-002: Validación datos (Estimado 05-15)           │
│   ├─ ARQ-003: Auditoría Excel (En progreso)               │
│   ├─ ARQ-004: QA CMI (Estimado 05-25)                     │
│   └─ ARQ-005: Plan Anual en BD (Estimado 05-30)           │
│                                                             │
│ Junio 2026 🚀 PRODUCCIÓN                                    │
│   └─ Deploy todas las decisiones                           │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 Lecciones de Decisiones Anteriores

**Decisión: Problema 1 - Refactorización DRY**

- **ID:** DEC-P1-001
- **Resultado:** Reducción de 85% código duplicado
- **Lección:** Parametrización es más mantenible que duplicación
- **Archivo:** [`services/strategic_indicators.py`](../../services/strategic_indicators.py)

**Decisión: Problema 2 - Casos Especiales Cumplimiento**

- **ID:** DEC-P2-001
- **Resultado:** Centralización en `core/semantica.py`
- **Lección:** Single Source of Truth previene divergencias
- **Archivo:** [`core/semantica.py`](../../core/semantica.py)

---

## 5. Governance de Documentación

### 5.1 Principios

1. **Single Source of Truth (SSOT):** Toda docs en `/docs/`
2. **KISS:** Cada documento = un solo propósito
3. **Documentación Viva:** Sincronizada con código
4. **Sin "Por si acaso":** No conservar docs obsoletos

### 5.2 Reducción MDV

| Métrica | Antes | Después | Reducción |
|---------|-------|---------|-----------|
| Documentos | 81 | 7 | **91%** |
| Carpetas | 16 | 2 (core, sql) | 87% |

**Target logrado:** 5-7 documentos finales en `docs/core/`

---

## 6. Lecciones Aprendidas

### 6.1 DRY Violations

**Pattern identificado:** Cuando 2+ funciones difieren solo en:
- Filter conditions
- Resource loaders
- Merge column names

**Solución genérica:** Extraer como parámetros.

### 6.2 Enum Comparisons

**Problema común:** Comparar enums directamente con strings.

**Solución:** Usar `.value` en comparaciones.

```python
# INCORRECTO
assert cat == CategoriaCumplimiento.PELIGRO

# CORRECTO
assert cat == CategoriaCumplimiento.PELIGRO.value
```

### 6.3 Testing Strategy

**Approach:** Tests unitarios por suite, fixtures centralizadas.

**Validación:** Sin regresiones en APIs públicas.

---

---

## 8. Hallazgos SOLID — Auditoría FASE 3 (jun-2026)

### 8.1 Violaciones Detectadas

#### SRP — Single Responsibility Principle
| Módulo | Violación | Severidad | Acción |
|---|---|---|---|
| `services/data_loader.py` | Mezcla `@st.cache_data` (infraestructura Streamlit) con lógica de carga ETL | Media | Extraer lógica pura en `services/loaders/data_access.py`; mantener wrapper Streamlit delgado |
| `core/calculos.py` | `generar_recomendaciones()` genera texto editorial junto a cálculos numéricos | Baja | Aceptable por su tamaño (~40 líneas); documentado como deuda técnica menor |

#### DRY — Don't Repeat Yourself
| Duplicación | Archivos | Decisión |
|---|---|---|
| `COL_ALIASES` | `scripts/etl/normalizacion.py` vs `scripts/consolidation/core/constants.py` | **Aceptada** — subpaquetes independientes. Agregar comentario cross-reference en ambos archivos |
| `MESES_ES` | `scripts/etl/normalizacion.py`, `scripts/consolidation/core/constants.py`, `core/config.py` | **Aceptada** — misma razón. Documentado |

#### DIP — Dependency Inversion Principle
| Módulo | Violación | Impacto | Acción |
|---|---|---|---|
| `services/data_loader.py` | Dependencia directa de `@st.cache_data` en funciones públicas | Coverage solo 23% — no testeable sin Streamlit | Deuda técnica registrada en ARQ-006 abajo |

#### OCP — Open/Closed Principle
| Módulo | Situación |
|---|---|
| `core/config.py:IDS_PLAN_ANUAL` | ✅ BIEN — carga dinámica desde Excel, extensible sin modificar código |
| `scripts/consolidation/core/rules_engine.py:evaluar_regla()` | 🟡 Leve — agregar nuevo TipoRegla requiere editar el switch. Impacto bajo mientras el motor no esté activo |

### 8.2 Nuevas Decisiones ARQ

#### ARQ-006: Deuda Técnica — data_loader.py sin separar capa Streamlit

| Componente | Valor |
|---|---|
| **ID** | `ARQ-006` |
| **Área** | Servicios / Testing |
| **Problema** | `services/data_loader.py` tiene 23% coverage porque `@st.cache_data` no es testeable sin Streamlit corriendo |
| **Decisión actual** | Mantener estado actual — refactorizar en SGIND v2 (FastAPI no tiene esta restricción) |
| **Acción diferida** | Extraer lógica pura a `services/loaders/data_access.py` en siguiente sprint de Streamlit |
| **Status** | 🟡 Deuda técnica registrada |
| **Fecha** | 2026-06-17 |

#### ARQ-007: COL_ALIASES — Duplicación Aceptada por Contexto

| Componente | Valor |
|---|---|
| **ID** | `ARQ-007` |
| **Área** | ETL / Consolidación |
| **Decisión** | `COL_ALIASES` duplicado en `scripts/etl/normalizacion.py` y `scripts/consolidation/core/constants.py` es **intencional** |
| **Razón** | Los módulos son subpaquetes independientes. Unificarlos crearía dependencia circular o requeriría un tercer módulo compartido sin valor arquitectónico claro |
| **Condición de revisión** | Si los mapeos divergen en > 3 entradas, crear `core/etl_constants.py` como fuente única |
| **Status** | ✅ Decisión tomada |
| **Fecha** | 2026-06-17 |

### 8.3 Patrones de Diseño — Estado Actual

| Patrón | Módulo | Estado |
|---|---|---|
| **Strategy** | `scripts/etl/extraccion.py` — extracción por variables/series/directo | 🟡 Implícito, no formalizado con interfaz |
| **Repository** | `core/db/operations.py` | ✅ Implementado |
| **Factory** | `scripts/etl/builders.py` — constructores de registros Excel | 🟡 Implícito |
| **Observer** | `scripts/etl/notifications.py` | ✅ Implementado |
| **Facade** | `core/semantica.py` — re-exporta `core/domain` | ✅ Correcto uso |
| **Pipeline** | `services/loaders/pipeline.py` — 5 fases ETL | ✅ Bien estructurado |

---

## 9. Decisiones FASE 7 — Modularización (jun-2026)

### ARQ-008: Shim en `streamlit_app/services/` — Patrón Aceptado

| Componente | Valor |
|---|---|
| **ID** | `ARQ-008` |
| **Área** | Estructura de módulos / Streamlit |
| **Decisión** | `streamlit_app/services/strategic_indicators.py` es un shim deliberado que re-exporta desde `services.strategic_indicators` canónico |
| **Razón** | Streamlit resuelve imports relativos al CWD del `app.py`; el shim evita errores de path sin duplicar lógica |
| **Condición de revisión** | Eliminar el shim cuando `app.py` migre a `streamlit_app/` o se use SGIND v2 |
| **Status** | ✅ Aceptado — no requiere acción |
| **Fecha** | 2026-06-17 |

**Estructura del shim:**
```python
# streamlit_app/services/strategic_indicators.py
from services.strategic_indicators import *  # re-export limpio, 0 lógica propia
```

---

### ARQ-009: `utils/` Raíz — Directorio Vestigial

| Componente | Valor |
|---|---|
| **ID** | `ARQ-009` |
| **Área** | Estructura de módulos |
| **Decisión** | El directorio `utils/` en la raíz contiene solo `__init__.py`. No consolidar con `streamlit_app/utils/` |
| **Razón** | `streamlit_app/utils/formatting.py` es formateo de presentación UI (no ETL). `scripts/etl/normalizacion.py` es normalización de datos. Contextos distintos, unificarlos crearía dependencia incorrecta |
| **Acción** | `utils/` raíz puede eliminarse en siguiente limpieza de FASE 1; `__init__.py` no tiene importadores activos |
| **Status** | 🟡 Pendiente limpieza menor |
| **Fecha** | 2026-06-17 |

---

## 10. Decisiones FASE 8 — CI/CD (jun-2026)

### ARQ-010: Coverage Gate en CI — Umbral 50%

| Componente | Valor |
|---|---|
| **ID** | `ARQ-010` |
| **Área** | CI/CD / Calidad |
| **Decisión** | Agregar `--cov-fail-under=50` al workflow `test.yml` y extender cobertura a `scripts/` |
| **Razón** | Sin `--cov-fail-under`, el CI nunca rechazaba PRs por pérdida de cobertura. El 50% refleja el estado actual (903 tests) y actúa como piso, no como meta |
| **Meta futura** | Subir a `--cov-fail-under=70` al completar tests de `escritura.py`, `fuentes.py`, `purga.py` |
| **Status** | ✅ Implementado en `.github/workflows/test.yml` |
| **Fecha** | 2026-06-17 |

**Cambio aplicado:**
```yaml
# .github/workflows/test.yml — antes
pytest tests/ --cov=core --cov=services --cov=streamlit_app ...

# después
pytest tests/ --cov=core --cov=services --cov=streamlit_app --cov=scripts \
  --cov-fail-under=50 ...
```

---

### ARQ-011: `deploy-staging.yml` — Corrección de Plataforma

| Componente | Valor |
|---|---|
| **ID** | `ARQ-011` |
| **Área** | CI/CD / Deploy |
| **Problema** | `deploy-staging.yml` referenciaba Render.com (`RENDER_DEPLOY_HOOK_URL`) pero la producción real está en **Streamlit Community Cloud** |
| **Decisión** | Corregir comentarios; renombrar secret a `STAGING_DEPLOY_HOOK_URL`; Streamlit Cloud deploya automáticamente desde `main` via GitHub integration sin webhook explícito |
| **Situación staging** | No existe entorno staging dedicado actualmente. El workflow es un placeholder para cuando se configure uno |
| **Status** | ✅ Corregido en `.github/workflows/deploy-staging.yml` |
| **Fecha** | 2026-06-17 |

---

### ARQ-012: `main_indicadores.yml` — Workflow Azure Obsoleto

| Componente | Valor |
|---|---|
| **ID** | `ARQ-012` |
| **Área** | CI/CD / Deploy |
| **Situación** | `.github/workflows/main_indicadores.yml` despliega en Azure Web App con Python 3.14. La app de producción es Streamlit Community Cloud, no Azure |
| **Decisión** | El workflow Azure puede ser de una prueba piloto anterior. Mantener desactivado (no tiene trigger automático activo) hasta confirmar si Azure Web App es un destino de deploy válido |
| **Acción** | Confirmar con el equipo si el deploy Azure sigue activo; si no, eliminar el workflow en siguiente limpieza |
| **Status** | 🟡 Pendiente confirmación |
| **Fecha** | 2026-06-17 |

---

### 10.1 Tabla Consolidada CI/CD

| Workflow | Trigger | Estado | Gap identificado |
|---|---|---|---|
| `test.yml` | push/PR a main, develop | ✅ Activo | Corregido: `--cov-fail-under=50` + `--cov=scripts` agregado |
| `lint.yml` | push/PR a main, develop | ⚠️ No bloqueante | Todos los steps tienen `continue-on-error: true` |
| `deploy-staging.yml` | push a develop | ⚠️ Placeholder | No hay staging real; Render→Streamlit Cloud corregido |
| `pipeline_automatico.yml` | cron día 5/mes 06:00 UTC | ✅ Bien diseñado | Requiere `ANTHROPIC_API_KEY` secret en GitHub |
| `main_indicadores.yml` | push a main | 🟡 Dudoso | Despliega Azure; posiblemente obsoleto |
| `docker-publish.yml` | push a main + tags | ✅ Activo | Para SGIND v2 container |

---

## 7. Referencias

- **Problemas resueltos:** [`08-PROBLEMAS-RESUELTOS/`](../../08-PROBLEMAS-RESUELTOS/)
- **Governance:** [`GOVERNANCE.md`](../../GOVERNANCE.md)
- **Decisiones:** [`DECISION_PROBLEMA_1_OPCION_A_MEJORADA.md`](../../08-PROBLEMAS-RESUELTOS/DECISION_PROBLEMA_1_OPCION_A_MEJORADA.md)
