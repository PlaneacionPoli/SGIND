"""Servicio de generación del Informe Ejecutivo PDF (Cierre PDI 2022-2025).

A diferencia de pdf_service.py (reportlab, tablas planas), este informe se
arma como plantilla HTML/CSS (Jinja2) y se rasteriza a PDF con Playwright
(Chromium headless) — permite gradientes, tarjetas y barras que reportlab
no reproduce con fidelidad. Ver docs de la propuesta en el chat 2026-09-27.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "informe_ejecutivo"


def _image_data_uri(filename: str) -> str:
    path = _TEMPLATE_DIR / "assets" / filename
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _logo_data_uri() -> str:
    return _image_data_uri("logo.png")


def _portada_data_uri() -> str:
    """Foto oficial de portada (fachada + diagonales + logo + título ya
    incluidos en la imagen) — assets/Portada.png del repo."""
    return _image_data_uri("portada.png")

# STRATEGIC_LINE_DEFS["icon"] (resumen_builders.py) → glifo del encabezado
# de cada página de línea en el Informe Ejecutivo.
_ICON_GLYPHS = {
    "rocket": "↗",  # ↗ Expansión
    "chart": "⚙",  # ⚙ Transformación Organizacional
    "medal": "☆",  # ☆ Calidad
    "bulb": "✦",  # ✦ Experiencia
    "leaf": "☘",  # ☘ Sostenibilidad
    # U+1F393 (🎓) es de un plano Unicode que las fuentes base de Chromium en
    # el contenedor no siempre cubren (se ve como tofu) — se usa un símbolo
    # del mismo bloque que el resto de iconos (garantizado por las fuentes
    # que instala `playwright install --with-deps`).
    "graduation": "❖",  # ❖ Educación para toda la vida
}

_ANIO_COLORS = {
    2022: "#1F2937",
    2023: "#F59E0B",
    2024: "#06B6D4",
    2025: "#EC0677",
    2026: "#A6CE38",
}

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _estado_de(cumplimiento: float | None, *, stand_by: bool = False) -> dict[str, str]:
    """Badge de estado del Anexo/Cómo-leer-este-informe: escala única 100/90
    (distinta del régimen interno Nivel de cumplimiento, que varía por tipo
    de indicador — ver app/domain/categorization.py). Esta escala es
    deliberadamente simple para lectura ejecutiva; el propio informe advierte
    que está pendiente de validación institucional."""
    if stand_by:
        return {"label": "Stand by", "color": "#6B7280", "icon": "◎"}
    if cumplimiento is None:
        return {"label": "Sin medición", "color": "#94A3B8", "icon": "⊝"}
    if cumplimiento >= 100:
        return {"label": "Cumplido", "color": "#16A34A", "icon": "✓"}
    if cumplimiento >= 90:
        return {"label": "En progreso", "color": "#D97706", "icon": "◐"}
    return {"label": "Atención", "color": "#DC2626", "icon": "⚠"}


def _build_verificacion(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Recalcula el consolidado de cada línea desde sus tres perspectivas ya
    guardadas (retos.cumplimiento, proyectos_cumplimiento_promedio,
    indicadores_cumplimiento_promedio) y lo compara contra
    cumplimiento_consolidado — mismo chequeo que pdi_validation.V1, aplicado
    directo sobre el payload que va al PDF (detecta regresiones futuras)."""
    filas = []
    consolidados = []
    for li in data.get("lineas", []):
        partes = [
            v
            for v in (
                li["retos"]["cumplimiento"],
                li.get("proyectos_cumplimiento_promedio"),
                li.get("indicadores_cumplimiento_promedio"),
            )
            if v is not None
        ]
        recalculado = round(sum(partes) / len(partes), 2) if partes else None
        informe = li.get("cumplimiento_consolidado")
        consolidados.append(informe)
        formula = " + ".join(f"{v:g}" for v in partes)
        filas.append(
            {
                "linea": li["linea"],
                "color": li["color"],
                "formula": f"({formula}) / {len(partes)}" if partes else "N/A",
                "recalculado": recalculado,
                "informe": informe,
                "coincide": recalculado is not None
                and informe is not None
                and abs(recalculado - informe) <= 0.15,
            }
        )
    validos = [c for c in consolidados if c is not None]
    global_recalc = round(sum(validos) / len(validos), 2) if validos else None
    global_informe = data.get("cumplimiento_global")
    filas.append(
        {
            "linea": "Global",
            "color": "#0B2A5B",
            "formula": "promedio de los 6 consolidados",
            "recalculado": global_recalc,
            "informe": global_informe,
            "coincide": global_recalc is not None
            and global_informe is not None
            and abs(global_recalc - global_informe) <= 0.15,
            "es_global": True,
        }
    )
    return filas


def _build_conciliaciones(data: dict[str, Any]) -> dict[str, Any]:
    lineas = data.get("lineas", [])
    conteo_por_linea = [
        len([ind for obj in li["objetivos"] for ind in obj["indicadores"]]) for li in lineas
    ]
    total_calc = sum(conteo_por_linea)
    sin_medicion_nombres = [
        ind["indicador"]
        for li in lineas
        for obj in li["objetivos"]
        for ind in obj["indicadores"]
        if ind.get("cumplimiento") is None
    ]

    proy_por_linea = [len(li["proyectos"]) for li in lineas]
    total_proy_calc = sum(proy_por_linea)

    return {
        "indicadores_por_linea": [str(n) for n in conteo_por_linea],
        "indicadores_total_calc": total_calc,
        "sin_medicion_nombres": sin_medicion_nombres,
        "proyectos_por_linea": [str(n) for n in proy_por_linea],
        "proyectos_total_calc": total_proy_calc,
        "proyectos_total_portada": data.get("total_proyectos"),
    }


def generar_informe_ejecutivo(data: dict[str, Any]) -> bytes:
    """Renderiza el Informe Ejecutivo PDF a partir del payload de
    ResumenService.get_informe_ejecutivo().

    Returns:
        Bytes del PDF generado (A4, sin márgenes de navegador).
    """
    css = (_TEMPLATE_DIR / "report.css").read_text(encoding="utf-8")
    template = _env.get_template("report.html")
    html = template.render(
        data=data,
        css=css,
        anio_colors=_ANIO_COLORS,
        icon_glyphs=_ICON_GLYPHS,
        logo_data_uri=_logo_data_uri(),
        portada_data_uri=_portada_data_uri(),
        generated_at=datetime.now(UTC).strftime("%d/%m/%Y %H:%M UTC"),
        estado_de=_estado_de,
        verificacion=_build_verificacion(data),
        conciliaciones=_build_conciliaciones(data),
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"},
            )
        finally:
            browser.close()

    return pdf_bytes
