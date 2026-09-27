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
