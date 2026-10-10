"""Seguimiento Operativo: alertas de periodicidad, cumplimiento por corte y correos."""

from datetime import date

import pandas as pd
import pytest

from app.domain.alertas_builders import (
    construir_eml,
    corte_de_apertura,
    cortes_a_notificar,
    fecha_limite,
    indicadores_a_reportar,
    nombre_archivo,
    plazo_de,
    proximo_corte,
    renderizar_mensaje,
)
from app.domain.calendario_co import es_habil, festivos, habil_anterior
from app.domain.seguimiento_builders import (
    build_dashboard,
    build_filtros,
    detectar_vencidos,
)
from app.services.alertas_service import normalizar_emails


def _tracking() -> pd.DataFrame:
    filas = [
        # Id, Indicador, Proceso, Periodicidad, Año, Mes, Estado
        (1, "Ind A", "Calidad", "Mensual", 2026, 5, "Reportado"),
        (1, "Ind A", "Calidad", "Mensual", 2026, 6, "Pendiente"),
        (2, "Ind B", "Calidad", "Semestral", 2025, 12, "Reportado"),
        (2, "Ind B", "Calidad", "Semestral", 2026, 6, "Reportado"),
        (3, "Ind C", "Finanzas", "Trimestral", 2026, 3, "Pendiente"),  # nunca reportado
        (4, "Ind D", "Finanzas", "Anual", 2025, 12, "No aplica"),  # no se exige
        (5, "Ind E", "Finanzas", "Mensual", 2026, 6, "Reportado"),
    ]
    df = pd.DataFrame(
        filas, columns=["Id", "Indicador", "Proceso", "Periodicidad", "Año", "Mes", "Estado"]
    )
    df["Id"] = df["Id"].astype(str)
    df["Año"] = df["Año"].astype("Int64")
    df["Mes"] = df["Mes"].astype("Int64")
    return df


def test_vencidos_sin_reporte_y_no_aplica():
    vencidos, _ = detectar_vencidos(_tracking(), referencia=date(2026, 10, 9))
    ids = set(vencidos["Id"])
    assert "3" in ids  # nunca reportado → vencido
    assert "4" not in ids  # solo "No aplica" → no se exige
    fila = vencidos[vencidos["Id"] == "3"].iloc[0]
    assert pd.isna(fila["diff_meses"]) and fila["ultimo_reporte"] == "Sin reporte"
    # Ind A: último reporte may-2026, mensual, hoy oct → vencido por 5 meses
    assert vencidos[vencidos["Id"] == "1"].iloc[0]["diff_meses"] == 5
    # "Sin reporte" encabeza la lista
    assert vencidos.iloc[0]["Id"] == "3"


def test_alertas_respetan_filtro_de_proceso():
    vencidos, por_vencer = detectar_vencidos(
        _tracking(), referencia=date(2026, 10, 9), proceso="Finanzas"
    )
    assert set(vencidos["Proceso"]) == {"Finanzas"}
    assert set(por_vencer["Proceso"]) <= {"Finanzas"}


def test_por_vencer_semestral_consumio_80pct():
    # Ind B semestral, último reporte jun-2026; en oct-2026 van 4 de 6 meses (≥80 %)
    _, por_vencer = detectar_vencidos(_tracking(), referencia=date(2026, 10, 9))
    assert "2" in set(por_vencer["Id"])


def test_filtros_default_es_el_corte_mas_reciente():
    f = build_filtros(_tracking())
    assert f["anio_default"] == 2026
    assert f["mes_default"] == 6  # no diciembre fijo
    assert f["meses_por_anio"]["2025"] == [12]


def test_dashboard_cumplimiento_y_detalle_curado():
    r = build_dashboard(_tracking(), anio=2026, mes=6, referencia=date(2026, 10, 9))
    assert r["kpis"]["cumplimiento_pct"] == pytest.approx(66.7, abs=0.1)
    # Peor cumplimiento primero
    assert r["cumplimiento_procesos"][0]["proceso"] == "Calidad"
    assert r["cumplimiento_procesos"][0]["pendientes"] == 1
    # Detalle: columnas curadas y pendientes primero
    assert set(r["detalle"][0]) == {"Id", "Indicador", "Proceso", "Periodicidad", "Corte", "Estado"}
    assert r["detalle"][0]["Estado"] == "Pendiente"
    assert r["detalle"][0]["Corte"] == "Jun 2026"
    assert r["alertas"]["referencia"] == "2026-10-09"


def test_calendario_de_cortes():
    # 12-jul: faltan 3 días para el 15-jul → corte jun-2026 a notificar con 5 días de aviso
    assert (2026, 6) in cortes_a_notificar(date(2026, 7, 12), 5, 15)
    assert cortes_a_notificar(date(2026, 7, 1), 5, 15) == []
    assert proximo_corte(date(2026, 10, 9), 15) == (2026, 9)  # límite 15-oct aún no pasó


def test_indicadores_a_reportar_respeta_periodicidad_y_estado():
    df = _tracking()
    jun = indicadores_a_reportar(df, 2026, 6)
    # Mensual pendiente (1) y trimestral sin fila (3, jun es trimestre) deben salir;
    # el semestral ya reportado (2), el reportado mensual (5) y el no-aplica (4) no.
    assert set(jun["Id"]) == {"1", "3"}
    # 1 tiene fila Pendiente en jun; 3 solo tiene fila de marzo → "Por reportar" en jun
    assert dict(zip(jun["Id"], jun["Estado"], strict=True)) == {
        "1": "Pendiente",
        "3": "Por reportar",
    }
    jul = indicadores_a_reportar(df, 2026, 7)
    # Solo los mensuales aplican en julio y aún no hay fila → "Por reportar"
    assert set(jul["Id"]) == {"1", "5"}
    assert set(jul["Estado"]) == {"Por reportar"}


def _ind(**extra) -> pd.DataFrame:
    fila = {"Id": "1", "Indicador": "<b>Ind</b> & co", "Proceso": "P", "Subproceso": "Sub 1",
            "Periodicidad": "Mensual", "Estado": "Pendiente"}
    return pd.DataFrame([fila | extra])


def test_plazos_por_proceso_ignoran_tildes_y_mayusculas():
    esp = {"Planeación Financiera": 25, "GESTIÓN AMBIENTAL": 20, "Tesorería": 25}
    assert plazo_de("PLANEACION FINANCIERA", 15, esp) == 25
    assert plazo_de("Gestión Ambiental", 15, esp) == 20
    assert plazo_de("tesoreria", 15, esp) == 25
    assert plazo_de("Gestión de calidad", 15, esp) == 15  # general


def test_festivos_colombia_2026():
    esperados = {
        (1, 1), (1, 12), (3, 23), (4, 2), (4, 3), (5, 1), (5, 18), (6, 8), (6, 15), (6, 29),
        (7, 13), (7, 20), (8, 7), (8, 17), (10, 12), (11, 2), (11, 16), (12, 8), (12, 25),
    }
    assert {(d.month, d.day) for d in festivos(2026)} == esperados


def test_festivos_colombia_2027_y_2028():
    # Listas publicadas para 2027 y 2028. Incluyen el festivo de la Virgen de Chiquinquirá
    # (Ley 2578 de 2026): 9-jul trasladado al lunes -> 12-jul-2027 y 10-jul-2028.
    esperados_2027 = {
        (1, 1), (1, 11), (3, 22), (3, 25), (3, 26), (5, 1), (5, 10), (5, 31), (6, 7), (7, 5),
        (7, 12), (7, 20), (8, 7), (8, 16), (10, 18), (11, 1), (11, 15), (12, 8), (12, 25),
    }
    esperados_2028 = {
        (1, 1), (1, 10), (3, 20), (4, 13), (4, 14), (5, 1), (5, 29), (6, 19), (6, 26), (7, 3),
        (7, 10), (7, 20), (8, 7), (8, 21), (10, 16), (11, 6), (11, 13), (12, 8), (12, 25),
    }
    assert {(d.month, d.day) for d in festivos(2027)} == esperados_2027
    assert {(d.month, d.day) for d in festivos(2028)} == esperados_2028
    assert fecha_limite(2026, 12, 15) == date(2027, 1, 15)  # viernes hábil
    assert fecha_limite(2027, 6, 20) == date(2027, 7, 19)  # 20-jul festivo -> lunes 19
    assert fecha_limite(2028, 6, 13) == date(2028, 7, 13)  # jueves hábil


def test_fecha_limite_se_corre_al_dia_habil_anterior():
    assert es_habil(date(2026, 7, 15)) and not es_habil(date(2026, 7, 20))  # festivo
    assert habil_anterior(date(2026, 8, 15)) == date(2026, 8, 14)  # sábado -> viernes
    assert habil_anterior(date(2026, 6, 15)) == date(2026, 6, 12)  # festivo lunes -> viernes
    # Corte jun-2026: 30-jun + 15 = 15-jul (miércoles hábil); +20 = 20-jul (festivo) -> 17-jul
    assert fecha_limite(2026, 6, 15) == date(2026, 7, 15)
    assert fecha_limite(2026, 6, 20) == date(2026, 7, 17)
    # Corte jul-2026: 31-jul + 15 = 15-ago (sábado) -> 14-ago
    assert fecha_limite(2026, 7, 15) == date(2026, 8, 14)


def test_aviso_de_apertura_primeros_dias_del_mes():
    assert corte_de_apertura(date(2026, 7, 1), 3) == (2026, 6)
    assert corte_de_apertura(date(2026, 7, 3), 3) == (2026, 6)
    assert corte_de_apertura(date(2026, 7, 4), 3) is None
    assert corte_de_apertura(date(2026, 1, 2), 3) == (2025, 12)  # cruce de año


def test_ventana_de_aviso_depende_del_plazo_del_proceso():
    # Corte jun-2026: límite 15-jul (plazo 15) o 25-jul (plazo 25). Hoy 21-jul, 5 días de aviso.
    hoy = date(2026, 7, 21)
    assert (2026, 6) not in cortes_a_notificar(hoy, 5, 15)  # ya venció
    assert (2026, 6) in cortes_a_notificar(hoy, 5, 25)  # faltan 4 días


def test_subproceso_en_el_consolidado():
    jun = indicadores_a_reportar(_tracking(), 2026, 6, {"1": "Sub A", "3": "Sub C"})
    assert dict(zip(jun["Id"], jun["Subproceso"], strict=True)) == {"1": "Sub A", "3": "Sub C"}


def test_render_mensaje_html_escapa_valores_y_arma_tabla():
    msg = renderizar_mensaje(
        "Corte {corte} {proceso}",
        "<p>Corte al mes de {corte_mes}. Hasta {fecha_limite} ({dias_restantes} d).</p>"
        "{tabla_html}<p>{otro}</p>",
        proceso="Calidad <x>",
        anio=2026,
        mes=6,
        plazo_dias=15,
        hoy=date(2026, 7, 12),
        indicadores=_ind(),
    )
    assert msg.asunto == "Corte Junio 2026 Calidad <x>"
    assert "mes de junio" in msg.html and "15 de julio de 2026" in msg.html and "(3 d)" in msg.html
    # Tabla con los 4 campos pedidos y valores escapados (sin inyección de HTML)
    for etiqueta in ("ID", "Nombre del indicador", "Subproceso", "Frecuencia"):
        assert f">{etiqueta}</th>" in msg.html
    assert "&lt;b&gt;Ind&lt;/b&gt; &amp; co" in msg.html and "Sub 1" in msg.html
    assert "{otro}" in msg.html  # placeholder desconocido intacto
    assert "• [1] <b>Ind</b> & co — Sub 1 (Mensual)" in msg.texto
    assert "<" not in msg.texto.replace("<b>Ind</b>", "")  # el texto plano no lleva etiquetas


def test_render_mensaje_texto_plano_se_convierte_a_html_seguro():
    msg = renderizar_mensaje(
        "A", "Hola {proceso}\n{tabla_indicadores}", proceso="<i>P</i>", anio=2026, mes=6,
        plazo_dias=15, hoy=date(2026, 7, 1), indicadores=_ind(),
    )
    assert "&lt;i&gt;P&lt;/i&gt;" in msg.html and "<br>" in msg.html


def test_eml_es_borrador_sin_enviar():
    from email import message_from_bytes

    msg = renderizar_mensaje(
        "Asunto ñ", "<p>Hola</p>{tabla_html}", proceso="P", anio=2026, mes=6,
        plazo_dias=15, hoy=date(2026, 7, 1), indicadores=_ind(),
    )
    raw = construir_eml(msg, para=["a@x.co", "b@x.co"], cc=["c@x.co"])
    em = message_from_bytes(raw)
    assert em["X-Unsent"] == "1"  # Outlook lo abre como borrador
    assert em["To"] == "a@x.co, b@x.co" and em["Cc"] == "c@x.co"
    assert {p.get_content_type() for p in em.walk()} >= {"text/plain", "text/html"}
    # Sin destinatarios también es válido (se completan en Outlook)
    assert message_from_bytes(construir_eml(msg, para=[]))["To"] is None
    assert nombre_archivo("apertura", 2026, 6, "GESTIÓN AMBIENTAL") == "apertura_2026-06_gestion_ambiental.eml"


def test_normalizar_emails():
    assert normalizar_emails("A@x.co; b@x.co,\n a@x.co") == ["a@x.co", "b@x.co"]
    assert normalizar_emails("") == []
    with pytest.raises(ValueError):
        normalizar_emails("no-es-correo")


@pytest.mark.asyncio
async def test_alertas_config_prohibido_para_procesos(client, auth_as_procesos):
    for method, url in (
        ("get", "/api/v1/seguimiento/alertas/config"),
        ("get", "/api/v1/seguimiento/alertas/historial"),
        ("get", "/api/v1/seguimiento/alertas/notificaciones"),
        ("get", "/api/v1/seguimiento/alertas/borrador?proceso=X"),
        ("post", "/api/v1/seguimiento/alertas/descargar-pendientes"),
    ):
        resp = await getattr(client, method)(url)
        assert resp.status_code == 403, url
    resp = await client.post("/api/v1/seguimiento/alertas/borradores", json={})
    assert resp.status_code == 403


def test_tendencia_matriz_y_periodicidad():
    from app.domain.seguimiento_builders import (
        build_matriz_calor,
        build_por_periodicidad,
        build_tendencia,
    )

    df = _tracking()
    t = build_tendencia(df)
    assert [x["corte"] for x in t] == ["Dic 2025", "Mar 2026", "May 2026", "Jun 2026"]
    jun = t[-1]  # Ind A pendiente, Ind B y E reportados
    assert (jun["reportados"], jun["pendientes"]) == (2, 1) and jun["cumplimiento_pct"] == 66.7
    # Con filtro de proceso la serie cambia
    assert build_tendencia(df, "Finanzas")[-1]["cumplimiento_pct"] == 100.0
    # "No aplica" no cuenta como exigible: Dic-2025 = 1 reportado de 1 exigible
    assert t[0]["cumplimiento_pct"] == 100.0

    m = build_matriz_calor(df, ultimos=2)
    assert [c["corte"] for c in m["cortes"]] == ["May 2026", "Jun 2026"]
    filas = {f["proceso"]: f for f in m["filas"]}
    assert filas["Calidad"]["celdas"][-1] == {"pct": 50.0, "pendientes": 1}
    assert filas["Finanzas"]["celdas"][0] is None  # Finanzas no reporta en mayo
    assert m["filas"][0]["proceso"] == "Calidad"  # peor promedio primero

    per = build_por_periodicidad(df[df["Año"] == 2026])
    assert [p["periodicidad"] for p in per] == ["Mensual", "Trimestral", "Semestral"]


def test_variacion_y_orden_del_detalle():
    base = build_dashboard(_tracking(), anio=2026, mes=6, referencia=date(2026, 10, 9))
    # May-2026: 1 reportado de 1 = 100 %; Jun-2026: 66.7 % → -33.3 pp
    assert base["kpis"]["variacion_pp"] == pytest.approx(-33.3, abs=0.1)
    por_id = build_dashboard(_tracking(), anio=2026, mes=6, orden_por="Id", orden_dir="desc")
    assert [d["Id"] for d in por_id["detalle"]] == ["5", "2", "1"]
    por_estado = build_dashboard(_tracking(), anio=2026, mes=6, orden_por="Estado", orden_dir="desc")
    assert por_estado["detalle"][0]["Estado"] == "Reportado"


def test_borradores_excluyen_indicadores_dados_de_baja_en_el_anio():
    df = _tracking()
    # Id 6: activo en 2025 (mensual) pero sin filas en 2026 → dado de baja, no se le avisa
    baja = pd.DataFrame(
        [("6", "Ind F", "Calidad", "Mensual", 2025, 12, "Reportado")],
        columns=["Id", "Indicador", "Proceso", "Periodicidad", "Año", "Mes", "Estado"],
    ).astype({"Año": "Int64", "Mes": "Int64"})
    junto = pd.concat([df, baja], ignore_index=True)
    assert "6" not in set(indicadores_a_reportar(junto, 2026, 7)["Id"])
    # un corte de un año sin filas usa el último año disponible (2026), no el de las bajas
    assert "6" not in set(indicadores_a_reportar(junto, 2027, 1)["Id"])
    assert {"1", "5"} <= set(indicadores_a_reportar(junto, 2027, 1)["Id"])


def test_listado_outlook_tiene_el_formato_que_lee_auto_correo():
    import io

    from app.domain.alertas_builders import construir_listado_outlook

    df = pd.DataFrame(
        [{"Id": "1", "Indicador": "Ind A", "Proceso": "Calidad", "Subproceso": "Sub", "Periodicidad": "Mensual", "Estado": "Pendiente"}]
    )
    fin = pd.DataFrame(
        [{"Id": "9", "Indicador": "Ind F", "Proceso": "Tesorería", "Subproceso": "", "Periodicidad": "Trimestral", "Estado": "Por reportar"}]
    )
    xl = construir_listado_outlook(
        {"Calidad": df, "Tesorería": fin},
        {"Calidad": ["a@x.co", "b@x.co"]},  # Tesorería sin destinatarios: no genera filas
        {"Calidad": 15, "Tesorería": 25},
        2026,
        9,
    )
    libro = pd.ExcelFile(io.BytesIO(xl))
    assert libro.sheet_names == ["Indicadores", "Destinatarios", "Parametros"]
    ind = libro.parse("Indicadores", dtype=str).fillna("")
    dest = libro.parse("Destinatarios", dtype=str)
    # columnas que exige leer_datos_excel() de Auto_Correo
    assert {"Id", "Indicador", "Proceso", "Periodicidad"} <= set(ind.columns)
    assert {"Proceso", "Correo"} <= set(dest.columns)
    assert dest.to_dict("records") == [{"Proceso": "Calidad", "Correo": "a@x.co"}, {"Proceso": "Calidad", "Correo": "b@x.co"}]
    fechas = dict(zip(ind["Proceso"], ind["FechaMaxima"], strict=True))
    assert fechas["Calidad"] == "15 de octubre de 2026"  # jueves hábil
    assert fechas["Tesorería"] == "23 de octubre de 2026"  # 25-oct es domingo → viernes 23
    params = dict(libro.parse("Parametros", dtype=str).values.tolist())
    assert params["CORTE_TEXTO"] == "30 de septiembre de 2026" and params["CORTE_ASUNTO"] == "Corte septiembre 2026"
