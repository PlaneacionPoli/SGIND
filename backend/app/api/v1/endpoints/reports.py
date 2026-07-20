"""Endpoints de generación de reportes PDF — SGIND v2 Fase 9."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.deps import get_excel_service
from app.core.security import require_reader
from app.models.user import User
from app.services.cmi_service import CMIService
from app.services.dashboard_service import DashboardService
from app.services.excel_reader import ExcelReaderService
from app.services.informe_service import InformeService
from app.services.pdf_service import (
    generar_ficha_indicador,
    generar_informe_procesos,
    generar_resumen_general,
)

router = APIRouter()


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _excel(excel: ExcelReaderService = Depends(get_excel_service)) -> ExcelReaderService:
    return excel


@router.get(
    "/resumen-general",
    summary="PDF Resumen General de Indicadores",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF con KPIs globales y tabla de indicadores.",
        }
    },
)
async def pdf_resumen_general(
    anio: int = Query(..., description="Año del reporte"),
    _user: User = Depends(require_reader),
    excel: ExcelReaderService = Depends(_excel),
) -> StreamingResponse:
    service = DashboardService(excel)
    kpis_list = service.get_kpis(anio=anio)
    semaforo = service.get_semaphore(anio=anio)

    # get_kpis devuelve lista de KPIResponse; extraemos los agregados
    kpis: dict = {}
    if kpis_list:
        for item in kpis_list:
            d = item if isinstance(item, dict) else (item.model_dump() if hasattr(item, "model_dump") else {})
            kpis.update(d)

    indicadores = semaforo if isinstance(semaforo, list) else []

    pdf_bytes = generar_resumen_general(
        anio=anio,
        kpis=kpis,
        indicadores=indicadores,
        generated_at=_now_iso(),
    )

    filename = f"resumen_general_{anio}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/informe-procesos",
    summary="PDF Informe por Procesos",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF con resumen ejecutivo, distribución y tabla de indicadores por proceso.",
        }
    },
)
async def pdf_informe_procesos(
    anio: int = Query(..., description="Año del reporte"),
    mes: int = Query(12, ge=1, le=12, description="Mes del reporte"),
    proceso: str | None = Query(None, description="Filtrar por proceso"),
    _user: User = Depends(require_reader),
    excel: ExcelReaderService = Depends(_excel),
) -> StreamingResponse:
    service = InformeService(excel)
    data = service.get_dashboard(
        anio=anio,
        mes=mes,
        proceso=proceso if proceso and proceso != "Todos" else None,
    )

    pdf_bytes = generar_informe_procesos(
        anio=anio,
        mes=mes,
        proceso=proceso or "Todos",
        data=data,
        generated_at=_now_iso(),
    )

    proceso_slug = (proceso or "todos").lower().replace(" ", "_")[:30]
    filename = f"informe_procesos_{anio}_{mes:02d}_{proceso_slug}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/ficha/{indicador_id}",
    summary="PDF de ficha individual de indicador",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF con meta, ejecución, cumplimiento e histórico del indicador.",
        }
    },
)
async def pdf_ficha_indicador(
    indicador_id: str,
    anio: int = Query(..., description="Año del corte"),
    mes: int | None = Query(None, ge=1, le=12),
    corte: str | None = Query(None, description="Junio o Diciembre (CMI Estratégico)"),
    origen: str = Query("estrategico", description="estrategico o procesos"),
    unidad: str | None = Query(None),
    proceso: str | None = Query(None),
    subproceso: str | None = Query(None),
    _user: User = Depends(require_reader),
    excel: ExcelReaderService = Depends(_excel),
) -> StreamingResponse:
    service = CMIService(excel)
    if origen == "procesos":
        ficha = service.get_procesos_indicador_ficha(
            indicador_id,
            anio=anio,
            mes=mes,
            unidad=unidad,
            proceso=proceso,
            subproceso=subproceso,
        )
    else:
        ficha = service.get_indicador_ficha(indicador_id, anio=anio, mes=mes, corte=corte)

    if ficha is None:
        raise HTTPException(status_code=404, detail="Indicador no encontrado para el corte seleccionado")

    pdf_bytes = generar_ficha_indicador(ficha, generated_at=_now_iso())

    filename = f"ficha_{indicador_id}_{anio}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
