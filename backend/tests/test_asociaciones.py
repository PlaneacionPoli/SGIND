"""Asociación indicador ↔ PDI: filtro por línea y ficha según vigencia (D7)."""

import pandas as pd

from app.domain.asociaciones import asociaciones_ficha, ids_de_linea

V22, V26 = "PDI-2022-2026", "PDI-2026-2030"


def _validas(*filas):
    return pd.DataFrame(filas, columns=["Id", "version_id", "linea_id", "objetivo_id", "meta_id"])


def test_filtro_por_linea_acepta_nombre_o_id_y_todos_es_sin_filtro():
    v = _validas(
        ["1", V22, "calidad", None, None],
        ["2", V22, "expansion", None, None],
        ["3", V26, "L4", None, None],
    )
    assert ids_de_linea(v, V22, "Calidad") == {"1"}
    assert ids_de_linea(v, V22, "expansion") == {"2"}
    assert ids_de_linea(v, V22, "Todos") is None and ids_de_linea(v, V22, None) is None
    assert ids_de_linea(v, V22, "Linea inexistente") == set()
    assert ids_de_linea(v, V26, "Desarrollo Sostenible") == {"3"}


def test_ficha_muestra_ambos_pdi_segun_fecha_de_inicio():
    v = _validas(
        ["7", V22, "calidad", "calidad-O1", None],
        ["7", V26, "L4", "L4-OI", None],
    )
    assert [a["version_id"] for a in asociaciones_ficha(v, "7", 2023, None)] == [V22, V26]
    assert [a["version_id"] for a in asociaciones_ficha(v, "7", 2027, None)] == [V26]
    assert [a["version_id"] for a in asociaciones_ficha(v, "7", 2018, 2024)] == [V22]
    # sin fecha de inicio: se muestran todas las asociaciones que existan
    assert [a["version_id"] for a in asociaciones_ficha(v, "7", None, None)] == [V22, V26]
    a = asociaciones_ficha(v, "7", 2023, None)[0]
    assert a["pdi"] == "PDI 2022-2026" and a["linea"] == "Calidad"
    assert asociaciones_ficha(v, "no-existe", 2023, None) == []
