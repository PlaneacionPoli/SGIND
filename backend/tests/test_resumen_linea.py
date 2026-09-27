"""Tests de ResumenService.get_resumen_linea — endpoint nuevo del portal
Resumen General (hoja por línea estratégica), ver docs/migration plan
'Rediseño Resumen General'. Reutiliza build_informe_ejecutivo_lineas, misma
fuente que el Informe Ejecutivo PDF."""

import pytest

from app.api.deps import get_excel_service
from app.core.config import get_settings
from app.services.resumen_service import ResumenService


@pytest.fixture(scope="module")
def resumen_service() -> ResumenService:
    settings = get_settings()
    excel = get_excel_service(settings)
    return ResumenService(excel)


@pytest.mark.parametrize("key", ["expansion", "educacion-para-toda-la-vida"])
@pytest.mark.parametrize("anio", [None, 2023])
def test_get_resumen_linea_shape(resumen_service: ResumenService, key: str, anio: int | None):
    result = resumen_service.get_resumen_linea(key=key, anio=anio)
    assert result is not None
    assert isinstance(result["linea"], str) and result["linea"]
    assert isinstance(result["color"], str) and result["color"].startswith("#")
    assert isinstance(result["icon"], str) and result["icon"]

    retos = result["retos"]
    assert set(retos) == {"avance_real", "avance_esperado", "cumplimiento", "n_areas"}

    for item in result["proyectos"]:
        assert {"id", "nombre", "linea", "anio_inicio", "anio_fin", "estado", "stand_by"}.issubset(item)

    for objetivo in result["objetivos"]:
        assert objetivo["objetivo"]
        for ind in objetivo["indicadores"]:
            assert {"indicador", "meta", "ejecucion", "cumplimiento", "nivel", "nivel_color"}.issubset(ind)


def test_get_resumen_linea_key_desconocida(resumen_service: ResumenService):
    assert resumen_service.get_resumen_linea(key="linea-que-no-existe") is None


def test_get_resumen_linea_slug_con_guiones_normaliza_igual_que_espacios(
    resumen_service: ResumenService,
):
    con_guiones = resumen_service.get_resumen_linea(key="transformacion-organizacional")
    con_espacios = resumen_service.get_resumen_linea(key="transformacion organizacional")
    assert con_guiones is not None
    assert con_guiones["linea"] == con_espacios["linea"]
