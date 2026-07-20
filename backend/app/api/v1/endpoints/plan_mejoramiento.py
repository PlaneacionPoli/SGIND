from fastapi import APIRouter, Depends, Query

from app.api.deps import get_excel_service
from app.core.security import require_reader
from app.models.user import User
from app.schemas.common import PlanMejoramientoDashboardResponse, PlanMejoramientoFiltrosResponse
from app.services.excel_reader import ExcelReaderService
from app.services.plan_mejoramiento_service import PlanMejoramientoService

router = APIRouter()


def _service(excel: ExcelReaderService = Depends(get_excel_service)) -> PlanMejoramientoService:
    return PlanMejoramientoService(excel)


@router.get("/filtros", response_model=PlanMejoramientoFiltrosResponse)
async def plan_mejoramiento_filtros(
    _user: User = Depends(require_reader),
    service: PlanMejoramientoService = Depends(_service),
) -> PlanMejoramientoFiltrosResponse:
    """Devuelve años, cortes, factores y características disponibles."""
    return PlanMejoramientoFiltrosResponse(**service.get_filtros())


@router.get("/dashboard", response_model=PlanMejoramientoDashboardResponse)
async def plan_mejoramiento_dashboard(
    anio: int | None = Query(None),
    corte: str | None = Query(None, description="Junio o Diciembre"),
    factor: str | None = Query(None),
    caracteristica: str | None = Query(None),
    nombre: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: PlanMejoramientoService = Depends(_service),
) -> PlanMejoramientoDashboardResponse:
    return PlanMejoramientoDashboardResponse(
        **service.get_dashboard(
            anio=anio,
            corte=corte,
            factor=factor,
            caracteristica=caracteristica,
            nombre=nombre,
        )
    )
