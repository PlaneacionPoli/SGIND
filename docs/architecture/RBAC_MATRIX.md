# Matriz RBAC — SGIND v2

**Fecha:** 2026-06-13  
**Nota:** El sistema Streamlit actual no implementa roles; esta matriz define el **sistema destino**.

## Roles

| Rol | Descripción | Usuarios típicos |
|-----|-------------|------------------|
| `procesos` | Lectura dashboards e indicadores | Responsables de proceso |
| `calidad` | Lectura + OM CRUD + admin | Equipo de calidad |
| `desempeno` | Lectura + OM CRUD + admin | Gerencia desempeño |

## Matriz endpoint × rol

| Endpoint | procesos | calidad | desempeno |
|----------|:--------:|:-------:|:---------:|
| `GET /api/v1/health` | ✅ | ✅ | ✅ |
| `GET /api/v1/auth/login` | ✅ | ✅ | ✅ |
| `GET /api/v1/auth/me` | ✅ | ✅ | ✅ |
| `GET /api/v1/dashboard/kpis` | ✅ | ✅ | ✅ |
| `GET /api/v1/dashboard/excel-files` | ✅ | ✅ | ✅ |
| `GET /api/v1/indicators` | ✅ | ✅ | ✅ |
| `GET /api/v1/indicators/{id}` | ✅ | ✅ | ✅ |
| `GET /api/v1/cmi/*` | ✅ | ✅ | ✅ |
| `GET /api/v1/om` | ✅ | ✅ | ✅ |
| `POST /api/v1/om` | ❌ | ✅ | ✅ |
| `PUT /api/v1/om/{id}` | ❌ | ✅ | ✅ |
| `DELETE /api/v1/om/{id}` | ❌ | ✅ | ✅ |
| `POST /api/v1/ia/*` | ✅ | ✅ | ✅ |
| `POST /api/v1/etl/run` | ❌ | ✅ | ✅ |
| `GET /api/v1/export/*` | ✅ | ✅ | ✅ |

## Implementación FastAPI

```python
require_reader = require_roles("procesos", "calidad", "desempeno")
require_admin  = require_roles("calidad", "desempeno")
```

## Asignación de rol

1. Primer login OIDC → rol default `procesos`
2. Admin asigna rol en tabla `users.role_id`
3. JWT incluye claim `role` para frontend
