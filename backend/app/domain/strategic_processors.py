"""Procesadores estratégicos — portado desde services/strategic_indicators/processors.py."""

from __future__ import annotations

import pandas as pd

from app.domain.cmi_filters import CMIFilterService
from app.services.excel_reader import ExcelReaderService
from app.services.strategic_loaders import StrategicLoaders, PENDIENTE

PENDIENTE_STR = PENDIENTE


def _normalize_flag_series(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        raw = series.astype(str).str.strip().str.lower()
        mapped = raw.map(
            {"1": 1, "1.0": 1, "si": 1, "true": 1, "x": 1, "0": 0, "0.0": 0, "no": 0, "false": 0, "": 0}
        )
        numeric = numeric.fillna(mapped)
    return numeric


def _normalize_id_value(val) -> str:
    if pd.isna(val):
        return ""
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        return str(int(val)) if val.is_integer() else str(val).strip()
    text = str(val).strip()
    try:
        num = float(text)
        if num.is_integer():
            return str(int(num))
    except Exception:
        return text
    return text


def cierre_por_corte(df_cierres: pd.DataFrame, anio: int, mes: int) -> pd.DataFrame:
    if df_cierres.empty:
        return df_cierres
    df = df_cierres.copy()
    cutoff = int(anio) * 100 + int(mes)
    cutoff_date = pd.Timestamp(int(anio), int(mes), 1) + pd.offsets.MonthEnd(0)
    if "Anio" in df.columns and "Mes" in df.columns:
        ym = pd.to_numeric(df["Anio"], errors="coerce") * 100 + pd.to_numeric(df["Mes"], errors="coerce")
        by_period = ym.notna() & (ym <= cutoff)
        if "Fecha" in df.columns:
            by_date = (
                ym.isna()
                & df["Fecha"].notna()
                & (pd.to_datetime(df["Fecha"], errors="coerce") <= cutoff_date)
            )
            df = df[by_period | by_date].copy()
        else:
            df = df[by_period].copy()
    elif "Fecha" in df.columns:
        df = df[pd.to_datetime(df["Fecha"], errors="coerce") <= cutoff_date].copy()
    if df.empty:
        return df
    if "Fecha" in df.columns:
        df = df.sort_values(["Id", "Fecha"]).drop_duplicates(subset=["Id"], keep="last")
    else:
        df = df.drop_duplicates(subset=["Id"], keep="last")
    return df.reset_index(drop=True)


class StrategicProcessors:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._loaders = StrategicLoaders(excel)
        self._cmi = CMIFilterService(excel)

    def preparar_pdi_con_cierre(self, anio: int, mes: int = 12) -> pd.DataFrame:
        base = self._loaders.load_worksheet_flags()
        catalog = self._loaders.load_pdi_catalog()
        cierres = self._loaders.load_cierres()
        if base.empty or cierres.empty:
            return pd.DataFrame()
        if "FlagPlanEstrategico" not in base.columns:
            return pd.DataFrame()

        flag_vals = _normalize_flag_series(base["FlagPlanEstrategico"])
        indicators = base[flag_vals == 1].copy()
        if "Proyecto" in indicators.columns:
            proyecto_vals = _normalize_flag_series(indicators["Proyecto"])
            indicators = indicators[proyecto_vals != 1].copy()
        if indicators.empty:
            return pd.DataFrame()

        merge_cols = ["Id", "Indicador"]
        if "Linea" in indicators.columns:
            merge_cols.append("Linea")
        if "Objetivo" in indicators.columns:
            merge_cols.append("Objetivo")

        indicators["Id"] = indicators["Id"].apply(_normalize_id_value)
        cierres_cut = cierre_por_corte(cierres, anio, mes)
        cierres_cut["Id"] = cierres_cut["Id"].apply(_normalize_id_value)

        result = indicators[merge_cols].merge(cierres_cut, on="Id", how="left", suffixes=("", "_cierre"))
        if "Indicador_cierre" in result.columns:
            result["Indicador"] = result["Indicador"].where(
                result["Indicador"].notna() & (result["Indicador"].astype(str).str.strip() != ""),
                result["Indicador_cierre"],
            )
            result = result.drop(columns=["Indicador_cierre"])

        if not catalog.empty and "Linea" in result.columns and "Objetivo" in result.columns:
            result = result.merge(catalog, on=["Linea", "Objetivo"], how="left", suffixes=("", "_cat"))

        if "Nivel de cumplimiento" in result.columns:
            result["Nivel de cumplimiento"] = result["Nivel de cumplimiento"].fillna(PENDIENTE_STR)

        return self._cmi.filter_estrategico(result.reset_index(drop=True))

    def preparar_cna_con_cierre(self, anio: int, mes: int = 12) -> pd.DataFrame:
        base = self._loaders.load_worksheet_flags()
        catalog = self._loaders.load_cna_catalog()
        cierres = self._loaders.load_cierres()
        if base.empty or cierres.empty:
            return pd.DataFrame()
        if "FlagCNA" not in base.columns:
            return pd.DataFrame()

        flag_vals = _normalize_flag_series(base["FlagCNA"])
        indicators = base[flag_vals == 1].copy()
        if indicators.empty:
            return pd.DataFrame()

        merge_cols = ["Id", "Indicador"]
        for col in ("Factor", "Caracteristica"):
            if col in indicators.columns:
                merge_cols.append(col)

        indicators["Id"] = indicators["Id"].apply(_normalize_id_value)
        cierres_cut = cierre_por_corte(cierres, anio, mes)
        cierres_cut["Id"] = cierres_cut["Id"].apply(_normalize_id_value)

        result = indicators[merge_cols].merge(cierres_cut, on="Id", how="left", suffixes=("", "_cierre"))
        if "Indicador_cierre" in result.columns:
            result["Indicador"] = result["Indicador"].where(
                result["Indicador"].notna() & (result["Indicador"].astype(str).str.strip() != ""),
                result["Indicador_cierre"],
            )
            result = result.drop(columns=["Indicador_cierre"])

        if not catalog.empty and "Factor" in result.columns and "Caracteristica" in result.columns:
            result = result.merge(catalog, on=["Factor", "Caracteristica"], how="left", suffixes=("", "_cat"))

        if "Nivel de cumplimiento" in result.columns:
            result["Nivel de cumplimiento"] = result["Nivel de cumplimiento"].fillna(PENDIENTE_STR)

        return self._cmi.filter_estrategico(result.reset_index(drop=True))

    def load_proyectos(self) -> pd.DataFrame:
        return self._loaders.load_proyectos()

    def preparar_proyectos_con_cierre(self, anio: int, mes: int = 12) -> pd.DataFrame:
        proy = self._loaders.load_proyectos()
        if proy.empty:
            return pd.DataFrame()
        df = cierre_por_corte(proy, anio, mes)
        if df.empty:
            return df
        sort_cols = [c for c in ["Fecha", "Anio", "Mes"] if c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols, na_position="last")
        return df.drop_duplicates(subset=["Id"], keep="last").reset_index(drop=True)

    def load_historico_por_linea(self) -> pd.DataFrame:
        cierres = self._loaders.load_cierres()
        if cierres.empty:
            return pd.DataFrame()
        df = self._cmi.filter_estrategico(cierres.copy())
        if "Linea" not in df.columns and "Id" in df.columns:
            ws = self._loaders.load_worksheet_flags()
            if not ws.empty and "Linea" in ws.columns:
                ws = ws.copy()
                ws["Id"] = ws["Id"].apply(_normalize_id_value)
                df["Id"] = df["Id"].apply(_normalize_id_value)
                df = df.merge(ws[["Id", "Linea"]].drop_duplicates("Id"), on="Id", how="left")
        return df

    def latest_month_for_year(self, anio: int) -> int | None:
        cierres = self._loaders.load_cierres()
        if cierres.empty or "Anio" not in cierres.columns:
            return None
        subset = cierres[cierres["Anio"] == anio]
        if subset.empty or "Mes" not in subset.columns:
            return None
        months = pd.to_numeric(subset["Mes"], errors="coerce").dropna().astype(int)
        return int(months.max()) if not months.empty else None
