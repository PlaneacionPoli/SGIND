"""Dependencia FastAPI: resuelve y valida el PDI pedido (`?pdi=<version_id>`)."""

from fastapi import Depends, HTTPException, Query

from app.domain.marcos import Marco, get_marco, marco_por_defecto


def get_pdi_marco(
    pdi: str | None = Query(
        None,
        description="version_id del PDI (p. ej. PDI-2022-2026). Vacío = el vigente con datos.",
    ),
) -> Marco:
    """404 si el PDI no existe, 422 si no es un PDI, 409 si aún no tiene datos
    cargados (nunca se sirven datos de otro ciclo en su lugar)."""
    if pdi is None:
        return marco_por_defecto("PDI")
    try:
        marco = get_marco(pdi)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"PDI no encontrado: {pdi}") from None
    if marco.tipo != "PDI":
        raise HTTPException(status_code=422, detail=f"{pdi} no es un PDI")
    if not marco.datos_disponibles:
        raise HTTPException(
            status_code=409,
            detail=f"{marco.nombre}: la información de este ciclo aún no está cargada",
        )
    return marco


def pdi_para(modulo: str):
    """Dependencia que además exige que el módulo esté habilitado para el PDI pedido
    (409 si no): el Resumen General aún no está listo para el PDI 2026-2030."""

    def _dep(marco: Marco = Depends(get_pdi_marco)) -> Marco:
        if not marco.sirve(modulo):
            raise HTTPException(
                status_code=409,
                detail=f"{marco.nombre}: el módulo {modulo} aún no está disponible para este ciclo",
            )
        return marco

    return _dep
