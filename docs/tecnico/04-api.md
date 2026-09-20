# Inventario real de la API (`backend/app/api/v1/endpoints/`)

Guards reales (`backend/app/core/security.py:83-97`):
`require_reader = require_roles("procesos","calidad","desempeno")` (cualquier
usuario autenticado), `require_admin = require_roles("calidad","desempeno")`.
No existe un tercer nivel — el rol `procesos` nunca puede escribir en `/om`.

| Método | Ruta | Propósito | `response_model` | Auth |
|---|---|---|---|---|
| GET | `/api/v1/health` | Health check | Sí | Ninguna |
| GET | `/api/v1/auth/login` | Redirige a Azure AD OAuth | No (redirect) | Ninguna |
| GET | `/api/v1/auth/login-url` | URL de login Azure AD en JSON | Sí | Ninguna |
| GET | `/api/v1/auth/callback` | Callback OAuth, emite JWT | No (redirect) | Ninguna |
| POST | `/api/v1/auth/email-login` | Login validando solo dominio de correo institucional, sin password | Sí | Ninguna |
| GET | `/api/v1/auth/me` | Perfil del usuario actual | Sí | `get_current_user` |
| POST | `/api/v1/auth/logout` | Cierra sesión | Sí | `require_reader` |
| POST | `/api/v1/auth/dev-token` | Emite JWT sin BD/OIDC; oculto de OpenAPI; bloqueado solo si `environment=="production"` | Sí | Ninguna (auto-bloqueo condicional — ver [`07-seguridad.md`](07-seguridad.md)) |
| GET | `/api/v1/dashboard/kpis` | KPIs globales | Sí | `require_reader` |
| GET | `/api/v1/dashboard/excel-files` | Lista archivos Excel disponibles | Sí | `require_reader` |
| GET | `/api/v1/dashboard/semaphore` | Semaforización por indicador | Sí | `require_reader` |
| GET | `/api/v1/dashboard/trend` | Tendencia de cumplimiento | Sí | `require_reader` |
| GET | `/api/v1/dashboard/filtros` | Opciones de filtro | Sí | `require_reader` |
| GET | `/api/v1/dashboard/lineas` | Cumplimiento por línea estratégica | Sí | `require_reader` |
| GET | `/api/v1/dashboard/sunburst` | Datos jerárquicos | **No** (`list[dict]`) | `require_reader` |
| GET | `/api/v1/dashboard/yoy` | Comparación año contra año | **No** (`list[dict]`) | `require_reader` |
| GET | `/api/v1/dashboard/resumen-completo` | Resumen consolidado | Sí | `require_reader` |
| GET | `/api/v1/dashboard/narrativa` | Narrativa heurística del dashboard | Sí | `require_reader` |
| GET | `/api/v1/indicators` | Lista indicadores con filtros | Sí | `require_reader` |
| GET | `/api/v1/indicators/{id}` | Detalle de indicador (404 si no existe) | Sí | `require_reader` |
| GET | `/api/v1/cmi/filtros` | Filtros CMI Estratégico | Sí | `require_reader` |
| GET | `/api/v1/cmi/estrategico-dashboard` | Dashboard CMI Estratégico | Sí | `require_reader` |
| GET | `/api/v1/cmi/indicador/{id}` | Ficha de indicador CMI Estratégico | Sí | `require_reader` |
| GET | `/api/v1/cmi/estrategico` | Vista CMI Estratégico completa | Sí | `require_reader` |
| GET | `/api/v1/cmi/procesos/filtros` | Filtros CMI Procesos | Sí | `require_reader` |
| GET | `/api/v1/cmi/procesos-dashboard` | Dashboard CMI Procesos | Sí | `require_reader` |
| GET | `/api/v1/cmi/procesos/indicador/{id}` | Ficha CMI Procesos | Sí | `require_reader` |
| GET | `/api/v1/cmi/procesos/export` | Exporta a xlsx/csv | No (binario) | `require_reader` |
| GET | `/api/v1/cmi/procesos` | Listado CMI Procesos | Sí | `require_reader` |
| GET | `/api/v1/cmi/alertas` | Indicadores en alerta/peligro | Sí | `require_reader` |
| GET | `/api/v1/om/matriz` | Matriz OM (cruza Excel + BD) | Sí | `require_reader` |
| GET | `/api/v1/om/plan-accion` | Actividades del plan de acción | **No** (`list[dict]`) | `require_reader` |
| GET | `/api/v1/om` | Lista registros OM | Sí | `require_reader` |
| POST | `/api/v1/om` | Crea registro OM (upsert) | Sí | `require_admin` |
| PUT | `/api/v1/om/{id}` | Actualiza registro OM | Sí | `require_admin` |
| PATCH | `/api/v1/om/{id}/cerrar` | Cierra OM | Sí | `require_admin` |
| DELETE | `/api/v1/om/{id}` | Borra registro OM | 204 | `require_admin` |
| GET | `/api/v1/seguimiento/filtros` | Filtros de seguimiento | Sí | `require_reader` |
| GET | `/api/v1/seguimiento/dashboard` | Dashboard de seguimiento | Sí | `require_reader` |
| GET | `/api/v1/seguimiento/export` | Exporta a xlsx | No (binario) | `require_reader` |
| GET | `/api/v1/plan-mejoramiento/filtros` | Filtros Plan de Mejoramiento | Sí | `require_reader` |
| GET | `/api/v1/plan-mejoramiento/dashboard` | Dashboard Plan de Mejoramiento | Sí | `require_reader` |
| GET | `/api/v1/plan-mejoramiento/indicadores` | Pestaña Indicadores | Sí | `require_reader` |
| GET | `/api/v1/plan-mejoramiento/indicadores/export` | Exporta a xlsx | No (binario) | `require_reader` |
| GET | `/api/v1/plan-mejoramiento/indicadores/detalle` | Detalle de indicador de plan | Sí | `require_reader` |
| GET | `/api/v1/plan-mejoramiento/metricas` | Pestaña Métricas | Sí | `require_reader` |
| GET | `/api/v1/plan-mejoramiento/metricas/detalle` | Detalle de métrica/subindicador | Sí | `require_reader` |
| GET | `/api/v1/informe/filtros` | Filtros Informe por Procesos | Sí | `require_reader` |
| GET | `/api/v1/informe/dashboard` | Dashboard Informe por Procesos | Sí | `require_reader` |
| GET | `/api/v1/pdi/filtros` | Filtros PDI/Acreditación | Sí | `require_reader` |
| GET | `/api/v1/pdi/dashboard` | Dashboard PDI/Acreditación | Sí | `require_reader` |
| GET | `/api/v1/reports/resumen-general` | PDF resumen general | No (streaming) | `require_reader` |
| GET | `/api/v1/reports/informe-procesos` | PDF informe por procesos | No (streaming) | `require_reader` |
| GET | `/api/v1/reports/ficha/{id}` | PDF ficha de indicador | No (streaming) | `require_reader` |

## Endpoints documentados en `RBAC_MATRIX.md` que NO existen en el código

- `POST /api/v1/etl/run`
- `GET /api/v1/export/*` (genérico — las exportaciones reales son
  específicas por módulo: `cmi/procesos/export`, `seguimiento/export`,
  `plan-mejoramiento/indicadores/export`)

Es un desfase de documentación (endpoints planeados que nunca se
construyeron), no una vulnerabilidad — no hay nada que proteger porque no
existen.

## Endpoints sin `response_model` tipado

`dashboard/sunburst`, `dashboard/yoy`, `om/plan-accion` — devuelven
`list[dict]` sin contrato Pydantic validado. Los endpoints de exportación
(`*/export`, `reports/*`) devuelven binarios/streaming, lo cual es esperado
y no cuenta como el mismo problema.

## Consumo real desde el frontend

Todos los endpoints anteriores tienen un wrapper correspondiente en
`frontend/src/lib/api.ts` y se consumen desde alguna página en
`frontend/src/app/(dashboard)/`. No se encontraron endpoints huérfanos sin
consumidor en el frontend.
