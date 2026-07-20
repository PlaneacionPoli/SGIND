from fastapi import APIRouter, Depends, Query



from app.api.deps import get_excel_service
from app.core.config import Settings, get_settings

from app.core.security import require_reader

from app.models.user import User

from app.schemas.common import (

    CMILineaItem,

    DashboardKPIsResponse,

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

    raw = dashboard.get_kpis(anio=anio, periodo=periodo, vista=vista)

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

    return excel.list_available_files()





@router.get("/semaphore", response_model=list[SemaphoreItem])

async def get_semaphore(

    anio: int | None = Query(None),

    periodo: str | None = Query(None),

    vista: str = Query("indicadores"),

    _user: User = Depends(require_reader),

    dashboard: DashboardService = Depends(_dashboard_service),

) -> list[SemaphoreItem]:

    raw = dashboard.get_semaphore(anio=anio, periodo=periodo, vista=vista)

    return [SemaphoreItem(**item) for item in raw]





@router.get("/trend", response_model=list[TrendItem])

async def get_trend(

    anio: int | None = Query(None),

    vista: str = Query("indicadores"),

    _user: User = Depends(require_reader),

    dashboard: DashboardService = Depends(_dashboard_service),

) -> list[TrendItem]:

    raw = dashboard.get_trend(anio=anio, vista=vista)

    return [TrendItem(**item) for item in raw]





@router.get("/filtros")

async def get_filtros(

    _user: User = Depends(require_reader),

    dashboard: DashboardService = Depends(_dashboard_service),

) -> dict:

    return dashboard.get_filtros()





@router.get("/lineas", response_model=list[CMILineaItem])

async def get_lineas(

    anio: int | None = Query(None),

    periodo: str | None = Query(None),

    vista: str = Query("indicadores"),

    _user: User = Depends(require_reader),

    dashboard: DashboardService = Depends(_dashboard_service),

) -> list[CMILineaItem]:

    raw = dashboard.get_lineas(anio=anio, periodo=periodo, vista=vista)

    return [CMILineaItem(**item) for item in raw]





@router.get("/sunburst")

async def get_sunburst(

    anio: int | None = Query(None),

    vista: str = Query("indicadores"),

    _user: User = Depends(require_reader),

    dashboard: DashboardService = Depends(_dashboard_service),

) -> list[dict]:

    return dashboard.get_sunburst(anio=anio, vista=vista)





@router.get("/yoy")

async def get_yoy(

    anio: int = Query(...),

    vista: str = Query("indicadores"),

    _user: User = Depends(require_reader),

    dashboard: DashboardService = Depends(_dashboard_service),

) -> list[dict]:

    return dashboard.get_yoy(anio=anio, vista=vista)





@router.get("/resumen-completo")
async def get_resumen_completo(
    anio: int = Query(...),
    vista: str = Query("indicadores"),
    rango: bool = Query(False),
    _user: User = Depends(require_reader),
    dashboard: DashboardService = Depends(_dashboard_service),
) -> dict:
    return dashboard.get_resumen_completo(anio=anio, vista=vista, rango=rango)


@router.get("/narrativa")

async def get_narrativa(

    anio: int | None = Query(None),

    vista: str = Query("indicadores"),

    _user: User = Depends(require_reader),

    dashboard: DashboardService = Depends(_dashboard_service),

) -> dict:

    return dashboard.get_narrativa(anio=anio, vista=vista)


