from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.api.deps import get_excel_service
from app.core.concurrency import run_sync
from app.core.security import require_reader
from app.models.user import User
from app.schemas.common import (
    PlanIndicadorDetalleResponse,
    PlanIndicadoresDashboardResponse,
    PlanMejoramientoDashboardResponse,
    PlanMejoramientoFiltrosResponse,
    PlanMetricaDetalleResponse,
    PlanMetricasDashboardResponse,
)
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
    return PlanMejoramientoFiltrosResponse(**await run_sync(service.get_filtros))


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
        **await run_sync(
            service.get_dashboard,
            anio=anio,
            corte=corte,
            factor=factor,
            caracteristica=caracteristica,
            nombre=nombre,
        )
    )


@router.get("/indicadores", response_model=PlanIndicadoresDashboardResponse)
async def plan_mejoramiento_indicadores(
    subvista: str = Query("metas", description="'metas' (2026-2030) o 'historico' (2025-2026)"),
    factor: str | None = Query(None),
    caracteristica: str | None = Query(None),
    tipo: str | None = Query(None),
    nombre: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: PlanMejoramientoService = Depends(_service),
) -> PlanIndicadoresDashboardResponse:
    """Pestaña 'Indicadores' del Plan de Mejoramiento — ver
    docs/migration/PLAN_MIGRACION_PRIORIZADO.md ítem 0. Factor/Característica
    son filtros globales del módulo, compartidos con /metricas."""
    return PlanIndicadoresDashboardResponse(
        **await run_sync(
            service.get_indicadores_dashboard,
            subvista=subvista,
            factor=factor,
            caracteristica=caracteristica,
            tipo=tipo,
            nombre=nombre,
        )
    )


@router.get("/indicadores/export")
async def plan_mejoramiento_indicadores_export(
    subvista: str = Query("metas"),
    factor: str | None = Query(None),
    caracteristica: str | None = Query(None),
    tipo: str | None = Query(None),
    nombre: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: PlanMejoramientoService = Depends(_service),
) -> Response:
    content = await run_sync(
        service.export_indicadores_excel,
        subvista=subvista,
        factor=factor,
        caracteristica=caracteristica,
        tipo=tipo,
        nombre=nombre,
    )
    filename = (
        "indicadores_metas.xlsx" if subvista != "historico" else "indicadores_cumplimiento.xlsx"
    )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/indicadores/detalle", response_model=PlanIndicadorDetalleResponse)
async def plan_mejoramiento_indicador_detalle(
    factor: str = Query(...),
    indicador: str = Query(...),
    _user: User = Depends(require_reader),
    service: PlanMejoramientoService = Depends(_service),
) -> PlanIndicadorDetalleResponse:
    detalle = await run_sync(service.get_indicador_detalle, factor=factor, indicador=indicador)
    if detalle is None:
        raise HTTPException(status_code=404, detail="Indicador no encontrado")
    return PlanIndicadorDetalleResponse(**detalle)


@router.get("/metricas", response_model=PlanMetricasDashboardResponse)
async def plan_mejoramiento_metricas(
    factor: str | None = Query(None),
    caracteristica: str | None = Query(None),
    tendencia: str | None = Query(None),
    nombre: str | None = Query(None),
    _user: User = Depends(require_reader),
    service: PlanMejoramientoService = Depends(_service),
) -> PlanMetricasDashboardResponse:
    """Pestaña 'Métricas' del Plan de Mejoramiento — ver
    docs/migration/PLAN_MIGRACION_PRIORIZADO.md ítem 0. Factor/Característica
    son filtros globales del módulo, compartidos con /indicadores."""
    return PlanMetricasDashboardResponse(
        **await run_sync(
            service.get_metricas_dashboard,
            factor=factor,
            caracteristica=caracteristica,
            tendencia=tendencia,
            nombre=nombre,
        )
    )


@router.get("/metricas/detalle", response_model=PlanMetricaDetalleResponse)
async def plan_mejoramiento_metrica_detalle(
    factor: str = Query(...),
    indicador: str = Query(...),
    subindicador: str | None = Query(None),
    grupo: str | None = Query(None, description="Subtotal (nivel intermedio) cuya ficha se pide"),
    _user: User = Depends(require_reader),
    service: PlanMejoramientoService = Depends(_service),
) -> PlanMetricaDetalleResponse:
    detalle = await run_sync(
        service.get_metrica_detalle,
        factor=factor,
        indicador=indicador,
        subindicador=subindicador,
        grupo=grupo,
    )
    if detalle is None:
        raise HTTPException(status_code=404, detail="Métrica no encontrada")
    return PlanMetricaDetalleResponse(**detalle)
