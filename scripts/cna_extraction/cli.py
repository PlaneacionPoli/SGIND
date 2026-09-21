"""
scripts/cna_extraction/cli.py

Entrypoint de la Fase 1. Deliberadamente solo soporta --diagnose: en esta
fase no existe ninguna forma de escribir data/output/ desde esta CLI — el
límite de "solo lectura" queda forzado por la herramienta, no solo por
convención.

Uso:
    python -m scripts.cna_extraction.cli --diagnose
    python -m scripts.cna_extraction.cli --diagnose --source "ruta/al/Anexo.xlsx"
"""

from __future__ import annotations

import argparse
from pathlib import Path

from core.config import DATA_RAW
from scripts.cna_extraction.diagnostics import run_diagnostics, write_report

DEFAULT_SOURCE = DATA_RAW / "Plan de mejoramiento" / "Anexo Estadístico Dcto. Autoevaluacion.xlsx"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fase 1 — diagnóstico de extracción CNA (solo lectura, sin escritura)."
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        required=True,
        help="Ejecuta el diagnóstico (única acción disponible en esta fase).",
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Ruta al Anexo Estadístico.")
    parser.add_argument("--out-dir", type=Path, default=Path("artifacts"), help="Directorio de salida del reporte.")
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"No se encontró el archivo fuente: {args.source}")

    report = run_diagnostics(args.source)
    json_path, md_path = write_report(report, args.out_dir)

    print(f"Reporte JSON: {json_path}")
    print(f"Reporte Markdown: {md_path}")
    print(f"Hojas procesadas: {report['sheets_procesados']} / {report['total_sheets_datos']}")
    print(f"Problemas detectados: {len(report['problems'])}")


if __name__ == "__main__":
    main()
