"""Lógica pura de las alertas por correo de Seguimiento Operativo.

Un "corte" es un (año, mes) de cierre de periodo. Cada indicador reporta en los
meses que le corresponden por su periodicidad y tiene hasta `plazo_dias` días
calendario después del último día de ese mes para reportar; si esa fecha no es día
hábil se corre al día hábil anterior (fecha límite).
"""

from __future__ import annotations

import calendar
import html
import re
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from app.domain.calendario_co import habil_anterior
from app.domain.loader_utils import ascii_lower
from app.domain.seguimiento_builders import MESES_NOMBRES, _nm

# Meses de cierre en que reporta cada periodicidad (periodicidad desconocida = mensual).
_MESES_REPORTE: dict[str, frozenset[int]] = {
    "mensual": frozenset(range(1, 13)),
    "bimestral": frozenset(range(2, 13, 2)),
    "trimestral": frozenset({3, 6, 9, 12}),
    "semestral": frozenset({6, 12}),
    "anual": frozenset({12}),
}

PLACEHOLDERS: dict[str, str] = {
    "proceso": "Nombre del proceso destinatario",
    "corte": "Corte a reportar, ej. «Junio 2026»",
    "corte_mes": "Mes del corte en minúscula, ej. «junio»",
    "anio": "Año del corte",
    "fecha_limite": "Fecha máxima de reporte del proceso, ej. «15 de julio de 2026»",
    "dias_restantes": "Días que faltan para la fecha límite",
    "total": "Cantidad de indicadores a reportar",
    "tabla_html": "Tabla con ID, nombre del indicador, subproceso y frecuencia",
}


def plazo_de(proceso: str, general: int, especificos: dict[str, int]) -> int:
    """Plazo del proceso (sin distinguir mayúsculas ni tildes) o el general."""
    clave = ascii_lower(proceso).strip()
    for nombre, dias in especificos.items():
        if ascii_lower(nombre).strip() == clave:
            return dias
    return general


def corte_anterior(hoy: date) -> tuple[int, int]:
    """Corte del mes recién cerrado."""
    return (hoy.year - 1, 12) if hoy.month == 1 else (hoy.year, hoy.month - 1)


def corte_de_apertura(hoy: date, dias_apertura: int) -> tuple[int, int] | None:
    """Corte que se abre hoy (el mes recién cerrado), si hoy está en los primeros días del mes."""
    return corte_anterior(hoy) if 1 <= hoy.day <= dias_apertura else None


def meses_de_reporte(periodicidad: str) -> frozenset[int]:
    return _MESES_REPORTE.get(_nm(periodicidad), _MESES_REPORTE["mensual"])


def fecha_limite(anio: int, mes: int, plazo_dias: int) -> date:
    """Último día del mes del corte + plazo, corrido al día hábil anterior.

    Si cae en fin de semana o festivo se adelanta (nunca se da más plazo del anunciado).
    """
    return habil_anterior(date(anio, mes, calendar.monthrange(anio, mes)[1]) + timedelta(days=plazo_dias))


def nombre_corte(anio: int, mes: int) -> str:
    return f"{MESES_NOMBRES[mes - 1]} {anio}"


def fecha_larga(d: date) -> str:
    return f"{d.day} de {MESES_NOMBRES[d.month - 1].lower()} de {d.year}"


def cortes_a_notificar(hoy: date, dias_antes: int, plazo_dias: int) -> list[tuple[int, int]]:
    """Cortes cuya fecha límite cae entre hoy y `dias_antes` días hacia adelante."""
    out: list[tuple[int, int]] = []
    for delta in range(-4, 3):  # meses alrededor de hoy; cubre plazos de hasta ~120 días
        total = hoy.year * 12 + (hoy.month - 1) + delta
        anio, mes0 = divmod(total, 12)
        mes = mes0 + 1
        restantes = (fecha_limite(anio, mes, plazo_dias) - hoy).days
        if 0 <= restantes <= dias_antes:
            out.append((anio, mes))
    return out


def proximo_corte(hoy: date, plazo_dias: int) -> tuple[int, int]:
    """Primer corte cuya fecha límite aún no ha pasado."""
    for delta in range(-4, 14):
        total = hoy.year * 12 + (hoy.month - 1) + delta
        anio, mes0 = divmod(total, 12)
        if fecha_limite(anio, mes0 + 1, plazo_dias) >= hoy:
            return anio, mes0 + 1
    return hoy.year, hoy.month


def indicadores_a_reportar(
    df: pd.DataFrame, anio: int, mes: int, subprocesos: dict[str, str] | None = None
) -> pd.DataFrame:
    """Indicadores que deben reportarse en el corte y aún no están reportados.

    Parte del universo de indicadores del tracking (el Excel solo trae filas de
    cortes ya generados, no de los futuros) y aplica la periodicidad de cada
    uno. Columnas: Id, Indicador, Proceso, Subproceso, Periodicidad, Estado
    ("Pendiente" si el tracking ya tiene la fila, "Por reportar" si no).
    """
    cols = ["Id", "Indicador", "Proceso", "Subproceso", "Periodicidad", "Estado"]
    needed = {"Id", "Año", "Mes", "Estado", "Proceso", "Indicador"}
    if df.empty or not needed.issubset(df.columns):
        return pd.DataFrame(columns=cols)

    work = df.copy()
    if "Periodicidad" not in work.columns:
        work["Periodicidad"] = "Mensual"
    work["_ym"] = pd.to_numeric(work["Año"], errors="coerce") * 12 + pd.to_numeric(
        work["Mes"], errors="coerce"
    )
    corte_ym = anio * 12 + mes
    estado = work["Estado"].astype(str).str.strip()

    # Indicadores que solo figuran como "No aplica" no se exigen.
    exigibles_ids = set(work.loc[estado != "No aplica", "Id"])
    # Solo los activos en el año del corte: las filas del tracking se generan desde el catálogo
    # anual de Kawak, así que un Id sin filas ese año se dio de baja (o aún no existía).
    # Para un corte de un año sin filas todavía se toma el último año disponible.
    anio_ref = anio if (work["Año"] == anio).any() else int(work["Año"].max())
    exigibles_ids &= set(work.loc[work["Año"] == anio_ref, "Id"])
    meta = (
        work[work["Id"].isin(exigibles_ids)]
        .sort_values("_ym")
        .drop_duplicates(subset="Id", keep="last")
    )
    # Los dados de baja (Vigencia Hasta anterior al corte) no se notifican.
    if "Vigencia Hasta" in meta.columns:
        hasta = pd.to_datetime(meta["Vigencia Hasta"], errors="coerce")
        fin_corte = pd.Timestamp(date(anio, mes, calendar.monthrange(anio, mes)[1]))
        meta = meta[hasta.isna() | (hasta >= fin_corte)]
    meta = meta[meta["Periodicidad"].apply(lambda p: mes in meses_de_reporte(str(p)))]

    del_corte = work[(work["_ym"] == corte_ym)]
    ya_reportados = set(del_corte.loc[del_corte["Estado"].astype(str).str.strip() == "Reportado", "Id"])
    en_tracking = set(del_corte["Id"])

    out = meta[~meta["Id"].isin(ya_reportados)].copy()
    out["Estado"] = out["Id"].apply(lambda i: "Pendiente" if i in en_tracking else "Por reportar")
    out["Subproceso"] = out["Id"].map(subprocesos or {}).fillna("")
    return out[cols].sort_values(["Proceso", "Indicador"]).reset_index(drop=True)


@dataclass(frozen=True)
class MensajeRenderizado:
    asunto: str
    html: str
    texto: str


_COLUMNAS_TABLA = (
    ("Id", "ID"),
    ("Indicador", "Nombre del indicador"),
    ("Subproceso", "Subproceso"),
    ("Periodicidad", "Frecuencia"),
)


def _filas(indicadores: pd.DataFrame) -> list[dict[str, str]]:
    filas = []
    for _, r in indicadores.iterrows():
        fila = {k: ("" if pd.isna(r.get(k)) else str(r.get(k, ""))) for k, _ in _COLUMNAS_TABLA}
        fila["Subproceso"] = fila["Subproceso"] or "—"
        filas.append(fila)
    return filas


def _tabla_html(filas: list[dict[str, str]]) -> str:
    th = "padding:6px 10px;text-align:left;background:#1F4E78;color:#fff;font-size:12px;border:1px solid #1F4E78"
    td = "padding:6px 10px;border:1px solid #cbd5e1;font-size:13px;vertical-align:top"
    head = "".join(f'<th style="{th}">{etq}</th>' for _, etq in _COLUMNAS_TABLA)
    body = "".join(
        "<tr>"
        + "".join(f'<td style="{td}">{html.escape(f[k])}</td>' for k, _ in _COLUMNAS_TABLA)
        + "</tr>"
        for f in filas
    )
    if not filas:
        body = f'<tr><td style="{td}" colspan="{len(_COLUMNAS_TABLA)}">Sin indicadores por reportar en este corte.</td></tr>'
    return (
        '<table style="border-collapse:collapse;width:100%;max-width:820px">'
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    )


def _tabla_texto(filas: list[dict[str, str]]) -> str:
    return "\n".join(
        f"  • [{f['Id']}] {f['Indicador']} — {f['Subproceso']} ({f['Periodicidad']})" for f in filas
    )


def _sustituir(plantilla: str, valores: dict[str, str]) -> str:
    """Reemplaza {clave} solo para claves conocidas; el resto del texto queda intacto."""
    return re.sub(r"\{(\w+)\}", lambda m: valores.get(m.group(1), m.group(0)), plantilla)


def _html_a_texto(fragmento: str) -> str:
    t = re.sub(r"(?i)<\s*br\s*/?>|</\s*(p|div|tr|table|ul)\s*>", "\n", fragmento)
    t = re.sub(r"(?i)<\s*li[^>]*>", "• ", t)
    t = re.sub(r"(?i)</\s*li\s*>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+\n", "\n", t)).strip()


def renderizar_mensaje(
    asunto: str,
    cuerpo: str,
    *,
    proceso: str,
    anio: int,
    mes: int,
    plazo_dias: int,
    hoy: date,
    indicadores: pd.DataFrame,
) -> MensajeRenderizado:
    """Renderiza asunto y cuerpo. El cuerpo es HTML de confianza (lo redactan los roles
    autorizados); los valores sustituidos sí se escapan. Si el cuerpo no tiene etiquetas se
    trata como texto plano."""
    limite = fecha_limite(anio, mes, plazo_dias)
    filas = _filas(indicadores)
    base = {
        "proceso": proceso,
        "corte": nombre_corte(anio, mes),
        "corte_mes": MESES_NOMBRES[mes - 1].lower(),
        "anio": str(anio),
        "fecha_limite": fecha_larga(limite),
        "dias_restantes": str(max((limite - hoy).days, 0)),
        "total": str(len(filas)),
    }
    asunto_final = _sustituir(asunto, base).replace("\n", " ").strip()

    es_html = bool(re.search(r"<\s*\w+[^>]*>", cuerpo))
    marca = "\x00TABLA\x00"
    valores = {k: html.escape(v) for k, v in base.items()} | {
        "tabla_indicadores": marca,
        "tabla_html": marca,
    }
    fuente = cuerpo if es_html else html.escape(cuerpo, quote=False).replace("\n", "<br>")
    cuerpo_html = _sustituir(fuente, valores)
    html_final = (
        '<div style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#1e293b">'
        f"{cuerpo_html.replace(marca, _tabla_html(filas))}</div>"
    )
    # La tabla se inserta después de quitar etiquetas: los nombres de indicador son datos,
    # no HTML, y no deben perder texto con "<...>".
    texto = _html_a_texto(cuerpo_html).replace(marca, "\n" + _tabla_texto(filas) + "\n")
    return MensajeRenderizado(asunto=asunto_final, html=html_final, texto=texto)


def construir_eml(
    msg: MensajeRenderizado, *, para: list[str], cc: list[str] | None = None
) -> bytes:
    """Mensaje .eml marcado como no enviado (X-Unsent): Outlook lo abre como borrador."""
    from email.message import EmailMessage

    em = EmailMessage()
    em["X-Unsent"] = "1"
    em["Subject"] = msg.asunto
    if para:
        em["To"] = ", ".join(para)
    if cc:
        em["Cc"] = ", ".join(cc)
    em.set_content(msg.texto)
    em.add_alternative(msg.html, subtype="html")
    return em.as_bytes()


def nombre_archivo(tipo: str, anio: int, mes: int, proceso: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", ascii_lower(proceso)).strip("_")[:60] or "proceso"
    return f"{tipo}_{anio}-{mes:02d}_{base}.eml"


def construir_listado_outlook(
    consolidado: dict[str, pd.DataFrame],
    destinatarios: dict[str, list[str]],
    plazo_por_proceso: dict[str, int],
    anio: int,
    mes: int,
    tipo: str = "recordatorio",
) -> bytes:
    """Libro .xlsx con la estructura que lee la automatización local Auto_Correo.

    Hojas: «Indicadores» (Id, Indicador, Proceso, Periodicidad, ...), «Destinatarios»
    (Proceso, Correo; una fila por correo) y «Parametros» (valores de la campaña). Auto_Correo
    crea con ellas borradores directamente en Outlook, sin permisos del tenant.
    """
    import io

    filas = []
    for proceso, df in sorted(consolidado.items()):
        limite = fecha_larga(fecha_limite(anio, mes, plazo_por_proceso[proceso]))
        for _, r in df.iterrows():
            filas.append(
                {
                    "Id": str(r["Id"]),
                    "Indicador": r["Indicador"],
                    "Proceso": proceso,
                    "Subproceso": r.get("Subproceso", "") or "",
                    "Periodicidad": r["Periodicidad"],
                    "Estado": r["Estado"],
                    "FechaMaxima": limite,
                }
            )
    cols = ["Id", "Indicador", "Proceso", "Subproceso", "Periodicidad", "Estado", "FechaMaxima"]
    indicadores = pd.DataFrame(filas, columns=cols)
    dest = pd.DataFrame(
        [{"Proceso": p, "Correo": c} for p in sorted(consolidado) for c in destinatarios.get(p, [])],
        columns=["Proceso", "Correo"],
    )
    fin_corte = date(anio, mes, calendar.monthrange(anio, mes)[1])
    general = max(plazo_por_proceso.values(), default=0)
    params = pd.DataFrame(
        [
            ("TIPO", tipo),
            ("CORTE_TEXTO", fecha_larga(fin_corte)),
            ("CORTE_ASUNTO", f"Corte {MESES_NOMBRES[mes - 1].lower()} {anio}"),
            ("FECHA_MAXIMA_MAS_TARDIA", fecha_larga(fecha_limite(anio, mes, general))),
            ("NOTA", "Cada proceso tiene su propia FechaMaxima en la hoja Indicadores."),
        ],
        columns=["Parametro", "Valor"],
    )
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        indicadores.to_excel(w, sheet_name="Indicadores", index=False)
        dest.to_excel(w, sheet_name="Destinatarios", index=False)
        params.to_excel(w, sheet_name="Parametros", index=False)
    return buf.getvalue()
