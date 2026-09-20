# Flujos end-to-end reales

## Flujo 1 — Producción de datos de indicadores (pipeline, manual)

```
[operador ejecuta manualmente]
scripts/run_pipeline.py (o agent_runner.py)
  → lee config/settings.toml [pipeline].steps
  1) scripts/consolidar_api.py
       data/raw/Kawak/{año}.xlsx + data/raw/API/{año}.xlsx
       → data/raw/Fuentes Consolidadas/Indicadores Kawak.xlsx
       → data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx
  2) scripts/actualizar_consolidado.py (orquestador de negocio real)
       usa 23 módulos de scripts/etl/*
       (carga, valida "Gate 1", construye registros, aplica correcciones
        AGENT5, valida "Gate 2/3", escribe, repara, respalda con rollback)
       → data/output/Resultados Consolidados.xlsx (+ .bak.xlsx + VALORES.xlsx)
  3) scripts/generar_reporte.py
       → artifacts/reporte_YYYYMMDD.json (métricas de calidad del run)

[proceso separado, también manual]
python -m scripts.cna_extraction.build_cli --write
  → data/output/Resultados_Consolidados_CNA.xlsx
```

**No hay ningún disparador automático.** Nadie ejecuta esto salvo un
operador humano. Si nadie lo corre, los indicadores del dashboard se
congelan en el último Excel generado — sin error visible para el usuario
del dashboard.

## Flujo 2 — Consulta de un indicador desde el dashboard

```
Usuario
  → Frontend: página en frontend/src/app/(dashboard)/<modulo>/page.tsx
  → frontend/src/lib/api.ts (Axios + interceptor 401)
  → Backend: backend/app/api/v1/endpoints/<modulo>.py (Depends(require_reader))
  → Servicio: backend/app/services/<modulo>_service.py
  → backend/app/services/etl_pipeline.py::leer_cierres()
       (lee Excel + 2 merges de enriquecimiento + derivación de fechas,
        con cache TTL)
  → backend/app/domain/calculos.py / categorization.py
       (normaliza y categoriza cumplimiento — o alguna de las 4
        reimplementaciones divergentes, según el módulo — ver 05-reglas-de-negocio.md)
  → Response Pydantic tipado (o dict sin tipar en 3 endpoints, ver 04-api.md)
  → Frontend renderiza (Plotly o Recharts) con su propio mapeo de color,
       que puede no coincidir con el que mandó el backend si el componente
       usa uno de los 4 mapas de color locales en vez del que llega en el payload
```

**Punto donde se rompe la trazabilidad:** entre el paso "pipeline produce
Excel" y "backend lee Excel" no hay ningún mecanismo que notifique al
backend que los datos cambiaron (no hay invalidación de caché automática ni
evento) — el caché TTL de `leer_cierres()` es el único control de
frescura, y es independiente de cuándo se ejecutó realmente el pipeline.

## Flujo 3 — Registro de una Oportunidad de Mejora (OM), único flujo con Postgres real

```
Usuario (rol calidad/desempeno)
  → Frontend: /gestion-om (canEdit = role === "calidad" || "desempeno")
  → frontend/src/lib/api.ts::createOM / updateOM / cerrarOM
  → backend/app/api/v1/endpoints/om.py (Depends(require_admin))
  → backend/app/services/om_service.py
  → backend/app/models/om.py (SQLAlchemy) → tabla registros_om (Postgres)
       UPSERT vía UNIQUE(id_indicador, periodo, anio)
  → trigger Postgres → tabla audit_log (nadie la lee después)
  → Frontend refresca vía React Query
```

Este es el único flujo con escritura transaccional real y control de
concurrencia (constraint único + upsert); todos los demás módulos son de
solo lectura sobre archivos Excel.

## Flujo 4 — Autenticación (tres mecanismos coexistentes)

```
a) Azure AD (SSO institucional):
   Frontend botón "Microsoft" → GET /auth/login → redirect Azure AD
   → GET /auth/callback?code= → JWT → frontend decodifica claims sin
     verificar firma (lib/jwt.ts) → guarda en Zustand/localStorage
   [depende de AZURE_CLIENT_ID/TENANT_ID/SECRET configurados; valores
    default vacíos en core/config.py — no verificado si funciona hoy]

b) Email institucional (login "temporal" según su propio comentario):
   Frontend → POST /auth/email-login (solo valida dominio de correo)
   → JWT → mismo flujo de guardado

c) Dev login:
   Frontend (solo si NODE_ENV=development o flag explícito)
   → POST /auth/dev-token (rol fijo, sin validar nada)
   → JWT
   [el endpoint solo se bloquea si settings.environment == "production"
    literal — activo en cualquier staging/QA con otro nombre de entorno]
```
