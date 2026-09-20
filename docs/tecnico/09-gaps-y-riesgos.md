# Gaps y riesgos (con evidencia)

## Crítico

| ID | Gap | Evidencia | Riesgo |
|---|---|---|---|
| G-01 | El pipeline que produce los datos de indicadores (`scripts/`, ~130 archivos incluyendo 23 módulos en `scripts/etl/`) no está integrado al backend ni automatizado | `backend/app` no tiene ningún `subprocess`/llamada hacia `scripts/*.py`; `.github/workflows/` no ejecuta el pipeline; `config/settings.toml [schedule]` está declarado sin implementación | Si nadie ejecuta el pipeline manualmente, los indicadores se congelan sin ningún error visible para el usuario |
| G-02 | ~~Entorno de pruebas del backend roto~~ **Corregido en Oleada 0 — era un falso negativo.** `backend/.venv312` (Python 3.12.10 + SQLAlchemy 2.0.36) ya existía y funciona; el fallo original se debía a correr con el Python 3.14 global en vez de este venv, documentado en `backend/README.md` desde antes de esta auditoría | Con el venv correcto: `SGIND_DATA_PATH=../data PYTHONPATH=. backend/.venv312/Scripts/python.exe -m pytest tests/ -q` → 123 passed, 16 skipped, 36 failed reales (triados en `08-testing.md`) | Ya no bloquea nada; riesgo remanente bajo — reforzar en onboarding/CI que se use `.venv312` |
| G-03 | Semaforización de cumplimiento duplicada en 4 implementaciones backend + 4 mapas de color frontend, con umbrales y colores distintos entre sí | `domain/procesos_builders.py`, `domain/cmi_builders.py` (x3) vs. `domain/categorization.py`; `cmiChartColors.ts`, `nivelUtils.tsx`, `CmiProcesosResumenTab.tsx`, `CmiVistaRapidaCards.tsx` | El mismo indicador puede mostrarse con distinto color/estado según qué pantalla del dashboard se consulte, especialmente en regímenes especiales (Plan Anual, Negativo-Porcentual) |

## Alto

| ID | Gap | Evidencia | Riesgo |
|---|---|---|---|
| G-04 | ~~`/auth/dev-token` solo se bloquea si `environment=="production"` literal~~ **Corregido en Oleada 0.** Nuevo flag `ENABLE_DEV_AUTH` (default `false`), requerido explícitamente tanto por el endpoint como por el bypass de BD en `get_current_user` | `backend/app/core/config.py`, `security.py:69`, `api/v1/endpoints/auth.py:87` | Antes: auto-emisión de JWT admin sin credenciales en cualquier staging/QA con otro nombre de entorno |
| G-05 | ~~Ruta rota en `excel_reader.py`~~ **Corregido en Oleada 0.** `PRIMARY_EXCEL_FILES` tenía dos rutas rotas, no una: `output/Consolidado_API_Kawak.xlsx` (real: `raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx`) y `raw/Excel_Entrada/CMI.xlsx` (no existe ninguna carpeta `Excel_Entrada`; el archivo real es `raw/Indicadores por CMI.xlsx`) | `backend/app/services/excel_reader.py:12-17` | Antes: lectura fallida o silenciosamente vacía si se invocaba alguno de esos dos candidatos de fallback |
| G-06 | `data/output/Seguimiento_Reporte.xlsx` no se regenera en el pipeline de `actualizar_consolidado.py` y tiene fecha de modificación más antigua que el resto | Sección "Modelo Excel" en `03-modelo-de-datos.md` | Módulo de Seguimiento podría mostrar datos desactualizados sin que nadie lo note |
| G-07 | Componente `IndicatorsTable.tsx` asume escala de porcentaje opuesta a `nivelUtils.tsx` (fracción 0-1 vs. 0-100) | `formatPct` vs. `fmtPct` | Bug latente de doble escala si el componente (hoy huérfano) se vuelve a conectar a una página |
| G-08 | ~~Documentación de migración describe una estructura `sgind-v2/*` inexistente~~ **Corregido en Oleada 1.** `STATUS.md` y `ROADMAP.md` reescritos con las rutas reales (`backend/`, `frontend/`, `database/`, `scripts/` en la raíz) | `docs/migration/STATUS.md`, `docs/migration/ROADMAP.md` | Antes: cualquier persona que siguiera esos documentos literalmente no encontraba los archivos |
| G-09 | `PLAN_MIGRACION_PRIORIZADO.md` (2026-09-18) ya estaba parcialmente desactualizado dos días después | Módulo Plan de Mejoramiento (Indicadores+Métricas) que decía "sin ningún equivalente en SGING" ya está implementado en `backend/app/domain/plan_mejoramiento_builders.py` | Marcado como superado por este plan de auditoría en `docs/migration/PLAN_MIGRACION_PRIORIZADO.md` (Oleada 1) — se conserva como referencia histórica, no como fuente de verdad vigente |

## Medio

| ID | Gap | Evidencia | Riesgo |
|---|---|---|---|
| G-10 | 3 de 7 tablas Postgres (`audit_log`, `ai_configs`, `ai_prompts`) sin consumidor en `backend/app` | Grep vacío en `backend/app` | Datos acumulándose sin uso; `audit_log` se sigue llenando vía trigger sin que nadie audite nada realmente |
| G-11 | Modelo ORM `Accion` importado pero sin service/endpoint que lo consulte directamente (los datos de acciones se leen vía Excel en `domain/om_builders.py`) | `models/__init__.py`, grep sobre `app/` | Posible código muerto o migración Excel→BD incompleta, requiere confirmación con el equipo |
| G-12 | `RBAC_MATRIX.md` documenta 2 endpoints inexistentes (`etl/run`, `export/*` genérico) | Grep vacío en `backend/app/api/v1/` | Documentación desalineada, sin impacto de seguridad real |
| G-13 | ~~Conteo de ADRs incorrecto en `ROADMAP.md`~~ **Corregido en Oleada 1** (decía 8, son 9 — se agregó ADR-009 a la lista) | `docs/migration/ROADMAP.md` | Menor, solo corrección editorial |
| G-14 | Dos librerías de gráficos en paralelo (Plotly + Recharts) sin convención documentada | `package.json`, uso disperso en `frontend/src/components/` | Peso de bundle innecesario, mayor superficie de mantenimiento |
| G-15 | ~~`.env.staging` trackeado en git~~ **Corregido en Oleada 0.** Se quitó del índice (`git rm --cached`, el archivo sigue en disco) y se agregó `.env.staging` a `.gitignore` | `.gitignore` | Antes: hábito de riesgo — un futuro valor real podría commitearse por accidente |
| G-16 | ~~Dos páginas completas y funcionales (PDI/Acreditación, Diagnóstico) sin ningún enlace de navegación visible~~ **Corregido en Oleada 1.** PDI/Acreditación se eliminó por completo (página, endpoints `/pdi/*`, schemas, tests, referencias en `navigation.ts`, mocks E2E). Diagnóstico se conservó como herramienta interna: sacada de `BETA_ITEMS`/`BETA_ITEM_META`, gateada por `isDiagnosticsEnabled()` (solo `NODE_ENV=development` o `NEXT_PUBLIC_ENABLE_DIAGNOSTICS=true`) | `config/navigation.ts`, `diagnostico/page.tsx` | Antes: funcionalidad terminada e invisible para el usuario final salvo que conociera la URL |
| G-17 | ~~Texto fijo engañoso en panel de Diagnóstico~~ **Corregido en Oleada 1.** Reemplazado por `AuthModeSummary`, que lee el estado real de sesión (`email`/`role` de `useAuthStore`) y los modos de login realmente habilitados | `diagnostico/page.tsx` | Antes: no reflejaba el modo de auth realmente activo |
| G-18 | `npm run build` no completa el paso de "standalone output" en este entorno (OneDrive) | Error de sistema de archivos, no de código | Bloquea builds/CI locales reproducibles si el repo permanece dentro de OneDrive |
| G-19 | Ítems sin meta real (`Meta=0`/`NULL`) en CMI por Procesos / Informe por Procesos se muestran como "Sin dato", indistinguibles de un dato realmente faltante | `domain/health_metrics.py::recalcular_cumplimiento_faltante` retorna NaN; `scripts/etl/agent5_corrections.py:73-85` señala estos casos en el pipeline pero la señal no llega al backend/frontend; no existe campo `Tipo`/`Clasificacion` tipo "Métrica" fuera de Plan de Mejoramiento (confirmado por grep, solo existe en `plan_mejoramiento_service.py:130,174`) | El usuario no puede distinguir "esto es una métrica de seguimiento sin meta por diseño" de "falta reportar este indicador" — ambos se ven idénticos (gris, "Sin dato") |
| G-20 | `docs/architecture/adrs/ADR-007-ia.md` documenta "Anthropic Claude" como proveedor de IA; el código real usa `google-genai` (Gemini) | ADR-007 líneas 1,6-7 vs. `backend/app/core/config.py:39-43` (comentario explícito: "Reemplaza a Anthropic Claude... por decisión de producto") y `requirements.txt` (`google-genai`, sin SDK de Anthropic) | ADR desactualizado — cualquiera que lo lea para entender la integración de IA real se equivoca de proveedor |

## No confirmado — requiere decisión de negocio, no auditoría de código

- Estado de `scripts/backup_sqlite.py`, `scripts/panel_monitoreo.py`,
  `scripts/ingesta_plantillas.py`, `scripts/analytics/*` — sin imports
  encontrados desde el core activo, pero podrían estar en uso vía
  Task Scheduler u otro mecanismo externo al repo (no verificable solo con
  lectura de código).
