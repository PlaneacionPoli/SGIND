"""Fichas: histórico completo e independiente del PDI; el resumen del CMI por procesos es semestral."""

import pytest

from app.api.deps import get_excel_service
from app.core.config import get_settings
from app.services.cmi_service import CMIService


@pytest.fixture(scope="module")
def svc() -> CMIService:
    return CMIService(get_excel_service(get_settings()))


def test_ficha_procesos_historico_no_depende_del_pdi_ni_del_anio(svc: CMIService):
    a = svc.get_procesos_indicador_ficha("69", anio=2026, mes=6, pdi="PDI-2022-2026")
    b = svc.get_procesos_indicador_ficha("69", anio=2026, mes=6, pdi="PDI-2026-2030")
    c = svc.get_procesos_indicador_ficha("69", anio=2024, mes=12, pdi="PDI-2026-2030")
    assert a and b and c
    assert a["historico"] == b["historico"] == c["historico"]
    # Todos los años y cortes intermedios (no solo junio/diciembre ni solo el año elegido).
    periodos = [h["periodo"] for h in a["historico"]]
    assert len({p[:4] for p in periodos}) >= 4
    assert any(p[5:] in ("03", "09") for p in periodos)
    assert periodos == sorted(periodos)


def test_ficha_procesos_linea_y_objetivo_si_dependen_del_pdi(svc: CMIService):
    a = svc.get_procesos_indicador_ficha("69", anio=2026, mes=6, pdi="PDI-2022-2026")
    b = svc.get_procesos_indicador_ficha("69", anio=2026, mes=6, pdi="PDI-2026-2030")
    assert a["linea_estrategica"] and b["linea_estrategica"]
    assert a["linea_estrategica"] != b["linea_estrategica"]
    assert a["asociaciones_pdi"][0]["seleccionado"] is True


def test_ficha_historico_trae_variacion_entre_periodos_consecutivos(svc: CMIService):
    h = svc.get_procesos_indicador_ficha("69", anio=2026, mes=6)["historico"]
    assert h[0]["variacion_cumplimiento_pp"] is None
    for prev, cur in zip(h, h[1:]):
        if prev["cumplimiento"] is not None and cur["cumplimiento"] is not None:
            esperado = round(cur["cumplimiento"] - prev["cumplimiento"], 1)
            assert cur["variacion_cumplimiento_pp"] == pytest.approx(esperado, abs=0.11)


def test_ficha_estrategica_historico_no_se_limita_al_ciclo_del_pdi(svc: CMIService):
    f = svc.get_indicador_ficha("203", anio=2025, mes=12, pdi="PDI-2022-2026")
    assert f and len({h["periodo"][:4] for h in f["historico"]}) >= 4


def test_resumen_cmi_procesos_solo_junio_y_diciembre(svc: CMIService):
    for anio in (2025, 2026):
        assert svc.get_procesos_filtros(anio=anio)["meses"] == [6, 12]
    assert svc.get_procesos_dashboard(anio=2026, mes=6)["meses_disponibles"] == [6, 12]


def test_vista_filtrada_responde_a_los_filtros_y_es_coherente(svc: CMIService):
    todas = svc.get_procesos_dashboard(anio=2026, mes=6)["vista_filtrada"]
    una = svc.get_procesos_dashboard(anio=2026, mes=6, unidad=todas["unidades_detalle"][0]["unidad"])[
        "vista_filtrada"
    ]
    assert len(una["unidades_detalle"]) == 1 < len(todas["unidades_detalle"])
    assert len(una["procesos_detalle"]) < len(todas["procesos_detalle"])
    # Jerarquía unidad → proceso → subproceso: todo proceso pertenece a una unidad listada.
    unidades = {u["unidad"] for u in todas["unidades_detalle"]}
    assert all(p["unidad"] in unidades for p in todas["procesos_detalle"])
    # El corte es el elegido (no el global más reciente, que puede estar incompleto).
    assert todas["mes_nombre"] == "Junio"


def test_indicador_69_se_lee_como_porcentaje_del_api(svc: CMIService):
    f = svc.get_procesos_indicador_ficha("69", anio=2026, mes=6)
    ultimo = f["historico"][-1]
    # Meta 90% y resultado ~91% (no los conteos 1.249 / 1.137 con unidad %).
    assert ultimo["meta"] == pytest.approx(90.0)
    assert 80 < ultimo["ejecucion"] < 100
    assert ultimo["cumplimiento"] == pytest.approx(ultimo["ejecucion"] / ultimo["meta"] * 100, abs=0.2)
