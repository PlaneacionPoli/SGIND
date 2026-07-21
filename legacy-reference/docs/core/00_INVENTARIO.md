# 00 - INVENTARIO DEL PROYECTO SGIND

**Documento:** 00_INVENTARIO.md  
**Versión:** 1.0  
**Fecha:** 17 de junio de 2026  
**Mantenido por:** Auditoría FASE 1

---

## Estructura General

El proyecto tiene **dos versiones coexistentes**:

| Versión | Estado | Stack | Punto de entrada |
|---|---|---|---|
| **Streamlit** | Producción | Python 3.14 + Streamlit + Pandas | `app.py` / `streamlit_app/main.py` |
| **SGIND v2** | Migración (Fases 0–4) | Next.js 14 + FastAPI + PostgreSQL | `sgind-v2/` |

---

## VERSIÓN STREAMLIT — Mapa de Archivos

### Punto de Entrada
| Archivo | Rol |
|---|---|
| `app.py` | Entrada raíz Streamlit (redirect a `streamlit_app/main.py`) |
| `streamlit_app/main.py` | Punto de entrada principal de la aplicación |
| `config.py` | Re-export de `core/config.py` para imports legacy — **no eliminar mientras `streamlit_app/app.py` lo importe** |

### Capa Dominio (`core/`)
| Archivo | Rol | Estado |
|---|---|---|
| `core/calculos.py` | KPIs, tendencia, recomendaciones, wrapper de categorización | ✅ Activo |
| `core/config.py` | Fuente única de umbrales, IDs_Plan_Anual, rutas | ✅ Canónico |
| `core/semantica.py` | Fachada legacy — re-exporta `core/domain` | 🟡 Legacy (mantener como fachada) |
| `core/proceso_types.py` | Tipos de proceso | ✅ Activo |
| `core/db_manager.py` | Persistencia OM dual SQLite/PostgreSQL | ✅ Activo |
| `core/domain/categorization.py` | **CATEGORIZACIÓN OFICIAL** — `categorizar_cumplimiento()` | ✅ Canónico |
| `core/domain/health_metrics.py` | **RECÁLCULO OFICIAL** — `recalcular_cumplimiento_faltante()` | ✅ Canónico |
| `core/domain/normalization.py` | Normalización de cumplimiento | ✅ Activo |
| `core/domain/__init__.py` | Re-exports de `core/domain` | ✅ Activo |
| `core/db/connection_manager.py` | Gestión de conexiones DB | ✅ Activo |
| `core/db/operations.py` | Operaciones CRUD | ✅ Activo |
| `core/db/schema_manager.py` | Gestión de esquemas | ✅ Activo |
| `core/db/data_normalizer.py` | Normalización de datos DB | ✅ Activo |
| `core/db/config_provider.py` | Configuración de base de datos | ✅ Activo |
| `core/modelo_datos/modelo.py` | Modelo de datos | ✅ Activo |
| `core/presentation/visual_mapping.py` | Mapeo visual | ✅ Activo |

### ETL Pipeline (`scripts/etl/`)
| Archivo | Rol |
|---|---|
| `cumplimiento.py` | **Cálculo de cumplimiento puro** — `calcular_cumplimiento()` |
| `extraccion.py` | Extracción de Meta/Ejecución desde API Kawak (variables/series/directo) |
| `formulas_excel.py` | Materialización de fórmulas Excel (col L/M) |
| `builders.py` | Constructores de registros para hojas Excel |
| `normalizacion.py` | Utilidades puras de normalización, `COL_ALIASES`, `make_llave()` |
| `signos.py` | Manejo de signos de indicadores |
| `fuentes.py` | Carga de fuentes consolidadas |
| `catalogo.py` | Catálogo de indicadores |
| `escritura.py` | Escritura en Excel |
| `purga.py` | Purga de registros |
| `periodos.py` | Manejo de períodos temporales |
| `no_aplica.py` | Lógica de "No Aplica" |
| `validacion_historica.py` | Validación de datos históricos |
| `validation_gate.py` | Puerta de validación del pipeline |
| `versioning.py` | Control de versiones de datos |
| `retry_handler.py` | Manejo de reintentos |
| `pipeline_metrics.py` | Métricas del pipeline |
| `notifications.py` | Notificaciones (SMTP/Slack) — pendiente tests de integración |
| `audit.py` | Auditoría del ETL |
| `config.py` | Configuración del ETL (lee `config/settings.toml`) |

### Scripts de Orquestación (`scripts/`)
| Archivo | Rol |
|---|---|
| `run_pipeline.py` | **Orquestador principal** — 3 pasos |
| `consolidar_api.py` | Paso 1: Consolida Kawak + API → Excel |
| `actualizar_consolidado.py` | Paso 2: Motor ETL principal |
| `generar_reporte.py` | Paso 3: Genera JSON/CSV de resumen |
| `run_consolidation.py` | Corredor del módulo de consolidación |
| `integrate_consolidado.py` | Integración del consolidado |
| `ingesta_plantillas.py` | Ingesta de plantillas Excel |
| `start_streamlit.py` | Lanzador de Streamlit |
| `backup_sqlite.py` | Backup de SQLite |
| `agent_runner.py` | Framework multi-agente de auditoría |
| `agent1_data_source_audit.py` … `agent9_code_quality.py` | 9 agentes de auditoría |

### Scripts de Diagnóstico (`scripts/diagnostics/`) ← *movidos en FASE 1*
| Archivo | Rol |
|---|---|
| `analyze_cmi_data.py` | Análisis de datos CMI |
| `check_ficha.py`, `check_indicators.py`, `check_indicators2.py`, `check_subindicadores.py` | Verificación de fichas e indicadores |
| `diagnose_duplicate_columns.py` | Diagnóstico de columnas duplicadas |
| `inspect_consolidado_cierre.py`, `list_all_ids_consolidado.py`, `load_consolidado_cierres.py` | Inspección del consolidado |
| `risk.py` | Generación de hoja Excel de riesgos |
| `verify_final_proyectos.py`, `verify_updated_data.py` | Verificación de datos de proyectos |

### Módulo de Consolidación (`scripts/consolidation/`)
| Archivo | Rol |
|---|---|
| `core/constants.py` | Constantes centralizadas (rutas, `AÑO_CIERRE_ACTUAL`, aliases de columnas) |
| `core/rules_engine.py` | Motor de reglas/alertas — **NO activo en prod**, activación prevista Junio 2026 |
| Demás módulos | Extracción, modelos, orquestación, métricas paralelas, utils |

### Módulo Analytics (`scripts/analytics/`)
| Archivo | Rol |
|---|---|
| `predictor.py` | Predicciones (MAE, RMSE, MAPE, R2) — **vacío tecnológico: no integrado en dashboard** |
| `data_preparator.py` | Preparación de datos para modelos predictivos |

### Servicios (`services/`)
| Archivo/Módulo | Rol |
|---|---|
| `data_loader.py` | Wrapper caché Streamlit sobre pipeline ETL |
| `procesos.py` | Servicio de procesos |
| `cmi_filters/` | Filtros CMI (filters.py, loaders.py, utils.py) |
| `strategic_indicators/` | Indicadores PDI/CNA (loaders.py, processors.py, utils.py) |
| `ficha_pdf/` | Generación PDF fichas técnicas (builder.py, charts.py, utils.py) |
| `caching_strategy/` | Estrategia de caché (base.py, implementations.py) |
| `loaders/pipeline.py` | Pipeline ETL de 5 fases para carga en Streamlit |

### Páginas Streamlit (`streamlit_app/pages/`)
18 páginas: `resumen_general`, `cmi_estrategico`, `cmi_por_procesos_resumen`, `diagnostico`, `gestion_om`, `informe_por_procesos`, `pdi_acreditacion`, `plan_mejoramiento`, `resumen_por_proceso`, `seguimiento_reportes`, `tablero_operativo` — más sus variantes `_config` y `_utils`.

### Tests (`tests/`)
56 archivos de tests. Coverage actual: **50%**. Meta: **80%**.

Módulos cubiertos en Sprint Pending (jun-2026):
- `scripts/etl/builders.py` → 88%
- `services/ficha_pdf/utils.py` → 100%
- `scripts/etl/fuentes.py` → 32%, `purga.py` → 30%, `escritura.py` → 29%

Módulos aún con baja cobertura (próximos sprints):
- `scripts/etl/escritura.py` (funciones openpyxl complejas)
- `scripts/etl/pipeline_metrics.py` (0%)
- `scripts/etl/workbook_io.py` (0%)
- `services/ficha_pdf/builder.py` (13% — requiere reportlab)
- `services/data_loader.py` (23% — DIP issue ARQ-006)

---

## VERSIÓN SGIND v2 — Mapa de Archivos

### Backend FastAPI (`sgind-v2/backend/app/`)
| Módulo | Rol |
|---|---|
| `domain/calculos.py` | Fase 5 completa: `aplicar_calculos_cumplimiento()` |
| `domain/categorization.py` | Categorización — portado de `core/domain/categorization.py` |
| `domain/health_metrics.py` | Recálculo faltante — portado de `core/domain/health_metrics.py` |
| `domain/constants.py` | Constantes de rangos de cumplimiento |
| `domain/cmi_builders.py` … `seguimiento_builders.py` | 11 builders de dominio |
| `services/etl_pipeline.py` | Pipeline ETL portado (mismas 5 fases) |
| `services/indicator_service.py` | Servicio REST de indicadores |
| `services/cmi_service.py` | Servicio CMI |
| `services/om_service.py` | Servicio Gestión OM |
| `core/config.py` | Configuración FastAPI |
| `core/database.py` | Conexión a PostgreSQL async |
| `core/security.py` | Autenticación MSAL |
| `core/ttl_cache.py` | Caché TTL local |

### Frontend Next.js (`sgind-v2/frontend/src/`)
| Módulo | Rol |
|---|---|
| `lib/api.ts` | Cliente HTTP central |
| `lib/types.ts` | Tipos TypeScript |
| `lib/utils.ts` | Utilidades frontend |
| `stores/auth-store.ts` | Estado global Zustand |
| `components/cmi/cmiChartColors.ts` | Colores de gráficos CMI |
| `components/` | ~65 componentes — algunos solo esqueleto |

---

## Documentación Activa (`docs/core/`)

| Documento | Estado | Última revisión |
|---|---|---|
| `00_INVENTARIO.md` | ✅ Activo | 17-jun-2026 |
| `01_Arquitectura.md` | ✅ Activo | abr-2026 |
| `02_Logica_Indicadores.md` | ✅ Actualizado v2.0 (FASE 2+3) | jun-2026 |
| `03_Modelo_Datos.md` | ✅ Activo | abr-2026 |
| `04_Dashboard.md` | ✅ Activo | abr-2026 |
| `05_Operativo.md` | ✅ Activo | abr-2026 |
| `06_Testing_Calidad.md` | ✅ Actualizado v2.1 (FASE 4 + Sprint Pending) | jun-2026 |
| `07_Decisiones.md` | ✅ Actualizado v3.0 (FASE 7+8 — ARQ-008 a ARQ-012) | jun-2026 |
| `08_Fuentes_Datos.md` | ✅ Nuevo (FASE 5) | jun-2026 |
| `09_ETL_Pipeline.md` | ✅ Nuevo (FASE 5) | jun-2026 |
| `10_Migracion_SGIND_v2.md` | ✅ Nuevo (FASE 5) | jun-2026 |
| `11_CICD_Automatizacion.md` | ✅ Nuevo (FASE 8) | jun-2026 |

### Archivados (`docs/archive/sessions/`) ← *22 archivos archivados en FASE 1*
Reportes de sesión de agentes (AGENT5*, AGENT9*, CHANGELOG_SESION*, etc.)

---

## Configuración Central

| Archivo | Contenido clave |
|---|---|
| `config/settings.toml` | `año_cierre=2025`, IDs Plan Anual, IDs Tope 100%, rutas, cron schedule |
| `core/config.py` | Umbrales de semaforización (Regular/PA/Negativo-Porcentual), `IDS_TOPE_100`, `IDS_NEGATIVO_PCT` (lista curada jul-2026, ver `02_Logica_Indicadores.md`) |
| `config/data_contracts.yaml` | Contratos de datos |
| `config/mapeos_procesos.yaml` | Mapeo de procesos |
| `.env.example` | `DATABASE_URL` para PostgreSQL (Supabase) |
| `.env.template` | SMTP, Slack Webhook, `ENVIRONMENT` |

---

## Vacíos Tecnológicos — FASE 6

### VAC-001 — Predictor no integrado en ningún dashboard

| Campo | Detalle |
|-------|---------|
| **Archivo** | `scripts/analytics/predictor.py` (+ `data_preparator.py`) |
| **Qué hace** | Predicción de cumplimiento proyectado (MAE, RMSE, MAPE, R2), simulación de escenarios, recomendaciones automáticas |
| **Estado** | Código completo y funcional. **No está importado en ninguna página Streamlit ni en SGIND v2** |
| **Evidencia** | Grep confirma 0 importaciones desde `streamlit_app/pages/`, 0 desde `sgind-v2/` |
| **Impacto** | Funcionalidad predictiva inactiva a pesar de estar implementada |
| **Acción** | Integrar en página `diagnostico.py` o crear nueva página "Predicciones" en Streamlit; luego portar a v2 |
| **Prioridad** | 🟡 Media — funcionalidad de valor pero no crítica para operación |

---

### VAC-002 — Rules Engine inactivo

| Campo | Detalle |
|-------|---------|
| **Archivo** | `scripts/consolidation/core/rules_engine.py` |
| **Qué hace** | Motor de alertas por umbrales (`critico_low=0.70`, `atencion_low=0.80`) — distintos a la semaforización estándar (0.80) |
| **Estado** | Código completo. No activado en producción |
| **Decisión** | Umbrales diferentes son **intencionales** (alertas de monitoreo ≠ categorización UI). Documentado en `07_Decisiones.md` ARQ-007 |
| **Acción** | Definir trigger de activación: ¿cuándo se ejecuta? ¿cron? ¿post-ETL? |
| **Prioridad** | 🟡 Media |

---

### VAC-003 — Autenticación Streamlit — alcance limitado

| Campo | Detalle |
|-------|---------|
| **Archivos** | `streamlit_app/auth.py`, `streamlit_app/auth_modules/guards.py`, `streamlit_app/auth_modules/providers.py` |
| **Qué hace** | OIDC Microsoft via `st.experimental_user` + allowlist de emails en `st.secrets` |
| **Estado** | Implementado y funcionando. Solo protege Streamlit Community Cloud |
| **Gap** | `require_auth()` no se llama en todas las páginas — verificar que cada `pages/*.py` llame `require_auth()` al inicio |
| **SGIND v2** | Usa MSAL con `core/security.py` — más robusto, con Bearer token JWT |
| **Prioridad** | 🔴 Alta — revisar páginas sin `require_auth()` |

---

### VAC-004 — Notificaciones sin tests de integración

| Campo | Detalle |
|-------|---------|
| **Archivo** | `scripts/etl/notifications.py` (EmailNotifier) |
| **Qué hace** | Envía resumen post-ETL por email (SMTP) |
| **Estado** | Código implementado (~79% cobertura unitaria). `EmailNotifier` se instancia en `actualizar_consolidado.py` pero se desactiva si no hay `SMTP_*` configurado |
| **Gap** | Sin tests de integración. SMTP no configurado en CI. El template `.env.template` tiene slots para `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` pero no hay secreto en GitHub Actions |
| **Acción** | Configurar SMTP_* en GitHub Secrets y agregar test smoke en CI |
| **Prioridad** | 🟡 Media |

---

### VAC-005 — Ficha PDF sin test de integración

| Campo | Detalle |
|-------|---------|
| **Archivos** | `services/ficha_pdf/builder.py` (13% coverage), `services/ficha_pdf/charts.py` (11%) |
| **Qué hace** | Genera PDF de ficha técnica con gráfico de tendencia (reportlab + kaleido) |
| **Estado** | Código funcional. `utils.py` al 100%. `builder.py` y `charts.py` no testeados |
| **Gap** | `chart_to_png` usa kaleido para renderizar Plotly a PNG — requiere `kaleido` instalado, falla silenciosamente si no está. No validado en CI |
| **Acción** | Verificar `kaleido` en `requirements.txt`. Agregar test de integración que genera un PDF mínimo |
| **SGIND v2** | No implementado en v2 |
| **Prioridad** | 🟡 Media |

---

### VAC-006 — SGIND v2: páginas con PagePlaceholder

| Campo | Detalle |
|-------|---------|
| **Evidencia** | Componente `src/components/PagePlaceholder.tsx` existe y es importado desde páginas no finalizadas |
| **Páginas afectadas** | Verificar cuáles páginas bajo `src/app/(dashboard)/` usan `<PagePlaceholder>` |
| **Gap** | Funcionalidad visible para el usuario pero sin implementación real |
| **Acción** | Inventariar páginas con placeholder → priorizar según uso |
| **Prioridad** | 🟡 Media — bloquea parity funcional para cutover |

---

### VAC-007 — Plan Mejoramiento solo en v2, no en Streamlit

| Campo | Detalle |
|-------|---------|
| **Streamlit** | Página `plan_mejoramiento.py` existe pero es editorial (sin CRUD real) |
| **SGIND v2** | `plan_mejoramiento_service.py` + endpoint REST completo |
| **Gap** | Streamlit no tiene backend de plan de mejoramiento funcional |
| **Acción** | Aceptar asimetría: Streamlit solo muestra, v2 gestiona. Documentar en `10_Migracion_SGIND_v2.md` |
| **Prioridad** | 🟢 Baja — diferencia intencional entre versiones |

---

### VAC-008 — Coverage 50% (meta: 80%)

| Campo | Detalle |
|-------|---------|
| **Estado actual** | 903 tests, 50% coverage (jun-2026) |
| **Brecha** | 30 pts para meta de 80% en módulos core/etl |
| **Módulos prioritarios** | `services/data_loader.py` (23%), `scripts/etl/escritura.py` (29%), `scripts/etl/fuentes.py` (32%), `scripts/etl/purga.py` (30%), `scripts/etl/pipeline_metrics.py` (0%) |
| **Acción** | Ver plan en `06_Testing_Calidad.md` sección 5.1 |
| **Prioridad** | 🟡 Media — no bloquea producción pero aumenta riesgo de regresiones |

---

## Archivos a NO Tocar

| Archivo | Razón |
|---|---|
| `config.py` (raíz) | Importado por `streamlit_app/app.py` como shim legacy |
| `generar_reporte.py` (raíz) | Script de reporte LMI diferente de `scripts/generar_reporte.py` |
| `.agent*.instructions.md` | Instrucciones para agentes IA — verificar si están referenciados antes de archivar |
