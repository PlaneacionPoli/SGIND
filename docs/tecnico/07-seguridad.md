# Seguridad — estado real

## RBAC

Bien implementado en lo que existe: todos los endpoints de negocio usan
`require_reader` o `require_admin` de forma consistente
(`backend/app/core/security.py:83-97`), incluyendo `DELETE /om/{id}` con
`require_admin` como corresponde. `RBAC_MATRIX.md` documenta dos endpoints
(`etl/run`, `export/*` genérico) que no existen en el código — desfase de
documentación, no vulnerabilidad.

En el frontend, el único gating real por rol está en Gestión OM
(`canEdit = role === "calidad" || role === "desempeno"`,
`gestion-om/page.tsx:27`). El resto del campo `role` en
`config/navigation.ts` solo resalta visualmente tarjetas — **cualquier
usuario autenticado, sin importar el rol, puede navegar a cualquier módulo
por URL**; la protección real de datos ocurre en el backend, no en el
frontend (correcto como diseño, pero hay que ser explícito de que la UI no
oculta nada por rol salvo ese botón de edición de OM).

## `/auth/dev-token` fuera de `production` — corregido en Oleada 0 (2026-09-20)

**Hallazgo original:** `get_current_user` construía el usuario
directamente del payload del JWT sin consultar la base de datos si
`settings.environment == "development"`, aceptando cualquier `role` del
token. `POST /auth/dev-token` solo se bloqueaba con HTTP 404 si
`environment` era literalmente `"production"` — cualquier staging/QA con
otro nombre de entorno quedaba expuesto a auto-escalada de privilegios sin
credenciales reales.

**Corrección aplicada:** se agregó `ENABLE_DEV_AUTH: bool = False` a
`Settings` (`backend/app/core/config.py`). Tanto el bypass de BD en
`get_current_user` (`security.py:69`) como el guard de
`POST /auth/dev-token` (`api/v1/endpoints/auth.py:87`) ahora dependen de
este flag explícito en vez de comparar el nombre del entorno. Por defecto
es `false` en cualquier despliegue; solo `backend/.env` (desarrollo local)
lo activa. Verificado con la suite de tests de `test_fase7_auth.py` sin
regresiones.

## Autenticación — mecanismos activos

Ver [`06-flujos-end-to-end.md`](06-flujos-end-to-end.md#flujo-4--autenticación-tres-mecanismos-coexistentes).
El comentario del propio código en `auth.py:62` describe el login por email
como "temporal", pero es el mecanismo que probablemente esté en uso real
(Azure AD depende de secretos con default vacío en `core/config.py:28-30`,
no verificado si están configurados en el entorno desplegado).

## JWT en el frontend

`frontend/src/lib/jwt.ts:2-9` decodifica el JWT **sin verificar la firma**
para extraer `email`/`role` y mostrarlos en la UI. Es aceptable para
lectura de claims en cliente (la seguridad real recae en el backend), pero
`canEdit` en Gestión OM confía en ese valor decodificado sin revalidación
local — no es un problema de seguridad en sí (el backend vuelve a validar
el rol en cada request), pero conviene documentarlo para que nadie asuma
que el frontend está "protegiendo" algo.

El token se persiste en `localStorage` (`stores/auth-store.ts`, zustand
persist) sin cifrar. El interceptor de Axios (`lib/api.ts:56-75`) limpia la
sesión y redirige a `/login` ante cualquier 401, pero no valida expiración
del JWT del lado del cliente antes de usarlo.

## Secretos

No se encontraron secretos reales versionados. `backend/.env` y
`frontend/.env.local` no están trackeados en git (cubiertos por
`.gitignore`). `.env.staging` (raíz) **sí está trackeado**, pese a que su
propio comentario interno dice que no debería estarlo — pero todos sus
valores son placeholders (`CHANGE_ME_...`, secretos vacíos), criticidad
baja. `frontend/.env.production` trackeado solo contiene variables públicas
de Next.js (`NEXT_PUBLIC_*`), correcto por diseño.

**Recomendación:** sacar `.env.staging` del control de versiones (o purgar
su historial si alguna vez tuvo un valor real) para que el propio comentario
del archivo deje de ser falso.

## IA

El backend usa `google-genai` (Gemini), no la API de Anthropic/Claude —
verificar si `docs/architecture/adrs/ADR-007` describe correctamente el
proveedor real usado.
