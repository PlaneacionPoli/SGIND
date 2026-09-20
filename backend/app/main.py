import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)


async def _warm_caches() -> None:
    """Precarga en segundo plano el pipeline pesado de Excel al arrancar,
    para que el primer usuario tras un cold start (Render free tier duerme
    el servicio) no espere el cálculo completo (hasta ~30s).

    Nota (2026-09-18): originalmente solo precalentaba CMI Procesos/Estratégico.
    Resumen General (ETLPipelineService, sin caché de resultado propia, ver
    docs/migration/PLAN_MIGRACION_PRIORIZADO.md) no estaba incluido — al ser
    la única combinación de datos que un usuario podía pedir "en frío" justo
    tras el arranque, es la explicación más probable del "Network Error"
    reportado solo en esa página. Se agrega aquí con los mismos
    anio/vista/rango con los que el frontend hace su primera petición
    (ver frontend/src/app/(dashboard)/resumen-general/page.tsx)."""
    try:
        from app.api.deps import get_excel_service
        from app.services.cmi_service import CMIService
        from app.services.dashboard_service import DashboardService

        excel = get_excel_service(settings)
        cmi = CMIService(excel)
        await asyncio.to_thread(cmi.get_procesos_dashboard)
        await asyncio.to_thread(cmi.get_dashboard)

        dashboard = DashboardService(excel)
        await asyncio.to_thread(dashboard.get_filtros)
        await asyncio.to_thread(
            dashboard.get_resumen_completo, anio=2025, vista="indicadores", rango=True
        )
        logging.info("Cache de indicadores precargado")
    except Exception:
        logging.exception("No se pudo precargar el cache de indicadores en el arranque")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.info("SGIND v2 backend iniciado — entorno: %s", settings.environment)
    asyncio.create_task(_warm_caches())
    yield
    logging.info("SGIND v2 backend detenido")


app = FastAPI(
    title="SGIND API",
    description="API del Sistema de Gestión de Indicadores — Politécnico Grancolombiano",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


class CatchExceptionsMiddleware(BaseHTTPMiddleware):
    """Convierte cualquier excepción no controlada en una respuesta 500 JSON.

    IMPORTANTE (2026-09-18): esto reemplaza a `@app.exception_handler(Exception)`.
    Un exception_handler para la clase base `Exception` corre en
    Starlette/FastAPI POR FUERA de la cadena de `add_middleware` (incluido
    CORSMiddleware) — la respuesta de error que genera NUNCA recibe el header
    `Access-Control-Allow-Origin`. El navegador entonces reporta "bloqueado
    por política de CORS" en vez de mostrar el 500 real, ocultando el error
    verdadero (ver docs/migration/PLAN_MIGRACION_PRIORIZADO.md — bug
    "Network Error" en Resumen General, causado en realidad por un 500).
    Como middleware (registrado ANTES que CORSMiddleware, por lo tanto más
    interno en la pila), la respuesta de error SÍ pasa por CORSMiddleware al
    volver, y recibe el header correctamente.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:  # noqa: BLE001 — último resguardo, se relanza logueado
            logging.exception("Error no manejado: %s", exc)
            return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


app.add_middleware(CatchExceptionsMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
