# Testing — estado real (verificado ejecutando, no leyendo README)

## Backend

- **Corrección (2026-09-20, Oleada 0):** el hallazgo original de esta
  sección decía que `pytest` no podía ejecutarse por incompatibilidad
  Python 3.14/SQLAlchemy 2.0.36. Eso fue un **falso negativo** del primer
  pase de auditoría: se ejecutó con el Python 3.14 global de Windows en vez
  de usar el entorno correcto del proyecto. **Ya existe un virtualenv
  válido en `backend/.venv312`** (Python 3.12.10 + SQLAlchemy 2.0.36,
  alineado con `requirements.txt`), documentado en `backend/README.md`
  desde el 2026-09-18 (antes de esta auditoría). Con
  `backend/.venv312/Scripts/python.exe -m pytest`, la suite corre:
  **109 passed, 16 skipped, 35 failed** (SGIND_DATA_PATH=../data; cifra
  actualizada en Oleada 1 tras eliminar el módulo PDI y sus 14 tests, ver
  `09-gaps-y-riesgos.md` G-16).
- **Los 35 fallos reales, triados:**
  - `tests/test_fase10_staging.py` (18 fallos) — esperan una estructura
    `sgind-v2/*` que no existe en este repo (mismo problema que G-08 en
    `STATUS.md`/`ROADMAP.md`); tests a reescribir con las rutas reales, no
    un problema de código de producción.
  - `tests/test_fase4_completions.py` (6 fallos, `assert 500 == ...`) —
    requieren PostgreSQL activo para el CRUD de OM; fallan por falta de
    base de datos en el entorno local, no por un bug.
  - `tests/test_fase8_migration.py` (3 fallos, `ModuleNotFoundError`) —
    import roto, a revisar.
  - `tests/test_domain.py::test_retos_category_umbral_95` — a revisar,
    podría ser un síntoma de la duplicación de umbrales (G-03).
  - `tests/test_operational_modules.py`, `tests/test_performance_cache.py`
    — dependen de `Resultados Consolidados.xlsx` con datos reales o de
    rendimiento bajo caché caliente; a revisar caso por caso.
  - **Corrección:** el fallo `test_fase6_contracts.py::test_semaforo_colores_design_tokens`
    que se atribuyó inicialmente a G-03 (duplicación de semáforo) era en
    realidad específico de `app/services/pdi_service.py` — ya no existe,
    el test se eliminó junto con el módulo PDI (Oleada 1). G-03 sigue
    siendo un hallazgo real (ver `05-reglas-de-negocio.md`), pero este
    test en particular no era su evidencia.
  - Ninguno de estos 35 fallos es un problema del entorno Python — el
    entorno ya funciona.
- **Cifras de tests de `STATUS.md`/`ROADMAP.md`:** con el entorno correcto
  se pueden verificar de nuevo; quedan pendientes de comparar una por una
  contra las cifras históricas citadas (20/26, 9+2, 11, 12, 24), ver
  `09-gaps-y-riesgos.md` (G-02, actualizado).
- **`ruff check`/`ruff format --check` — corregido en Oleada 0.** El
  hallazgo original decía "2 errores"; al ejecutar el comando exacto de CI
  (`ruff check app tests`, `backend-lint.yml`) se encontraron en realidad
  **14 errores** (`UP035`/`UP038`, imports e `isinstance` con tuplas en vez
  de `X | Y`) y **13 archivos sin formatear** según `ruff format --check`
  (ese segundo check ni siquiera se había corrido en la auditoría
  original). Se aplicaron `ruff check --fix --unsafe-fixes` y
  `ruff format`, verificados con `pytest` después (mismos 123 passed / 36
  failed / 16 skipped, sin regresiones). Ambos comandos de CI pasan limpio
  ahora.

## Frontend

- **`npm run build`:** el compilador de Next.js pasa limpio
  (`✓ Compiled successfully`, `✓ Generating static pages (17/17)`), pero el
  proceso completo falla al final en el paso de "standalone output"
  (`Error: UNKNOWN: unknown error, copyfile ... threadChild.js`). Es un
  error de sistema de archivos de Windows/OneDrive (el repo vive en una
  carpeta sincronizada por OneDrive, que bloquea archivos intermitentemente
  durante la sincronización) — no es un error de código. Recomendación:
  mover el repo fuera de una carpeta sincronizada por OneDrive para
  builds/CI locales fiables, o excluir la carpeta de la sincronización.
- **`npm run lint`: pasa limpio** (`✔ No ESLint warnings or errors`).
- Suite unitaria: `vitest`, solo un archivo de test
  (`src/lib/design-tokens.test.ts`) — cobertura mínima de lógica real de
  componentes.
- Suite E2E: `@playwright/test` configurado (`playwright.config.ts`,
  scripts `test:e2e*`), no se ejecutó en esta auditoría (requiere el stack
  completo levantado).

## Matriz de riesgo por falta de tests (componentes CORE)

| Componente CORE | Tests | Riesgo |
|---|---|---|
| `domain/categorization.py` (semáforo canónico) | No confirmable (pytest roto) | Alto — es la regla más reutilizada del sistema |
| `domain/calculos.py` | No confirmable | Alto |
| Las 4 reimplementaciones divergentes de semáforo (`cmi_builders.py`, `procesos_builders.py`) | No confirmable | Alto — además de no tener certeza de tests, ya se sabe que divergen entre sí |
| `services/om_service.py` (única escritura transaccional real) | No confirmable | Alto |
| `services/etl_pipeline.py` (merges de enriquecimiento) | No confirmable | Medio-alto |
| `scripts/etl/*` (pipeline de producción real de datos) | Sin evidencia de tests automatizados encontrada en esta auditoría | Alto — es el proceso menos observable y más manual de todo el sistema |
| Frontend `nivelUtils.tsx`/`cmiChartColors.ts` (colores) | Un solo test de design-tokens | Medio |

## Prioridad de remediación

1. Arreglar el entorno de pruebas del backend (bloqueante para verificar
   cualquier otra afirmación de calidad).
2. Corregir los 2 errores de `ruff`.
3. Una vez el entorno funcione, escribir tests de regresión que comparen
   las 4 implementaciones divergentes de semáforo contra
   `categorization.py` para el mismo input — así cualquier corrección de
   duplicación queda protegida contra reintroducir el bug.
