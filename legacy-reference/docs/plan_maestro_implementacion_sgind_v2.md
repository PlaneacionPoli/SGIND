# Plan Maestro de Implementación — Cierre de Brechas SGIND-v2

**Fecha:** 2026-07-11
**Fuente de verdad:** [Comparativo Streamlit vs. SGIND-v2](comparativo_streamlit_vs_sgind_v2.md)
**Encaje con el proyecto**: este plan **no crea una nueva numeración de fases**. El proyecto de migración ya tiene fases 0-12 documentadas en `sgind-v2/docs/migration/ROADMAP.md` y `STATUS.md`. Este Plan Maestro se ejecuta **dentro de la Fase 11 (UAT / Validación)**, actualmente "En progreso", como el ciclo de cierre de brechas que debe completarse **antes** de firmar `ACCEPTANCE_DOCUMENT.md` y avanzar a Fase 12 (Cutover). Se organiza en 4 bloques (11.A-11.D) equivalentes a los 4 "Fases" pedidos en el prompt original, renombrados para no chocar con la numeración oficial.

---

## 1. Resumen ejecutivo

**Estado actual de SGIND-v2** (según `STATUS.md`, 2026-06-19): Fases 0-10 completadas (arquitectura, modelo de datos, backend, frontend, testing E2E, auth Azure AD, migración de datos, PDF, staging). Fase 3 (Design System) y Fase 11 (UAT) en progreso; Fase 12 (Cutover) con artefactos listos pero sin ejecutar.

**Equivalencia funcional estimada** (comparativo §15): **~85-90%** sobre los 7 módulos activos del menú Streamlit; **~65-70%** si se incluyen los módulos huérfanos del legacy (Tablero Operativo Nivel 3, no enrutado pero funcional).

**Principales fortalezas de v2**: RBAC real con 3 roles vía Azure AD + JWT (vs. whitelist plana en legacy), CRUD completo de Gestión OM sobre PostgreSQL, exportación PDF de reportes completos (funcionalidad nueva, no existía en legacy), separación arquitectónica routers/servicios/dominio, suite de tests E2E (Playwright) y 21 archivos de test backend por fase.

**Principales brechas**: (1) alcance no confirmado del Tablero Operativo Nivel 3 (Kanban/QC/Trazabilidad); (2) narrativa con IA generativa real (Claude) del legacy no replicada — v2 solo tiene heurísticas de reglas; (3) umbrales de semáforo de PDI/Acreditación reimplementados fuera de la función central de categorización, con riesgo real de inconsistencia numérica; (4) deuda de consistencia interna en v2 (3 definiciones de colores de semáforo, 3 librerías de gráficos sin wrapper único, cascada de filtros rota en Informe por Procesos).

**Riesgos del proyecto**: firmar `ACCEPTANCE_DOCUMENT.md` sin haber verificado paridad numérica en PDI/Acreditación, sin haber confirmado con negocio el estado del Tablero Operativo N3, y sin haber ejecutado UAT real con usuarios (a la fecha `UAT_BUGS.md` solo contiene la plantilla de ejemplo).

**Recomendación general**: no avanzar a Fase 12 (Cutover) hasta cerrar los Bloques 11.A y 11.B de este plan (estabilización y paridad funcional) y ejecutar al menos una ronda de UAT real con `scripts/uat_verify.py` mostrando paridad ≤0.01%, tal como exige el Hito H8 ya definido en `ROADMAP.md`.

---

## 2. Consolidación de hallazgos

| Categoría | Hallazgos (ref. comparativo) |
|---|---|
| **Funcionalidades faltantes** | Tablero Operativo N3 (Kanban/QC/Trazabilidad) sin destino confirmado (§2.8); IA generativa real en fichas CMI (§2.2, §11); PDF de ficha individual de indicador (§2.2, §11); heatmap/radar/gauge/bullet chart del catálogo `heatmap_chart.py` (§3); treemap Factor→Característica en Plan de Mejoramiento (§3); sparklines de tendencia (§3); motor ECharts de respaldo (§3, no crítico) |
| **Funcionalidades incompletas** | CRUD OM en UI (backend completo, frontend solo lectura+creación — `STATUS.md:36`); paginación de Seguimiento Operativo (trunca a 200 filas, §2.6); persistencia de filtros en URL (solo `cmi_linea`, §5) |
| **Errores funcionales** | Umbrales PDI/Acreditación con escala distinta a `categorizar_cumplimiento` central (§4, riesgo crítico de cifras inconsistentes); cascada Subproceso no dependiente de Proceso en Informe por Procesos (§5, regresión frente a CMI Procesos del propio v2) |
| **Mejoras visuales** | 3 definiciones distintas de colores de nivel de semáforo en frontend (§4, §6); mezcla de Plotly/Recharts/SVG-manual sin wrapper único (§3, §6) |
| **Mejoras de UX** | Sin persistencia de filtros en URL (compartido con legacy, §5, §7); exportación de imagen de gráficos deshabilitada activamente (`displayModeBar:false`, §3) |
| **Mejoras de rendimiento** | Sin ETL hacia BD analítica (ambos sistemas leen Excel en cada ciclo de caché, §8); caché de proceso no compartida entre workers Uvicorn (§8, backend) |
| **Mejoras de arquitectura** | Endpoints de negocio sin `response_model` Pydantic (PDI, plan-mejoramiento, informe, seguimiento, fichas CMI — §9-10); documentación de fases desactualizada (`RBAC_MATRIX.md`, `docs/phase-4/README.md` referencian endpoints `/ia/*`, `/etl/run` inexistentes) |
| **Refactorizaciones** | Consolidar helper de filtro "Todos"/"Todas" duplicado en ~10 builders backend; eliminar componentes React muertos (`SemaphoreChart`, `TrendChart`, `SunburstChart`, `PagePlaceholder`, etc. — 12 archivos sin importar) |
| **Optimizaciones** | Paginación server-side real en Seguimiento Operativo; invalidación de caché cruzada entre workers backend |
| **Nuevas funcionalidades propuestas** | Predicciones de cumplimiento (reutilizar `scripts/analytics/predictor.py` del repo raíz si aplica), alertas proactivas, benchmarking externo, simulación de metas, panel de administración de catálogos/usuarios (§13) |

---

## 3. Priorización

| Hallazgo | Prioridad | Impacto | Complejidad | Justificación |
|---|---|---|---|---|
| Umbrales PDI/Acreditación inconsistentes | **Crítica** | Institucional + Usuario | Baja | Un mismo indicador puede mostrar semáforo distinto entre pantallas — rompe la confianza del usuario final en los datos; el fix es un refactor puntual y acotado |
| Confirmar alcance Tablero Operativo N3 | **Crítica** | Institucional + Operativo | — (decisión) | Sin esta decisión no se puede cerrar el backlog ni calcular el % real de equivalencia funcional; bloquea la firma del acta de aceptación |
| UAT real con usuarios (ronda 1 y 2) | **Crítica** | Institucional | — (proceso) | Ya está bloqueada según `UAT_BUGS.md` (solo plantilla); es precondición explícita del Hito H8 |
| Cascada Subproceso rota en Informe por Procesos | Alta | Operativo | Baja | Usuarios de Informe por Procesos ven un comportamiento distinto al de CMI Procesos, generando confusión operativa; fix de una tarde |
| IA generativa real en fichas | Alta | Usuario | Media | Funcionalidad diferenciadora visible al usuario final que existía en legacy; requiere decisión de producto + integración de API externa |
| PDF de ficha individual | Alta | Usuario | Baja-Media | Reutiliza `pdf_service.py` ya existente; brecha visible y acotada |
| `response_model` faltante en endpoints de negocio | Alta | Técnico | Media | Contratos API frágiles ante cambios de frontend; riesgo técnico silencioso que puede romper producción sin aviso |
| CRUD OM completo en frontend | Media | Operativo | Baja | Backend ya lo soporta; solo falta exponer formularios de editar/cerrar |
| Paginación real Seguimiento Operativo | Media | Usuario | Baja-Media | Pérdida de visibilidad si el dataset crece; no crítico mientras el volumen actual sea manejable |
| Unificar librería de gráficos | Media | Técnico | Media | Deuda de mantenimiento a mediano plazo, no bloqueante para cutover |
| Unificar colores de semáforo (3 fuentes) | Media | Técnico + Usuario | Baja | Riesgo de drift visual; fix mecánico de consolidación |
| Gráficas heatmap/radar/gauge/bullet | Baja-Media | Usuario | Media | Depende de confirmar si estaban en uso real en producción legacy |
| Persistencia de filtros en URL | Baja | Usuario | Media | Mejora de UX compartida por ambos sistemas, no es una regresión de v2 |
| Limpieza de código muerto (componentes React) | Baja | Técnico | Baja | No afecta al usuario, mejora mantenibilidad |
| Actualizar documentación de fases | Baja | Técnico | Baja | Solo confusión interna del equipo, sin impacto en producción |
| Nuevas funcionalidades (IA predictiva, benchmarking, simulación) | Baja (para este ciclo) | Institucional | Alta | Deseables pero no bloquean el cutover; se agenda como Bloque 11.D / backlog v2.1 |

---

## 4. Backlog Maestro

| ID | Épica | Módulo | Historia de usuario | Descripción funcional | Criterios de aceptación | Dependencias | Prioridad | Complejidad | Estimación | Responsable sugerido | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A-01 | A. Paridad numérica | PDI/Acreditación (backend) | Como usuario de PDI/Acreditación, quiero que el semáforo de un indicador coincida con el que veo en CMI/Resumen General, para confiar en los datos | Refactorizar `PDIService._classify_estado` para reutilizar `domain/categorization.py::categorizar_cumplimiento()` en vez de umbrales hardcodeados en escala de % entero. **Nota (jul-2026): `categorizar_cumplimiento()` ahora tiene 3 regímenes** (Regular, Plan Anual, Negativo-Porcentual — ver `IDS_NEGATIVO_PCT` en `constants.py`), no 2; el refactor debe delegar completamente en la función central para heredar los 3 automáticamente, no solo replicar Regular+PA | Mismos indicadores muestran el mismo nivel de semáforo en PDI y en CMI, incluyendo los 4 IDs del régimen Negativo-Porcentual (121, 207, 377, 561) si aparecen en PDI/Acreditación; test unitario que compara ambos paths con el mismo input | Ninguna | Crítica | Baja | 8h | Backend | Por hacer |
| A-02 | A. Paridad numérica | Todos | Como Product Owner, quiero un reporte de paridad numérica end-to-end (v2 vs. legacy) para todos los módulos, no solo KPIs globales | Extender `scripts/uat_verify.py` para cubrir PDI/Acreditación, Plan de Mejoramiento y Seguimiento Operativo | Reporte JSON con diff ≤0.01% en los 4 módulos no cubiertos hoy | A-01 | Crítica | Media | 16h | Backend/QA | Por hacer |
| B-01 | B. Confirmación de alcance | Tablero Operativo N3 | Como Product Owner, quiero una decisión formal sobre el Tablero Operativo N3 para poder cerrar el backlog de paridad funcional | Sesión con stakeholders de Calidad/Procesos; documentar decisión (migrar / descontinuar) en un ADR o nota de alcance | Decisión documentada y aprobada por el sponsor del proyecto | Ninguna | Crítica | — | 4h (reunión) | Product Owner | **Hecho** — decisión: **migrar** (ver `ADR-009-decisiones-bloque-11a.md`) |
| B-02 | B. Confirmación de alcance | Tablero Operativo N3 | Como usuario operativo, quiero el módulo Kanban/QC/Trazabilidad en v2 si B-01 confirma que sigue en uso | Diseñar e implementar el módulo equivalente en Next.js/FastAPI, reutilizando patrones ya existentes (filtros, tabs, KPIs) | Paridad funcional con `tablero_operativo.py` legacy validada por usuarios reales | B-01 (solo si aplica) | Alta (confirmada) | Alta | 80-120h | Full-stack | Activado — pendiente de exploración del legacy |
| C-01 | C. IA y narrativas | CMI Estratégico, CMI Procesos | Como Product Owner, quiero decidir si se porta la integración con Claude del legacy o se documenta como decisión de producto | Evaluar costo/beneficio de portar `services/ai_analysis.py` (legacy) al backend v2, dado que `ADR-007-ia.md` ya contempla IA | Decisión documentada; si es "sí", historia C-02 se activa | Ninguna | Alta | — | 4h (análisis) | Product Owner + Arquitecto | **Hecho** — decisión: **integrar Claude real** (ver `ADR-009-decisiones-bloque-11a.md`) |
| C-02 | C. IA y narrativas | CMI Estratégico, CMI Procesos | Como analista, quiero ver un análisis narrativo generado por IA real en la ficha de un indicador, igual que en el legacy | Integrar API de Claude en `narrativa_ia`/`generate_ficha_narrativa_heuristica`, con fallback heurístico si no hay API key (igual patrón que legacy) | Ficha de indicador muestra narrativa generada por LLM cuando `ANTHROPIC_API_KEY` está configurada; fallback funcional sin key | C-01 (si aprueba) | Alta (confirmada) | Media | 24h | Backend | Activado |
| D-01 | D. Exportación y reportes | CMI Estratégico | Como usuario, quiero descargar en PDF la ficha individual de un indicador, igual que en el legacy | Extender `pdf_service.py` con función `generar_ficha_indicador(indicador_id)` + endpoint `GET /reports/ficha/{id}` + botón en `CmiFichaModal` | PDF descargable con los mismos datos que muestra el modal (meta/ejecución/histórico/nivel) | Ninguna | Alta | Baja-Media | 12h | Full-stack | Por hacer |
| E-01 | E. Consistencia de filtros/UX | Informe por Procesos | Como usuario de Informe por Procesos, quiero que el filtro Subproceso dependa de Proceso, igual que en CMI Procesos | Aplicar el mismo patrón de `cmi-procesos/page.tsx:68-71,175` a `informe-procesos/page.tsx` | Al cambiar Proceso, Subproceso se resetea y solo muestra opciones válidas | Ninguna | Alta | Baja | 4h | Frontend | Por hacer |
| E-02 | E. Consistencia de filtros/UX | Seguimiento Operativo | Como usuario, quiero ver todos los registros de la tabla de detalle, no solo los primeros 200 | Implementar paginación server-side en `GET /seguimiento/dashboard` o un endpoint paginado dedicado, y consumirlo en el frontend | Tabla soporta más de 200 filas sin pérdida de datos, con paginación visible | Ninguna | Media | Baja-Media | 12h | Full-stack | Por hacer |
| E-03 | E. Consistencia de filtros/UX | Global | Como usuario, quiero que mis filtros persistan al recargar o compartir un enlace | Sincronizar `useState` de filtros con `useSearchParams`/`router.replace` en cada página, extendiendo el patrón ya usado para `cmi_linea` | Recargar la página o abrir el enlace compartido conserva año/mes/proceso/etc. | Ninguna | Baja | Media | 20h (todas las páginas) | Frontend | Por hacer |
| F-01 | F. Deuda de arquitectura | Frontend (global) | Como desarrollador, quiero una única fuente de colores de nivel de semáforo | Eliminar duplicados en `CmiResumenTab.tsx`, `nivelUtils.tsx`, `cmiChartColors.ts`; consolidar en `design-tokens.ts` | Un solo objeto de colores importado en los 3 puntos de uso actuales | Ninguna | Media | Baja | 6h | Frontend | Por hacer |
| F-02 | F. Deuda de arquitectura | Frontend (global) | Como desarrollador, quiero una librería de gráficos consistente para reducir deuda de mantenimiento | Migrar `CmiDonutNivelPlotly` (SVG manual) y `CmiProcesosBarPlotly` (CSS manual) a Plotly, o documentar la excepción como decisión de diseño | Todas las gráficas usan Plotly o hay un ADR que justifica la excepción | F-01 | Media | Media | 16h | Frontend | Por hacer |
| F-03 | F. Deuda de arquitectura | Frontend (global) | Como desarrollador, quiero eliminar componentes no utilizados para reducir confusión en el codebase | Borrar `SemaphoreChart.tsx`, `TrendChart.tsx`, `SunburstChart.tsx`, `PagePlaceholder.tsx`, `LineCards.tsx`, `NarrativaBlock.tsx`, `FilterBar.tsx`, `EmptyState.tsx`, `ErrorState.tsx`, `Skeleton.tsx`, `IndicatorsTable.tsx`, `YoYTable.tsx`, `CmiProcesosTabHighlight.tsx` (o integrarlos si aún se planean usar) | `grep` de imports confirma cero referencias tras el borrado; build pasa limpio | Ninguna | Baja | Baja | 4h | Frontend | Por hacer |
| G-01 | G. Contratos API | Backend (PDI, plan-mejoramiento, informe, seguimiento, fichas CMI) | Como desarrollador frontend, quiero contratos de API tipados para no romper la UI con cambios silenciosos del backend | Definir `response_model` Pydantic para los endpoints que hoy devuelven `dict` sin tipar | `openapi.json` refleja schemas completos para los 5 endpoints listados; tests de contrato (`test_fase6_contracts.py`) extendidos a estos endpoints | Ninguna | Alta | Media | 20h | Backend | Por hacer |
| G-02 | G. Contratos API | Backend (dominio, global) | Como desarrollador, quiero eliminar la duplicación del helper de filtro "Todos"/"Todas" repetido en builders | Extraer helper compartido en `domain/` y reemplazar las ~10 implementaciones locales | Un solo punto de definición, reutilizado en todos los builders afectados | Ninguna | Baja | Baja | 6h | Backend | Por hacer |
| H-01 | H. Documentación y UAT | Migración | Como equipo de proyecto, quiero documentación de fases actualizada y consistente | Actualizar `docs/phase-4/README.md` y `RBAC_MATRIX.md` para reflejar el estado real del código (sin endpoints `/ia/*`, `/etl/run` inexistentes) | Documentos no contradicen `STATUS.md` ni el código real | Ninguna | Baja | Baja | 4h | Arquitecto/Tech Lead | Por hacer |
| H-02 | H. Documentación y UAT | Migración | Como Product Owner, quiero ejecutar la Ronda 1 de UAT con usuarios clave | Presentar v2 en staging, completar `UAT_CHECKLIST.md`, registrar hallazgos reales en `UAT_BUGS.md` | Checklist completo; bugs reales registrados con severidad | Cierre de Bloques 11.A y 11.B (ver §5) | Crítica | — | 16h (sesiones) | Product Owner/QA | Por hacer |
| H-03 | H. Documentación y UAT | Migración | Como Product Owner, quiero corregir todos los bugs bloqueantes antes de la Ronda 2 de UAT | Triage y resolución de ítems 🔴 BLOQUEANTE de `UAT_BUGS.md` | Cero bugs 🔴 BLOQUEANTE abiertos | H-02 | Crítica | Variable | Variable | Equipo completo | Por hacer |
| H-04 | H. Documentación y UAT | Migración | Como Product Owner, quiero verificar paridad numérica final y firmar el acta de aceptación | Ejecutar `scripts/uat_verify.py` en todos los módulos, Ronda 2 de UAT, firma de `ACCEPTANCE_DOCUMENT.md` | Paridad ≤0.01% en todos los módulos; acta firmada por usuarios clave | H-03, A-02 | Crítica | — | 8h | Product Owner | Por hacer |

*Backlog inicial de 20 historias trazables 1:1 a los hallazgos Crítica/Alta/Media del comparativo. Las historias de Prioridad Baja (persistencia de filtros completa, limpieza de código muerto, documentación) se incluyen para completitud pero no bloquean el cutover — ver Bloque 11.C.*

---

## 5. Roadmap por fases (sub-bloques de la Fase 11 — UAT/Validación)

### Bloque 11.A — Estabilización
**Objetivo**: eliminar riesgos de inconsistencia de datos y errores funcionales visibles antes de exponer v2 a usuarios reales en UAT.
- A-01 (umbrales PDI), E-01 (cascada Subproceso Informe Procesos), G-01 (contratos API), B-01 (decisión Tablero Operativo N3).
- **Salida**: sistema con cifras consistentes entre módulos y contratos de API estables — condición previa para que la Ronda 1 de UAT (H-02) tenga sentido.

### Bloque 11.B — Paridad funcional
**Objetivo**: cerrar las brechas funcionales frente al legacy identificadas como Alta prioridad.
- D-01 (PDF de ficha), C-01/C-02 (IA real, condicional a decisión de producto), B-02 (Tablero Operativo N3, condicional a B-01), CRUD OM completo en UI.
- **Salida**: SGIND-v2 iguala o supera la cobertura funcional del legacy en el alcance confirmado como vigente.

### Bloque 11.C — Optimización
**Objetivo**: reducir deuda técnica y mejorar consistencia visual/UX sin bloquear el cutover.
- F-01, F-02, F-03 (consistencia visual y limpieza), E-02 (paginación), E-03 (persistencia de filtros), G-02 (refactor helper), H-01 (documentación).
- **Salida**: base de código más mantenible; puede ejecutarse en paralelo a H-02/H-03 (UAT) ya que no afecta paridad funcional ni numérica.

### Bloque 11.D — Evolución (post-cutover / backlog v2.1)
**Objetivo**: funcionalidades nuevas que ninguno de los dos sistemas tiene hoy — explícitamente fuera del criterio de cierre de Fase 11.
- IA predictiva de tendencias, alertas proactivas, benchmarking externo, simulación de metas, panel de administración de catálogos/usuarios, automatización de informes.
- **Salida**: backlog de producto para el ciclo posterior al Hito H9 (Go-live). No se estima en este plan (ver §13 del comparativo para el listado completo).

> **Regla de secuencia**: H-02 (UAT Ronda 1) no debe iniciar hasta cerrar Bloque 11.A. H-04 (firma de aceptación, Hito H8) no debe ejecutarse hasta cerrar Bloque 11.B y H-03. Bloque 11.C puede correr en paralelo a todo lo anterior sin riesgo, dado que no toca lógica de cálculo ni contratos de datos.

---

## 6. Plan por módulo

| Módulo | Objetivo | Actividades clave | Dependencias | Riesgos | Entregables | Criterios de aceptación | Tiempo estimado |
|---|---|---|---|---|---|---|---|
| PDI / Acreditación | Eliminar riesgo de inconsistencia numérica | A-01 | Ninguna | Cambiar umbral puede alterar semáforos ya mostrados a usuarios de staging — comunicar el cambio | Servicio refactorizado + test unitario | Test compara `_classify_estado` vs `categorizar_cumplimiento` con mismos inputs, 0 diffs | 1-2 días |
| Informe por Procesos | Corregir cascada de filtros | E-01 | Ninguna | Bajo | PR con fix + test E2E de filtro | Cypress/Playwright test confirma reseteo de Subproceso al cambiar Proceso | 0.5 día |
| CMI Estratégico / CMI Procesos | Cerrar brecha de IA real y exportación PDF de ficha | C-01, C-02 (condicional), D-01 | Decisión de producto (C-01) | Costo de API Claude en producción; falta de fallback si se agota cuota | Endpoint de narrativa IA + endpoint PDF de ficha + botones en frontend | Narrativa generada por LLM visible con fallback funcional; PDF descargable con datos correctos | 3-5 días (según C-01) |
| Gestión OM | Completar CRUD en UI | Formularios de editar/cerrar sobre endpoints ya existentes (`PUT`, `PATCH /cerrar`, `DELETE`) | Ninguna (backend ya listo) | Bajo | Formularios conectados + validación de rol en UI | Usuario con rol `calidad`/`desempeno` puede editar y cerrar un OM desde la interfaz | 1-2 días |
| Seguimiento Operativo | Paginación real | E-02 | Ninguna | Medio (cambio de contrato de API) | Endpoint paginado + tabla con paginación en frontend | Tabla muestra >200 filas sin pérdida de datos | 1.5 días |
| Tablero Operativo N3 | Decidir y, si aplica, migrar | B-01, B-02 | Decisión de negocio | Alto si se decide migrar tarde en el ciclo (afecta cronograma completo) | ADR de decisión + (si aplica) módulo Next.js/FastAPI equivalente | Decisión documentada; si aplica, paridad funcional validada por usuarios reales de Kanban/QC/Trazabilidad | 0.5 día (decisión) + 10-15 días (si se migra) |
| Todos (transversal) | Consistencia visual y contratos de API | F-01, F-02, F-03, G-01, G-02 | Ninguna | Bajo | PRs de refactor incremental | Build/lint/tests pasan; `openapi.json` completo | 5-7 días acumulados |

---

## 7. Plan técnico

- **Base de datos**: sin cambios de esquema requeridos por este ciclo; verificar que `PDIService` (A-01) no dependa de columnas adicionales fuera de lo ya modelado en `domain/categorization.py`.
- **APIs**: añadir `response_model` Pydantic a `pdi.py`, `plan_mejoramiento.py`, `informe.py`, `seguimiento.py`, fichas CMI (G-01); nuevo endpoint `GET /reports/ficha/{id}` (D-01); extender `GET /seguimiento/dashboard` o crear endpoint paginado (E-02).
- **Backend**: refactor de `PDIService._classify_estado` (A-01); extracción de helper de filtro "Todos" (G-02); integración condicional de Claude en `narrativa_ia` (C-02).
- **Frontend**: unificación de colores de semáforo en `design-tokens.ts` (F-01); migración de gráficas SVG/CSS manuales a Plotly o ADR de excepción (F-02); limpieza de componentes muertos (F-03); patrón de filtros dependientes replicado en Informe por Procesos (E-01); sincronización de filtros con `useSearchParams` (E-03).
- **Componentes reutilizables**: al resolver F-02/F-03, evaluar extraer un wrapper único `<PlotlyChart>` que estandarice `displayModeBar`, `responsive` y tema, reduciendo la necesidad de repetir configuración por componente.
- **Seguridad**: sin cambios adicionales requeridos — RBAC ya cubierto en Fase 7 (completada); solo pendiente la acción manual ya documentada (App Registration Azure AD en tenant institucional) fuera del alcance de este plan.
- **Rendimiento / caché**: evaluar en Bloque 11.C si la caché TTL en memoria por worker (`ttl_cache.py`) requiere mover a un backend compartido (Redis) antes de escalar a múltiples workers Uvicorn en producción — no bloqueante para Fase 11, sí recomendable antes de Fase 12 si el despliegue de producción usa más de un worker.
- **Optimización de consultas**: no aplica (no hay motor de BD relacional para las consultas analíticas — siguen siendo sobre Excel/pandas); fuera de alcance de este ciclo.
- **Documentación técnica**: H-01 (actualizar `RBAC_MATRIX.md` y `docs/phase-4/README.md`).

---

## 8. Plan de calidad

| Tipo de prueba | Alcance en este plan | Herramienta / artefacto existente | Criterio de aprobación |
|---|---|---|---|
| Unitarias | A-01 (comparación de umbrales), G-02 (helper de filtro) | `pytest`, `tests/` backend | Nuevos tests pasan; cobertura del módulo afectado no disminuye |
| Integración | G-01 (contratos de API) | `test_fase6_contracts.py` extendido | `openapi.json` valida contra schemas Pydantic para los 5 endpoints afectados |
| Funcionales | E-01 (cascada de filtros), CRUD OM en UI, D-01 (PDF de ficha) | Playwright E2E (`frontend/e2e/`) | Nuevo spec por funcionalidad; pasa en CI |
| Regresión | Todo el backlog | Suite E2E completa (`navegacion.spec.ts`, `kpis.spec.ts`, `semaforo.spec.ts`) + `pytest tests/` completo | 100% de la suite existente sigue pasando tras cada PR |
| Rendimiento | E-02 (paginación) | Medición manual de tiempo de respuesta antes/después (no hay harness de carga existente) | Tiempo de carga de la tabla no empeora respecto al estado actual con el mismo dataset |
| Seguridad | CRUD OM en UI | Verificación manual de que solo roles `calidad`/`desempeno` ven los controles de edición | Usuario con rol `procesos` no puede editar/cerrar OM desde la UI ni vía llamada directa al endpoint (ya cubierto por `require_admin`, solo falta validar UI) |
| Accesibilidad | F-01 (consistencia de color) | No hay herramienta automatizada configurada — recomendación: incorporar `axe-core` en Bloque 11.C si se prioriza | Contraste de badges de semáforo cumple WCAG AA (verificación manual mínima si no se automatiza) |
| Responsive | No priorizado en este ciclo (fuera de hallazgos críticos del comparativo) | — | Diferido a Fase 3 (Design System), ya "En progreso" de forma independiente |
| Validación de datos | A-02 (paridad numérica extendida) | `scripts/uat_verify.py` extendido a PDI/Plan Mejoramiento/Seguimiento | Diff ≤0.01% entre v2 y legacy para el mismo periodo/dataset en los 4 módulos cubiertos |

**Regla general**: ningún ítem del backlog maestro se marca "Hecho" sin que su criterio de aceptación (§4) esté verificado por al menos un tipo de prueba de esta tabla, siguiendo la regla ya vigente en el proyecto ("Build + lint + tests deben pasar antes de cerrar cualquier fase o tarea" — `ROADMAP.md`).

---

## 9. Gestión de riesgos

| Riesgo | Probabilidad | Impacto | Criticidad | Plan de mitigación | Plan de contingencia | Responsable |
|---|---|---|---|---|---|---|
| Umbrales PDI inconsistentes se descubren después del cutover | Media | Alto | **Alta** | Ejecutar A-01/A-02 antes de cerrar Bloque 11.A, con test automatizado que impida regresión futura | Si se detecta post-cutover: hotfix urgente + comunicación a usuarios afectados + re-ejecución de `uat_verify.py` | Backend Lead |
| Tablero Operativo N3 resulta ser crítico y se descubre tarde en el ciclo | Media | Alto | **Alta** | Forzar la decisión B-01 al inicio del Bloque 11.A, no dejarla para el final | Si se decide migrar tarde: replantear cronograma de Fase 11/12, comunicar retraso a stakeholders con anticipación | Product Owner |
| UAT real no se ejecuta con suficiente profundidad (se firma el acta sin validación genuina) | Baja-Media | Alto | **Alta** | H-02/H-03/H-04 como gate obligatorio antes de Fase 12, con checklist de 80+ criterios ya existente (`UAT_CHECKLIST.md`) | Si se presiona por fecha: escalar a sponsor del proyecto antes de aceptar firma sin validación completa | Product Owner + Sponsor |
| Integración de IA real (Claude) introduce costo operativo no presupuestado | Media | Medio | Media | Decisión C-01 debe incluir estimación de costo de API antes de aprobar C-02 | Si el costo es alto: mantener heurística actual y documentar como decisión de producto (no regresión, sino alcance definido) | Product Owner |
| Cambios en `response_model` (G-01) rompen contratos que el frontend ya asume implícitamente | Baja | Medio | Media | Ejecutar G-01 con tests de contrato antes de tocar frontend; hacerlo en una rama separada con revisión de diffs de `openapi.json` | Si rompe algo: rollback del PR de schema, ajustar y re-desplegar en staging antes de reintentar | Backend Lead |
| Deuda de caché por worker (multi-proceso Uvicorn) causa datos desincronizados en producción con >1 worker | Baja (si producción usa 1 worker inicialmente) | Medio | Media | Confirmar configuración de workers de producción antes de Fase 12; si es >1, evaluar caché compartida (Redis) antes del cutover | Si aparece en producción: reducir a 1 worker temporalmente mientras se implementa caché compartida | DevOps/Backend Lead |

---

## 10. Cronograma (sprints de 2 semanas, dentro de Fase 11)

| Sprint | Objetivo | Historias | Entregables | Dependencias | Hito |
|---|---|---|---|---|---|
| **Sprint 1** | Cerrar Bloque 11.A (estabilización) | A-01, E-01, G-01, B-01 (decisión) | Umbrales unificados, filtro corregido, contratos API tipados, decisión Tablero N3 documentada | Ninguna | Fin de Bloque 11.A |
| **Sprint 2** | Iniciar Bloque 11.B (paridad funcional) | D-01, C-01 (decisión), CRUD OM en UI | PDF de ficha, decisión sobre IA real, formularios de edición/cierre de OM | Sprint 1 | — |
| **Sprint 3** | Continuar Bloque 11.B / iniciar UAT Ronda 1 | C-02 (si aplica), A-02, H-02 | Narrativa IA integrada (condicional), reporte de paridad extendido, checklist UAT completado | Sprint 1 (11.A cerrado) | UAT Ronda 1 ejecutada |
| **Sprint 4** | Corrección de hallazgos de UAT + Bloque 11.C en paralelo | H-03, F-01, F-02, F-03, E-02 | Cero bugs bloqueantes, consistencia visual, paginación real | Sprint 3 | — |
| **Sprint 5** | Cierre y validación final | H-04, E-03, G-02, H-01 (documentación) | `ACCEPTANCE_DOCUMENT.md` firmado, filtros persistentes, documentación actualizada | Sprint 4 | **Hito H8 — UAT aprobado** |
| **Sprint 6 (condicional)** | Solo si B-01 determina migrar Tablero Operativo N3 | B-02 | Módulo Tablero Operativo equivalente en v2 | B-01 = "migrar" | Ajusta fecha de H8 si aplica |

*Tras Sprint 5 (o 6 si aplica), el proyecto queda listo para retomar Fase 12 (Cutover) según el runbook ya existente (`CUTOVER_RUNBOOK.md`), fuera del alcance de este plan.*

---

## 11. Indicadores del proyecto (KPIs)

| KPI | Definición | Fuente de medición |
|---|---|---|
| % de funcionalidades migradas | Historias del backlog maestro en estado "Hecho" / total | Tablero de sprint (Jira/Linear/GitHub Projects) |
| % de funcionalidades validadas | Historias con criterio de aceptación verificado por prueba / total "Hecho" | Resultados de CI + checklist manual |
| Cobertura de pruebas | % líneas cubiertas backend/frontend | `pytest --cov`, reporte de Playwright |
| Defectos por sprint | Bugs nuevos registrados en `UAT_BUGS.md` por sprint | `UAT_BUGS.md` |
| Tiempo promedio de resolución de defectos | Días entre apertura y cierre de un bug en `UAT_BUGS.md` | `UAT_BUGS.md` (con fecha de apertura/cierre) |
| Velocidad del equipo | Puntos/horas completados por sprint vs. estimado | Tablero de sprint |
| Cumplimiento del cronograma | Sprints entregados en fecha / total planificado (§10) | Seguimiento de hitos |
| % de paridad numérica | Resultado de `scripts/uat_verify.py` por módulo | Reporte JSON de `uat_verify.py` |
| Disponibilidad del sistema (staging) | Uptime durante el ciclo de UAT | Monitoreo de staging (smoke tests, `smoke_test.py`) |
| Tiempo de respuesta de la aplicación | P50/P95 de endpoints críticos (`/dashboard/*`, `/cmi/*`) | Medición manual o APM si se incorpora en Bloque 11.C |
| Satisfacción de usuarios (UAT) | Resultado cualitativo de `UAT_CHECKLIST.md` (% de criterios aprobados sin observaciones) | `UAT_CHECKLIST.md` |

---

## 12. Criterios de cierre

La migración se considera lista para avanzar a Fase 12 (Cutover) cuando:

1. **Paridad funcional alcanzada**: todas las historias de Prioridad Crítica y Alta del backlog maestro (§4) están en estado "Hecho", incluyendo la decisión formal sobre el Tablero Operativo N3 (B-01) y, si aplica, su implementación (B-02).
2. **Validación de todos los módulos**: `UAT_CHECKLIST.md` completado al 100% para los 9 módulos activos (+ Tablero Operativo N3 si aplica), sin observaciones abiertas de severidad alta.
3. **Ausencia de defectos críticos**: cero bugs con severidad 🔴 BLOQUEANTE en `UAT_BUGS.md`.
4. **Paridad numérica verificada**: `scripts/uat_verify.py` reporta diferencia ≤0.01% entre v2 y legacy en todos los módulos con datos cuantitativos (incluyendo PDI/Acreditación tras A-01).
5. **Aprobación por parte de los usuarios**: `ACCEPTANCE_DOCUMENT.md` firmado por los usuarios clave designados (directivos, analistas de planeación), conforme al Hito H8 ya definido en `ROADMAP.md`.
6. **Documentación técnica actualizada**: `RBAC_MATRIX.md`, `docs/phase-4/README.md` y `STATUS.md` reflejan el estado real del sistema (H-01).
7. **Despliegue exitoso en producción**: ejecución del `CUTOVER_RUNBOOK.md` (Fase 12, fuera del alcance directo de este plan pero condicionada a los 6 puntos anteriores) con monitoreo de 48 horas sin incidentes críticos.

---

## Recomendaciones finales

1. **No fijar fecha de cutover hasta cerrar B-01** (decisión sobre Tablero Operativo N3) — es la única incertidumbre de este plan que puede alterar el cronograma en un orden de magnitud (días vs. semanas adicionales).
2. **Priorizar A-01 sobre cualquier otra tarea de Sprint 1** — es el hallazgo de mayor riesgo reputacional (cifras distintas del mismo indicador en pantallas distintas) y tiene la complejidad más baja de todo el backlog crítico.
3. **Tratar C-01/C-02 (IA real) como decisión de producto, no como bug** — a diferencia de A-01, no hay una "respuesta correcta" única; documentar la decisión evita que quede como brecha percibida indefinidamente.
4. **Ejecutar Bloque 11.C en paralelo, nunca como bloqueante** — ninguna de sus tareas afecta paridad numérica ni funcional; retrasar el cutover por deuda visual sería desproporcionado frente al riesgo real.
5. **Complementar este plan con validación visual en navegador** antes de Sprint 3 (UAT Ronda 1) — todo el análisis previo (comparativo + este plan) se basó en revisión de código estático, no en interacción real con ambas aplicaciones.
