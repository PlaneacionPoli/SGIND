from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_excel_service
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import require_admin, require_reader
from app.models.user import User
from app.schemas.common import RegistroOMCerrar, RegistroOMCreate, RegistroOMResponse, RegistroOMUpdate
from app.services.excel_reader import ExcelReaderService
from app.services.om_matriz_service import OMMatrizService
from app.services.om_service import OMService

router = APIRouter()
_om_service = OMService()


def _excel(settings: Settings = Depends(get_settings)) -> ExcelReaderService:
    return get_excel_service(settings)


def _matriz_service(excel: ExcelReaderService = Depends(_excel)) -> OMMatrizService:
    return OMMatrizService(excel)


@router.get("/matriz")
async def om_matriz(
    anio: int = Query(...),
    mes: str = Query("Diciembre"),
    proceso: str | None = Query(None),
    subproceso: str | None = Query(None),
    mostrar_alerta: bool = Query(False),
    _user: User = Depends(require_reader),
    db: AsyncSession = Depends(get_db),
    service: OMMatrizService = Depends(_matriz_service),
) -> dict:
    return await service.get_matriz(
        db,
        anio=anio,
        mes=mes,
        proceso=proceso,
        subproceso=subproceso,
        mostrar_alerta=mostrar_alerta,
    )


@router.get("", response_model=list[RegistroOMResponse])
async def list_om(
    anio: int | None = Query(None),
    periodo: str | None = Query(None),
    _user: User = Depends(require_reader),
    db: AsyncSession = Depends(get_db),
) -> list[RegistroOMResponse]:
    registros = await _om_service.list_registros(db, anio=anio, periodo=periodo)
    return registros


@router.post("", response_model=RegistroOMResponse, status_code=status.HTTP_201_CREATED)
async def create_om(
    data: RegistroOMCreate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> RegistroOMResponse:
    data.registrado_por = user.email
    return await _om_service.create(db, data)


@router.put("/{registro_id}", response_model=RegistroOMResponse)
async def update_om(
    registro_id: int,
    data: RegistroOMUpdate,
    _user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> RegistroOMResponse:
    registro = await _om_service.update(db, registro_id, data)
    if registro is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado")
    return registro


@router.patch("/{registro_id}/cerrar", response_model=RegistroOMResponse)
async def cerrar_om(
    registro_id: int,
    data: RegistroOMCerrar,
    _user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> RegistroOMResponse:
    """Cierra un OM: establece tiene_om=0. Acepta comentario opcional."""
    registro = await _om_service.cerrar(db, registro_id, data)
    if registro is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado")
    return registro


@router.delete("/{registro_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_om(
    registro_id: int,
    _user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await _om_service.delete(db, registro_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado")
