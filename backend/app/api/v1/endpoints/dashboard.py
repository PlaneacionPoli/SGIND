from fastapi import APIRouter, Depends, Query

from app.api.deps import get_excel_service
from app.core.concurrency import run_sync
from app.core.config import Settings, get_settings
from app.core.security import require_reader
from app.models.user import User
from app.schemas.common import (
    CMILineaItem,
    DashboardFiltrosResponse,
    DashboardKPIsResponse,
    DashboardNarrativaResponse,
    DashboardResumenCompletoResponse,
    ExcelFileInfo,
    KPIResponse,
    SemaphoreItem,
    TrendItem,
)
from app.services.dashboard_service import DashboardService
from app.services.excel_reader import ExcelReaderService

router = APIRouter()


def _excel_service(settings: Settings = Depends(get_settings)) -> ExcelReaderService:
    return get_excel_service(settings)


def _dashboard_service(excel: ExcelReaderService = Depends(_excel_service)) -> DashboardService:
    return DashboardService(excel)


@router.get("/kpis", response_model=DashboardKPIsResponse)
async def get_kpis(
    anio: int | None = Query(None),
    periodo: str | None = Query(None),
    vista: str = Query("indicadores"),
    _user: User = Depends(require_reader),
    dashboard: DashboardService = Depends(_dashboard_service),
) -> DashboardKPIsResponse:
    raw = await run_sync(dashboard.get_kpis, anio=anio, periodo=periodo, vista=vista)

    return DashboardKPIsResponse(
        anio=anio,
        periodo=periodo,
        kpis=[KPIResponse(**k) for k in raw],
        source="consolidado-cierres",
    )


@router.get("/excel-files", response_model=list[ExcelFileInfo])
async def list_excel_files(
    _user: User = Depends(require_reader),
    excel: ExcelReaderService = Depends(_excel_service),
) -> list[ExcelFileInfo]:
    return await run_sync(excel.list_available_files)


@router.get("/semaphore", response_model=list[SemaphoreItem])
async def get_semaphore(
    anio: int | None = Query(None),
    periodo: str | None = Query(None),
    vista: str = Query("indicadores"),
    _user: User = Depends(require_reader),
    dashboard: DashboardService = Depends(_dashboard_service),
) -> list[SemaphoreItem]:
    raw = await run_sync(dashboard.get_semaphore, anio=anio, periodo=periodo, vista=vista)

    return [SemaphoreItem(**item) for item in raw]


@router.get("/trend", response_model=list[TrendItem])
async def get_trend(
    anio: int | None = Query(None),
    vista: str = Query("indicadores"),
    _user: User = Depends(require_reader),
    dashboard: DashboardService = Depends(_dashboard_service),
) -> list[TrendItem]:
    raw = await run_sync(dashboard.get_trend, anio=anio, vista=vista)

    return [TrendItem(**item) for item in raw]


@router.get("/filtros", response_model=DashboardFiltrosResponse)
async def get_filtros(
    _user: User = Depends(require_reader),
    dashboard: DashboardService = Depends(_dashboard_service),
) -> DashboardFiltrosResponse:
    return DashboardFiltrosResponse(**await run_sync(dashboard.get_filtros))


@router.get("/lineas", response_model=list[CMILineaItem])
async def get_lineas(
    anio: int | None = Query(None),
    periodo: str | None = Query(None),
    vista: str = Query("indicadores"),
    _user: User = Depends(require_reader),
    dashboard: DashboardService = Depends(_dashboard_service),
) -> list[CMILineaItem]:
    raw = await run_sync(dashboard.get_lineas, anio=anio, periodo=periodo, vista=vista)

    return [CMILineaItem(**item) for item in raw]


@router.get("/sunburst")
async def get_sunburst(
    anio: int | None = Query(None),
    vista: str = Query("indicadores"),
    _user: User = Depends(require_reader),
    dashboard: DashboardService = Depends(_dashboard_service),
) -> list[dict]:
    return await run_sync(dashboard.get_sunburst, anio=anio, vista=vista)


@router.get("/yoy")
async def get_yoy(
    anio: int = Query(...),
    vista: str = Query("indicadores"),
    _user: User = Depends(require_reader),
    dashboard: DashboardService = Depends(_dashboard_service),
) -> list[dict]:
    return await run_sync(dashboard.get_yoy, anio=anio, vista=vista)


@router.get("/resumen-completo", response_model=DashboardResumenCompletoResponse)
async def get_resumen_completo(
    anio: int = Query(...),
    vista: str = Query("indicadores"),
    rango: bool = Query(False),
    _user: User = Depends(require_reader),
    dashboard: DashboardService = Depends(_dashboard_service),
) -> DashboardResumenCompletoResponse:
    return DashboardResumenCompletoResponse(
        **await run_sync(dashboard.get_resumen_completo, anio=anio, vista=vista, rango=rango)
    )


@router.get("/narrativa", response_model=DashboardNarrativaResponse)
async def get_narrativa(
    anio: int | None = Query(None),
    vista: str = Query("indicadores"),
    _user: User = Depends(require_reader),
    dashboard: DashboardService = Depends(_dashboard_service),
) -> DashboardNarrativaResponse:
    return DashboardNarrativaResponse(
        **await run_sync(dashboard.get_narrativa, anio=anio, vista=vista)
    )
