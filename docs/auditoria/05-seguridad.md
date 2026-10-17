# 05 — Seguridad (Fase 7)

> Auditoría 2026-10-16, **solo lectura / análisis estático**. Los valores de secretos están
> enmascarados. No se ejecutaron pruebas contra Render/Vercel/Railway/Gemini/Microsoft.
> Nada de lo aquí escrito prueba que el sistema sea "seguro": solo lo revisado.

Estados de evidencia: **C** = Confirmado en código · **P** = Probable (requiere validación) · **NV** = No verificable.

## Resumen

| ID | Sev. | Estado | Hallazgo |
|----|------|:------:|----------|
| S-01 | **Crítico** | C | `POST /auth/email-login` emite JWT sin verificar identidad |
| S-02 | **Alto** | C | `secret_key` con default público y sin validación de arranque |
| S-03 | **Alto** | C | Dependencias frontend con 3 críticas / 4 altas (Next 14.2.35, axios, maplibre/plotly) |
| S-04 | Medio | C | HTML de IA / Excel sin escapar + `dangerouslySetInnerHTML` (XSS) |
| S-05 | Medio | C | Token JWT en query string (`/auth/callback?token=`) |
| S-06 | Medio | C | Sin rate limiting ni lockout por IP en ningún endpoint de auth |
| S-07 | Medio | C | OTP implementado en servicio pero **sin endpoint**: control inexistente en la práctica |
| S-08 | Medio | C | Contenedores backend corren como root (con Chromium/Playwright) |
| S-09 | Bajo | C | `/docs` y `/redoc` abiertos en producción; sin cabeceras de seguridad |
| S-10 | Bajo | C | `.env.staging` estuvo versionado (commit `90dfaab`); solo placeholders |
| S-11 | Bajo | C | Matriz `RBAC_MATRIX.md` no coincide con el código (DELETE OM) |
| S-12 | Bajo | C | JWT de 480 min, sin revocación, sin `aud`/`iss`/`jti` |
| S-13 | Bajo | C | Workflow `actualizar-datos` con `contents: write` |
| S-14 | Info | NV | Datos personales en Excel, envío de datos a Gemini, SMTP, secretos de Render |

## Detalle

### S-01 — Login por correo sin verificación de identidad (Crítico, C)
- Evidencia: `backend/app/api/v1/endpoints/auth.py:61-70` y `backend/app/services/auth_service.py:243-264`.
  El propio docstring admite: *"No hay verificación de identidad: quien conozca un correo
  autorizado puede entrar con él."* El frontend lo usa (`frontend/src/lib/api.ts:104`).
- Escenario: un atacante que conozca (o adivine, el dominio es `@poligran.edu.co`) un correo de
  `ALLOWED_EMAILS` o `ADMIN_EMAILS` obtiene un JWT con ese rol, incluido **administrador**
  (borrar OM, publicar narrativas IA). Nombres de directivos suelen ser deducibles.
- Mitigación: exponer ya el flujo OTP (`request_otp`/`verify_otp` existen), o restringir a
  Azure OIDC; retirar `email-login` en producción.
- Verificación: prueba que `POST /auth/email-login` con correo autorizado devuelva 404/410 en
  producción y que sin OTP válido no se emita token.

### S-02 — `SECRET_KEY` por defecto sin guardia (Alto, C)
- `backend/app/core/config.py:29` → `"change-me-in-production"`. `.env`, `.env.staging` y
  `backend/.env` locales también tienen placeholders (`cha***`/`CHA***`). `main.py` no aborta
  si `environment=="production"` y la clave es la default. Render la define con `sync:false`
  (no se puede verificar que esté puesta → **NV**).
- Impacto: con la clave por defecto cualquiera forja JWT (`sub`=admin) y OTP hashes. Con
  `ENABLE_DEV_AUTH=true` el rol viene del claim del token (`security.py:44-50,69`), sin BD.
- Acción: validador pydantic que falle al arrancar si `environment!="development"` y la clave
  es default o <32 bytes; fallar también si `enable_dev_auth` y `environment=="production"`.
- Rotar la clave real si alguna vez fue la default.

### S-03 — Dependencias vulnerables (Alto, C)
`npm audit --omit=dev`: 7 vulnerabilidades (3 críticas, 4 altas).
- `next@14.2.35` (crítica; fix en 16.4.2, salto mayor): varias DoS/SSRF/cache poisoning; algunas
  RCE aplican a Windows-host o Image Optimizer con AVIF (revisar si se usa `next/image`).
- `axios` (alta, directa, `fixAvailable`): ~20 avisos (prototype pollution, SSRF por redirect…).
- `maplibre-gl` → `plotly.js` (crítica, XSS sanitizer bypass), `postcss`, `probe-image-size`,
  `source-map-js`.
- `pip-audit` no está instalado en `.venv312`: **dependencias Python sin auditar** (NV).
- Acción: `npm.cmd update axios plotly.js`; planificar Next 15/16 como oleada propia con
  pruebas e2e; instalar `pip-audit` en CI.

### S-04 — XSS por HTML no escapado (Medio, C)
- `narrativa_ia_service.py:125-134` y `narrativa_ia_proceso_service.py:230-267` interpolan en HTML
  la salida de Gemini (`diagnostico`, `riesgo`, `recomendacion`) y campos del Excel (`proceso`,
  `nombre`, `indicador`) **sin `html.escape`**. El frontend los pinta con
  `dangerouslySetInnerHTML` en `CmiFichaModal.tsx:122`, `CmiProcesosFichaModal.tsx:92`,
  `CmiLineaAnalisis.tsx:180`, `CmiProcesosAnalisisTab.tsx:142,331`, `ExecutiveNarrative.tsx:19`,
  `TrendVariationTables.tsx:73`. No hay DOMPurify/sanitizador (grep sin resultados).
- Escenario: texto malicioso en una celda del Excel (inyección de prompt o directa) acaba como
  `<img onerror=…>` en el navegador de un administrador → robo del JWT (en localStorage,
  ver AuthGuard/Zustand persist). La fuente es interna, por eso Medio, pero es cadena completa.
- Acción: escapar en backend y permitir solo `<strong>/<br>` (o sanitizar con DOMPurify en UI).
  Prueba: celda con `<img src=x onerror=…>` no debe ejecutar.
- Positivo: Jinja2 usa `select_autoescape`; el `| safe` de `report.html:6` solo inyecta CSS propio.

### S-05 — Token en URL (Medio, C)
`auth.py:58` redirige a `{frontend}/auth/callback?token=<JWT>`: queda en historial del navegador,
logs de proxy/Vercel y cabecera `Referer`. Usar fragmento (`#`) o intercambio por código de un
solo uso.

### S-06 — Sin límite de tasa (Medio, C)
Búsqueda de `slowapi|rate.?limit` en `backend/app`: sin resultados. Solo existe el reenvío de OTP
por correo (60 s) y 5 intentos por correo. Sin límite por IP ni en `email-login`, generación PDF
(Playwright) ni llamadas a Gemini (costo/DoS).

### S-07 — OTP sin endpoint (Medio, C)
`request_otp`/`verify_otp` y el modelo `LoginOtp` existen, pero ningún router los expone
(grep en `api/`: solo `email-login`). La documentación y `render.yaml` (SMTP) sugieren que
el OTP está activo → **documentación engañosa** y control de seguridad inexistente.
Además `_otp_hash` usa HMAC con la `secret_key` (bien), pero 6 dígitos + 5 intentos/correo
sin límite por IP admite fuerza bruta distribuida lenta.

### S-08 — Docker como root (Medio, C)
`backend/Dockerfile` y `Dockerfile.render` no definen `USER` (frontend sí: `nextjs`). El contenedor
ejecuta Chromium (`playwright install --with-deps`) como root; un fallo en la generación de PDF
(HTML con contenido de Excel) tendría privilegios altos.

### S-09 — Superficie expuesta (Bajo, C)
`main.py:70-71` deja `/docs` y `/redoc` siempre activos. Sin `TrustedHostMiddleware` ni
cabeceras (HSTS, X-Content-Type-Options, CSP). CORS con `allow_credentials=True` y
`allow_methods/headers=["*"]`; el regex de Render
(`^(https://sgind(-[a-z0-9-]+)?-planeacion-poli\.vercel\.app|https://sgind\.vercel\.app)$`) está
anclado y es aceptable, mientras el equipo de Vercel controle esos subdominios.

### S-10 — Secretos en git (Bajo, C)
- `.env`, `backend/.env`, `.env.staging` están en `.gitignore` y **no** versionados hoy.
- Historial: `.env.staging` se versionó en `90dfaab` y se quitó en `a6e2483`; sus valores de
  `SECRET_KEY`/`POSTGRES_PASSWORD` empiezan por `CHANGE…` (placeholder). **No se hallaron
  claves reales** (patrones `AIza…`, `sk-…`, `ghp_…`, URLs con credenciales) en el árbol ni en ese
  archivo histórico. El historial completo (182 commits) no se barrió con herramienta dedicada
  (gitleaks/trufflehog no disponibles) → barrido exhaustivo **NV**.
- `sgind_dev_password` aparece como default en `config.py:27`, `docker-compose.yml`, scripts y
  docs. Es de desarrollo; el compose de staging sí exige contraseña (`:?`).
- `frontend/.env.production` versionado: solo URL pública del backend; aceptable.
- `.claude/worktrees/*` contiene copias completas del repo (ver 04-documentacion-y-huerfanos).

### S-11 — RBAC documentado vs. código (Bajo, C)
`RBAC_MATRIX.md:37` marca `DELETE /om/{id}` ✅ para `calidad` y `desempeno`; el código usa
`require_om_deleter = require_roles("administrador")` (`security.py:102`). El código es más
estricto: corregir la doc. Por endpoint: 39 `require_reader`, 17 `require_operational`,
3 `require_admin`, 2 `require_auditor_ia`, 1 `require_om_deleter`, 2 `get_current_user`.
Públicos: `/health`, `/auth/login*`, `/auth/callback`, `/auth/email-login`, `/auth/dev-token`
(404 salvo `ENABLE_DEV_AUTH`). Ningún endpoint de datos queda sin dependencia (matriz completa
por endpoint pendiente en `06-matriz-trazabilidad.md`).

### S-12 — Sesión (Bajo, C)
HS256 simétrico, 480 min, sin `jti`, sin lista de revocación; `logout` solo devuelve una URL.
El rol se relee de BD en cada petición (bueno), salvo en modo dev.

### S-13 — CI (Bajo, C)
`actualizar-datos.yml` tiene `contents: write` + `issues: write` y dispara un deploy hook de
Render con `secrets.RENDER_DEPLOY_HOOK_URL`. Aceptable si solo corre en `schedule`/
`workflow_dispatch`; confirmar que no hay `pull_request_target`. `keep-alive` pega a `/health`
cada 10 min (solo costo).

### S-14 — No verificable
- Contenido real de variables en Render/Vercel/Railway (SECRET_KEY, ALLOWED_EMAILS, SMTP).
- Datos personales en `data/**/*.xlsx` y qué campos viajan a Gemini (prompts incluyen nombres de
  indicador/proceso y cifras; no se vieron correos). Base legal de tratamiento: decisión humana.
- Respaldo/restauración de Postgres.

## Prioridad sugerida
1. S-01 (cerrar `email-login` o implementar OTP) y S-02 (guardia de arranque + verificar/rotar clave).
2. S-04 y S-03 (escape/sanitización; `axios`, `plotly`; plan Next).
3. S-05, S-06, S-08, S-07/S-11 (documentación).
