#!/usr/bin/env python3
"""
Diagnóstico independiente que genera un Excel con análisis de por qué los indicadores aparecen como 'Peligro'.

Salida: `artifacts/diagnostic_niveles_proceso_<fecha>.xlsx` con hojas:
 - file_inspection
 - load_cierres_summary
 - load_cierres_bins
 - preparar_pdi_summary
 - preparar_pdi_bins
 - preparar_pdi_sample
 - fuente_counts

Ejecutar desde la raíz del repo:
    python scripts/diagnose_niveles_proceso.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime
import traceback
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

try:
    from streamlit_app.services import strategic_indicators as si
except Exception:
    si = None


def to_number_series(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"diagnostic_niveles_proceso_{ts}.xlsx"

    sheets = {}

    # Inspección del archivo de resultados consolidados si está disponible
    out_xlsx = getattr(si, "OUT_XLSX", ROOT / "data" / "output" / "Resultados Consolidados.xlsx") if si else ROOT / "data" / "output" / "Resultados Consolidados.xlsx"
    sheets["file_inspection"] = {"path": str(out_xlsx), "exists": out_xlsx.exists()}
    try:
        if out_xlsx.exists():
            xl = pd.ExcelFile(out_xlsx, engine="openpyxl")
            sheets["file_inspection"]["sheets"] = xl.sheet_names
    except Exception as e:
        sheets["file_inspection"]["error"] = str(e)

    # Analizar load_cierres
    if si is None:
        print("No se pudo importar streamlit_app.services.strategic_indicators. Ejecuta desde la raíz del repo con el entorno correcto.")
    try:
        cierre = si.load_cierres() if si else pd.DataFrame()
    except Exception as e:
        cierre = pd.DataFrame()
        sheets["load_cierres_error"] = str(e)

    if not cierre.empty:
        # resumen numérico
        s = to_number_series(cierre.get("cumplimiento_pct") if "cumplimiento_pct" in cierre.columns else cierre.get("Cumplimiento"))
        if s is None:
            s = pd.Series(dtype=float)
        desc = s.describe(percentiles=[0.25, 0.5, 0.75]).to_frame().T
        sheets["load_cierres_summary"] = desc
        # bins
        bins = {
            "<80": int((s < 80).sum()),
            "80-99.9": int(((s >= 80) & (s < 100)).sum()),
            "100-104.9": int(((s >= 100) & (s < 105)).sum()),
            ">=105": int((s >= 105).sum()),
            "NaN": int(s.isna().sum()),
        }
        sheets["load_cierres_bins"] = pd.DataFrame([bins])
        sheets["load_cierres_head"] = cierre.head(50)
    else:
        sheets["load_cierres_summary"] = pd.DataFrame()

    # Analizar preparar_pdi_con_cierre
    try:
        # determinar año/mes a usar
        cierres = cierre if not cierre.empty else (si.load_cierres() if si else pd.DataFrame())
    except Exception:
        cierres = pd.DataFrame()

    anio = None
    mes = None
    if not cierres.empty:
        for c in ["Anio", "Año"]:
            if c in cierres.columns:
                yrs = to_number_series(cierres[c]).dropna().astype(int)
                if not yrs.empty:
                    anio = int(yrs.max())
                    break
        for c in ["Mes", "Mes_num"]:
            if c in cierres.columns:
                ms = to_number_series(cierres[c]).dropna().astype(int)
                if not ms.empty:
                    mes = int(ms.max())
                    break

    if anio is None:
        anio = datetime.now().year
    if mes is None:
        mes = 12

    try:
        pdi = si.preparar_pdi_con_cierre(int(anio), int(mes)) if si else pd.DataFrame()
    except Exception as e:
        pdi = pd.DataFrame()
        sheets["preparar_pdi_error"] = str(e)

    if not pdi.empty:
        s2 = to_number_series(pdi.get("cumplimiento_pct"))
        desc2 = s2.describe(percentiles=[0.25, 0.5, 0.75]).to_frame().T if not s2.empty else pd.DataFrame()
        sheets["preparar_pdi_summary"] = desc2
        bins2 = {
            "<80": int((s2 < 80).sum()),
            "80-99.9": int(((s2 >= 80) & (s2 < 100)).sum()),
            "100-104.9": int(((s2 >= 100) & (s2 < 105)).sum()),
            ">=105": int((s2 >= 105).sum()),
            "NaN": int(s2.isna().sum()),
        }
        sheets["preparar_pdi_bins"] = pd.DataFrame([bins2])
        # sample rows and detect source
        cols = [c for c in ["Id", "Indicador", "Linea", "Meta", "Ejecucion", "Cumplimiento", "cumplimiento_pct", "Nivel de cumplimiento", "Sentido"] if c in pdi.columns]
        sample = pdi[cols].head(200).copy()

        def detect_source(row):
            if pd.notna(row.get("cumplimiento_pct")):
                return "cumplimiento_pct"
            if pd.notna(row.get("Cumplimiento")) and str(row.get("Cumplimiento")).strip() != "":
                return "Cumplimiento_column"
            if pd.notna(row.get("Meta")) and pd.notna(row.get("Ejecucion")):
                try:
                    meta = float(row.get("Meta"))
                    ejec = float(row.get("Ejecucion"))
                    if meta != 0:
                        return "Meta/Ejecucion"
                except Exception:
                    pass
            return "none"

        sample["fuente_detectada"] = sample.apply(detect_source, axis=1)
        sheets["preparar_pdi_sample"] = sample
        sheets["fuente_counts"] = sample["fuente_detectada"].value_counts().to_frame(name="count")
    else:
        sheets["preparar_pdi_summary"] = pd.DataFrame()

    # Escribir Excel
    try:
        with pd.ExcelWriter(out_file, engine="openpyxl") as writer:
            for name, data in sheets.items():
                if isinstance(data, dict):
                    pd.DataFrame([data]).to_excel(writer, sheet_name=name, index=False)
                elif isinstance(data, pd.DataFrame):
                    # truncate sheet name if too long
                    sheet = name[:31]
                    data.to_excel(writer, sheet_name=sheet, index=False)
                else:
                    try:
                        pd.DataFrame([{"value": str(data)}]).to_excel(writer, sheet_name=name, index=False)
                    except Exception:
                        pd.DataFrame([{"value": repr(data)}]).to_excel(writer, sheet_name=name[:31], index=False)
        print(f"Informe Excel generado en: {out_file}")
    except Exception as e:
        print("Error al escribir Excel:", e)
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
