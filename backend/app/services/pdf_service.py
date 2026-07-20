"""
Servicio de generación de reportes PDF — SGIND v2 Fase 9.

Usa reportlab para generar PDFs con la paleta de colores oficial:
  Peligro=#ef4444  Alerta=#f59e0b  Cumplimiento=#22c55e  Sobrecumplimiento=#3b82f6
"""

from __future__ import annotations

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Colores del sistema ───────────────────────────────────────────────────────
C_PELIGRO = colors.HexColor("#ef4444")
C_ALERTA = colors.HexColor("#f59e0b")
C_CUMPLE = colors.HexColor("#22c55e")
C_SOBRE = colors.HexColor("#3b82f6")
C_SINDAT = colors.HexColor("#6b7280")
C_POLI = colors.HexColor("#003366")  # azul institucional Poli
C_BG_HEADER = colors.HexColor("#f1f5f9")
C_BORDER = colors.HexColor("#cbd5e1")

_SEMAFORO_MAP: dict[str, colors.HexColor] = {
    "sobrecumplimiento": C_SOBRE,
    "cumplimiento": C_CUMPLE,
    "alerta": C_ALERTA,
    "peligro": C_PELIGRO,
    "sin dato": C_SINDAT,
    "sin_dato": C_SINDAT,
}

_SEMAFORO_HEX: dict[str, str] = {
    "sobrecumplimiento": "#3b82f6",
    "cumplimiento": "#22c55e",
    "alerta": "#f59e0b",
    "peligro": "#ef4444",
    "sin dato": "#6b7280",
    "sin_dato": "#6b7280",
}


def _semaforo_color(estado: str | None) -> colors.HexColor:
    return _SEMAFORO_MAP.get((estado or "").lower(), C_SINDAT)


def _semaforo_hex(estado: str | None) -> str:
    return _SEMAFORO_HEX.get((estado or "").lower(), "#6b7280")


# ── Estilos ───────────────────────────────────────────────────────────────────

def _make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "sgind_title",
            fontSize=18,
            textColor=C_POLI,
            leading=22,
            fontName="Helvetica-Bold",
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "sgind_subtitle",
            fontSize=11,
            textColor=colors.HexColor("#475569"),
            leading=14,
            fontName="Helvetica",
            alignment=TA_LEFT,
        ),
        "section": ParagraphStyle(
            "sgind_section",
            fontSize=13,
            textColor=C_POLI,
            leading=17,
            fontName="Helvetica-Bold",
            spaceBefore=14,
            spaceAfter=4,
        ),
        "body": base["Normal"],
        "cell": ParagraphStyle(
            "sgind_cell",
            fontSize=8,
            leading=10,
            fontName="Helvetica",
        ),
        "cell_bold": ParagraphStyle(
            "sgind_cell_bold",
            fontSize=8,
            leading=10,
            fontName="Helvetica-Bold",
        ),
        "kpi_label": ParagraphStyle(
            "sgind_kpi_label",
            fontSize=9,
            textColor=colors.HexColor("#64748b"),
            fontName="Helvetica",
            alignment=TA_CENTER,
        ),
        "kpi_value": ParagraphStyle(
            "sgind_kpi_value",
            fontSize=22,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ),
        "footer": ParagraphStyle(
            "sgind_footer",
            fontSize=7,
            textColor=colors.HexColor("#94a3b8"),
            alignment=TA_CENTER,
        ),
    }


# ── Bloque KPI ────────────────────────────────────────────────────────────────

def _kpi_row(items: list[tuple[str, str, str | None]], styles: dict) -> Table:
    """Crea una fila de tarjetas KPI (label, valor, color_hex)."""
    n = len(items)
    col_w = 17 * cm / n

    header_cells = [Paragraph(label, styles["kpi_label"]) for label, _, _ in items]
    value_cells = []
    for _, valor, color in items:
        p = Paragraph(valor, ParagraphStyle(
            "kpi_v_tmp",
            fontSize=22,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
            textColor=colors.HexColor(color) if color else C_POLI,
        ))
        value_cells.append(p)

    t = Table([header_cells, value_cells], colWidths=[col_w] * n)
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_BG_HEADER, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ── Tabla de indicadores ──────────────────────────────────────────────────────

def _indicadores_table(indicadores: list[dict[str, Any]], styles: dict) -> Table:
    headers = ["ID", "Indicador", "Meta", "Ejecución", "Estado"]
    col_widths = [2 * cm, 8 * cm, 2.5 * cm, 2.5 * cm, 3.5 * cm]

    rows: list[list] = [[Paragraph(h, styles["cell_bold"]) for h in headers]]
    for ind in indicadores[:80]:  # límite para no superar página
        estado = ind.get("estado") or ind.get("semaforo") or "Sin dato"
        color = _semaforo_color(estado)
        estado_p = Paragraph(
            estado.capitalize(),
            ParagraphStyle("cell_estado", fontSize=8, leading=10,
                           fontName="Helvetica-Bold", textColor=color),
        )

        def _fmt(v: Any) -> str:
            if v is None:
                return "—"
            try:
                return f"{float(v):.1f}"
            except (TypeError, ValueError):
                return str(v)

        rows.append([
            Paragraph(str(ind.get("id") or ind.get("Id") or ""), styles["cell"]),
            Paragraph(str(ind.get("indicador") or ind.get("Indicador") or "")[:90], styles["cell"]),
            Paragraph(_fmt(ind.get("meta") or ind.get("Meta")), styles["cell"]),
            Paragraph(_fmt(ind.get("ejecucion") or ind.get("Ejecucion")), styles["cell"]),
            estado_p,
        ])

    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_POLI),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_BG_HEADER]),
        ("GRID", (0, 0), (-1, -1), 0.3, C_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


# ── Distribución semáforo ─────────────────────────────────────────────────────

def _distribucion_table(dist: dict[str, int], styles: dict) -> Table:
    """Tabla horizontal con conteos de distribución de estados."""
    labels = {
        "cumple": ("Cumplimiento", C_CUMPLE),
        "alerta": ("Alerta", C_ALERTA),
        "peligro": ("Peligro / Crítico", C_PELIGRO),
        "critico": ("Crítico", C_PELIGRO),
        "sin_dato": ("Sin dato", C_SINDAT),
        "sin dato": ("Sin dato", C_SINDAT),
        "sobrecumplimiento": ("Sobrecumplimiento", C_SOBRE),
    }
    rows_header = []
    rows_val = []
    widths = []
    for key, cnt in dist.items():
        if key in labels:
            label_text, color = labels[key]
        else:
            label_text, color = key.capitalize(), C_SINDAT
        rows_header.append(Paragraph(label_text, styles["kpi_label"]))
        rows_val.append(Paragraph(
            str(cnt),
            ParagraphStyle("d_val", fontSize=18, fontName="Helvetica-Bold",
                           alignment=TA_CENTER, textColor=color),
        ))
        widths.append(17 * cm / max(len(dist), 1))

    if not rows_header:
        return Spacer(0, 0)  # type: ignore[return-value]

    t = Table([rows_header, rows_val], colWidths=widths)
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_BG_HEADER, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ── Pie de página ─────────────────────────────────────────────────────────────

def _on_page(canvas, doc):
    """Número de página en el pie."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#94a3b8"))
    canvas.drawCentredString(
        A4[0] / 2,
        1.2 * cm,
        f"Sistema de Indicadores Estratégicos Poli — Página {doc.page}",
    )
    canvas.restoreState()


def _on_page_landscape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#94a3b8"))
    canvas.drawCentredString(
        landscape(A4)[0] / 2,
        1.2 * cm,
        f"Sistema de Indicadores Estratégicos Poli — Página {doc.page}",
    )
    canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Reporte 1 — Resumen General
# ─────────────────────────────────────────────────────────────────────────────

def generar_resumen_general(
    anio: int,
    kpis: dict[str, Any],
    indicadores: list[dict[str, Any]],
    generated_at: str = "",
) -> bytes:
    """
    Genera PDF del Resumen General con KPIs globales y tabla de indicadores.

    Args:
        anio: año del reporte
        kpis: dict con claves total, cumple, alerta, peligro, sin_dato, pct_cumple, ...
        indicadores: lista de dicts con id, indicador, meta, ejecucion, estado
        generated_at: timestamp ISO (solo informativo)

    Returns:
        Bytes del PDF generado.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = _make_styles()
    story = []

    # ── Encabezado ──
    story.append(Paragraph("Resumen General de Indicadores", styles["title"]))
    story.append(Paragraph(
        f"Año {anio}" + (f" · Generado: {generated_at}" if generated_at else ""),
        styles["subtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=C_POLI))
    story.append(Spacer(1, 0.4 * cm))

    # ── KPIs resumen ──
    total = kpis.get("total_indicadores") or kpis.get("total") or len(indicadores)
    pct = kpis.get("pct_cumple") or kpis.get("porcentaje_cumplimiento") or 0
    cumple = kpis.get("cumple") or kpis.get("cumplimiento") or 0
    alerta = kpis.get("alerta") or 0
    peligro = kpis.get("peligro") or kpis.get("critico") or 0

    kpi_items = [
        ("Total indicadores", str(total), None),
        ("% Cumplimiento", f"{pct:.1f}%" if isinstance(pct, (int, float)) else str(pct), "#22c55e"),
        ("En cumplimiento", str(cumple), "#22c55e"),
        ("En alerta", str(alerta), "#f59e0b"),
        ("En peligro", str(peligro), "#ef4444"),
    ]
    story.append(_kpi_row(kpi_items, styles))
    story.append(Spacer(1, 0.5 * cm))

    # ── Tabla de indicadores ──
    story.append(Paragraph("Detalle de Indicadores", styles["section"]))
    if indicadores:
        story.append(_indicadores_table(indicadores, styles))
        if len(indicadores) > 80:
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph(
                f"* Se muestran los primeros 80 de {len(indicadores)} indicadores.",
                styles["subtitle"],
            ))
    else:
        story.append(Paragraph("Sin datos de indicadores disponibles.", styles["body"]))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Reporte 2 — Informe por Procesos
# ─────────────────────────────────────────────────────────────────────────────

def generar_informe_procesos(
    anio: int,
    mes: int,
    proceso: str,
    data: dict[str, Any],
    generated_at: str = "",
) -> bytes:
    """
    Genera PDF del Informe por Procesos.

    Args:
        anio: año del reporte
        mes: mes del reporte (1-12)
        proceso: nombre del proceso filtrado (o "Todos")
        data: respuesta completa del endpoint /informe/dashboard
        generated_at: timestamp ISO

    Returns:
        Bytes del PDF generado.
    """
    MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_nombre = MESES[mes] if 1 <= mes <= 12 else str(mes)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = _make_styles()
    story = []

    # ── Encabezado ──
    story.append(Paragraph("Informe por Procesos", styles["title"]))
    subtitle_parts = [f"Año {anio} · {mes_nombre}"]
    if proceso and proceso != "Todos":
        subtitle_parts.append(f"Proceso: {proceso}")
    if generated_at:
        subtitle_parts.append(f"Generado: {generated_at}")
    story.append(Paragraph(" · ".join(subtitle_parts), styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_POLI))
    story.append(Spacer(1, 0.4 * cm))

    # ── Resumen ejecutivo ──
    resumen = data.get("resumen_ejecutivo") or {}
    if resumen:
        story.append(Paragraph("Resumen Ejecutivo", styles["section"]))
        kpi_items = [
            ("Total indicadores", str(resumen.get("total", 0)), None),
            ("Cumplimiento", str(resumen.get("cumple", 0)), "#22c55e"),
            ("Alerta", str(resumen.get("alerta", 0)), "#f59e0b"),
            ("Peligro", str(resumen.get("peligro", 0)), "#ef4444"),
            ("Sin dato", str(resumen.get("sin_dato", 0)), "#6b7280"),
        ]
        if "pct_cumple" in resumen:
            pct = resumen["pct_cumple"]
            kpi_items.insert(1, ("% Cumplimiento", f"{pct:.1f}%", "#22c55e"))
        story.append(_kpi_row(kpi_items, styles))
        story.append(Spacer(1, 0.3 * cm))

    # ── Distribución semáforo ──
    dist = data.get("distribucion_estado") or {}
    if dist:
        story.append(Paragraph("Distribución por estado", styles["section"]))
        story.append(_distribucion_table(dist, styles))
        story.append(Spacer(1, 0.3 * cm))

    # ── Tabla de indicadores ──
    indicadores = data.get("indicadores") or []
    story.append(Paragraph("Indicadores", styles["section"]))
    if indicadores:
        # En landscape añadimos columna proceso
        headers = ["ID", "Proceso", "Indicador", "Meta", "Ejecución", "Estado"]
        col_widths = [2 * cm, 4.5 * cm, 9 * cm, 2.2 * cm, 2.2 * cm, 3.5 * cm]
        rows: list[list] = [[Paragraph(h, styles["cell_bold"]) for h in headers]]

        for ind in indicadores[:100]:
            estado = ind.get("estado") or ind.get("semaforo") or "Sin dato"
            color = _semaforo_color(estado)

            def _fmt(v: Any) -> str:
                if v is None:
                    return "—"
                try:
                    return f"{float(v):.1f}"
                except (TypeError, ValueError):
                    return str(v)

            rows.append([
                Paragraph(str(ind.get("id") or ind.get("Id") or ""), styles["cell"]),
                Paragraph(str(ind.get("proceso") or ind.get("Proceso") or "")[:40], styles["cell"]),
                Paragraph(str(ind.get("indicador") or ind.get("Indicador") or "")[:100], styles["cell"]),
                Paragraph(_fmt(ind.get("meta") or ind.get("Meta")), styles["cell"]),
                Paragraph(_fmt(ind.get("ejecucion") or ind.get("Ejecucion")), styles["cell"]),
                Paragraph(
                    estado.capitalize(),
                    ParagraphStyle("est_tmp", fontSize=8, leading=10,
                                   fontName="Helvetica-Bold", textColor=color),
                ),
            ])

        t = Table(rows, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), C_POLI),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_BG_HEADER]),
            ("GRID", (0, 0), (-1, -1), 0.3, C_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t)

        if len(indicadores) > 100:
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph(
                f"* Se muestran los primeros 100 de {len(indicadores)} indicadores.",
                styles["subtitle"],
            ))
    else:
        story.append(Paragraph("Sin datos de indicadores para los filtros seleccionados.", styles["body"]))

    # ── Análisis IA (texto) ──
    analisis_ia = data.get("analisis_ia") or {}
    if analisis_ia:
        story.append(Paragraph("Análisis IA", styles["section"]))
        for key, texto in analisis_ia.items():
            if texto and isinstance(texto, str):
                story.append(Paragraph(f"<b>{key.replace('_', ' ').capitalize()}:</b> {texto}", styles["body"]))
                story.append(Spacer(1, 0.2 * cm))

    doc.build(story, onFirstPage=_on_page_landscape, onLaterPages=_on_page_landscape)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Reporte 3 — Ficha individual de indicador
# ─────────────────────────────────────────────────────────────────────────────

def generar_ficha_indicador(
    ficha: dict[str, Any],
    generated_at: str = "",
) -> bytes:
    """
    Genera PDF de la ficha individual de un indicador (CMI Estratégico / Procesos).

    Args:
        ficha: dict con los mismos datos que devuelve el modal de ficha
            (Id, Indicador, Linea, Meta, Ejecucion, cumplimiento_pct,
            "Nivel de cumplimiento", Descripcion, historico, ...).
        generated_at: timestamp ISO (solo informativo)

    Returns:
        Bytes del PDF generado.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = _make_styles()
    story: list[Any] = []

    indicador_id = ficha.get("Id") or ficha.get("id") or ""
    nombre = ficha.get("Indicador") or ficha.get("indicador") or "Indicador"
    linea = ficha.get("Linea") or ficha.get("Proceso") or ""

    story.append(Paragraph(f"Ficha del indicador {indicador_id}", styles["title"]))
    subtitle_parts = [nombre]
    if linea:
        subtitle_parts.append(str(linea))
    if generated_at:
        subtitle_parts.append(f"Generado: {generated_at}")
    story.append(Paragraph(" · ".join(str(p) for p in subtitle_parts), styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_POLI))
    story.append(Spacer(1, 0.4 * cm))

    def _fmt(v: Any) -> str:
        if v is None:
            return "—"
        try:
            return f"{float(v):.1f}"
        except (TypeError, ValueError):
            return str(v)

    meta = ficha.get("Meta") or ficha.get("meta")
    ejecucion = ficha.get("Ejecucion") or ficha.get("ejecucion")
    cumplimiento = ficha.get("cumplimiento_pct")
    nivel = ficha.get("Nivel de cumplimiento") or ficha.get("Estado") or "Sin dato"

    kpi_items = [
        ("Meta", _fmt(meta), None),
        ("Ejecución", _fmt(ejecucion), None),
        ("Cumplimiento", f"{float(cumplimiento):.1f}%" if isinstance(cumplimiento, (int, float)) else "—", "#1A3A5C"),
        ("Nivel", str(nivel), _semaforo_hex(nivel)),
    ]
    story.append(_kpi_row(kpi_items, styles))
    story.append(Spacer(1, 0.4 * cm))

    descripcion = ficha.get("Descripcion") or ficha.get("descripcion")
    if descripcion and isinstance(descripcion, str):
        story.append(Paragraph("Descripción", styles["section"]))
        story.append(Paragraph(descripcion, styles["body"]))
        story.append(Spacer(1, 0.3 * cm))

    historico = ficha.get("historico") or []
    if historico:
        story.append(Paragraph("Histórico", styles["section"]))
        headers = ["Periodo", "Meta", "Ejecución", "Cumplimiento"]
        col_widths = [4 * cm, 4 * cm, 4 * cm, 4 * cm]
        rows: list[list] = [[Paragraph(h, styles["cell_bold"]) for h in headers]]
        for item in historico:
            rows.append([
                Paragraph(str(item.get("periodo", "")), styles["cell"]),
                Paragraph(_fmt(item.get("meta")), styles["cell"]),
                Paragraph(_fmt(item.get("ejecucion")), styles["cell"]),
                Paragraph(_fmt(item.get("cumplimiento")), styles["cell"]),
            ])
        t = Table(rows, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), C_POLI),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_BG_HEADER]),
            ("GRID", (0, 0), (-1, -1), 0.3, C_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("Sin histórico disponible para este indicador.", styles["body"]))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()
