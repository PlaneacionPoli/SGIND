"""Cargador del Centro de Proyectos PMO — fuente OFICIAL de proyectos para
el cronograma "PROYECTOS PMO" del Informe Ejecutivo y de la hoja de línea
(Comienzo/Fin/% completado reales por proyecto), distinta de
Cierres/Consolidado (build_proyectos_gantt), que solo cubre proyectos con
cierre cargado. Confirmado con negocio, 2026-09-27.

Produce las columnas que build_proyectos_pmo_gantt (resumen_builders.py)
espera: Id, Indicador, Linea, anio_inicio, anio_fin, cumplimiento_pct,
estado."""

from __future__ import annotations

import pandas as pd

from app.services.excel_reader import ExcelReaderService

PMO_PATH = "raw/Proyectos/centroDeProyectos_PMO_2026.xlsx"
PMO_SHEET = "centroDeProyectos"

_COLS = {
    "Nombre del proyecto": "Indicador",
    "0. Estado del proyecto": "estado",
    "% completado": "cumplimiento_pct",
    "4. Líneas estratégicas": "Linea",
    "Comienzo": "_fecha_inicio",
    "Fin": "_fecha_fin",
}

_OUT_COLS = ["Id", "Indicador", "Linea", "anio_inicio", "anio_fin", "cumplimiento_pct", "estado"]


def _parse_pct(value) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, int | float):
        num = float(value)
        return round(num * 100, 1) if num <= 1 else round(num, 1)
    text = str(value).strip().replace("%", "").replace(",", ".")
    try:
        return round(float(text), 1)
    except ValueError:
        return None


def _parse_fecha(value) -> pd.Timestamp | None:
    if pd.isna(value) or value in ("", None):
        return None
    if isinstance(value, pd.Timestamp):
        return value
    try:
        parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
        return None if pd.isna(parsed) else parsed
    except (ValueError, TypeError):
        return None


class ProyectosPmoLoader:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel

    def _exists(self) -> bool:
        return (self._excel.data_root / PMO_PATH).exists()

    def load(self) -> pd.DataFrame:
        """Id, Indicador, Linea, anio_inicio, anio_fin, cumplimiento_pct,
        estado — una fila por proyecto del Centro de Proyectos PMO
        (raw/Proyectos/centroDeProyectos_PMO_2026.xlsx)."""
        empty = pd.DataFrame(columns=_OUT_COLS)
        if not self._exists():
            return empty
        try:
            df = self._excel.read_excel(PMO_PATH, sheet_name=PMO_SHEET)
        except Exception:
            return empty
        df.columns = [str(c).strip() for c in df.columns]
        available = {src: dst for src, dst in _COLS.items() if src in df.columns}
        if "Nombre del proyecto" not in available:
            return empty

        out = df[list(available.keys())].rename(columns=available)
        out = out[
            out["Indicador"].notna() & (out["Indicador"].astype(str).str.strip() != "")
        ].copy()
        out = out.reset_index(drop=True)
        out["Id"] = [f"PMO-{i + 1}" for i in range(len(out))]
        out["Indicador"] = out["Indicador"].astype(str).str.strip()
        out["Linea"] = out["Linea"].apply(lambda v: str(v).strip() if pd.notna(v) else "")
        out["estado"] = out["estado"].apply(lambda v: str(v).strip() if pd.notna(v) else "")
        out["cumplimiento_pct"] = out["cumplimiento_pct"].apply(_parse_pct)

        fecha_inicio = out["_fecha_inicio"].apply(_parse_fecha)
        fecha_fin = out["_fecha_fin"].apply(_parse_fecha)
        anio_inicio: list[int | None] = []
        anio_fin: list[int | None] = []
        for fi, ff in zip(fecha_inicio, fecha_fin, strict=True):
            ai = int(fi.year) if fi is not None else None
            af = int(ff.year) if ff is not None else ai
            ai = ai if ai is not None else af
            if ai is not None and af is not None and af < ai:
                ai, af = af, ai
            anio_inicio.append(ai)
            anio_fin.append(af)
        out["anio_inicio"] = anio_inicio
        out["anio_fin"] = anio_fin
        out = out[out["anio_inicio"].notna() & out["anio_fin"].notna()].copy()
        out["anio_inicio"] = out["anio_inicio"].astype(int)
        out["anio_fin"] = out["anio_fin"].astype(int)

        return out[_OUT_COLS].reset_index(drop=True)
