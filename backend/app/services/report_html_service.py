"""Servicio de generación del Informe Ejecutivo PDF (Cierre PDI 2022-2025).

A diferencia de pdf_service.py (reportlab, tablas planas), este informe se
arma como plantilla HTML/CSS (Jinja2) y se rasteriza a PDF con Playwright
(Chromium headless) — permite gradientes, tarjetas y barras que reportlab
no reproduce con fidelidad. Ver docs de la propuesta en el chat 2026-09-27.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "informe_ejecutivo"

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
