"""Generador del tracking (scripts/generar_seguimiento.py) sin LMI, ids_métrica desde Kawak y
validación de frescura del orquestador. Todo con archivos temporales: no toca data/."""

from __future__ import annotations

import importlib
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def gs():
    sys.path.insert(0, str(REPO / "scripts"))
    tenia = "SGIND_DATA_PATH" in os.environ
    mod = importlib.import_module("generar_seguimiento")
    if not tenia:  # el módulo fija un valor por defecto al importarse; no se filtra a otros tests
        os.environ.pop("SGIND_DATA_PATH", None)
    return mod


def _kawak_2026(path: Path, filas: list[dict]) -> None:
    pd.DataFrame(filas).to_excel(path, index=False)


def test_leer_kawak_anual_usa_solo_filas_consolidadas_y_fechas_del_encabezado(gs, tmp_path):
    _kawak_2026(
        tmp_path / "2026.xlsx",
        [
            {"Id": 1, "Nombre variable/consolidado": "Consolidado Global", "2026-01-31 Periodo 32": 90, "2026-02-28 Periodo 33": 91, "2026-03-31 Periodo 34": None},
            # fila de variable con dato en marzo: NO cuenta como indicador reportado
            {"Id": 1, "Nombre variable/consolidado": "Variable A", "2026-01-31 Periodo 32": None, "2026-02-28 Periodo 33": None, "2026-03-31 Periodo 34": 5},
            {"Id": 2, "Nombre variable/consolidado": "Consolidado Global", "2026-01-31 Periodo 32": "-", "2026-02-28 Periodo 33": None, "2026-03-31 Periodo 34": None},
        ],
    )
    lookup, ultimo = gs.leer_kawak_anual(str(tmp_path), [2026])
    assert set(lookup) == {("1", 2026, 1), ("1", 2026, 2)}
    assert ultimo[2026] == date(2026, 2, 28)


def test_tracking_combina_api_y_archivo_anual_sin_fuente_lmi(gs):
    catalogo = {2026: {"1": "Mensual", "2": "Trimestral"}}
    meta = {2026: {"1": {"Indicador": "A", "Proceso": "P1"}, "2": {"Indicador": "B", "Proceso": "P2"}}}
    calendario = [(2026, 1), (2026, 2), (2026, 3)]
    df = gs.construir_tracking_largo(
        catalogo,
        {("1", 2026, 1): 10},  # API
        {("1", 2026, 2): True},  # archivo anual de Kawak
        calendario,
        meta,
    )
    estados = {(r.Id, r.Mes): (r.Estado, r.Fuente) for r in df.itertuples()}
    assert estados[("1", 1)] == ("Reportado", "Kawak")
    assert estados[("1", 2)] == ("Reportado", "Kawak anual")
    assert estados[("1", 3)] == ("Pendiente", "—")
    assert ("2", 1) not in estados and estados[("2", 3)][0] == "Pendiente"  # trimestral: solo marzo
    assert not df["Fuente"].astype(str).str.contains("LMI").any()


def test_main_genera_el_archivo_sin_necesitar_lmi(gs, tmp_path, monkeypatch):
    kawak = tmp_path / "Kawak"
    kawak.mkdir()
    _kawak_2026(
        kawak / "2026.xlsx",
        [
            {"Id": 1, "Indicador": "Ind uno", "Proceso": "Calidad", "Periodicidad": "Mensual", "Nombre variable/consolidado": "Consolidado Global",
             "2026-01-31 Periodo 1": 1, "2026-02-28 Periodo 2": None, "2026-03-31 Periodo 3": None},
            {"Id": 2, "Indicador": "Ind dos", "Proceso": "Finanzas", "Periodicidad": "Trimestral", "Nombre variable/consolidado": "Consolidado Global",
             "2026-01-31 Periodo 1": None, "2026-02-28 Periodo 2": None, "2026-03-31 Periodo 3": None},
        ],
    )
    api = tmp_path / "Consolidado_API_Kawak.xlsx"
    pd.DataFrame([{"ID": 1, "fecha": "2026-02-28", "resultado": 5}, {"ID": 2, "fecha": "2026-03-31", "resultado": 7}]).to_excel(api, index=False)
    monkeypatch.setattr(gs, "RUTA_KAWAK_DIR", str(kawak))
    monkeypatch.setattr(gs, "RUTA_KAWAK_API", str(api))
    monkeypatch.setattr(gs, "RUTA_CONSOLIDADOS", str(tmp_path / "no_existe.xlsx"))
    monkeypatch.setattr(gs, "FECHA_INICIO", date(2026, 1, 1))
    salida = tmp_path / "out" / "Seguimiento_Reporte.xlsx"

    assert gs.main(["--salida", str(salida), "--fecha-ref", "2026-03-31"]) == 0

    t = pd.read_excel(salida, sheet_name="Tracking Mensual")
    t.columns = [str(c).strip() for c in t.columns]
    assert {"Id", "Indicador", "Proceso", "Periodicidad", "Año", "Mes", "Estado"} <= set(t.columns)
    assert not any("Periodo " in str(c) and c != "Periodo" for c in t.columns)  # sin columnas de periodo de Kawak
    est = {(int(r.Id), int(r.Mes)): r.Estado for r in t.itertuples()}
    assert est == {(1, 1): "Reportado", (1, 2): "Reportado", (1, 3): "Pendiente", (2, 3): "Reportado"}


def test_main_no_sobrescribe_si_no_hay_catalogos(gs, tmp_path, monkeypatch):
    monkeypatch.setattr(gs, "RUTA_KAWAK_DIR", str(tmp_path / "vacio"))
    monkeypatch.setattr(gs, "FECHA_INICIO", date(2026, 1, 1))
    salida = tmp_path / "Seguimiento_Reporte.xlsx"
    salida.write_bytes(b"archivo previo")
    assert gs.main(["--salida", str(salida), "--fecha-ref", "2026-03-31"]) == 2
    assert salida.read_bytes() == b"archivo previo"  # no se pisa con un resultado vacío


def test_ids_metrica_une_todos_los_anios_de_kawak(tmp_path, monkeypatch):
    sys.path.insert(0, str(REPO))
    fuentes = importlib.import_module("scripts.etl.fuentes")
    kawak = tmp_path / "Kawak"
    kawak.mkdir()
    pd.DataFrame(
        [{"Id": 268, "Indicador": "Solo 2025", "Tipo": "Metrica"}, {"Id": 10, "Indicador": "Normal", "Tipo": "Eficacia"}]
    ).to_excel(kawak / "2025.xlsx", index=False)
    pd.DataFrame(
        [{"Id": 626, "Indicador": "Nueva", "Tipo": "Metrica"}, {"Id": 11, "Indicador": "Total metrica x", "Tipo": "Eficacia"}]
    ).to_excel(kawak / "2026.xlsx", index=False)
    monkeypatch.setattr(fuentes, "BASE_PATH", tmp_path)
    # 268 (dado de baja en 2026) sigue siendo Métrica; 11 lo es por su nombre; 10 no
    assert fuentes.cargar_ids_metrica() == {"268", "626", "11"}
    monkeypatch.setattr(fuentes, "BASE_PATH", tmp_path / "sin_kawak")
    assert fuentes.cargar_ids_metrica() == set()


def _tracking_hasta(path: Path, anio: int, mes: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"Id": [1, 1], "Año": [anio, anio], "Mes": [mes - 1 or 12, mes]}).to_excel(path, sheet_name="Tracking Mensual", index=False)


def test_frescura_avisa_si_el_tracking_esta_atrasado(tmp_path):
    sys.path.insert(0, str(REPO / "scripts"))
    rp = importlib.import_module("run_pipeline")
    _tracking_hasta(tmp_path / "data" / "output" / "Seguimiento_Reporte.xlsx", 2026, 7)
    avisos = rp._frescura_seguimiento(tmp_path, {}, datetime(2026, 10, 9))
    assert any("07/2026" in a and "09/2026" in a for a in avisos)


def test_frescura_no_avisa_si_esta_al_dia_y_posterior_a_las_fuentes(tmp_path):
    sys.path.insert(0, str(REPO / "scripts"))
    rp = importlib.import_module("run_pipeline")
    kawak = tmp_path / "data" / "raw" / "Kawak"
    kawak.mkdir(parents=True)
    (kawak / "2026.xlsx").write_bytes(b"x")
    os.utime(kawak / "2026.xlsx", (time.time() - 3600, time.time() - 3600))  # fuente de hace 1 h
    _tracking_hasta(tmp_path / "data" / "output" / "Seguimiento_Reporte.xlsx", 2026, 9)
    assert rp._frescura_seguimiento(tmp_path, {}, datetime(2026, 10, 9)) == []
    # una fuente más nueva que el tracking sí genera aviso
    os.utime(kawak / "2026.xlsx", (time.time() + 3600, time.time() + 3600))
    assert any("anterior a la ultima actualizacion" in a for a in rp._frescura_seguimiento(tmp_path, {}, datetime(2026, 10, 9)))
