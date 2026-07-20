import pandas as pd

from app.domain.calculos import calcular_kpis, enriquecer_dataframe, normalizar_cumplimiento, obtener_ultimo_registro
from app.domain.categorization import categorizar_cumplimiento


def test_normalizar_cumplimiento_decimal():
    assert normalizar_cumplimiento(0.95) == 0.95


def test_normalizar_cumplimiento_porcentaje_string():
    assert normalizar_cumplimiento("0,95") == 0.95


def test_categorizar_regular_cumplimiento():
    assert categorizar_cumplimiento(1.0, id_indicador="100") == "Cumplimiento"


def test_categorizar_plan_anual():
    assert categorizar_cumplimiento(0.96, id_indicador="373") == "Cumplimiento"
    assert categorizar_cumplimiento(0.90, id_indicador="373") == "Alerta"


def test_categorizar_negativo_pct_cumplimiento():
    assert categorizar_cumplimiento(1.0199, id_indicador="121") == "Cumplimiento"


def test_categorizar_negativo_pct_alerta():
    assert categorizar_cumplimiento(1.05, id_indicador="207") == "Alerta"
    assert categorizar_cumplimiento(1.10, id_indicador="207") == "Alerta"


def test_categorizar_negativo_pct_peligro():
    assert categorizar_cumplimiento(1.1001, id_indicador="377") == "Peligro"


def test_categorizar_negativo_pct_no_aplica_fuera_de_lista():
    assert categorizar_cumplimiento(1.10, id_indicador="104") == "Sobrecumplimiento"


def test_calcular_kpis():
    df = pd.DataFrame({
        "Id": ["1", "2", "3"],
        "Cumplimiento_norm": [0.70, 0.90, 1.02],
        "Categoria": ["Peligro", "Alerta", "Cumplimiento"],
    })
    total, conteos = calcular_kpis(df)
    assert total == 3
    assert conteos["Peligro"]["n"] == 1
    assert conteos["Alerta"]["n"] == 1


def test_obtener_ultimo_registro():
    df = pd.DataFrame({
        "Id": ["1", "1"],
        "Fecha": ["2025-01-01", "2025-06-01"],
        "Cumplimiento_norm": [0.8, 0.9],
        "Categoria": ["Alerta", "Cumplimiento"],
    })
    ultimo = obtener_ultimo_registro(df)
    assert len(ultimo) == 1
    assert ultimo.iloc[0]["Cumplimiento_norm"] == 0.9


def test_enriquecer_dataframe():
    df = pd.DataFrame({
        "Id": ["373", "100"],
        "Cumplimiento": [0.96, 0.70],
    })
    out = enriquecer_dataframe(df)
    assert "Categoria" in out.columns
    assert out.loc[out["Id"] == "373", "Categoria"].iloc[0] == "Cumplimiento"
    assert out.loc[out["Id"] == "100", "Categoria"].iloc[0] == "Peligro"


def test_build_proyectos_gantt_span():
    from app.domain.resumen_builders import build_proyectos_gantt

    df = pd.DataFrame({
        "Id": ["1", "1", "2", "2"],
        "Indicador": ["Proyecto A", "Proyecto A", "Proyecto B", "Proyecto B"],
        "Linea": ["Calidad", "Calidad", "Experiencia", "Experiencia"],
        "Anio": [2022, 2024, 2023, 2025],
        "cumplimiento_pct": [50.0, 100.0, 0.0, 80.0],
    })
    gantt = build_proyectos_gantt(df, anio_min=2022, anio_max=2026)
    assert gantt["anio_min"] == 2022
    assert len(gantt["items"]) == 2

    proy_a = next(item for item in gantt["items"] if item["id"] == "1")
    assert proy_a["anio_inicio"] == 2022
    assert proy_a["anio_fin"] == 2024
    assert proy_a["duracion_anios"] == 3
    assert proy_a["anios_activos"] == [2022, 2024]
    assert proy_a["cumplimiento"] == 100.0
    assert proy_a["estado"] == "Cerrado"


def test_retos_category_umbral_95():
    from app.domain.resumen_builders import _retos_category

    assert _retos_category(99.9) == "Cumplimiento"
    assert _retos_category(95.0) == "Cumplimiento"
    assert _retos_category(94.9) == "Alerta"
    assert _retos_category(79.9) == "Peligro"
    assert _retos_category(105.0) == "Sobrecumplimiento"


def test_build_strategy_cards_consolidado_desglose():
    from app.domain.resumen_builders import build_strategy_cards

    linea_summary = pd.DataFrame(
        [
            {
                "Linea": "Calidad",
                "N_Indicadores": 9,
                "N_Proyectos": 13,
                "N_Retos": 63,
                "N_Total": 85,
                "Cumpl_Promedio": 102.9,
            }
        ]
    )
    cards = build_strategy_cards(linea_summary, None, vista="consolidado")
    calidad = next(c for c in cards if c["linea"] == "Calidad")
    assert calidad["n_indicadores"] == 9
    assert calidad["n_proyectos"] == 13
    assert calidad["n_retos"] == 63


def test_generate_narrative_consolidado_dinamica():
    from app.domain.resumen_builders import generate_narrative_consolidado

    linea_summary = pd.DataFrame(
        [
            {
                "Linea": "Calidad",
                "Cumpl_Promedio": 102.9,
                "N_Indicadores": 9,
                "N_Proyectos": 13,
                "N_Retos": 63,
            },
            {
                "Linea": "Expansion",
                "Cumpl_Promedio": 104.3,
                "N_Indicadores": 11,
                "N_Proyectos": 2,
                "N_Retos": 25,
            },
        ]
    )
    narrativa = generate_narrative_consolidado(
        linea_summary,
        ind_count=53,
        proy_count=42,
        retos_count=285,
        anio=2025,
    )
    assert "2025" in narrativa["texto"]
    assert "53" in narrativa["texto"]
    assert "42" in narrativa["texto"]
    assert "285" in narrativa["texto"]
    assert "Expansión" in narrativa["texto"] or "Expansion" in narrativa["texto"]
    assert narrativa["health_rate"] > 0
    assert "<strong>" in narrativa["texto"]
