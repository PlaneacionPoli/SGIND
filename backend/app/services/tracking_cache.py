"""Caché del pipeline ETL de tracking (consolidado semestral / histórico)."""

from __future__ import annotations

import pandas as pd

from app.core.ttl_cache import cache_get
from app.services.etl_pipeline import ETLPipelineService
from app.services.excel_reader import ExcelReaderService

_TRACKING_CACHE: dict[tuple[str, bool], tuple[float, pd.DataFrame]] = {}


def get_tracking_dataframe(excel: ExcelReaderService, *, historico: bool = False) -> pd.DataFrame:
    root = str(excel.data_root.resolve())
    key = (root, historico)

    def _load() -> pd.DataFrame:
        etl = ETLPipelineService(excel)
        return etl.ejecutar(historico=historico)

    return cache_get(_TRACKING_CACHE, key, _load)


def clear_tracking_cache() -> None:
    _TRACKING_CACHE.clear()
