# Plan de Implementación — Cierre de Hallazgos y Mejoras SGIND v2

**Última actualización:** 2026-08-17
**Origen:** [`Comparativo funcional Streamlit vs. SGING`](../../../Sistema_Indicadores_Poli/docs/comparativo_streamlit_vs_sgind_v2.md) (informe de referencia, revisado y actualizado 2026-08-17) más verificación directa de código sobre este repositorio.
**Estado:** 🔄 Propuesto — pendiente de ejecución por fases.

---

## Contexto

El informe comparativo Streamlit vs. SGING identificó hallazgos concretos de lógica de negocio, datos, filtros, visuales, arquitectura y menús en este repositorio. Este documento traduce cada hallazgo **verificado directamente en el código actual** (no solo el informe original) en tareas ejecutables por fases, más un conjunto acotado de mejoras nuevas (administración de usuarios, comparativos multi-año) confirmadas con el equipo como MVP a incluir.

Dos hallazgos del informe original ya estaban resueltos o parcialmente resueltos al momento de esta verificación y se documentan como tal en vez de repetirse como tareas pendientes (ver Fase 2, ítems 2.1 y 2.3).

**Decisiones de alcance confirmadas:**
- Se incluye la reactivación de los 5 módulos ocultos del menú (`plan-mejoramiento`, `seguimiento-operativo`, `gestion-om`, `pdi-acreditacion`, `diagnostico`), con checklist de validación por módulo (Fase 6).
- Panel de administración de usuarios/roles y comparativos multi-año se implementan como MVP acotado (Fases 7 y 8), no solo como propuesta de diseño.

**Principio de ejecución:** cada fase es mergeable/desplegable de forma independiente, en línea con la regla de "Documentación viva" y "Build + lint + tests antes de cerrar cualquier fase" de [`ROADMAP.md`](ROADMAP.md). El orden respeta dependencias técnicas (paleta antes de reactivar módulos que la usan, paginación antes de reactivar Seguimiento Operativo), no solo prioridad de negocio.

---

## Fase 0 — Higiene base (sin riesgo, sin dependencias)

**0.1 Formateo/lint del backend**
- Crear `backend/pyproject.toml` con `[tool.ruff]` (lint + format).
- `ruff format backend/app` para arreglar el formato roto de `backend/app/api/v1/endpoints/dashboard.py` (doble salto de línea sistemático, único archivo así en el proyecto) — **hacerlo antes de la Fase 2** para no mezclar reformateo con cambio funcional en el diff.
- Añadir `.github/workflows/backend-lint.yml` (hoy solo existe `keep-alive.yml`) con `ruff check` + `ruff format --check` en PRs.
- Verificación: `ruff format --diff` antes de aplicar (confirmar que no hay cambios semánticos) + `pytest backend/tests` completo debe seguir en verde tras el reformateo.

**0.2 Vitest + Testing Library en frontend**
- No existe ningún framework de unit testing hoy (`frontend/package.json` solo tiene Playwright E2E). Se elige **Vitest** sobre Jest porque comparte config con el toolchain Vite/esbuild del proyecto (Next 14 + TS), arranca más rápido y requiere menos configuración manual para App Router/RSC que Jest+ts-jest.
- Añadir `vitest`, `@vitejs/plugin-react`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`; crear `frontend/vitest.config.ts` y `frontend/vitest.setup.ts`; scripts `test:unit` / `test:unit:watch` en `package.json`.
- Cobertura inicial, en orden de valor: `design-tokens.ts` (`getSemaforoColor`/`getSemaforoBg`, tras Fase 1) → `nivelUtils.tsx` (`NivelBadge`) → el hook `useCascadingProcessFilters` nuevo de Fase 4 (mayor ROI, es lógica compartida entre 2 páginas).
- Verificación: `next build` debe seguir pasando sin interferencia de Vitest.

---

## Fase 1 — Consolidar la paleta de semáforo (una sola fuente de verdad)

**Por qué primero:** es la dependencia compartida más ancha del plan — toca los 4 módulos activos hoy y los 5 que se reactivarán en Fase 6. Cierra además una violación directa de la regla "Semaforización centralizada" de [`ROADMAP.md`](ROADMAP.md#reglas-de-desarrollo).

### Problema confirmado
Coexisten **5 definiciones de color con hex inconsistentes** para los mismos 4-5 niveles (Peligro/Alerta/Cumplimiento/Sobrecumplimiento/Sin dato):

| Fuente | Familia | Ejemplo (Peligro) |
|---|---|---|
| `frontend/src/lib/design-tokens.ts:20-45` (se autodeclara "fuente única") | Flat | `#ef4444` |
| `frontend/tailwind.config.ts:28-38` | Flat (coincide con design-tokens) | `#ef4444` |
| `frontend/src/components/cmi/cmiChartColors.ts:3-9` (`NIVEL_COLORS`) | Media | `#D32F2F` |
| `frontend/src/components/cmi/nivelUtils.tsx:1-7` (`NIVEL_STYLES`, texto+fondo) | Oscura/contraste | `#B71C1C` / `#FEE2E2` |
| `frontend/src/components/cmi/CmiProcesosBarPlotly.tsx:6-12` (`NIVEL_COLOR`) | Oscura (coincide con nivelUtils) | `#B71C1C` |
| Backend `backend/app/domain/constants.py::COLOR_CATEGORIA` | Media (coincide con cmiChartColors) | `#D32F2F` |
| Backend `backend/app/services/pdi_service.py:15-21::NIVEL_COLOR` | Flat (coincide con design-tokens) | `#ef4444` |

### Decisión de diseño
Adoptar la familia **oscura/alto-contraste** (`nivelUtils.tsx`/`CmiProcesosBarPlotly.tsx`) como canónica: es la que ya se renderiza en la mayoría de superficies visibles hoy (badges, barras CMI) y tiene mejor contraste texto/fondo. Unificar "Sobrecumplimiento" en `#1D4ED8` (texto) / color sólido derivado para gráficos.

### Frontend
1. Reescribir `frontend/src/lib/design-tokens.ts`: reemplazar hex de `SEMAFORO`/`SEMAFORO_COLOR`/`SEMAFORO_BG` por los valores canónicos; **añadir el 5º nivel "Sin dato"/"Pendiente de reporte"** que hoy falta ahí; exportar variante texto/fondo (para reemplazar `NIVEL_STYLES`).
2. `frontend/tailwind.config.ts:28-38`: sincronizar a mano con los mismos valores (Tailwind no puede importar TS en `theme.extend`); dejar comentario `// DEBE coincidir con src/lib/design-tokens.ts::SEMAFORO`.
3. `frontend/src/components/cmi/cmiChartColors.ts`: eliminar `NIVEL_COLORS` local, importar de `design-tokens.ts` (mantener `STRATEGIC_PALETTE`, no relacionado).
4. `frontend/src/components/cmi/nivelUtils.tsx`: eliminar `NIVEL_STYLES` local, `NivelBadge` consume `design-tokens.ts`.
5. `frontend/src/components/cmi/CmiProcesosBarPlotly.tsx:6-12`: eliminar `NIVEL_COLOR` local, importar de `design-tokens.ts`.

Orden de edición: `design-tokens.ts` primero (con el 5º nivel), luego los 3 consumidores, `tailwind.config.ts` al final.

### Backend
1. `backend/app/domain/constants.py::COLOR_CATEGORIA` pasa a ser la única fuente backend, con los valores canónicos (mismo hex string que `design-tokens.ts`).
2. `backend/app/services/pdi_service.py:15-21`: eliminar `NIVEL_COLOR` local duplicado, importar `COLOR_CATEGORIA` de `app.domain.constants`; confirmar que las claves coinciden exactamente (`"Sin dato"` vs. la clave que use `pdi_service.py` hoy).
3. Añadir test `backend/tests/test_domain.py::test_color_categoria_hex_valido` que valida que todas las claves de `CategoriaCumplimiento` tienen entrada en `COLOR_CATEGORIA`.

### Verificación
- Regresión visual manual en `cmi-procesos`, `informe-procesos`, `resumen-general`, `pdi-acreditacion`: confirmar que los colores no cambian donde ya se usaba la familia oscura, y sí mejoran (consistencia) donde se usaba la flat en Plotly.
- Hacer este cambio en su propia rama/PR, aislado del resto, para poder revertir con un solo `git revert` si algo se ve mal en producción.

---

## Fase 2 — Backend: tipado de endpoints, código muerto, test de regresión PDI

Puede ejecutarse en paralelo con Fase 1.

### 2.1 Response models para 6 endpoints sin tipar
Patrón de referencia ya correcto en el propio proyecto: `backend/app/api/v1/endpoints/indicators.py:17` y la mayoría de `dashboard.py`.

Endpoints a tipar (definir schemas nuevos en `backend/app/schemas/common.py`, reutilizando sub-schemas existentes donde aplique):
- `dashboard.py:151` `/filtros` → `FiltrosDashboardResponse`
- `dashboard.py:191` `/sunburst` → `list[SunburstNodeItem]`
- `dashboard.py:211` `/yoy` → `list[YoYItem]`
- `dashboard.py:231` `/resumen-completo` → `ResumenCompletoResponse` (componer con `KPIResponse`, `SemaphoreItem`, `TrendItem`, `CMILineaItem` ya existentes)
- `dashboard.py:242` `/narrativa` → `NarrativaResponse`
- `indicators.py:45` `/{indicator_id}` → `IndicatorDetailResponse`

Metodología: escribir cada schema como reflejo fiel de lo que el servicio devuelve **hoy** (no idealizar tipos), correr `pytest backend/tests` (hay tests de contrato como `test_fase6_contracts.py`), y probar cada endpoint manualmente contra datos reales antes de mergear. Usar uniones (`int | str | None`) donde el dato real sea inconsistente en vez de forzar un tipo que rompa el endpoint.

### 2.2 Modelo `Accion` muerto
Confirmado sin uso en ningún endpoint/servicio (`backend/app/models/accion.py:12-22`). Antes de eliminar:
- `grep -rn "Accion" backend/app` para reconfirmar cero referencias en el momento de ejecución.
- Verificar si `/plan-mejoramiento` (que se valida en Fase 6.2) depende de él pese al grep — si depende, mantenerlo y documentar su uso real en vez de eliminarlo.
- Si se confirma muerto: eliminar `backend/app/models/accion.py` y su referencia en `backend/app/models/__init__.py`. Revisar `database/migrations/` por si existe una migración que creó la tabla `acciones` en producción (si existe, documentar como deuda o planear migración de limpieza, no bloqueante para este plan).

### 2.3 Extender el test de regresión PDI existente
`backend/tests/test_pdi_service.py::test_classify_estado_matches_categorizar_cumplimiento` ya existe y confirma que `PDIService._classify_estado` reutiliza correctamente `categorizar_cumplimiento` (el hallazgo de "riesgo alto" del informe de julio ya está resuelto en el código). Falta cobertura del régimen Negativo-Porcentual:
- Añadir casos parametrizados con `id_indicador` en `IDS_NEGATIVO_PCT` (`"121"`, `"207"`, `"377"`, `"561"`) en rangos bajo/entre/sobre 102-110%.
- Añadir caso con `id_indicador` en `IDS_NEGATIVO_PCT` pero `cumpl_pct=None` (confirmar que "Sin dato" tiene prioridad).
- Verificación: `pytest backend/tests/test_pdi_service.py -v`.

---

## Fase 3 — Paginación real en Seguimiento Operativo

Sin dependencia de Fases 1-2. **Debe completarse antes de reactivar `/seguimiento-operativo` en Fase 6.**

### Backend
Patrón de referencia exacto: `backend/app/services/indicator_service.py:119-145` (`limit`/`offset`, `df.iloc[offset:offset+limit]`, retorno `{total, items, limit, offset}`) + `backend/app/api/v1/endpoints/indicators.py:17-27` (`Query(500, ge=1, le=5000)` / `Query(0, ge=0)`).

- `backend/app/services/seguimiento_service.py::get_dashboard` (líneas 48-61): localizar en `app/domain/seguimiento_builders.py` dónde se genera el detalle de "Tracking Mensual" hoy devuelto completo. Añadir `limit`/`offset`, aplicar slice sobre el DataFrame de detalle, incluir `total`/`limit`/`offset` en la respuesta.
- `backend/app/api/v1/endpoints/seguimiento.py`: añadir los mismos `Query(...)` que `indicators.py`.
- Tipar la respuesta con schema Pydantic en la misma pasada (evita tocar el archivo dos veces si cae también en el alcance de Fase 2.1).
- **El endpoint de exportación Excel NO se pagina** — confirmar explícitamente que `export_excel` sigue trayendo el dataset completo filtrado.
- Test nuevo/extendido verificando `total` correcto y que `offset` fuera de rango no rompe.

### Frontend
- `frontend/src/app/(dashboard)/seguimiento-operativo/page.tsx:49-53`: eliminar `DETALLE_DISPLAY_LIMIT`/slice en cliente (y el aviso de truncado de líneas 193-198).
- Añadir estado `page`/`pageSize` al `useQuery`, controles de paginación (Anterior/Siguiente + "X-Y de Z"), manteniendo el botón "Descargar Excel" apuntando al export sin paginar.
- `frontend/src/lib/api.ts`: actualizar firma de la función fetch de seguimiento.
- Verificación: cambiar de página dispara un nuevo fetch (no slice en memoria); el conteo total coincide con el que antes mostraba el aviso de truncado.

---

## Fase 4 — Hook compartido `useCascadingProcessFilters`

Después de Fase 1 (para que use la paleta ya consolidada si expone algo visual); antes de Fase 6 si `plan-mejoramiento`/`gestion-om` resultan compartir el mismo patrón de cascada (verificar en 6.2).

### Problema confirmado
`frontend/src/app/(dashboard)/cmi-procesos/page.tsx:75-78` e `frontend/src/app/(dashboard)/informe-procesos/page.tsx:71-74` tienen la lógica de cascada Unidad→Proceso→Subproceso **idéntica carácter por carácter**, mismo estado, mismo fetch de filtros, mismo reset de subproceso. Única divergencia real: `cmi-procesos` resetea el mes al cambiar de año (línea 193-196), `informe-procesos` no (línea 191).

### Diseño del hook
`frontend/src/hooks/useCascadingProcessFilters.ts` (confirmar convención real de ubicación de hooks en el repo antes de crear el directorio; ajustar si ya existe un patrón distinto).

Responsabilidades:
- Estado: `anio`, `mes`, `unidad`, `proceso`, `subproceso`, `clasificacion`, `frecuencia`.
- Fetch de filtros vía `fetchCMIProcesosFiltros(anio)`, con prefijo de `queryKey` parametrizable por página (evita colisión de caché de React Query entre `cmi-procesos` e `informe-procesos`).
- `subprocesosFiltrados` derivado de `subprocesos_por_proceso[proceso]`.
- Reset de `subproceso` a `"Todos"` al cambiar `proceso`.
- **Resolución consciente de la divergencia**: adoptar el comportamiento de `cmi-procesos` (resetear mes al cambiar año, evita filtros inválidos silenciosos) también en `informe-procesos` — documentar este cambio de comportamiento visible explícitamente en el PR.
- **Persistencia de filtros en URL** (mejora de UX incluida aquí, ver hallazgo de filtros del informe original): usar `useSearchParams`/`useRouter` de Next 14 App Router para reflejar los filtros activos en la URL — mismo vehículo natural que ya centraliza el estado.

### Migración
- Migrar `cmi-procesos` primero (comportamiento de referencia), verificar visualmente, luego `informe-procesos` (el único cambio de comportamiento visible ahí es el reset de mes).
- Riesgo principal: un `queryKey` mal generalizado que comparta caché entre páginas — cubrir con test unitario (Fase 0.2) y verificación manual navegando entre páginas sin recarga completa.

---

## Fase 5 — Visuales: exportación, limpieza, componentes base

En paralelo con Fases 3-4. Depende de Fase 1 solo en 5.2.

### 5.1 Habilitar exportación de imagen (11 ubicaciones)
Todas las instancias de `displayModeBar: false` deshabilitan hoy la descarga de PNG:
`ProyectosGanttChart.tsx:120`, `SunburstPlotlyChart.tsx:72`, `CmiBarLineasPlotly.tsx:91`, `seguimiento-operativo/page.tsx:174`, `CmiCatalogChartsPlotly.tsx:42,75`, `CmiCumplimientoHorizBarPlotly.tsx:61`, `pdi-acreditacion/page.tsx:180,196,338`, `CmiProcesosAnalisisTab.tsx:176`.

Cambio uniforme:
```ts
config={{
  displayModeBar: true,
  modeBarButtonsToRemove: ["zoom2d","pan2d","select2d","lasso2d","zoomIn2d","zoomOut2d","autoScale2d","resetScale2d","hoverClosestCartesian","hoverCompareCartesian","toggleSpikelines"],
  displaylogo: false,
  responsive: true,
}}
```
Si no existe ya un wrapper común de Plotly, crear `frontend/src/components/charts/PlotlyBase.tsx` y centralizar el `config` ahí (evita que una futura fase vuelva a divergir la configuración en 11 sitios).

### 5.2 `CmiDonutNivelPlotly.tsx` / `CmiProcesosBarPlotly.tsx` — posponer migración a Plotly puro
Ambos son SVG/CSS manual pese al nombre, con features custom (línea de meta, tooltips, deltas ▲▼) no triviales de replicar con la API estándar de Plotly. El problema real de fondo (paleta duplicada) ya se resuelve en Fase 1 sin migrar de librería. Acción de bajo riesgo en este plan: renombrar o documentar en cabecera que son implementación manual, no Plotly, para evitar confusión futura.

### 5.3 Eliminar componentes de chart muertos
`frontend/src/components/charts/SemaphoreChart.tsx`, `TrendChart.tsx`, `SunburstChart.tsx` — sin ningún import activo confirmado (no confundir con `SunburstPlotlyChart.tsx`, que sí está en uso). Re-confirmar con grep en el momento de ejecución, eliminar, verificar que `next build` sigue pasando.

### 5.4 Componentes UI base (alcance acotado)
Ya existe `frontend/src/components/ui/KPICard.tsx` como precedente de carpeta `ui/`. Antes de construir más: inventariar cuántos botones/selects se reimplementan con las mismas clases Tailwind repetidas. Si son >5-6 ocurrencias, extraer `Button.tsx`/`Select.tsx` a `frontend/src/components/ui/` — usarlos primero en los filtros de cascada de Fase 4. `Modal` genérico queda fuera de alcance (ya existe `CmiProcesosFichaModal.tsx` funcionando, sin evidencia de duplicación que justifique la abstracción ahora).

Sidebar colapsable/responsive para mobile: **fuera de alcance de este plan** (esfuerzo no trivial, más urgente después de que Fase 6 aumente el contenido del sidebar).

---

## Fase 6 — Reactivar los 5 módulos ocultos del menú

Al final, después de Fases 1, 3 y 4 (paleta, paginación de seguimiento, filtros compartidos), porque varios módulos ocultos heredan directamente esas correcciones.

### 6.1 Cambio mecánico
`frontend/src/config/navigation.ts:19-23`: mover cada línea comentada a `NAV_ITEMS` (Plan de Mejoramiento, Seguimiento Operativo, Gestión OM — ya tienen entrada en `NAV_ITEM_META:92-115`) o a `BETA_ITEMS` (PDI Acreditación, Diagnóstico — en `BETA_ITEM_META:118-131`, su estado "beta" es intencional).

### 6.2 Checklist de validación por módulo (orden recomendado, menor a mayor riesgo)

**Nota de proceso:** los módulos se ocultaron "por pedido explícito" según el propio comentario del código — confirmar con el stakeholder que originó ese pedido que ya no aplica, módulo por módulo, antes de reactivar en producción. Esto es una aprobación de negocio, no solo técnica.

1. **`/seguimiento-operativo`** (tras Fase 3): paginación funciona con datos reales; export Excel completo intacto; sin errores de consola; `displayModeBar` (Fase 5.1, línea 174) correctamente configurado.
2. **`/plan-mejoramiento`**: confirmar si depende del modelo `Accion` (Fase 2.2) — si sí, revisar antes de decidir eliminar el modelo.
3. **`/gestion-om`**: evaluar si comparte el patrón de cascada de Fase 4 — si sí, adoptar `useCascadingProcessFilters` en esta misma fase.
4. **`/pdi-acreditacion`** (BETA): usa `NIVEL_COLOR` propio en `pdi_service.py` — confirmar que Fase 1.2 no rompió nada; tiene 3 de las 11 instancias de `displayModeBar` (líneas 180, 196, 338) — confirmar Fase 5.1 aplicada.
5. **`/diagnostico`** (BETA): módulo menos explorado — hacer una pasada de exploración dedicada (página + endpoints) antes de reactivar.

Checklist mínimo por módulo:
- [ ] Carga sin error 500/404 con datos reales.
- [ ] Consola sin errores/warnings de React.
- [ ] Filtros devuelven datos coherentes, no vacíos por defecto.
- [ ] Exportación (si aplica) probada manualmente.
- [ ] Roles en `NAV_ITEM_META` confirmados vigentes con negocio.

---

## Fase 7 — Panel de administración de usuarios/roles (MVP)

El RBAC de 3 roles ya existe en BD (`backend/app/models/user.py`, `backend/app/core/security.py:81-95` con `require_roles`/`require_admin`) — falta solo exposición HTTP + UI.

### Backend
Nuevo `backend/app/api/v1/endpoints/admin_users.py`:
- `GET /admin/users` — listar usuarios con su rol (protegido con `require_admin`).
- `PATCH /admin/users/{id}` — cambiar `role_id`/`is_active`.
- `GET /admin/roles` — listar los 3 roles fijos (de solo lectura; no exponer creación de roles nuevos en este MVP, ya que `RoleName` parece estar hardcodeado como tipo en varios lugares).
- Confirmar el flujo real de alta de usuario (probablemente automático vía Azure AD/SSO, dado `azure_oid` en el modelo `User`) antes de asumir que el panel necesita creación manual — si el alta es automática, el MVP solo gestiona rol/estado de usuarios existentes.
- Test: extender `backend/tests/test_fase7_auth.py` para confirmar que un rol `procesos` recibe 403 en estos endpoints nuevos.

### Frontend
- Nueva ruta `frontend/src/app/(dashboard)/admin/usuarios/page.tsx`: tabla de usuarios con selector de rol inline (reutilizar `Select` de Fase 5.4 si ya existe) + toggle activo/inactivo.
- Entrada en `navigation.ts` con `roles: ["calidad", "desempeno"]` en su meta.
- Verificación: un usuario con rol `procesos` no ve la entrada en el menú (defensa en profundidad, aunque el backend ya la bloquea).

**Fuera de alcance de este plan:** panel de catálogos (procesos, líneas, indicadores) editable desde UI sin depender de Excel — requiere decisión de arquitectura de datos (fuente de verdad Excel vs. BD relacional) que merece su propio diseño, ligada a la deuda pendiente de ETL hacia base de datos analítica.

---

## Fase 8 — Comparativos multi-año (MVP)

Extensión incremental sobre `dashboard.py::/yoy` (`GET /dashboard/yoy`, ya tipado en Fase 2.1 con `list[YoYItem]`), que hoy hace comparación año-contra-año.

- Backend: extender el servicio subyacente para aceptar un rango de años (ej. `anios: list[int]` o `n_anios: int = 3`) en vez de un único año base, devolviendo series de 3-5 años por indicador/línea.
- Frontend: nuevo componente de línea temporal multi-año (reutilizando Plotly, ya presente) en el módulo donde hoy vive el YoY (confirmar ubicación exacta — probablemente `resumen-general` o `cmi-estrategico`).
- Verificación: comparar cifras contra el cálculo YoY existente para 2 años consecutivos — deben coincidir exactamente (es un superset, no un cálculo distinto).

**Fuera de alcance de este plan** (requieren infraestructura o decisiones de producto no exploradas): alertas proactivas (requiere notificaciones/cron/email), predicciones (requiere ETL analítico consolidado primero), benchmarking externo (requiere fuente de datos externa), simulación de metas (requiere definición de UX/reglas de negocio nueva).

---

## Orden de ejecución

```
Fase 0 (higiene)  ──┐
                     ├─→ Fase 1 (paleta) ──┐
Fase 2 (backend)  ───┘                     ├─→ Fase 6 (reactivación módulos)
Fase 3 (paginación) ────────────────────────┤
Fase 4 (filtros compartidos + URL) ─────────┤
Fase 5 (visuales) ───────────────────────────┘
Fase 7 (admin usuarios) — independiente, en paralelo a cualquier otra
Fase 8 (comparativos multi-año) — después de Fase 2 (depende de /yoy tipado)
```

## Verificación end-to-end del plan completo

- Backend: `pytest backend/tests` en verde tras cada fase; `ruff check`/`ruff format --check` limpio (Fase 0 en adelante).
- Frontend: `next build` sin errores tras cada fase; `npm run test:unit` (Vitest, Fase 0.2) en verde; `npm run test:e2e` (Playwright existente) en verde, especialmente `semaforo.spec.ts` tras Fase 1 y `navegacion.spec.ts` tras Fase 6.
- Regresión visual manual: capturas antes/después en los 4 módulos activos tras Fase 1, y en cada módulo reactivado según el checklist de Fase 6.2.
- Ningún endpoint de exportación (Excel/PDF) debe paginarse — verificar explícitamente en Fase 3.
- Aprobación de negocio explícita módulo por módulo antes de cada reactivación en Fase 6 (no es solo un gate técnico).

---

## Seguimiento de avance

| Fase | Nombre | Estado | Avance |
|------|--------|--------|--------|
| 0 | Higiene base (lint backend + Vitest) | ⏳ Pendiente | 0% |
| 1 | Paleta de semáforo consolidada | ⏳ Pendiente | 0% |
| 2 | Tipado de endpoints + test PDI | ⏳ Pendiente | 0% |
| 3 | Paginación Seguimiento Operativo | ⏳ Pendiente | 0% |
| 4 | Hook `useCascadingProcessFilters` | ⏳ Pendiente | 0% |
| 5 | Visuales (exportación, limpieza) | ⏳ Pendiente | 0% |
| 6 | Reactivación de módulos ocultos | ⏳ Pendiente | 0% |
| 7 | Panel admin usuarios/roles (MVP) | ⏳ Pendiente | 0% |
| 8 | Comparativos multi-año (MVP) | ⏳ Pendiente | 0% |

_Actualizar esta tabla al cerrar cada fase, siguiendo la convención de [`STATUS.md`](STATUS.md)._
