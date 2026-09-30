from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_excel_service
from app.core.concurrency import run_sync
from app.core.security import require_auditor_ia, require_reader
from app.models.user import User
from app.schemas.common import InformeDashboardResponse, InformeFiltrosResponse
from app.services.excel_reader import ExcelReaderService
from app.services.informe_service import InformeService
from app.services.narrativa_ia_proceso_service import (
    leer_narrativa_ia_proceso,
    publicar_narrativa_ia_proceso,
)

router = APIRouter()


def _service(excel: ExcelReaderService = Depends(get_excel_service)) -> InformeService:
    return InformeService(excel)


@router.get("/filtros", response_model=InformeFiltrosResponse)
async def informe_filtros(
    _user: User = Depends(require_reader),
    service: InformeService = Depends(_service),
) -> InformeFiltrosResponse:
    """Devuelve años, meses, procesos y subprocesos disponibles."""
    return InformeFiltrosResponse(**await run_sync(service.get_filtros))


@router.get("/dashboard", response_model=InformeDashboardResponse)
async def informe_dashboard(
    anio: int = Query(...),
    mes: int | None = Query(None, ge=1, le=12),
    unidad: str | None = Query(None),
    proceso: str | None = Query(None),
    subproceso: str | None = Query(None),
    clasificacion: str | None = Query(None),
    frecuencia: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: InformeService = Depends(_service),
) -> InformeDashboardResponse:
    return InformeDashboardResponse(
        **await run_sync(
            service.get_dashboard,
            anio=anio,
            mes=mes or 12,
            unidad=unidad,
            proceso=proceso,
            subproceso=subproceso,
            clasificacion=clasificacion,
            frecuencia=frecuencia,
        )
    )


@router.get("/narrativa-ia/borrador")
async def informe_narrativa_ia_borrador(
    proceso: str = Query(...),
    anio: int = Query(...),
    mes: int = Query(..., ge=1, le=12),
    _user: User = Depends(require_auditor_ia),
) -> dict[str, Any]:
    """Borrador pendiente de auditoría — solo visible para rol auditor_ia/administrador,
    nunca se expone en /dashboard a lectores normales."""
    return await run_sync(leer_narrativa_ia_proceso, proceso, anio, mes)


@router.post("/narrativa-ia/publicar")
async def informe_narrativa_ia_publicar(
    proceso: str = Query(...),
    anio: int = Query(...),
    mes: int = Query(..., ge=1, le=12),
    user: User = Depends(require_auditor_ia),
) -> dict[str, Any]:
    """Publica el borrador vigente: queda visible en /dashboard y la versión
    publicada anterior (si existía) se archiva en el historial de auditoría."""
    try:
        return await run_sync(
            publicar_narrativa_ia_proceso,
            proceso=proceso,
            anio=anio,
            mes=mes,
            revisor_email=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
