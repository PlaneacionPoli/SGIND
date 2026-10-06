from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_excel_service
from app.core.concurrency import run_sync
from app.core.security import require_reader
from app.models.user import User
from app.services.excel_reader import ExcelReaderService
from app.services.polisigs_service import get_polisigs

router = APIRouter()


@router.get("")
async def polisigs(
    _user: User = Depends(require_reader),
    excel: ExcelReaderService = Depends(get_excel_service),
) -> dict[str, Any]:
    """Cumplimiento 2026 de la política POLISIGS, por objetivo e indicador."""
    try:
        return await run_sync(get_polisigs, excel)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
