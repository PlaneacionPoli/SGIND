from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_excel_service
from app.core.security import require_reader
from app.models.user import User
from app.schemas.common import IndicatorListResponse
from app.services.excel_reader import ExcelReaderService
from app.services.indicator_service import IndicatorService

router = APIRouter()


def _indicator_service(excel: ExcelReaderService = Depends(get_excel_service)) -> IndicatorService:
    return IndicatorService(excel)


@router.get("", response_model=IndicatorListResponse)
async def list_indicators(
    anio: int | None = Query(None),
    periodo: str | None = Query(None),
    proceso: str | None = Query(None),
    categoria: str | None = Query(None),
    linea: str | None = Query(None),
    vista: str | None = Query(None),
    ultimo: bool = Query(True),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    _user: User = Depends(require_reader),
    service: IndicatorService = Depends(_indicator_service),
) -> IndicatorListResponse:
    data = service.list_indicators(
        anio=anio,
        periodo=periodo,
        proceso=proceso,
        categoria=categoria,
        linea=linea,
        vista=vista,
        ultimo=ultimo,
        limit=limit,
        offset=offset,
    )
    return IndicatorListResponse(**data)


@router.get("/{indicator_id}")
async def get_indicator(
    indicator_id: str,
    anio: int | None = Query(None),
    _user: User = Depends(require_reader),
    service: IndicatorService = Depends(_indicator_service),
) -> dict:
    detail = service.get_indicator(indicator_id, anio=anio)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicador no encontrado")
    return detail
