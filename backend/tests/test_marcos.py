"""Registro de marcos versionados (PDI/CNA) — impact_report.md §4.1."""

import pytest

from app.domain.marcos import (
    get_marco,
    get_marcos,
    marco_activo,
    marcos_traslapados,
    parse_marcos,
)


def _raw(**overrides):
    base = {
        "tipo": "PDI",
        "version_id": "PDI-X",
        "anio_datos_desde": 2022,
        "anio_datos_hasta": 2025,
        "estado": "cerrado",
    }
    base.update(overrides)
    return base


# ── Registro real (app/data/marcos.toml) ─────────────────────────────

def test_registro_tiene_ambos_pdi():
    ids = [m.version_id for m in get_marcos("PDI")]
    assert ids == ["PDI-2022-2026", "PDI-2026-2030"]


def test_pdi_activo_es_2026_2030():
    assert marco_activo("PDI").version_id == "PDI-2026-2030"


def test_pdi_2022_2026_cierra_con_datos_hasta_2025():
    # D3: 2026 pertenece solo al PDI 2026-2030
    m = get_marco("PDI-2022-2026")
    assert m.anios == [2022, 2023, 2024, 2025]
    assert not m.incluye_anio(2026)
    assert get_marco("PDI-2026-2030").incluye_anio(2026)


def test_cada_anio_pertenece_a_un_solo_pdi():
    for anio in range(2022, 2031):
        assert len([m for m in get_marcos("PDI") if m.incluye_anio(anio)]) == 1


def test_solo_pdi_2022_2026_tiene_datos_por_ahora():
    # El 2026-2030 queda bloqueado hasta cargar taxonomía y filtrar el backend
    assert get_marco("PDI-2022-2026").datos_disponibles
    assert not get_marco("PDI-2026-2030").datos_disponibles


def test_get_marco_desconocido():
    with pytest.raises(KeyError):
        get_marco("PDI-1900-1904")


# ── Regla de la ficha (D7): traslape por fecha de inicio ─────────────

def test_indicador_iniciado_2023_aplica_a_ambos_pdi():
    ids = [m.version_id for m in marcos_traslapados("PDI", 2023)]
    assert ids == ["PDI-2022-2026", "PDI-2026-2030"]


def test_indicador_iniciado_2027_solo_pdi_2026_2030():
    ids = [m.version_id for m in marcos_traslapados("PDI", 2027)]
    assert ids == ["PDI-2026-2030"]


def test_indicador_finalizado_2024_solo_pdi_2022_2026():
    ids = [m.version_id for m in marcos_traslapados("PDI", 2020, 2024)]
    assert ids == ["PDI-2022-2026"]


# ── Validaciones de parse_marcos ─────────────────────────────────────

def test_rechaza_dos_activos_del_mismo_tipo():
    with pytest.raises(ValueError, match="activo"):
        parse_marcos({"marco": [
            _raw(version_id="A", estado="activo"),
            _raw(version_id="B", estado="activo"),
        ]})


def test_rechaza_version_duplicada():
    with pytest.raises(ValueError, match="duplicado"):
        parse_marcos({"marco": [_raw(), _raw()]})


def test_rechaza_rango_invertido():
    with pytest.raises(ValueError):
        parse_marcos({"marco": [_raw(anio_datos_desde=2026, anio_datos_hasta=2022)]})


def test_rechaza_tipo_invalido():
    with pytest.raises(ValueError, match="tipo"):
        parse_marcos({"marco": [_raw(tipo="ISO")]})


def test_marco_sin_fin_incluye_anios_futuros():
    (m,) = parse_marcos({"marco": [_raw(tipo="CNA", anio_datos_desde=2027, anio_datos_hasta=None)]})
    assert m.incluye_anio(2040)
    assert not m.incluye_anio(2026)


# ── Endpoint ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_endpoint_lista_pdi(client, auth_as_procesos):
    r = await client.get("/api/v1/marcos", params={"tipo": "PDI"})
    assert r.status_code == 200
    body = r.json()
    assert [m["version_id"] for m in body] == ["PDI-2022-2026", "PDI-2026-2030"]
    assert {m["estado"] for m in body} == {"activo", "cerrado"}


@pytest.mark.asyncio
async def test_endpoint_tipo_invalido(client, auth_as_procesos):
    r = await client.get("/api/v1/marcos", params={"tipo": "ISO"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_endpoint_detalle_y_404(client, auth_as_procesos):
    r = await client.get("/api/v1/marcos/PDI-2022-2026")
    assert r.status_code == 200
    assert r.json()["anio_datos_hasta"] == 2025
    r = await client.get("/api/v1/marcos/NO-EXISTE")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_endpoint_requiere_auth(client):
    r = await client.get("/api/v1/marcos")
    assert r.status_code in (401, 403)


# ── Aislamiento del PDI en la API y en las cachés ────────────────────

def test_marco_por_defecto_es_el_vigente_con_datos():
    from app.domain.marcos import marco_por_defecto
    # Hoy solo el 2022-2026 tiene datos; el 2026-2030 está bloqueado.
    assert marco_por_defecto("PDI").version_id == "PDI-2022-2026"


def test_anios_del_marco_2022_igualan_la_constante_historica():
    # Guard de regresión: el registro debe reproducir el rango que antes
    # estaba hardcodeado en resumen_service.ANIOS_RANGO.
    from app.services.resumen_service import ANIOS_RANGO
    assert get_marco("PDI-2022-2026").anios == ANIOS_RANGO


def test_etiqueta_de_cierre_conserva_el_texto_historico():
    assert get_marco("PDI-2022-2026").etiqueta_cierre == "Cierre PDI 2022-2025"
    assert get_marco("PDI-2026-2030").etiqueta_cierre == "Cierre PDI 2026-2030"


@pytest.mark.asyncio
async def test_pdi_sin_datos_responde_409_en_dashboard_y_cmi(client, auth_as_procesos):
    for url in (
        "/api/v1/dashboard/resumen-completo?anio=2026",
        "/api/v1/cmi/estrategico-dashboard",
        "/api/v1/cmi/procesos/filtros",
        "/api/v1/reports/informe-ejecutivo",
    ):
        r = await client.get(url, params={"pdi": "PDI-2026-2030"})
        assert r.status_code == 409, url
        assert "no está cargada" in r.json()["detail"]


@pytest.mark.asyncio
async def test_pdi_inexistente_404_y_tipo_incorrecto_422(client, auth_as_procesos):
    r = await client.get("/api/v1/cmi/filtros", params={"pdi": "PDI-1900-1904"})
    assert r.status_code == 404
    r = await client.get("/api/v1/cmi/filtros", params={"pdi": "CNA-ACTUAL"})
    assert r.status_code == 422


def test_cache_de_resumen_se_separa_por_pdi(monkeypatch):
    """Dos PDI con el mismo anio/vista/rango no comparten entrada de caché."""
    from app.domain import marcos as m
    from app.services import resumen_service as rs

    marcos = parse_marcos({"marco": [
        _raw(version_id="PDI-A", anio_datos_desde=2022, anio_datos_hasta=2025, datos_disponibles=True),
        _raw(version_id="PDI-B", anio_datos_desde=2026, anio_datos_hasta=2030, datos_disponibles=True),
    ]})
    monkeypatch.setattr(m, "load_marcos", lambda *a, **k: tuple(marcos))
    monkeypatch.setattr(rs, "get_marco", m.get_marco)

    llamadas: list[str] = []

    class Fake(rs.ResumenService):
        def __init__(self):  # sin Excel
            self._excel = type("E", (), {"ttl": 60})()

        def _get_resumen_completo_uncached(self, *, anio, vista, rango, marco):
            llamadas.append(marco.version_id)
            return {"pdi": marco.version_id}

    rs._RESUMEN_COMPLETO_CACHE.clear()
    svc = Fake()
    assert svc.get_resumen_completo(anio=2026, vista="indicadores", rango=True, pdi="PDI-A") == {"pdi": "PDI-A"}
    assert svc.get_resumen_completo(anio=2026, vista="indicadores", rango=True, pdi="PDI-B") == {"pdi": "PDI-B"}
    assert svc.get_resumen_completo(anio=2026, vista="indicadores", rango=True, pdi="PDI-A") == {"pdi": "PDI-A"}
    assert llamadas == ["PDI-A", "PDI-B"]  # la 3.ª llamada salió de caché
    rs._RESUMEN_COMPLETO_CACHE.clear()
