# 11 - CI/CD Y AUTOMATIZACIONES

**Documento:** 11_CICD_Automatizacion.md  
**Versión:** 1.0  
**Fecha:** 17 de junio de 2026  
**Status:** ✅ Activo

---

## 1. Resumen

El proyecto usa **GitHub Actions** con 6 workflows. La app de producción (Streamlit) despliega automáticamente desde `main` via Streamlit Community Cloud. SGIND v2 usa Docker.

| Workflow | Trigger | Propósito | Bloqueante |
|---|---|---|---|
| `test.yml` | push/PR → main, develop | Tests + cobertura | ✅ Sí (falla si coverage < 50%) |
| `lint.yml` | push/PR → main, develop | Ruff, mypy, bandit | ⚠️ No (continue-on-error) |
| `deploy-staging.yml` | push → develop | Placeholder staging | ❌ No (no hay staging real) |
| `pipeline_automatico.yml` | cron día 5/mes 06:00 UTC | Ejecutar pipeline ETL mensual | ✅ Sí |
| `main_indicadores.yml` | push → main | Deploy Azure Web App | 🟡 Estado incierto |
| `docker-publish.yml` | push → main + tags v* | Publicar imagen Docker SGIND v2 | ✅ Sí |

---

## 2. Workflows Detallados

### 2.1 `test.yml` — Tests y Cobertura

**Archivo:** [`.github/workflows/test.yml`](../../.github/workflows/test.yml)

**Cuándo corre:** En cada push o PR hacia `main` o `develop`.

**Matrix:** Python 3.10 y 3.11 (ambas versiones en paralelo).

**Pasos:**
1. Checkout del repositorio
2. Setup Python con cache de pip
3. Instalar `requirements.txt` + `requirements-dev.txt`
4. Ejecutar pytest con cobertura:
   ```bash
   pytest tests/ \
     --cov=core --cov=services --cov=streamlit_app --cov=scripts \
     --cov-report=xml --cov-report=html --cov-report=term \
     --cov-fail-under=50
   ```
5. Subir reporte a Codecov (`coverage.xml`)
6. Generar badge `coverage.svg`
7. Comentar en PR con resumen de cobertura (verde ≥ 80%, naranja ≥ 60%)

**Gate de calidad:** `--cov-fail-under=50` — el CI falla si la cobertura global cae por debajo del 50%.

**Secrets necesarios:** `GITHUB_TOKEN` (automático).

**Gaps conocidos:**
- Python matrix solo incluye 3.10 y 3.11; el proyecto corre Python 3.14 en producción.
- `MINIMUM_GREEN: 80` en el comentario de PR es visual únicamente; no bloquea el merge.
- La meta de coverage es 70%; el umbral CI (50%) es conservador para no romper el CI actual.

---

### 2.2 `lint.yml` — Análisis Estático

**Archivo:** [`.github/workflows/lint.yml`](../../.github/workflows/lint.yml)

**Cuándo corre:** En cada push o PR hacia `main` o `develop`.

**Herramientas:**
| Herramienta | Propósito | Bloqueante |
|---|---|---|
| `ruff check` | Linting Python (PEP 8, imports, unused vars) | ⚠️ No |
| `ruff format --check` | Verificar formato | ⚠️ No |
| `mypy` | Type checking estático | ⚠️ No |
| `bandit` | Análisis de seguridad (OWASP) | ⚠️ No |

**Gap:** Todos los steps tienen `continue-on-error: true` — los errores de lint no bloquean merges. Esto es intencional para no bloquear el flujo de trabajo mientras se adopta el linter progresivamente, pero implica que código con errores puede entrar a `main`.

**Acción futura:** Eliminar `continue-on-error: true` del step `ruff check` cuando el codebase sea 100% limpio.

---

### 2.3 `deploy-staging.yml` — Deploy Staging

**Archivo:** [`.github/workflows/deploy-staging.yml`](../../.github/workflows/deploy-staging.yml)

**Cuándo corre:** Push a `develop` o manualmente (`workflow_dispatch`).

**Estado:** Placeholder. No existe un entorno staging dedicado actualmente.

**Flujo:**
1. Trigger de deploy (comentario, sin acción real)
2. Trigger opcional de deploy hook si `STAGING_DEPLOY_HOOK_URL` está configurado
3. Health check del smoke test contra `STAGING_URL` (si configurado)

**Nota de plataforma:** La producción usa **Streamlit Community Cloud**, que despliega automáticamente desde `main` sin webhook explícito. Este workflow estaba documentado incorrectamente como "Render.com" — corregido en FASE 8 (jun-2026).

**Secrets opcionales:**
- `STAGING_DEPLOY_HOOK_URL` — URL del hook del entorno staging
- `STAGING_URL` — URL base del entorno staging para health check

---

### 2.4 `pipeline_automatico.yml` — ETL Mensual Automático

**Archivo:** [`.github/workflows/pipeline_automatico.yml`](../../.github/workflows/pipeline_automatico.yml)

**Cuándo corre:** Cron el día 5 de cada mes a las 06:00 UTC.

**Propósito:** Ejecutar el pipeline ETL completo (Paso 1 → Paso 2 → Paso 3) y hacer commit de los datos actualizados al repositorio.

**Jobs:**
1. **`run-pipeline`:**
   - Instala dependencias
   - Ejecuta `scripts/consolidar_api.py`
   - Ejecuta `scripts/actualizar_consolidado.py`
   - Si `ANTHROPIC_API_KEY` está configurado: usa Claude como agente de diagnóstico en caso de fallo
   - Hace commit y push de `data/output/Resultados_Consolidados.xlsx` y `artifacts/`

2. **`verify-outputs`:**
   - Verifica que los archivos de salida existen y tienen el tamaño esperado
   - Corre `scripts/generar_reporte.py` para validar métricas post-ETL

**Secrets requeridos:**
| Secret | Uso | ¿Requerido? |
|---|---|---|
| `GITHUB_TOKEN` | Commit de datos actualizados | ✅ Automático |
| `ANTHROPIC_API_KEY` | Diagnóstico IA en fallos | ⚠️ Opcional (pipeline funciona sin él) |

**Diseño notable:** En caso de error, el pipeline intenta diagnóstico automático via Claude antes de fallar, generando un resumen del error en el log del workflow.

---

### 2.5 `main_indicadores.yml` — Deploy Azure Web App

**Archivo:** [`.github/workflows/main_indicadores.yml`](../../.github/workflows/main_indicadores.yml)

**Cuándo corre:** Push a `main`.

**Propósito:** Deploy de la app a Azure Web App (Python 3.14, slot "Production").

**Estado:** 🟡 Incierto. La producción documentada es Streamlit Community Cloud. Este workflow puede ser:
- Un deploy alternativo/paralelo a Azure que no está activo
- Un vestigio de una prueba piloto de migración a Azure
- Un deploy activo no documentado

**Acción requerida:** Confirmar con el equipo de infraestructura si este deploy Azure está activo. Si no lo está, eliminar el workflow para evitar confusión.

**Secrets necesarios:** `AZUREAPPSERVICE_PUBLISHPROFILE_*` (para Azure).

---

### 2.6 `docker-publish.yml` — Publicar Imagen SGIND v2

**Archivo:** [`.github/workflows/docker-publish.yml`](../../.github/workflows/docker-publish.yml)

**Cuándo corre:** Push a `main` o push de tags `v*` (ej. `v1.0.0`).

**Propósito:** Construir y publicar la imagen Docker de SGIND v2 (backend FastAPI) al registro de contenedores (GitHub Container Registry o Docker Hub).

**Uso:** Para despliegues de SGIND v2 via Docker Compose o en VPS/Render/Railway.

---

## 3. Flujo de Deploy — Streamlit (Producción)

```
Desarrollador
    │
    ├─ push → develop
    │         │
    │         ├─ test.yml (matrix 3.10/3.11) — falla si coverage < 50%
    │         ├─ lint.yml (no bloqueante)
    │         └─ deploy-staging.yml (placeholder)
    │
    └─ PR → main (aprobado)
              │
              ├─ test.yml — GATE OBLIGATORIO
              ├─ lint.yml
              └─ merge a main
                    │
                    └─ Streamlit Community Cloud
                         auto-deploy desde main
                         (sin webhook, sin action)
```

---

## 4. Flujo de Deploy — SGIND v2 (Docker)

```
push a main o tag v*
    │
    └─ docker-publish.yml
          │
          └─ Imagen Docker → ghcr.io / Docker Hub
                │
                └─ Deploy manual via:
                     docker compose up (local)
                     o VPS/Render/Railway con imagen
```

---

## 5. Secretos de GitHub Actions

| Secret | Workflow | Estado | Descripción |
|---|---|---|---|
| `GITHUB_TOKEN` | Todos | ✅ Automático | Token de GitHub para operaciones básicas |
| `ANTHROPIC_API_KEY` | `pipeline_automatico.yml` | ⚠️ Opcional | Claude para diagnóstico de fallos ETL |
| `STAGING_DEPLOY_HOOK_URL` | `deploy-staging.yml` | ❌ No configurado | Hook para staging (no existe aún) |
| `STAGING_URL` | `deploy-staging.yml` | ❌ No configurado | URL del health check staging |
| `AZUREAPPSERVICE_PUBLISHPROFILE_*` | `main_indicadores.yml` | 🟡 Incierto | Credenciales Azure (estado desconocido) |

---

## 6. Verificación Local

```bash
# Ejecutar tests con mismo comando que CI
pytest tests/ \
  --cov=core --cov=services --cov=streamlit_app --cov=scripts \
  --cov-report=term-missing \
  --cov-fail-under=50

# Verificar lint (sin bloquear)
ruff check .
ruff format --check .

# Ejecutar pipeline ETL manualmente
python scripts/consolidar_api.py
python scripts/actualizar_consolidado.py
python scripts/generar_reporte.py
```

---

## 7. Referencias

- **Workflows:** [`.github/workflows/`](../../.github/workflows/)
- **Decisiones CI/CD:** [`07_Decisiones.md` sección 10](07_Decisiones.md#10-decisiones-fase-8--cicd-jun-2026)
- **Pipeline ETL:** [`09_ETL_Pipeline.md`](09_ETL_Pipeline.md)
- **Testing y cobertura:** [`06_Testing_Calidad.md`](06_Testing_Calidad.md)
- **SGIND v2 Docker:** [`sgind-v2/docker-compose.yml`](../../sgind-v2/docker-compose.yml)
