from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_excel_service
from app.core.concurrency import run_sync
from app.core.security import require_reader
from app.models.user import User
from app.services.excel_reader import ExcelReaderService
from app.services.polisigs_service import ANIO, ANIOS, CORTES, MES_CORTE, get_polisigs

router = APIRouter()


@router.get("")
async def polisigs(
    anio: int = Query(ANIO),
    mes: int = Query(MES_CORTE, description="Mes de corte: 6 (junio) o 12 (diciembre)"),
    _user: User = Depends(require_reader),
    excel: ExcelReaderService = Depends(get_excel_service),
) -> dict[str, Any]:
    """Cumplimiento de la política (por defecto, corte junio 2026) POLISIGS, por objetivo e indicador."""
    if anio not in ANIOS:
        raise HTTPException(status_code=422, detail=f"anio debe ser uno de {ANIOS}")
    if mes not in CORTES:
        raise HTTPException(status_code=422, detail=f"mes debe ser uno de {CORTES}")
    try:
        return await run_sync(get_polisigs, excel, anio, mes)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
