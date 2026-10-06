"""Taxonomía por versión y validación de las hojas de PDI (columna PDI 1/0) — impact_report.md §4.1."""

from pathlib import Path

import pandas as pd
import pytest

from app.domain.marcos import get_marcos
from app.domain.resumen_builders import CANONICAL_OBJETIVOS, norm_key
from app.domain.taxonomia import (
    load_taxonomia,
    parse_flag01,
    parse_taxonomia,
    resolver_asociaciones,
)

V22 = "PDI-2022-2026"
V26 = "PDI-2026-2030"
OBJ_1 = "Consolidar el Modelo Educativo Intergeneracional, Innovador y Multimodal"
META_1 = "Diseñar e implementar el Modelo"


def _df(*filas):
    return pd.DataFrame(filas, columns=["Id", "version_id", "PDI", "Linea", "Objetivo", "Meta"])


# ── Taxonomías ───────────────────────────────────────────────────────

def test_conteos_pdi_2026_2030_segun_skill():
    t = load_taxonomia(V26)
    assert [ln.nombre for ln in t.lineas] == [
        "Calidad e Innovación Educativa",
        "Experiencia Centrada en las Personas",
        "Expansión con Compromiso Social",
        "Desarrollo Sostenible",
    ]
    assert sum(len(ln.objetivos) for ln in t.lineas) == 10
    assert len(list(t.iter_metas())) == 22


def test_taxonomia_2022_2026_coincide_con_constantes_canonicas():
    t = load_taxonomia(V22)
    assert sum(len(ln.objetivos) for ln in t.lineas) == 11
    for linea in t.lineas:
        canon = CANONICAL_OBJETIVOS[norm_key(linea.nombre)]
        assert [norm_key(o.nombre) for o in linea.objetivos] == [norm_key(c) for c in canon]


def test_todo_marco_con_taxonomia_la_tiene_cargable():
    for m in get_marcos("PDI"):
        assert m.taxonomia
        assert load_taxonomia(m.taxonomia).version_id == m.version_id
        assert m.hoja_asociacion == m.version_id.replace("-", "_")


def test_ids_duplicados_rechazados():
    base = {"id": "x", "numero": 1, "nombre": "n", "metas": []}
    with pytest.raises(ValueError, match="duplicados"):
        parse_taxonomia({"version_id": "V", "lineas": [{"id": "x", "nombre": "L", "objetivos": [base]}]})


# ── Cruce por nombre ─────────────────────────────────────────────────

def test_asociacion_valida_resuelve_ids_ignorando_tildes_y_espacios():
    r = resolver_asociaciones(_df(["10", V26, 1, "calidad e innovacion educativa", OBJ_1 + " ", META_1]))
    assert r.errores == []
    assert r.validas.iloc[0].to_dict() == {
        "Id": "10", "version_id": V26,
        "linea_id": "calidad-e-innovacion-educativa",
        "objetivo_id": "calidad-e-innovacion-educativa-O1",
        "meta_id": "calidad-e-innovacion-educativa-O1-M1",
    }


def test_fila_sin_asociar_se_omite_sin_error():
    r = resolver_asociaciones(_df(["10", V26, 1, None, None, None]))
    assert r.errores == [] and r.validas.empty


def test_objetivo_de_otra_linea_y_meta_de_otro_objetivo_son_error():
    r = resolver_asociaciones(_df(
        ["1", V26, 1, "Desarrollo Sostenible", OBJ_1, None],
        ["2", V26, 1, "Desarrollo Sostenible",
         "Garantizar una gestión sostenible que impacte positivamente en la comunidad y el ambiente",
         "Consolidar el ADN Poli como pilar de la experiencia institucional"],
    ))
    assert r.validas.empty
    assert "no pertenece a la línea" in r.errores[0]["motivo"] and r.errores[0]["fila"] == 2
    assert "Meta no pertenece" in r.errores[1]["motivo"]


def test_meta_tolerante_conserva_el_objetivo_en_un_pdi_cerrado():
    df = _df(["9", V22, 1, "Calidad", "Asegurar la alta calidad a nivel institucional", "Al 2025 alcanzar la acreditacion"])
    r = resolver_asociaciones(df, V22, meta_tolerante=True)
    assert len(r.validas) == 1 and r.validas.iloc[0]["meta_id"] is None
    assert len(r.advertencias) == 1 and r.errores == []
    assert len(resolver_asociaciones(df, V22).errores) == 1  # estricto: error


def test_regla_meta_pdi_1_exige_meta_y_0_no_puede_tenerla():
    ln = "Calidad e Innovación Educativa"
    r = resolver_asociaciones(_df(
        ["1", V26, 1, ln, OBJ_1, META_1],     # ok: estratégico con meta
        ["2", V26, 1, ln, OBJ_1, None],       # estratégico sin meta
        ["3", V26, 0, ln, OBJ_1, None],       # proceso sin meta: ok
        ["4", V26, 0, ln, OBJ_1, META_1],     # proceso con meta
        ["5", V26, None, ln, OBJ_1, None],    # sin marcador
    ))
    assert len(r.validas) == 5  # incumplir la regla no descarta la fila
    assert [i["Id"] for i in r.incumplimientos] == ["2", "4", "5"]


def test_duplicados_version_sin_taxonomia_y_filtro_por_version():
    r = resolver_asociaciones(_df(
        ["1", "PDI-1999", 1, "X", None, None],
        ["11", V26, 1, "Desarrollo Sostenible", None, None],
        ["11", V26, 1, "Desarrollo Sostenible", None, None],
    ))
    motivos = [e["motivo"] for e in r.errores]
    assert any("sin taxonomía" in m for m in motivos) and "asociación repetida" in motivos
    r = resolver_asociaciones(_df(
        ["10", V26, 1, "Desarrollo Sostenible", None, None],
        ["10", V22, 1, "Calidad", None, None],
    ), version_id=V22)
    assert list(r.validas["version_id"]) == [V22]


def test_columnas_faltantes():
    with pytest.raises(ValueError, match="faltan columnas"):
        resolver_asociaciones(pd.DataFrame({"Id": [1]}))


def test_parse_flag01():
    assert [parse_flag01(v) for v in (1, 0, "1", "0", 1.0, True, "1.0")] == [1, 0, 1, 0, 1, 1, 1]
    assert [parse_flag01(v) for v in (None, "", "Sí", 2, float("nan"))] == [None] * 5


# ── Endpoint ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_endpoint_taxonomia(client, auth_as_procesos):
    r = await client.get(f"/api/v1/marcos/{V26}/taxonomia")
    assert r.status_code == 200
    body = r.json()
    assert len(body["lineas"]) == 4
    assert sum(len(o["metas"]) for ln in body["lineas"] for o in ln["objetivos"]) == 22
    assert (await client.get("/api/v1/marcos/NO-EXISTE/taxonomia")).status_code == 404
    assert (await client.get("/api/v1/marcos/CNA-ACTUAL/taxonomia")).status_code == 404


# ── Catálogo real ────────────────────────────────────────────────────

@pytest.mark.parametrize("version", [V22, V26])
def test_catalogo_real_hoja_del_pdi_sin_errores_de_asociacion(version):
    """Planeación asocia a mano (hojas PDI_* de data/raw/Catalogo de Indicadores.xlsx).
    Una línea/objetivo/meta fuera de la taxonomía o repetida debe fallar aquí."""
    path = Path(__file__).resolve().parents[2] / "data" / "raw" / "Catalogo de Indicadores.xlsx"
    if not path.exists():
        pytest.skip("catálogo no disponible en este entorno")
    marco = next(m for m in get_marcos("PDI") if m.version_id == version)
    try:
        df = pd.read_excel(path, sheet_name=marco.hoja_asociacion)
    except ValueError:
        pytest.skip(f"hoja {marco.hoja_asociacion} aún no existe")
    df["version_id"] = version
    r = resolver_asociaciones(df, meta_tolerante=marco.estado == "cerrado")
    assert r.errores == [], r.errores[:5]
