# AUDITORÍA Y RECONSTRUCCIÓN DOCUMENTAL DEL ESTADO ACTUAL — SGING v2

## 1. OBJETIVO

Producir **documentación viva, real y actualizada** de SGING v2 (este
repositorio), tomando el código fuente como única fuente de verdad, y
dejarla en dos capas de lenguaje:

- **Funcional/ejecutiva** — para directivos, analistas de planeación y
  usuarios de negocio que no leen código: qué hace el sistema, qué módulos
  existen, cómo se calculan los indicadores, en lenguaje llano y sin jerga
  técnica innecesaria.
- **Técnica** — para desarrolladores: arquitectura real, endpoints, modelo de
  datos, reglas de negocio con su ubicación exacta en el código, gaps y
  deuda técnica.

No es una comparación contra el Streamlit legacy ni contra ningún otro
aplicativo — describe lo que este repositorio es y hace **hoy**.

Objetivos concretos:

1. Leer y mapear el código real de `backend/`, `frontend/`, `database/` y
   `scripts/` (pipeline de datos).
2. Identificar el CORE funcional: gestión de indicadores, cálculo de
   cumplimiento/semaforización, consolidación de datos, y los módulos de
   dashboard que consumen esos datos.
3. Contrastar cada afirmación de `docs/migration/STATUS.md`,
   `docs/migration/ROADMAP.md` y los ADRs en `docs/architecture/adrs/`
   contra el código — corregir o marcar como obsoleto lo que no se sostenga.
4. Inventariar reglas de negocio y trazarlas hasta su implementación exacta
   (archivo + función).
5. Documentar el modelo de datos real (Postgres vía `database/migrations/` +
   los Excel de `data/` que el backend aún lee).
6. Construir un modelo de nodos/relaciones (grafo) limitado al CORE y sus
   dependencias directas.
7. Identificar vacíos, deuda técnica y riesgos, con evidencia verificable.
8. Priorizar oportunidades de mejora.
9. Publicar el resultado como documentación consultable por ambos públicos.

**Fuera de alcance:** comparar contra `legacy-reference/`, Streamlit, o
cualquier otro aplicativo. Si aparece código que solo tiene sentido en
relación al sistema anterior (p. ej. scripts de migración SQLite→Postgres),
descríbelo por lo que hace hoy en este repo, no por su relación con el
legacy.

---

## 2. PRINCIPIO FUNDAMENTAL: EL CÓDIGO ES LA FUENTE DE VERDAD

No asumas que `STATUS.md`, `ROADMAP.md` o los ADRs reflejan el estado
actual. Para cada afirmación:

**Código → configuración → modelo de datos → API → frontend → tests → doc**

Si hay contradicción entre documento y código:
- documenta la contradicción explícitamente (cita el archivo/línea);
- describe qué está realmente implementado;
- marca la sección del documento como obsoleta.

No modifiques código de negocio durante esta fase, salvo lo estrictamente
necesario para ejecutar una prueba de diagnóstico (correr `pytest`, `npm run
build`, `npm run lint` para confirmar el estado real).

---

## 3. ALCANCE — QUÉ LEER

| Área | Ruta |
|---|---|
| Backend (FastAPI) | `backend/app/api/v1/endpoints/`, `backend/app/domain/`, `backend/app/services/`, `backend/app/models/`, `backend/app/schemas/`, `backend/app/core/` |
| Frontend (Next.js) | `frontend/src/app/`, `frontend/src/components/`, `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts`, `frontend/src/stores/`, `frontend/src/hooks/` |
| Base de datos | `database/migrations/`, `database/queries/`, `database/scripts/` |
| Pipeline de datos (produce los Excel que hoy lee el backend) | `scripts/etl/`, `scripts/cna_extraction/`, `scripts/plan_mejoramiento/`, `scripts/run_pipeline.py`, `scripts/agent_runner.py`, `scripts/consolidar_api.py`, `scripts/actualizar_consolidado.py`, `scripts/generar_reporte.py` |
| Datos consolidados | `data/output/`, `data/raw/`, `data/audit/` |
| Configuración | `config/`, `.env.example` de `backend/` y `frontend/` |
| Documentación existente | `docs/architecture/`, `docs/migration/`, `docs/phase-*/` |
| Tests | `backend/tests/`, `frontend/e2e/` |
| CI/CD | `.github/workflows/` |

No analizar `legacy-reference/` como objeto de comparación; solo si algo del
backend/scripts lo referencia activamente (confirmar con grep de imports,
no asumir).

---

## 4. FASE 1 — INVENTARIO REAL

Para cada área: listar módulos/archivos y su propósito real (no el que
sugiere el nombre); confirmar tecnología real leyendo
`requirements.txt`/`package.json`, no los ADRs.

Verificar en particular `backend/app/services/etl_pipeline.py`: ¿extrae/
consolida datos realmente, o solo lee un Excel ya producido por `scripts/`?
Esto determina si el backend depende de un proceso externo no documentado.

---

## 5. FASE 2 — EL CORE DEL SISTEMA

No asumir de antemano cuáles son los componentes CORE; confirmar con
evidencia:

**Indicadores y cálculo**
- ¿`backend/app/domain/calculos.py` es realmente la fuente única de
  fórmulas, o hay lógica de cálculo/semaforización duplicada en
  `services/` o en componentes de `frontend/src/components/charts` / `cmi/`?
- Ubicar cada regla de clasificación de cumplimiento/tendencia/
  semaforización y verificar si hay más de una implementación.

**Consolidación de datos**
- Qué produce hoy `scripts/etl/*` y `scripts/cna_extraction/` (archivos de
  salida en `data/output/*.xlsx`) y qué consume el backend de ellos.
- Si hay automatización real (cron, GitHub Action) o es manual — confirmar
  en `.github/workflows/`.
- Qué pasa con el backend si `data/output/` deja de actualizarse.

**APIs y endpoints CORE**
- Para cada endpoint en `backend/app/api/v1/endpoints/`: propósito, modelo
  de entrada/salida (`response_model` presente o no), autenticación.
- Cuáles tienen consumidor real en `frontend/src/lib/api.ts` y cuáles no.

**Frontend CORE**
- Páginas de `frontend/src/app/(dashboard)/` conectadas a datos reales vs.
  placeholder/mock.
- Componentes con lógica de negocio que debería vivir en
  `backend/app/domain/`.

---

## 6. FASE 3 — MODELO DE DATOS REAL

- Esquema Postgres real (`database/migrations/*.sql`): tablas, PK/FK,
  constraints.
- Qué tablas usa el backend en producción hoy vs. cuáles existen en el
  esquema pero no se usan.
- Qué datos siguen viviendo en Excel y no en Postgres, y qué endpoints
  dependen de esos Excel directamente.
- Entidades duplicadas, campos calculados que deberían persistirse (o
  viceversa), tablas huérfanas.

---

## 7. FASE 4 — REGLAS DE NEGOCIO

Inventario exhaustivo:

| ID | Regla | Ubicación (archivo:función) | Entrada | Salida | Criticidad |
|---|---|---|---|---|---|

Diferenciar: regla implementada y usada / implementada pero sin caller
(código muerto) / documentada pero no implementada.

---

## 8. FASE 5 — SEGURIDAD Y TESTING (estado actual)

- Autenticación real (`backend/app/services/auth_service.py`, Azure AD/MSAL,
  JWT): qué está activo hoy vs. qué requiere configuración manual pendiente.
- RBAC: confirmar los guards realmente aplicados por endpoint, no solo lo
  documentado en `docs/architecture/RBAC_MATRIX.md`.
- Ejecutar `pytest` (`backend/tests/`) y `playwright` (`frontend/e2e/`),
  reportar qué pasa/falla/se salta hoy.
- Secretos: si aparecen en config o `.env` versionado, reportar
  `SECRET_FOUND → ubicación → criticidad` sin exponer el valor.

---

## 9. FASE 6 — DOCUMENTACIÓN EXISTENTE

| Documento | Estado (vigente/parcial/obsoleto) | Contradicción encontrada | Acción |
|---|---|---|---|

Incluye explícitamente `STATUS.md` y `ROADMAP.md`.

---

## 10. FASE 7 — GAPS, RIESGOS Y OPORTUNIDADES

Gaps clasificados en: documentación, funcional, técnico, datos, seguridad,
calidad, UX — cada uno con evidencia (archivo/línea).

Oportunidades:

| ID | Oportunidad | Problema actual (evidencia) | Beneficio | Esfuerzo | Riesgo | Prioridad |
|---|---|---|---|---|---|---|

Separar en Quick Wins / Mejoras estructurales / Refactorizaciones / Cambios
arquitectónicos. No proponer eliminar nada sin verificar referencias/imports.

---

## 11. FASE 8 — MODELO DE GRAFO (acotado al CORE)

Grafo limitado al CORE y sus dependencias directas: Indicador, Meta,
Medición, Regla de cálculo, Pipeline de consolidación, Endpoint, Página de
dashboard, Tabla/entidad de datos.

Relaciones mínimas: `USES`, `CALLS`, `DEPENDS_ON`, `CALCULATES`, `PERSISTS`,
`READS`, `DISPLAYS`, `TESTED_BY`, `DOCUMENTED_BY`. Cada relación cita su
evidencia (archivo).

Generar en `docs/graph/`: `nodes.json`, `relationships.json`,
`core-graph.json`, `impact-matrix.json`.

```json
{
  "nodes": [
    {"id": "calculos-domain", "type": "module", "name": "domain/calculos.py", "core": true}
  ],
  "relationships": [
    {"source": "dashboard-endpoint", "target": "calculos-domain", "type": "CALLS", "evidence": "backend/app/api/v1/endpoints/dashboard.py"}
  ]
}
```

---

## 12. FASE 9 — ENTREGABLE: DOCUMENTACIÓN VIVA DUAL

Este es el entregable central, no un informe adicional.

### 12.1 Markdown versionado en el repo

```
docs/
├── funcional/          # lenguaje llano, para usuarios no técnicos
│   ├── 01-que-es-sging.md          # propósito, quién lo usa, para qué
│   ├── 02-modulos.md               # qué hace cada módulo del dashboard
│   ├── 03-como-se-calculan-los-indicadores.md
│   ├── 04-glosario.md
│   └── 05-preguntas-frecuentes.md
└── tecnico/             # para desarrolladores
    ├── 01-arquitectura.md
    ├── 02-core-del-sistema.md
    ├── 03-modelo-de-datos.md
    ├── 04-api.md
    ├── 05-reglas-de-negocio.md
    ├── 06-flujos-end-to-end.md
    ├── 07-seguridad.md
    ├── 08-testing.md
    ├── 09-gaps-y-riesgos.md
    └── 10-oportunidades-de-mejora.md
```

Cada documento debe:
- reemplazar (no complementar a ciegas) la parte correspondiente de
  `STATUS.md`/`ROADMAP.md`/ADRs si esta auditoría encontró que estaban
  desactualizados;
- citar la evidencia (archivo/función) en la versión técnica;
- evitar jerga en la versión funcional — un directivo debe poder leer
  `docs/funcional/03-como-se-calculan-los-indicadores.md` y entender la
  fórmula de cumplimiento sin saber Python.

### 12.2 Portal HTML navegable (Artifact)

Publicar además un Artifact HTML que sirva de portal de consulta para
usuarios no técnicos que no quieren abrir el repositorio:

- navegación entre las secciones funcionales (qué es el sistema, módulos,
  cómo se calculan los indicadores, glosario, FAQ);
- una vista simplificada del grafo CORE (Indicador → Meta → Medición →
  Regla → Resultado → Dashboard) en lenguaje visual, no técnico;
- enlaces o referencias a la documentación técnica en `docs/tecnico/` para
  quien quiera profundizar;
- generarlo siguiendo las guías de diseño de artifacts del entorno (cargar
  la skill de diseño de artifacts antes de escribirlo), sin inventar datos:
  todo el contenido debe salir de lo verificado en las fases anteriores.

---

## 13. REGLAS PARA EL ANÁLISIS

1. No inventar funcionalidades ni asumir que algo existe porque debería.
2. No asumir que `STATUS.md`/`ROADMAP.md`/ADRs son correctos.
3. No modificar código de negocio durante el diagnóstico.
4. No declarar algo obsoleto o código muerto sin buscar referencias/imports.
5. No comparar contra el legacy Streamlit ni contra ningún otro aplicativo.
6. Toda conclusión debe tener evidencia (archivo, línea o comando ejecutado).
7. La documentación funcional debe ser legible por alguien sin conocimiento
   técnico; si una sección no puede simplificarse sin perder precisión,
   así indícalo y deja el detalle en la versión técnica.
