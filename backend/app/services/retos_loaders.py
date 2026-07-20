"""Cargadores del Plan de Retos — portado desde resumen_general.py."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

from app.services.excel_reader import ExcelReaderService

RETOS_PATH = "raw/Retos/Plan de retos.xlsx"


def _norm_key(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("_", " ")
    text = re.sub(r"[^0-9a-z]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class RetosLoaders:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel

    def _exists(self) -> bool:
        return (self._excel.data_root / RETOS_PATH).exists()

    def load_retos_data(self, anio: int) -> tuple[pd.DataFrame, pd.DataFrame]:
        if not self._exists():
            return pd.DataFrame(), pd.DataFrame()
        try:
            linea_df = self._excel.read_excel(RETOS_PATH, sheet_name="Linea")
            obj_df = self._excel.read_excel(RETOS_PATH, sheet_name="Objetivo")
            linea_df.columns = [str(c).strip() for c in linea_df.columns]
            obj_df.columns = [str(c).strip() for c in obj_df.columns]
            if "Año" in linea_df.columns:
                linea_df = linea_df[linea_df["Año"] == anio].copy()
            if "Año" in obj_df.columns:
                obj_df = obj_df[obj_df["Año"] == anio].copy()
            for df in (linea_df, obj_df):
                if "Línea Estratégica" in df.columns:
                    df.rename(columns={"Línea Estratégica": "Linea"}, inplace=True)
                if "Cumplimiento" in df.columns:
                    df.rename(columns={"Cumplimiento": "cumplimiento_pct"}, inplace=True)
                    df["cumplimiento_pct"] = pd.to_numeric(df["cumplimiento_pct"], errors="coerce") * 100
            if "Objetivo" not in obj_df.columns:
                obj_df["Objetivo"] = None
            return linea_df, obj_df
        except Exception:
            return pd.DataFrame(), pd.DataFrame()

    def load_area_count(self, anio: int) -> int:
        if not self._exists():
            return 0
        try:
            df = self._excel.read_excel(RETOS_PATH, sheet_name="Areas")
            df.columns = [str(c).strip() for c in df.columns]
            normalized = {}
            for c in df.columns:
                text = str(c).strip().lower()
                text = unicodedata.normalize("NFKD", text)
                text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
                text = text.replace("º", "").replace("°", "").replace(" ", "")
                normalized[text] = c
            year_col = normalized.get("ano") or normalized.get("anio")
            count_col = normalized.get("n")
            if year_col and count_col:
                row = df[df[year_col] == anio]
                if not row.empty:
                    value = row.iloc[0][count_col]
                    return int(value) if pd.notna(value) else 0
        except Exception:
            pass
        return 0

    def load_planes(self, anio: int) -> pd.DataFrame:
        if not self._exists():
            return pd.DataFrame(columns=["Linea", "N_Planes"])
        try:
            df = self._excel.read_excel(RETOS_PATH, sheet_name="Planes")
            df.columns = [str(c).strip() for c in df.columns]
            if "Año" in df.columns:
                df = df[df["Año"] == anio].copy()
            if "Desglose" in df.columns:
                df = df.rename(columns={"Desglose": "Linea"})
            if "N°" in df.columns:
                df = df.rename(columns={"N°": "N_Planes"})
            elif "N" in df.columns:
                df = df.rename(columns={"N": "N_Planes"})
            if "Linea" not in df.columns or "N_Planes" not in df.columns:
                return pd.DataFrame(columns=["Linea", "N_Planes"])
            out = df[["Linea", "N_Planes"]].copy()
            out["Linea"] = out["Linea"].astype(str).str.strip()
            out["N_Planes"] = pd.to_numeric(out["N_Planes"], errors="coerce").fillna(0).astype(int)
            return out
        except Exception:
            return pd.DataFrame(columns=["Linea", "N_Planes"])
