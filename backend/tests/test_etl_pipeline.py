import pytest

from app.core.config import Settings
from app.services.etl_pipeline import ETLPipelineService
from app.services.excel_reader import ExcelReaderService
from app.services.indicator_service import IndicatorService


@pytest.fixture
def settings():
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    data_path = root / "data"
    return Settings(
        sgind_data_path=str(data_path),
        excel_cache_ttl_seconds=60,
        environment="development",
    )


@pytest.fixture
def excel(settings):
    return ExcelReaderService(settings)


@pytest.fixture
def etl(excel):
    return ETLPipelineService(excel)


def test_etl_pipeline_loads_data(etl):
    try:
        df = etl.ejecutar()
    except FileNotFoundError:
        pytest.skip("Archivo consolidado no disponible en data/")
    assert not df.empty
    assert "Id" in df.columns
    assert "Categoria" in df.columns or "Cumplimiento" in df.columns


def test_indicator_service_filter_anio(excel):
    service = IndicatorService(excel)
    try:
        result = service.list_indicators(anio=2025, limit=10)
    except FileNotFoundError:
        pytest.skip("Archivo consolidado no disponible")
    assert "total" in result
    assert "items" in result
    if result["total"] > 0:
        for item in result["items"]:
            if item.get("Anio") is not None:
                assert item["Anio"] == 2025
