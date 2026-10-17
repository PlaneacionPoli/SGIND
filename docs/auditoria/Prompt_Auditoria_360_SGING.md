# Prompt de auditoría 360° — SGING (Sistema de Gestión de Indicadores, Poli)

> Versión ajustada del prompt maestro `Prompt_Auditoria_360_Metodologia_Proyectos.md`
> al repositorio real de SGING. Conserva los principios y la estructura por fases del
> original, pero elimina lo que no aplica (p. ej. Machine Learning, microservicios) y
> añade los riesgos propios de este sistema.

## Rol

Actúa como un equipo multidisciplinario: arquitecto/a de software, desarrollador/a
full-stack (FastAPI + Next.js), ingeniero/a de datos (ETL sobre Excel), especialista en BI
y visualización de indicadores, especialista en seguridad de aplicaciones y en calidad,
testing y DevOps.

Objetivo: auditar SGING con evidencia verificable, producir un diagnóstico priorizado y un
plan de corrección, y destilar de ello una metodología reutilizable para los demás
proyectos del workspace `Proyectos_DS`.

---

## 0. Contexto verificado del proyecto (punto de partida, no sustituto de la inspección)

Verifica cada punto antes de darlo por cierto; si algo ya no coincide, es un hallazgo.

- **Qué es:** plataforma de seguimiento de indicadores institucionales del Politécnico
  Grancolombiano (PDI, CMI estratégico y por procesos, Plan de Mejoramiento, Retos/Proyectos,
  Gestión OM, Seguimiento operativo, Informe por procesos, POLISIGS).
- **Backend:** `backend/` — FastAPI 0.115, SQLAlchemy async + asyncpg, Pydantic 2, JWT
  (python-jose), OTP por correo, MSAL, `google-genai` (Gemini) para narrativas, reportlab /
  playwright / jinja2 para PDF e informes. Capas: `app/api/v1/endpoints`, `app/services`,
  `app/domain` (reglas de negocio y *builders*), `app/models`, `app/schemas`, `app/core`.
- **Frontend:** `frontend/` — Next.js 14 (App Router), React 18, TanStack Query, Zustand,
  Tailwind, Plotly **y** Recharts, Vitest + Playwright.
- **Datos:** el backend lee **Excel** desde `data/` (`data/output/Resultados Consolidados.xlsx`
  como fuente oficial) y usa PostgreSQL 16 solo para usuarios/auditoría/alertas
  (`database/migrations/001..006`). Existe además `data/db/registros_om.db` (SQLite).
- **Pipeline de datos:** `scripts/` (~130 archivos; `scripts/etl/` con ~23 módulos,
  `run_pipeline.py`) — ejecución manual; `config/data_contracts.yaml` define contratos.
- **Otros artefactos:** `Tablero BI/` (PBIP/semantic model de Power BI), `legacy-reference/`
  (código Streamlit previo, solo referencia), `artifacts/` (logs y reportes de corridas),
  `core/` y `services/data_validation` en la raíz.
- **Despliegue:** `docker-compose*.yml`, `render.yaml`, Railway, Netlify/Vercel, y
  workflows en `.github/workflows/` (`backend-lint`, `frontend-e2e`, `actualizar-datos`,
  `keep-alive`).
- **Documentación existente:** `docs/funcional`, `docs/tecnico` (incluye
  `09-gaps-y-riesgos.md`), `docs/architecture` (ADRs 001–009, `RBAC_MATRIX.md`),
  `docs/migration` (incl. `PLAN_CIERRE_HALLAZGOS.md` y `PROMPT_AUDITORIA_ACTUAL.md`),
  `docs/graph`, y numerosos `DEPLOY_*.md` en la raíz.

**Auditorías previas:** ya existen hallazgos G-01…G-20 y varias "oleadas" de corrección.
No los repitas. Tu trabajo es (a) **re-verificar** cuáles marcados como "corregidos" lo
están realmente, (b) detectar lo que no se vio, y (c) señalar la documentación que sigue
sin coincidir con el código. Un "corregido" sin evidencia en el código actual se reporta
como regresión o falso cierre.

---

## 1. Principios obligatorios

1. Inspecciona antes de proponer. Fuente de verdad: código y ejecución, no documentos.
2. Todo hallazgo lleva evidencia (ruta:línea, comando, salida) y un estado:
   **Confirmado**, **Probable (requiere validación)** o **No verificable**.
3. Distingue funcionalidad *implementada y verificada*, *parcial*, *simulada*, *con errores*,
   *duplicada*, *pendiente* o *no evaluable*. Que exista el archivo no prueba que funcione.
4. No inventes ni declares pruebas aprobadas que no ejecutaste. Registra cada comando
   y su resultado relevante.
5. **Modo diagnóstico, solo lectura.** No modifiques ni elimines código, datos ni
   configuración hasta entregar el diagnóstico y recibir autorización. Los entregables
   de la auditoría se escriben únicamente en `docs/auditoria/`.
6. No expongas secretos: enmascara valores (`abc***`) y recomienda rotación si hay
   exposición histórica. No ejecutes pruebas destructivas ni contra sistemas externos
   (producción en Render/Vercel/Railway, Gemini, Microsoft) sin autorización explícita.
7. Un archivo sin referencias **no** es automáticamente huérfano: considera imports
   dinámicos, convenciones de Next.js (rutas, `layout`, `loading`), tareas programadas,
   workflows de GitHub, Docker, Task Scheduler y ejecución manual de `scripts/`.
8. No mezcles severidad con esfuerzo. No recomiendes tecnologías nuevas sin justificar
   el costo de complejidad.
9. Sin recomendaciones genéricas: cada una con impacto, prioridad, acción, criterio de
   aceptación y prueba de verificación.

### Reglas del entorno (Windows / OneDrive)

- Backend: usar **`backend/.venv312`** (Python 3.12), nunca el Python global 3.14.
  Ejemplo: `SGIND_DATA_PATH=../data PYTHONPATH=. backend/.venv312/Scripts/python.exe -m pytest tests/ -q`.
- Frontend: `npm.cmd`, no `npm`. Fallos `EINVAL readlink` / `ENOENT _document`: borrar
  `.next` y reintentar; es OneDrive, no un defecto del código.
- Sin `make`. Rutas con espacios/acentos entre comillas. No usar `git stash`.
- No ejecutes el pipeline de `scripts/` sobre `data/` real: trabaja sobre una copia en un
  directorio temporal (el ETL escribe Excel y ya hubo un incidente por la hoja
  *Variables* ausente que dejó Meta/Ejecución=100 en ~88 indicadores).

---

## 2. Fases de la auditoría

Trabaja por etapas, prioriza por riesgo y deja registro de progreso. Si una fase es
inviable por tamaño, acótala y declara la limitación.

### Fase 1 — Inventario y arquitectura real

- Inventario agrupado por: `backend/app/{api,services,domain,models,schemas,core}`,
  `frontend/src/{app,components,hooks,lib,stores,config}`, `scripts/` y `scripts/etl`,
  `database/`, `config/`, `core/` y `services/` (raíz), `data/*`, `Tablero BI/`,
  `legacy-reference/`, `artifacts/`, `.github/`, `docs/`.
- Reconstruye la arquitectura **implementada** (diagramas Mermaid: contexto, componentes,
  flujo de datos Excel→ETL→API→UI, despliegue). Marca lo inferido.
- Puntos a decidir explícitamente: ¿qué lee realmente el backend, Excel o Postgres?;
  ¿quién usa `data/db/registros_om.db`?; ¿qué hacen `core/` y `services/` en la raíz
  frente a `backend/app/core`?; ¿`Tablero BI` se alimenta de las mismas fuentes que la
  API y calcula igual?; ¿qué parte de `legacy-reference/` sigue referenciada?

### Fase 2 — Calidad de código y arquitectura

- **Backend:** separación `endpoints → services → domain`; duplicación entre *builders*
  (`cmi_builders`, `procesos_builders`, `resumen_builders`, `om_builders`, `informe_builders`…);
  manejo de errores; tipado y validación Pydantic; `ttl_cache`/`tracking_cache`
  (invalidez, tamaño, concurrencia); lectura repetida de Excel; trabajo bloqueante dentro
  de funciones `async`; `core/concurrency.py`; generación de PDF/Playwright en proceso web.
- **Frontend:** componentes huérfanos (p. ej. `IndicatorsTable.tsx`), doble escala de
  porcentaje (fracción 0–1 vs 0–100), dos librerías de gráficos (Plotly/Recharts) y su
  costo en bundle, manejo de estados de carga/error/vacío, tipos TypeScript, accesibilidad.
- **Pipeline:** idempotencia, reprocesamiento, respaldo previo (`_backup_pre_*`), logs,
  reintentos (`retry_handler`), `validation_gate`, `versioning`, acoplamiento con rutas
  absolutas o nombres de hoja Excel.
- Ejecuta: `ruff`, `pytest` (backend), `vitest` y `tsc --noEmit` (frontend); `playwright`
  solo si el entorno local lo permite. Registra pasa/falla/omitido con cifras.

### Fase 3 — Catálogo funcional

Por cada módulo (`resumen-general`, `cmi-estrategico`, `cmi-procesos`, `informe-procesos`,
`plan-mejoramiento`, `gestion-om`, `seguimiento-operativo`, `seleccion-pdi`, `polisigs`,
`diagnostico`, login/OTP, exportaciones PDF/Excel, narrativas IA, alertas) documenta:
página → componentes → endpoint → servicio → builder de dominio → fuente de datos →
pruebas, y asígnale uno de los estados de la sección 1.3. Verifica estados vacíos,
errores y roles. Señala módulos redundantes, ocultos o sin consumidor.

### Fase 4 — Calidad analítica, dashboards y UX/UI

- **Una sola definición de cada cifra.** Verifica que cumplimiento, semáforo, signo
  (indicadores inversos), tipo de acumulación, periodicidad especial, escala de moneda,
  años/ciclos y "No aplica" se calculen igual en: backend, frontend, exportaciones PDF/Excel,
  narrativas IA y `Tablero BI` (DAX). Contrasta con `docs/funcional/03-como-se-calculan-los-indicadores.md`.
- Casos límite: Meta=0/NULL (hoy se ve igual que "sin dato"), indicadores sin hoja
  *Variables*, valores 0–1 vs 0–100, periodos sin reporte, regímenes especiales
  (Plan Anual vs. otros), cambios de filtro (año/periodo/línea/proceso) y su propagación.
- Trazabilidad: de la tarjeta/gráfico → endpoint → fila del Excel fuente. Fecha de corte
  visible y frescura de datos (el pipeline es manual: ¿se avisa si está desactualizado?).
- Por cada gráfico/tabla/reporte: ¿qué pregunta responde y qué decisión permite?; conservar,
  rediseñar, fusionar o retirar. Revisa responsive, contraste, navegación y exportación.
- Las narrativas generadas por Gemini: ¿se basan solo en datos calculados?, ¿hay riesgo
  de cifras inventadas?, ¿se registra qué prompt/versión/datos se usaron?

### Fase 5 — Datos y ETL

- Linaje completo: fuentes (`data/raw`, API Kawak, anexos CNA, POLISIGS) →
  `scripts/etl` → `data/output/*.xlsx` → backend → UI → Power BI.
- Calidad: completitud, unicidad de `Id`, consistencia entre hojas, integridad entre
  catálogo y consolidado, validez según `config/data_contract*.yaml` (nota: hay **dos**
  archivos de contrato, `data_contract.yaml` y `data_contracts.yaml`; ¿cuál se usa?).
- Reconciliación: recomputa una muestra de indicadores desde la fuente y compara con lo
  que muestran API y UI. Distingue error de dato, de código y diferencia legítima.
- Higiene de `data/output`: múltiples copias (`- copia`, `.bak`, `revvv.xlsx`) y
  carpetas `_backup_pre_*`: ¿cuál es la fuente oficial?, ¿qué lee el sistema?, ¿qué debe
  versionarse, archivarse o ignorarse?
- Datos personales: ¿hay información de personas en los Excel o en git?

### Fase 6 — Documentación, archivos huérfanos y deuda técnica

- Verifica cada documento contra el código: `README.md` de la raíz (solo dice "SGIND"),
  `docs/tecnico/*`, `docs/funcional/*`, ADRs (p. ej. ADR-007 menciona Anthropic y el código
  usa Gemini), `RBAC_MATRIX.md` frente a las dependencias reales de roles en cada endpoint,
  y los 5 `DEPLOY_*`/`RAILWAY_*` de la raíz (¿cuál plataforma es la vigente?, ¿se
  contradicen?). Clasifica: vigente / parcial / desactualizado / duplicado / contradictorio.
- Ejecuta las instrucciones de instalación y arranque tal como están escritas; registra
  dónde fallan.
- Candidatos a revisar (no a borrar): `scripts/` (¿cuáles aparecen en workflows, Docker o
  `run_pipeline.py`?), `core/` y `services/` de la raíz, `impact_report.md`,
  `backend/backend.log`, `frontend/*.log`, `frontend/test-results`, `artifacts/`,
  `legacy-reference/`, tablas Postgres sin consumidor (p. ej. `acciones`), `audit_log` sin
  retención, dependencias declaradas y no usadas (p. ej. `requirements.txt` frente a imports).
- Por elemento: ID, ruta, propósito aparente, referencias (incl. dinámicas), impacto de
  retirarlo, recomendación (conservar/investigar/integrar/archivar/eliminar) y validación previa.
- Repositorio: archivos que no deberían estar versionados (logs, binarios, Excel con datos,
  caches), ausentes que deberían estar, y duplicación de fuentes de verdad (constantes,
  paletas, reglas).

### Fase 7 — Seguridad

Revisión defensiva; no declares el sistema "seguro" por no hallar fallas en lectura estática.

- **Secretos:** `.env*`, `docker-compose*.yml` (defaults como `sgind_dev_password`),
  `render.yaml`, `DEPLOY_*.md`, frontend, scripts, notebooks y **historial de git**
  (`git log -S`/búsqueda de patrones). Enmascara cualquier hallazgo.
- **Autenticación/autorización:** `core/security.py`, `api/deps.py`, `pdi_deps.py`,
  `auth.py` (login, OTP, `ALLOWED_EMAILS`, `dev-token`/`ENABLE_DEV_AUTH`, expiración JWT de
  480 min, algoritmo HS256 y gestión de `SECRET_KEY`, limitación de intentos de OTP).
  Verifica en el **servidor** que cada endpoint exija el rol que `RBAC_MATRIX.md` declara;
  construye la matriz endpoint × rol real y compárala con la documentada.
- **API/web:** CORS (el regex de Render), inyección (SQL, plantillas Jinja/HTML de
  informes y PDF → XSS/SSRF vía Playwright), rutas de archivos en exportaciones y lectura de
  Excel (path traversal), subida de archivos, límites de tasa, cabeceras, mensajes de error
  y logs con datos sensibles, `NEXT_PUBLIC_*` con valores sensibles.
- **IA:** envío de datos institucionales a Gemini (qué campos, base legal/consentimiento),
  inyección de prompt desde datos del Excel, manejo de la clave API.
- **Infra/dependencias:** `pip-audit`/`npm audit` si hay red; versiones sin soporte; Docker
  (usuario no root, volúmenes `ro`), workflows de CI (permisos, secretos, `keep-alive`),
  separación dev/staging/prod, respaldo y restauración de Postgres y de los Excel.
- Clasifica: crítico / alto / medio / bajo y *confirmada* / *configuración riesgosa* /
  *no verificable*, con escenario, condiciones, mitigación y prueba de verificación.

### Fase 8 — Matriz de trazabilidad

Tabla *elemento → documentación → implementación → prueba → estado → acción* para:
funcionalidades, endpoints, indicadores/fórmulas, etapas del pipeline, controles de
seguridad, documentos y archivos. Lista explícitamente: funciones documentadas e
inexistentes, implementadas sin documentar, reglas distintas entre módulos, indicadores
con valores distintos según pantalla/exportación, y riesgos críticos sin prueba (cobertura
real con `pytest --cov`; hoy hay pruebas fallidas y omitidas por triar).

### Fase 9 — Hallazgos consolidados y plan

Un único registro (sin duplicar ni repetir G-xx ya cerrados con evidencia), con: ID,
dimensión, descripción, estado de evidencia, ubicación, impacto, severidad, probabilidad,
esfuerzo, dependencias, prioridad, acción, criterio de aceptación, prueba de verificación,
responsable por rol. Orden: seguridad y pérdida/corrupción de datos → cifras incorrectas
o desactualizadas → disponibilidad → estructura y pruebas → limpieza validada →
documentación → rendimiento/UX → estandarización. Plan por oleadas con criterios de salida.

### Fase 10 — Metodología reutilizable

Destila lo aprendido en un estándar para el portafolio `Proyectos_DS`, con base común y
extensiones por tipo (dashboard estático, Streamlit, full-stack FastAPI+Next.js, ETL sobre
Excel, ciencia de datos). Incluye: estructura de carpetas, gestión de configuración y
secretos, contratos de datos, definición única de indicadores, estrategia de pruebas,
documentación mínima proporcional, versionado de datos de salida, CI, Definición de
Terminado y checklist de auditoría periódica. No impongas la misma estructura a todo.

---

## 3. Entregables (en `docs/auditoria/`, sin sobrescribir nada existente)

Consolida en pocos documentos con un `README.md` índice:

1. `00-resumen-ejecutivo.md` — estado, riesgos top 10, decisiones requeridas.
2. `01-inventario-arquitectura.md` — inventario + diagramas Mermaid.
3. `02-catalogo-funcional.md` — módulos y estado de verificación.
4. `03-codigo-datos-analitica.md` — calidad, ETL, reconciliación de cifras, dashboards.
5. `04-documentacion-y-huerfanos.md` — auditoría documental e inventario de archivos.
6. `05-seguridad.md` — registro de vulnerabilidades y riesgos.
7. `06-matriz-trazabilidad.md` y `07-hallazgos-y-plan.md` (registro único + oleadas).
8. `08-metodologia-estandar.md` — estándar, estructuras y checklist de auditoría.
9. `09-limitaciones-y-decisiones.md` — qué no se pudo verificar y qué requiere aprobación
   humana (p. ej. borrar copias de Excel, destino de la tabla `acciones`, plataforma de
   despliegue vigente, rotación de secretos).

## 4. Criterio de cierre

Debes poder responder con evidencia: ¿qué hace realmente SGING y de dónde salen sus
cifras?; ¿se calculan igual en API, UI, exportaciones y Power BI?; ¿qué funciona, falla o
falta?; ¿qué hallazgos "corregidos" se sostienen?; ¿qué documentación engaña?; ¿qué archivos
y datos no aportan valor o no tienen fuente de verdad clara?; ¿qué riesgos de seguridad
atender primero?; ¿qué pasa si nadie corre el pipeline?; ¿qué no se pudo comprobar y por qué?

## 5. Instrucción de ejecución

Empieza por presentar el **alcance, componentes identificados y limitaciones de acceso**
(sin tocar archivos), luego ejecuta las fases en orden de riesgo y entrega el diagnóstico
inicial. **No modifiques ni elimines nada fuera de `docs/auditoria/` hasta que el diagnóstico
sea aprobado.** Si no puedes ejecutar algo, indica qué conclusiones son estáticas y cuáles
requieren validación en entorno funcional.
