from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.api.deps import get_excel_service
from app.core.security import require_reader
from app.models.user import User
from app.schemas.common import (
    CMIAlertasResponse,
    CMIDashboardResponse,
    CMIEstrategicoResponse,
    CMIFiltrosResponse,
    CMIProcesosDashboardResponse,
    CMIProcesosFiltrosResponse,
    CMIProcesosResponse,
    FichaIndicadorResponse,
)
from app.services.cmi_service import CMIService
from app.services.excel_reader import ExcelReaderService

router = APIRouter()


def _cmi_service(excel: ExcelReaderService = Depends(get_excel_service)) -> CMIService:
    return CMIService(excel)


@router.get("/filtros", response_model=CMIFiltrosResponse)
async def cmi_filtros(
    _user: User = Depends(require_reader),
    service: CMIService = Depends(_cmi_service),
) -> CMIFiltrosResponse:
    return CMIFiltrosResponse(**service.get_filtros())


@router.get("/estrategico-dashboard", response_model=CMIDashboardResponse)
async def cmi_estrategico_dashboard(
    anio: int | None = Query(None),
    mes: int | None = Query(None, ge=1, le=12),
    corte: str | None = Query(None, description="Junio o Diciembre"),
    _user: User = Depends(require_reader),
    service: CMIService = Depends(_cmi_service),
) -> CMIDashboardResponse:
    return CMIDashboardResponse(**service.get_dashboard(anio=anio, mes=mes, corte=corte))


@router.get("/indicador/{indicador_id}", response_model=FichaIndicadorResponse)
async def cmi_indicador_ficha(
    indicador_id: str,
    anio: int = Query(...),
    mes: int | None = Query(None, ge=1, le=12),
    corte: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: CMIService = Depends(_cmi_service),
) -> FichaIndicadorResponse:
    ficha = service.get_indicador_ficha(indicador_id, anio=anio, mes=mes, corte=corte)
    if ficha is None:
        raise HTTPException(status_code=404, detail="Indicador no encontrado para el corte seleccionado")
    return FichaIndicadorResponse(**ficha)


@router.get("/estrategico", response_model=CMIEstrategicoResponse)
async def cmi_estrategico(
    anio: int | None = Query(None),
    mes: int | None = Query(None, ge=1, le=12),
    corte: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: CMIService = Depends(_cmi_service),
) -> CMIEstrategicoResponse:
    return CMIEstrategicoResponse(**service.get_estrategico(anio=anio, mes=mes, corte=corte))


@router.get("/procesos/filtros", response_model=CMIProcesosFiltrosResponse)
async def cmi_procesos_filtros(
    anio: int | None = Query(None),
    _user: User = Depends(require_reader),
    service: CMIService = Depends(_cmi_service),
) -> CMIProcesosFiltrosResponse:
    return CMIProcesosFiltrosResponse(**service.get_procesos_filtros(anio=anio))


@router.get("/procesos-dashboard", response_model=CMIProcesosDashboardResponse)
async def cmi_procesos_dashboard(
    anio: int | None = Query(None),
    mes: int | None = Query(None, ge=1, le=12),
    unidad: str | None = Query(None),
    proceso: str | None = Query(None),
    subproceso: str | None = Query(None),
    clasificacion: str | None = Query(None),
    frecuencia: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: CMIService = Depends(_cmi_service),
) -> CMIProcesosDashboardResponse:
    return CMIProcesosDashboardResponse(
        **service.get_procesos_dashboard(
            anio=anio,
            mes=mes,
            unidad=unidad,
            proceso=proceso,
            subproceso=subproceso,
            clasificacion=clasificacion,
            frecuencia=frecuencia,
        )
    )


@router.get("/procesos/indicador/{indicador_id}", response_model=FichaIndicadorResponse)
async def cmi_procesos_indicador_ficha(
    indicador_id: str,
    anio: int = Query(...),
    mes: int | None = Query(None, ge=1, le=12),
    unidad: str | None = Query(None),
    proceso: str | None = Query(None),
    subproceso: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: CMIService = Depends(_cmi_service),
) -> FichaIndicadorResponse:
    ficha = service.get_procesos_indicador_ficha(
        indicador_id,
        anio=anio,
        mes=mes,
        unidad=unidad,
        proceso=proceso,
        subproceso=subproceso,
    )
    if ficha is None:
        raise HTTPException(status_code=404, detail="Indicador no encontrado para CMI por Procesos")
    return FichaIndicadorResponse(**ficha)


@router.get("/procesos/export")
async def cmi_procesos_export(
    anio: int = Query(...),
    mes: int | None = Query(None, ge=1, le=12),
    formato: str = Query("xlsx", description="xlsx o csv"),
    unidad: str | None = Query(None),
    proceso: str | None = Query(None),
    subproceso: str | None = Query(None),
    clasificacion: str | None = Query(None),
    frecuencia: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: CMIService = Depends(_cmi_service),
) -> Response:
    content, filename, media_type = service.export_procesos_indicadores(
        anio=anio,
        mes=mes,
        formato=formato,
        unidad=unidad,
        proceso=proceso,
        subproceso=subproceso,
        clasificacion=clasificacion,
        frecuencia=frecuencia,
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/procesos", response_model=CMIProcesosResponse)
async def cmi_procesos(
    anio: int | None = Query(None),
    _user: User = Depends(require_reader),
    service: CMIService = Depends(_cmi_service),
) -> CMIProcesosResponse:
    return CMIProcesosResponse(**service.get_procesos(anio=anio))


@router.get("/alertas", response_model=CMIAlertasResponse)
async def cmi_alertas(
    anio: int | None = Query(None),
    mes: int | None = Query(None, ge=1, le=12),
    corte: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    _user: User = Depends(require_reader),
    service: CMIService = Depends(_cmi_service),
) -> CMIAlertasResponse:
    return CMIAlertasResponse(**service.get_alertas(anio=anio, mes=mes, corte=corte, limit=limit))
