from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.security import require_reader
from app.domain.marcos import TIPOS_MARCO, Marco, get_marco, get_marcos
from app.domain.taxonomia import load_taxonomia
from app.models.user import User

router = APIRouter()


class MarcoResponse(BaseModel):
    tipo: str
    version_id: str
    nombre: str
    descripcion: str
    anio_datos_desde: int
    anio_datos_hasta: int | None
    estado: str
    orden: int
    imagen: str | None
    datos_disponibles: bool
    # Módulos del dashboard habilitados (vacío = todos si datos_disponibles).
    modulos: list[str] = []


def _to_response(m: Marco) -> MarcoResponse:
    return MarcoResponse(
        tipo=m.tipo,
        version_id=m.version_id,
        nombre=m.nombre,
        descripcion=m.descripcion,
        anio_datos_desde=m.anio_datos_desde,
        anio_datos_hasta=m.anio_datos_hasta,
        estado=m.estado,
        orden=m.orden,
        imagen=m.imagen,
        datos_disponibles=m.datos_disponibles,
        modulos=list(m.modulos),
    )


@router.get("", response_model=list[MarcoResponse])
async def list_marcos(
    tipo: str | None = Query(None, description="PDI | CNA; vacío = todos"),
    _user: User = Depends(require_reader),
) -> list[MarcoResponse]:
    """Marcos disponibles (alimenta la pantalla de selección de PDI)."""
    if tipo is not None and tipo not in TIPOS_MARCO:
        raise HTTPException(status_code=422, detail=f"tipo debe ser uno de {TIPOS_MARCO}")
    return [_to_response(m) for m in get_marcos(tipo)]


@router.get("/{version_id}", response_model=MarcoResponse)
async def read_marco(
    version_id: str,
    _user: User = Depends(require_reader),
) -> MarcoResponse:
    try:
        return _to_response(get_marco(version_id))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Marco no encontrado: {version_id}") from None


class MetaResponse(BaseModel):
    id: str
    nombre: str


class ObjetivoResponse(BaseModel):
    id: str
    numero: int
    nombre: str
    metas: list[MetaResponse]


class LineaResponse(BaseModel):
    id: str
    orden: int
    nombre: str
    objetivos: list[ObjetivoResponse]


class TaxonomiaResponse(BaseModel):
    version_id: str
    tipo: str
    lineas: list[LineaResponse]


@router.get("/{version_id}/taxonomia", response_model=TaxonomiaResponse)
async def read_taxonomia(
    version_id: str,
    _user: User = Depends(require_reader),
) -> TaxonomiaResponse:
    """Líneas, objetivos y metas del marco (alimenta filtros y fichas)."""
    try:
        marco = get_marco(version_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Marco no encontrado: {version_id}") from None
    if not marco.taxonomia:
        raise HTTPException(status_code=404, detail=f"{version_id} no tiene taxonomía")
    tax = load_taxonomia(marco.taxonomia)
    return TaxonomiaResponse(
        version_id=tax.version_id,
        tipo=tax.tipo,
        lineas=[
            LineaResponse(
                id=ln.id,
                orden=ln.orden,
                nombre=ln.nombre,
                objetivos=[
                    ObjetivoResponse(
                        id=o.id,
                        numero=o.numero,
                        nombre=o.nombre,
                        metas=[MetaResponse(id=m.id, nombre=m.nombre) for m in o.metas],
                    )
                    for o in ln.objetivos
                ],
            )
            for ln in tax.lineas
        ],
    )
