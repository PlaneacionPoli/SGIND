"""Benchmarks de rendimiento — valida optimizaciones de caché."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from app.api.deps import get_excel_service, reset_excel_service_for_tests
from app.core.config import get_settings
from app.domain.cmi_filters import _KAWAK_IDS_CACHE, _PROCESOS_IDS_CACHE, _WORKSHEET_CACHE
from app.domain.procesos_loaders import _PROCESS_MAP_CACHE
from app.services.cmi_service import CMIService, _YEAR_PREPARED_CACHE
from app.services.informe_service import InformeService
from app.services.tracking_cache import clear_tracking_cache


def _setup():
    settings = get_settings()
    settings.sgind_data_path = str(Path(__file__).resolve().parents[3] / "data")
    reset_excel_service_for_tests()
    clear_tracking_cache()
    _WORKSHEET_CACHE.clear()
    _KAWAK_IDS_CACHE.clear()
    _PROCESOS_IDS_CACHE.clear()
    _PROCESS_MAP_CACHE.clear()
    _YEAR_PREPARED_CACHE.clear()
    return get_excel_service(settings)


@pytest.fixture
def excel():
    return _setup()


def test_cmi_dashboard_under_3s_warm_cache(excel):
    svc = CMIService(excel)
    svc.get_procesos_dashboard(anio=2025, mes=11)
    t0 = time.perf_counter()
    svc.get_procesos_dashboard(anio=2025, mes=11)
    elapsed = time.perf_counter() - t0
    assert elapsed < 3.0, f"dashboard warm took {elapsed:.2f}s"


def test_informe_dashboard_under_4s_warm_cache(excel):
    svc = InformeService(excel)
    svc.get_dashboard(anio=2025, mes=11)
    t0 = time.perf_counter()
    svc.get_dashboard(anio=2025, mes=11)
    elapsed = time.perf_counter() - t0
    assert elapsed < 4.0, f"informe warm took {elapsed:.2f}s"


def test_kawak_ids_cached_across_calls(excel):
    from app.domain.cmi_filters import CMIFilterService

    cmi = CMIFilterService(excel)
    t0 = time.perf_counter()
    cmi._load_kawak_active_ids(2025)
    first = time.perf_counter() - t0
    t0 = time.perf_counter()
    cmi._load_kawak_active_ids(2025)
    second = time.perf_counter() - t0
    assert second < first * 0.1 or second < 0.05
