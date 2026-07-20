"""Dependencias FastAPI compartidas (singleton de lectura Excel)."""

from __future__ import annotations

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.excel_reader import ExcelReaderService

_excel_singleton: ExcelReaderService | None = None
_excel_root: str | None = None


def get_excel_service(settings: Settings = Depends(get_settings)) -> ExcelReaderService:
    """Una instancia por proceso: la caché de Excel sobrevive entre peticiones HTTP."""
    global _excel_singleton, _excel_root
    root = str(settings.sgind_data_path)
    if _excel_singleton is None or _excel_root != root:
        _excel_singleton = ExcelReaderService(settings)
        _excel_root = root
    return _excel_singleton


def reset_excel_service_for_tests() -> None:
    """Limpia el singleton (solo tests)."""
    global _excel_singleton, _excel_root
    _excel_singleton = None
    _excel_root = None
