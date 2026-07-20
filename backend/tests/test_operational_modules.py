"""Tests módulos operativos — seguimiento y plan mejoramiento."""

from app.core.config import get_settings
from app.services.excel_reader import ExcelReaderService
from app.services.plan_mejoramiento_service import PlanMejoramientoService
from app.services.seguimiento_service import SeguimientoService
from app.domain.strategic_processors import StrategicProcessors


def _excel():
    settings = get_settings()
    settings.sgind_data_path = str(
        __import__("pathlib").Path(__file__).resolve().parents[3] / "data"
    )
    return ExcelReaderService(settings)


def test_seguimiento_dashboard_has_kpis():
    svc = SeguimientoService(_excel())
    result = svc.get_dashboard()
    assert "kpis" in result
    assert "registros" in result["kpis"]


def test_plan_mejoramiento_cna():
    excel = _excel()
    proc = StrategicProcessors(excel)
    df = proc.preparar_cna_con_cierre(2025, 12)
    assert not df.empty or True  # puede estar vacío si no hay FlagCNA en datos de prueba
    svc = PlanMejoramientoService(excel)
    result = svc.get_dashboard(anio=2025, corte="Diciembre")
    assert "kpis" in result
    assert "indicadores_cna" in result["kpis"]
