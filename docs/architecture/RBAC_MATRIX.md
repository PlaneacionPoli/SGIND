# Matriz RBAC — SGIND v2

**Fecha:** 2026-06-13  
**Nota:** El sistema Streamlit actual no implementa roles; esta matriz define el **sistema destino**.

## Roles

| Rol | Descripción | Pantallas | Cómo se asigna |
|-----|-------------|-----------|----------------|
| `procesos` | Lectura de 5 pantallas: Resumen General, CMI Estratégico, CMI por Procesos, Informe por Procesos y Plan de Mejoramiento | 5 de 7 | Por defecto al primer login |
| `administrador` | Acceso total: las 7 pantallas, CRUD de OM y auditoría/publicación de narrativas IA | 7 de 7 | Variable de entorno `ADMIN_EMAILS` (ver abajo) |
| `calidad` | Igual que administrador (lectura total + OM CRUD) | 7 de 7 | Manual en `users.role_id` |
| `desempeno` | Igual que administrador (lectura total + OM CRUD) | 7 de 7 | Manual en `users.role_id` |
| `auditor_ia` | Lectura de las 5 pantallas de `procesos` **+** puede ver el borrador pendiente y publicar la narrativa IA de la pestaña "Análisis IA" del Informe por Procesos | 5 de 7 (+ auditoría IA) | Manual en `users.role_id` |

Seguimiento Operativo y Gestión OM **no** son visibles ni accesibles para `procesos` ni para `auditor_ia`.

## Matriz endpoint × rol

| Endpoint | procesos | administrador | calidad | desempeno | auditor_ia |
|----------|:--------:|:-------------:|:-------:|:---------:|:----------:|
| `GET /api/v1/health` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/v1/auth/login` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/v1/auth/me` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/v1/dashboard/*` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/v1/indicators` y `/{id}` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/v1/cmi/*` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/v1/informe/*` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/v1/plan-mejoramiento/*` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/v1/reports/*` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/v1/seguimiento/*` (incluye `export`) | ❌ | ✅ | ✅ | ✅ | ❌ |
| `GET /api/v1/om`, `/om/matriz`, `/om/plan-accion` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `POST /api/v1/om` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `PUT /api/v1/om/{id}` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `PATCH /api/v1/om/{id}/cerrar` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `DELETE /api/v1/om/{id}` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `GET /api/v1/cmi/procesos/export` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/v1/plan-mejoramiento/indicadores/export` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/v1/informe/narrativa-ia/borrador` | ❌ | ✅ | ❌ | ❌ | ✅ |
| `POST /api/v1/informe/narrativa-ia/publicar` | ❌ | ✅ | ❌ | ❌ | ✅ |

> Corregido en Oleada 4 (G-12): se retiraron `POST /api/v1/ia/*`, `POST /api/v1/etl/run`
> y `GET /api/v1/export/*` genérico — ninguno existe en `backend/app/api/v1/`
> (la IA se invoca dentro de los builders, el ETL corre fuera del backend en
> `scripts/`, y la exportación es por módulo).

## Implementación FastAPI

```python
require_reader      = require_roles("procesos", "administrador", "calidad", "desempeno", "auditor_ia")
require_operational = require_roles("administrador", "calidad", "desempeno")  # seguimiento y OM (lectura)
require_admin       = require_roles("administrador", "calidad", "desempeno")  # escritura de OM
require_auditor_ia  = require_roles("auditor_ia", "administrador")  # auditoría/publicación narrativa IA
```

## Asignación de rol

1. Primer login (OIDC o correo institucional) → rol `procesos`.
2. Los correos listados en la variable de entorno `ADMIN_EMAILS` (separados por coma, sin
   distinguir mayúsculas) reciben el rol `administrador` al iniciar sesión, aunque el usuario
   ya existiera con otro rol. Es la **única fuente** de ese rol: quien sale de la lista vuelve a
   `procesos` en su siguiente inicio de sesión. Los correos no se versionan (datos personales):
   se cargan en el entorno (Render → Environment, o `backend/.env` en local).
3. `calidad`, `desempeno` y `auditor_ia` se asignan a mano en `users.role_id`; el login no los
   modifica.
4. El JWT incluye el claim `role` para el frontend; la autoridad real en cada petición es
   `users.role_id` en la BD.
5. La BD necesita el rol: `database/migrations/004_add_rol_administrador.sql` (en bases ya
   desplegadas se aplica a mano con `psql -f`). `auditor_ia` requiere el mismo tipo de migración
   manual (`INSERT INTO roles (name) VALUES ('auditor_ia')`) antes de poder asignarse.
6. Frontend: el menú y el sidebar de `procesos` muestran solo sus 5 pantallas y entrar por URL
   directa a las otras redirige a `/menu` (`config/navigation.ts`, `AuthGuard`). La restricción
   real la impone el backend con 403. `auditor_ia` ve las mismas 5 pantallas que `procesos`, más
   el panel de auditoría de narrativa IA dentro de la pestaña "Análisis IA" del Informe por
   Procesos (`CmiProcesosAnalisisTab.tsx`).
