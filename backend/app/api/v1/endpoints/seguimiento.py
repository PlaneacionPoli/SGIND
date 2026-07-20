from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.api.deps import get_excel_service
from app.core.security import require_reader
from app.models.user import User
from app.schemas.common import SeguimientoDashboardResponse, SeguimientoFiltrosResponse
from app.services.excel_reader import ExcelReaderService
from app.services.seguimiento_service import SeguimientoService

router = APIRouter()


def _service(excel: ExcelReaderService = Depends(get_excel_service)) -> SeguimientoService:
    return SeguimientoService(excel)


@router.get("/filtros", response_model=SeguimientoFiltrosResponse)
async def seguimiento_filtros(
    _user: User = Depends(require_reader),
    service: SeguimientoService = Depends(_service),
) -> SeguimientoFiltrosResponse:
    """Devuelve años, meses, procesos y estados disponibles."""
    return SeguimientoFiltrosResponse(**service.get_filtros())


@router.get("/dashboard", response_model=SeguimientoDashboardResponse)
async def seguimiento_dashboard(
    anio: int | None = Query(None),
    mes: int | None = Query(None, ge=1, le=12),
    proceso: str | None = Query(None),
    estado: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: SeguimientoService = Depends(_service),
) -> SeguimientoDashboardResponse:
    return SeguimientoDashboardResponse(**service.get_dashboard(anio=anio, mes=mes, proceso=proceso, estado=estado))


@router.get("/export")
async def seguimiento_export(
    anio: int | None = Query(None),
    mes: int | None = Query(None, ge=1, le=12),
    proceso: str | None = Query(None),
    estado: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: SeguimientoService = Depends(_service),
) -> Response:
    content = service.export_excel(anio=anio, mes=mes, proceso=proceso, estado=estado)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=seguimiento_filtrado.xlsx"},
    )
