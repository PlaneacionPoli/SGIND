import asyncio
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)


async def _warm_caches() -> None:
    """Precarga en segundo plano el pipeline pesado de Excel al arrancar,
    para que el primer usuario tras un cold start (Render free tier duerme
    el servicio) no espere el cálculo completo (hasta ~30s)."""
    try:
        from app.api.deps import get_excel_service
        from app.services.cmi_service import CMIService

        excel = get_excel_service(settings)
        cmi = CMIService(excel)
        await asyncio.to_thread(cmi.get_procesos_dashboard)
        await asyncio.to_thread(cmi.get_dashboard)
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logging.exception("Error no manejado: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


app.include_router(api_router, prefix="/api/v1")
