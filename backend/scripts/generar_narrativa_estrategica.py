"""Genera y guarda la narrativa cualitativa del Informe Estratégico PDI
(Cierre 2022-2025) — corre UNA VEZ (la info es estática) y deja el
resultado en data/derived/narrativa_estrategica_2022_2025.json, que el PDF
y el dashboard consolidado leen sin volver a llamar a la IA.

Uso (desde backend/, con la venv activa):
    SGIND_DATA_PATH=../data python scripts/generar_narrativa_estrategica.py

Si hay GEMINI_API_KEY configurada, usa Gemini; si no, genera con el
heurístico basado en plantillas (ver narrativa_estrategica_service.py).
Volver a correr este script sobrescribe el JSON — hacerlo cuando cambien
los datos fuente (cierres, Centro de Proyectos) o se consiga una API key."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.services.excel_reader import ExcelReaderService  # noqa: E402
from app.services.narrativa_estrategica_service import generar_y_guardar  # noqa: E402
from app.services.resumen_service import ResumenService  # noqa: E402


def main() -> None:
    settings = get_settings()
    excel = ExcelReaderService(settings)
    svc = ResumenService(excel)
    path = generar_y_guardar(svc)
    print(f"Narrativa estratégica guardada en: {path}")


if __name__ == "__main__":
    main()
