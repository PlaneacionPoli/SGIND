import pandas as pd

from app.domain.calculos import (
    calcular_kpis,
    enriquecer_dataframe,
    normalizar_cumplimiento,
    obtener_ultimo_registro,
)
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
    assert categorizar_cumplimiento(1.0199, id_indicador="561") == "Cumplimiento"


def test_categorizar_negativo_pct_alerta():
    assert categorizar_cumplimiento(1.05, id_indicador="561") == "Alerta"
    assert categorizar_cumplimiento(1.10, id_indicador="561") == "Alerta"


def test_categorizar_negativo_pct_peligro():
    assert categorizar_cumplimiento(1.1001, id_indicador="561") == "Peligro"


def test_categorizar_presupuesto_semaforo_normal_sobre_valor_topado():
    for id_ in ("377", "207", "121", "Med 12"):
        assert categorizar_cumplimiento(1.00, id_indicador=id_) == "Cumplimiento"
        assert categorizar_cumplimiento(1.25, id_indicador=id_) == "Cumplimiento"
        assert categorizar_cumplimiento(0.90, id_indicador=id_) == "Alerta"
        assert categorizar_cumplimiento(0.79, id_indicador=id_) == "Peligro"


def test_semaforo_sobreejecucion_presupuesto():
    from app.domain.categorization import categorizar_sobreejecucion

    assert categorizar_sobreejecucion(1.10, "377") == "Normal"
    assert categorizar_sobreejecucion(1.1001, "207") == "Alerta"
    assert categorizar_sobreejecucion(0.70, "121") == "Normal"
    assert categorizar_sobreejecucion(1.50, "203") is None  # no es presupuesto
    assert categorizar_sobreejecucion(None, "377") is None


def test_ensure_nivel_presupuesto_dos_semaforos_y_tope_100():
    from app.domain.resumen_builders import ensure_nivel_cumplimiento

    df = pd.DataFrame({"Id": ["377", "377", "203"], "cumplimiento_pct": [125.0, 105.0, 125.0]})
    out = ensure_nivel_cumplimiento(ensure_nivel_cumplimiento(df))  # idempotente
    assert out["cumplimiento_pct"].tolist() == [100.0, 100.0, 125.0]
    assert out["Nivel de cumplimiento"].tolist() == [
        "Cumplimiento",
        "Cumplimiento",
        "Sobrecumplimiento",
    ]
    sobre = out["Nivel sobreejecucion"].tolist()
    assert sobre[:2] == ["Alerta", "Normal"] and pd.isna(sobre[2])


def test_categorizar_negativo_pct_no_aplica_fuera_de_lista():
    assert categorizar_cumplimiento(1.10, id_indicador="104") == "Sobrecumplimiento"


def test_calcular_kpis():
    df = pd.DataFrame(
        {
            "Id": ["1", "2", "3"],
            "Cumplimiento_norm": [0.70, 0.90, 1.02],
            "Categoria": ["Peligro", "Alerta", "Cumplimiento"],
        }
    )
    total, conteos = calcular_kpis(df)
    assert total == 3
    assert conteos["Peligro"]["n"] == 1
    assert conteos["Alerta"]["n"] == 1


def test_obtener_ultimo_registro():
    df = pd.DataFrame(
        {
            "Id": ["1", "1"],
            "Fecha": ["2025-01-01", "2025-06-01"],
            "Cumplimiento_norm": [0.8, 0.9],
            "Categoria": ["Alerta", "Cumplimiento"],
        }
    )
    ultimo = obtener_ultimo_registro(df)
    assert len(ultimo) == 1
    assert ultimo.iloc[0]["Cumplimiento_norm"] == 0.9


def test_enriquecer_dataframe():
    df = pd.DataFrame(
        {
            "Id": ["373", "100"],
            "Cumplimiento": [0.96, 0.70],
        }
    )
    out = enriquecer_dataframe(df)
    assert "Categoria" in out.columns
    assert out.loc[out["Id"] == "373", "Categoria"].iloc[0] == "Cumplimiento"
    assert out.loc[out["Id"] == "100", "Categoria"].iloc[0] == "Peligro"


def test_build_proyectos_gantt_span():
    from app.domain.resumen_builders import build_proyectos_gantt

    df = pd.DataFrame(
        {
            "Id": ["1", "1", "2", "2"],
            "Indicador": ["Proyecto A", "Proyecto A", "Proyecto B", "Proyecto B"],
            "Linea": ["Calidad", "Calidad", "Experiencia", "Experiencia"],
            "Anio": [2022, 2024, 2023, 2025],
            "cumplimiento_pct": [50.0, 100.0, 0.0, 80.0],
        }
    )
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
    assert "n_retos" not in calidad  # los planes de Retos no se suman por línea


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
        area_count=84,
        anio=2025,
    )
    assert "2025" in narrativa["texto"]
    assert "53" in narrativa["texto"]
    assert "42" in narrativa["texto"]
    assert "84" in narrativa["texto"]
    assert "Expansión" in narrativa["texto"] or "Expansion" in narrativa["texto"]
    assert narrativa["health_rate"] > 0
    assert "<strong>" in narrativa["texto"]


def test_metrica_sin_porcentaje_no_es_pendiente_de_reporte():
    import pandas as pd

    from app.domain.resumen_builders import NIVEL_METRICA, ensure_nivel_cumplimiento

    df = pd.DataFrame(
        {
            "Id": ["325", "999", "10"],
            "Indicador": [
                "Número de programas nuevos con registro calificado aprobado - Metrica",
                "Indicador común sin dato",
                "Indicador con dato",
            ],
            "cumplimiento_pct": [float("nan"), float("nan"), 105.0],
        }
    )
    out = ensure_nivel_cumplimiento(df)
    assert out.loc[0, "Nivel de cumplimiento"] == NIVEL_METRICA
    assert out.loc[1, "Nivel de cumplimiento"] == "Pendiente de reporte"
    assert out.loc[2, "Nivel de cumplimiento"] == "Sobrecumplimiento"


def test_filtro_por_linea_del_pdi_en_procesos():
    import pandas as pd

    from app.domain.procesos_builders import apply_ui_filters

    df = pd.DataFrame({"Id": ["1", "2", "3"], "Proceso": ["A", "A", "B"]})
    assert list(apply_ui_filters(df, ids_linea={"1", "3"})["Id"]) == ["1", "3"]
    assert apply_ui_filters(df, ids_linea=set()).empty  # línea sin indicadores
    assert len(apply_ui_filters(df, ids_linea=None)) == 3  # sin filtro por línea
    assert list(apply_ui_filters(df, proceso="A", ids_linea={"1", "3"})["Id"]) == ["1"]


def test_lectura_de_excel_bloqueado_usa_una_copia(tmp_path, monkeypatch):
    """Si Excel/OneDrive bloquea el archivo (PermissionError), se lee desde una copia temporal."""
    import pandas as pd

    from app.core.config import Settings
    from app.services.excel_reader import ExcelReaderService

    pd.DataFrame({"Id": [1, 2]}).to_excel(tmp_path / "bloqueado.xlsx", index=False)
    svc = ExcelReaderService(Settings(sgind_data_path=str(tmp_path)))
    original = pd.read_excel
    llamadas: list[str] = []

    def lectura(io, *args, **kwargs):
        llamadas.append(str(io))
        if len(llamadas) == 1:
            raise PermissionError(13, "Permission denied")
        return original(io, *args, **kwargs)

    monkeypatch.setattr(pd, "read_excel", lectura)
    df = svc.read_excel("bloqueado.xlsx", sheet_name=0, use_cache=False)
    assert list(df["Id"]) == [1, 2]
    assert (
        len(llamadas) == 2 and llamadas[0] != llamadas[1]
    )  # el segundo intento fue sobre la copia


def test_ejecucion_variacion_ordena_por_cumplimiento_pp_y_trae_unidad():
    from app.domain.procesos_builders import build_ejecucion_variacion

    cur = pd.DataFrame(
        {
            "Id": ["1", "2", "3", "4"],
            "Indicador": ["Pesos", "Porcentaje", "Conteo", "Menor es mejor"],
            "Ejecucion": [200_000_000_000.0, 55.0, 150.0, 20.0],
            "cumplimiento_pct": [105.0, 92.0, 100.0, 110.0],
            "Mes": ["Junio"] * 4,
            "Anio": [2026] * 4,
            "Meta_Signo": ["$", "%", "ENT", "DEC"],
            "Decimales_Meta": [0, 1, 0, 0],
        }
    )
    prev = pd.DataFrame(
        {
            "Id": ["1", "2", "3", "4"],
            "Ejecucion": [190_000_000_000.0, 50.0, 100.0, 30.0],
            "cumplimiento_pct": [100.0, 80.0, 90.0, 85.0],
            "Mes": [5] * 4,
            "Anio": [2026] * 4,
        }
    )
    out = build_ejecucion_variacion(cur, prev)
    # Se ordena por la mejora del % de cumplimiento (pp), no por la diferencia absoluta; el
    # indicador "menor es mejor" bajó su ejecución (-10) pero MEJORÓ su cumplimiento (+25 pp).
    assert [r["indicador"] for r in out["positiva"]] == [
        "Menor es mejor",
        "Porcentaje",
        "Conteo",
        "Pesos",
    ]
    assert out["positiva"][1]["signo"] == "%" and out["positiva"][1]["delta_cumpl_pp"] == 12.0
    assert out["positiva"][0]["delta"] == -10.0
    assert out["positiva"][0]["periodo_previo"] == "Mayo 2026"
    assert out["negativa"] == []
