from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_excel_service
from app.core.concurrency import run_sync
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import require_operational
from app.domain.alertas_builders import PLACEHOLDERS, fecha_limite, proximo_corte
from app.models.user import User
from app.schemas.alertas import (
    AlertaConfigOut,
    AlertaConfigUpdate,
    AlertasConfigResponse,
    BorradoresRequest,
    DestinatariosUpdate,
    EnvioOut,
    NotificacionesResponse,
    PlazoUpdate,
    VistaPreviaResponse,
)
from app.schemas.common import SeguimientoDashboardResponse, SeguimientoFiltrosResponse
from app.services.alertas_service import AlertasService, hoy_bogota
from app.services.excel_reader import ExcelReaderService
from app.services.seguimiento_service import SeguimientoService

router = APIRouter()


def _service(excel: ExcelReaderService = Depends(get_excel_service)) -> SeguimientoService:
    return SeguimientoService(excel)


def _alertas_service(
    excel: ExcelReaderService = Depends(get_excel_service),
    settings: Settings = Depends(get_settings),
) -> AlertasService:
    return AlertasService(excel, settings)


@router.get("/filtros", response_model=SeguimientoFiltrosResponse)
async def seguimiento_filtros(
    _user: User = Depends(require_operational),
    service: SeguimientoService = Depends(_service),
) -> SeguimientoFiltrosResponse:
    """Devuelve años, meses, procesos y estados disponibles."""
    return SeguimientoFiltrosResponse(**await run_sync(service.get_filtros))


@router.get("/dashboard", response_model=SeguimientoDashboardResponse)
async def seguimiento_dashboard(
    anio: int | None = Query(None),
    mes: int | None = Query(None, ge=1, le=12),
    proceso: str | None = Query(None),
    estado: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    orden_por: Literal["Id", "Indicador", "Proceso", "Periodicidad", "Corte", "Estado"]
    | None = Query(None),
    orden_dir: Literal["asc", "desc"] = Query("asc"),
    busqueda: str | None = Query(None, max_length=100),
    _user: User = Depends(require_operational),
    service: SeguimientoService = Depends(_service),
) -> SeguimientoDashboardResponse:
    return SeguimientoDashboardResponse(
        **await run_sync(
            service.get_dashboard,
            anio=anio,
            mes=mes,
            proceso=proceso,
            estado=estado,
            limit=limit,
            offset=offset,
            orden_por=orden_por,
            orden_dir=orden_dir,
            busqueda=busqueda,
        )
    )


@router.get("/export")
async def seguimiento_export(
    anio: int | None = Query(None),
    mes: int | None = Query(None, ge=1, le=12),
    proceso: str | None = Query(None),
    estado: str | None = Query(None),
    busqueda: str | None = Query(None, max_length=100),
    _user: User = Depends(require_operational),
    service: SeguimientoService = Depends(_service),
) -> Response:
    content = await run_sync(
        service.export_excel,
        anio=anio,
        mes=mes,
        proceso=proceso,
        estado=estado,
        busqueda=busqueda,
    )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=seguimiento_filtrado.xlsx"},
    )


# ── Alertas por correo ───────────────────────────────────────────────────────


@router.get("/alertas/config", response_model=AlertasConfigResponse)
async def alertas_config(
    _user: User = Depends(require_operational),
    db: AsyncSession = Depends(get_db),
    service: AlertasService = Depends(_alertas_service),
    settings: Settings = Depends(get_settings),
) -> AlertasConfigResponse:
    cfg = await service.get_config(db)
    anio, mes = proximo_corte(hoy_bogota(), cfg.plazo_dias)
    destinatarios, origen = await service.listar_destinatarios(db, con_origen=True)
    return AlertasConfigResponse(
        config=AlertaConfigOut.model_validate(cfg),
        destinatarios=destinatarios,
        origen_destinatarios=origen,
        plazos=await service.listar_plazos(db),
        procesos=await run_sync(service.procesos_disponibles),
        placeholders=PLACEHOLDERS,
        scheduler_activo=settings.alertas_scheduler_enabled,
        proximo_corte={
            "anio": anio,
            "mes": mes,
            "fecha_limite": fecha_limite(anio, mes, cfg.plazo_dias).isoformat(),
        },
    )


@router.put("/alertas/config", response_model=AlertaConfigOut)
async def alertas_config_update(
    body: AlertaConfigUpdate,
    user: User = Depends(require_operational),
    db: AsyncSession = Depends(get_db),
    service: AlertasService = Depends(_alertas_service),
) -> AlertaConfigOut:
    try:
        cfg = await service.update_config(db, body.model_dump(exclude_none=True), user.email)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AlertaConfigOut.model_validate(cfg)


@router.put("/alertas/destinatarios", response_model=dict[str, list[str]])
async def alertas_destinatarios_update(
    body: DestinatariosUpdate,
    _user: User = Depends(require_operational),
    db: AsyncSession = Depends(get_db),
    service: AlertasService = Depends(_alertas_service),
) -> dict[str, list[str]]:
    if body.proceso not in await run_sync(service.procesos_disponibles):
        raise HTTPException(status_code=404, detail="Proceso no existe en el tracking")
    try:
        await service.guardar_destinatarios(db, body.proceso, body.emails)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return await service.listar_destinatarios(db)


@router.put("/alertas/plazos", response_model=dict[str, int])
async def alertas_plazo_update(
    body: PlazoUpdate,
    _user: User = Depends(require_operational),
    db: AsyncSession = Depends(get_db),
    service: AlertasService = Depends(_alertas_service),
) -> dict[str, int]:
    if body.proceso not in await run_sync(service.procesos_disponibles):
        raise HTTPException(status_code=404, detail="Proceso no existe en el tracking")
    await service.guardar_plazo(db, body.proceso, body.plazo_dias)
    return await service.listar_plazos(db)


@router.get("/alertas/vista-previa", response_model=VistaPreviaResponse)
async def alertas_vista_previa(
    proceso: str = Query(..., min_length=1),
    anio: int | None = Query(None),
    mes: int | None = Query(None, ge=1, le=12),
    tipo: Literal["recordatorio", "apertura"] = Query("recordatorio"),
    _user: User = Depends(require_operational),
    db: AsyncSession = Depends(get_db),
    service: AlertasService = Depends(_alertas_service),
) -> VistaPreviaResponse:
    cfg = await service.get_config(db)
    plazos = await service.listar_plazos(db)
    return VistaPreviaResponse(
        **await run_sync(service.vista_previa, cfg, plazos, proceso, anio, mes, tipo)
    )


_ZIP = "application/zip"


def _zip_response(contenido: bytes, nombre: str, resumen: dict[str, Any]) -> Response:
    return Response(
        content=contenido,
        media_type=_ZIP,
        headers={
            "Content-Disposition": f"attachment; filename={nombre}",
            "X-Borradores-Total": str(resumen["total"]),
            "X-Borradores-Sin-Destinatarios": str(len(resumen["sin_destinatarios"])),
        },
    )


@router.get("/alertas/borrador")
async def alertas_borrador(
    proceso: str = Query(..., min_length=1),
    anio: int | None = Query(None),
    mes: int | None = Query(None, ge=1, le=12),
    tipo: Literal["recordatorio", "apertura"] = Query("recordatorio"),
    _user: User = Depends(require_operational),
    db: AsyncSession = Depends(get_db),
    service: AlertasService = Depends(_alertas_service),
) -> Response:
    """Un borrador .eml del proceso (Outlook lo abre como mensaje sin enviar)."""
    try:
        nombre, contenido = await service.borrador_proceso(db, proceso, anio, mes, tipo)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        content=contenido,
        media_type="message/rfc822",
        headers={"Content-Disposition": f"attachment; filename={nombre}"},
    )


@router.get("/alertas/listado-outlook")
async def alertas_listado_outlook(
    anio: int | None = Query(None),
    mes: int | None = Query(None, ge=1, le=12),
    tipo: Literal["recordatorio", "apertura"] = Query("recordatorio"),
    _user: User = Depends(require_operational),
    db: AsyncSession = Depends(get_db),
    service: AlertasService = Depends(_alertas_service),
) -> Response:
    """Listado_de_indicadores.xlsx con el formato de la automatización local Auto_Correo."""
    contenido, a, m = await service.listado_outlook(db, anio, mes, tipo)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=Listado_de_indicadores_{a}-{m:02d}.xlsx"
        },
    )


@router.post("/alertas/borradores")
async def alertas_borradores(
    body: BorradoresRequest,
    _user: User = Depends(require_operational),
    db: AsyncSession = Depends(get_db),
    service: AlertasService = Depends(_alertas_service),
) -> Response:
    """ZIP con un borrador .eml por proceso para el corte (por defecto, el próximo)."""
    contenido, resumen = await service.generar_paquete(
        db, body.anio, body.mes, body.tipo, body.procesos
    )
    nombre = f"borradores_{body.tipo}_{resumen['anio']}-{resumen['mes']:02d}.zip"
    return _zip_response(contenido, nombre, resumen)


@router.get("/alertas/notificaciones", response_model=NotificacionesResponse)
async def alertas_notificaciones(
    _user: User = Depends(require_operational),
    db: AsyncSession = Depends(get_db),
    service: AlertasService = Depends(_alertas_service),
) -> NotificacionesResponse:
    """Borradores que el programador dejó listos y nadie ha descargado."""
    return NotificacionesResponse(**await service.notificaciones(db))


@router.post("/alertas/descargar-pendientes")
async def alertas_descargar_pendientes(
    _user: User = Depends(require_operational),
    db: AsyncSession = Depends(get_db),
    service: AlertasService = Depends(_alertas_service),
) -> Response:
    contenido, resumen = await service.descargar_pendientes(db)
    return _zip_response(contenido, "borradores_pendientes.zip", resumen)


@router.get("/alertas/historial", response_model=list[EnvioOut])
async def alertas_historial(
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_operational),
    db: AsyncSession = Depends(get_db),
    service: AlertasService = Depends(_alertas_service),
) -> list[EnvioOut]:
    return [EnvioOut.model_validate(r) for r in await service.historial(db, limit)]
