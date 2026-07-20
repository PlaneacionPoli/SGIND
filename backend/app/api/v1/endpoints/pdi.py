from fastapi import APIRouter, Depends, Query

from app.api.deps import get_excel_service
from app.core.security import require_reader
from app.models.user import User
from app.schemas.common import PDIDashboardResponse, PDIFiltrosResponse
from app.services.excel_reader import ExcelReaderService
from app.services.pdi_service import PDIService

router = APIRouter()


def _service(excel: ExcelReaderService = Depends(get_excel_service)) -> PDIService:
    return PDIService(excel)


@router.get("/filtros", response_model=PDIFiltrosResponse)
async def pdi_filtros(
    _user: User = Depends(require_reader),
    service: PDIService = Depends(_service),
) -> PDIFiltrosResponse:
    """Devuelve opciones de filtro para la vista PDI/Acreditación."""
    return PDIFiltrosResponse(**service.get_filtros())


@router.get("/dashboard", response_model=PDIDashboardResponse)
async def pdi_dashboard(
    estado: str | None = Query(None),
    macro: str | None = Query(None),
    horizonte: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: PDIService = Depends(_service),
) -> PDIDashboardResponse:
    """Dashboard PDI/Acreditación con KPIs, treemap, benchmark y tabla."""
    return PDIDashboardResponse(**service.get_dashboard(estado=estado, macro=macro, horizonte=horizonte))
