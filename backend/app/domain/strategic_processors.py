"""Procesadores estratégicos — portado desde services/strategic_indicators/processors.py."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from app.domain.categorization import categorizar_cumplimiento
from app.domain.cmi_filters import CMIFilterService
from app.domain.health_metrics import recalcular_cumplimiento_faltante
from app.services.excel_reader import ExcelReaderService
from app.services.strategic_loaders import PENDIENTE, StrategicLoaders

PENDIENTE_STR = PENDIENTE

# Indicadores de ingresos (Sostenibilidad: Cumplimiento de Ingresos; Educación para toda la vida:
# total y sus tres componentes). En el cierre del PDI se muestran como la SUMA de los años del
# ciclo (meta y ejecución), no como el valor del último año.
IDS_INGRESOS_ACUMULADOS = frozenset({"203", "385", "386.1", "386.2", "386.3"})


def _normalize_flag_series(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        raw = series.astype(str).str.strip().str.lower()
        mapped = raw.map(
            {
                "1": 1,
                "1.0": 1,
                "si": 1,
                "true": 1,
                "x": 1,
                "0": 0,
                "0.0": 0,
                "no": 0,
                "false": 0,
                "": 0,
            }
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
        ym = pd.to_numeric(df["Anio"], errors="coerce") * 100 + pd.to_numeric(
            df["Mes"], errors="coerce"
        )
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

    def preparar_pdi_con_cierre(
        self, anio: int, mes: int = 12, *, solo_anio: bool = False
    ) -> pd.DataFrame:
        """solo_anio=True: un indicador solo cuenta si tiene cierre dentro del año elegido; no
        se arrastra el último valor de años anteriores (RN-21)."""
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
        if solo_anio and "Anio" in cierres.columns:
            cierres = cierres[pd.to_numeric(cierres["Anio"], errors="coerce") == int(anio)]
        cierres_cut = cierre_por_corte(cierres, anio, mes)
        if cierres_cut.empty:
            return pd.DataFrame()
        cierres_cut["Id"] = cierres_cut["Id"].apply(_normalize_id_value)

        result = indicators[merge_cols].merge(
            cierres_cut, on="Id", how="inner", suffixes=("", "_cierre")
        )
        # inner: un indicador sin ningun cierre hasta el corte aun no existia en
        # ese anio (p.ej. 2022 tiene 36 de los 53 del catalogo) y no debe contarse.
        if "Indicador_cierre" in result.columns:
            result["Indicador"] = result["Indicador"].where(
                result["Indicador"].notna() & (result["Indicador"].astype(str).str.strip() != ""),
                result["Indicador_cierre"],
            )
            result = result.drop(columns=["Indicador_cierre"])

        if not catalog.empty and "Linea" in result.columns and "Objetivo" in result.columns:
            result = result.merge(
                catalog, on=["Linea", "Objetivo"], how="left", suffixes=("", "_cat")
            )

        if "Nivel de cumplimiento" in result.columns:
            result["Nivel de cumplimiento"] = result["Nivel de cumplimiento"].fillna(PENDIENTE_STR)

        return self._cmi.filter_estrategico(result.reset_index(drop=True))

    def preparar_pdi_marco_con_cierre(self, anio: int, mes: int, version_id: str) -> pd.DataFrame:
        """Indicadores ESTRATÉGICOS (PDI = 1) de un PDI con hoja propia (p. ej. PDI 2026-2030),
        con su línea/objetivo/meta de esa hoja y el último cierre hasta el corte. Análogo a
        preparar_pdi_con_cierre, que sigue siendo el camino del PDI 2022-2026."""
        indicadores = self._loaders.load_indicadores_pdi(version_id)
        cierres = self._loaders.load_cierres()
        if indicadores.empty or cierres.empty:
            return pd.DataFrame()
        indicadores = indicadores[indicadores["PDI"] == 1].copy()
        if indicadores.empty:
            return pd.DataFrame()
        indicadores["Id"] = indicadores["Id"].apply(_normalize_id_value)
        # RN-21: un PDI con hoja propia solo mide dentro de su año. Un indicador anual sin cierre
        # en el año elegido queda «Pendiente de reporte»; NO se arrastra el valor de 2025 (eso
        # solo lo hace Indicadores POLISIGS).
        if "Anio" in cierres.columns:
            cierres = cierres[pd.to_numeric(cierres["Anio"], errors="coerce") == int(anio)]
        cierres_cut = cierre_por_corte(cierres, anio, mes)
        if not cierres_cut.empty:
            cierres_cut["Id"] = cierres_cut["Id"].apply(_normalize_id_value)
        else:
            cierres_cut = pd.DataFrame({"Id": []})
        result = indicadores[["Id", "Indicador", "Linea", "Objetivo", "Meta_Estrategica"]].merge(
            cierres_cut, on="Id", how="left", suffixes=("", "_cierre")
        )
        if "Indicador_cierre" in result.columns:
            result["Indicador"] = result["Indicador"].where(
                result["Indicador"].notna() & (result["Indicador"].astype(str).str.strip() != ""),
                result["Indicador_cierre"],
            )
            result = result.drop(columns=["Indicador_cierre"])
        if "Nivel de cumplimiento" not in result.columns:
            result["Nivel de cumplimiento"] = PENDIENTE_STR
        result["Nivel de cumplimiento"] = result["Nivel de cumplimiento"].fillna(PENDIENTE_STR)
        return result.reset_index(drop=True)

    def _acumular_ingresos_ciclo(self, cierre_pdi: pd.DataFrame, anios: Sequence[int]) -> pd.DataFrame:
        """Reemplaza Meta/Ejecución de los indicadores de ingresos por la suma de los cierres de
        diciembre de cada año del ciclo (solo años con meta y ejecución reportadas) y recalcula
        su cumplimiento."""
        cierres = self._loaders.load_cierres()
        if cierres.empty or not {"Id", "Anio", "Mes", "Meta", "Ejecucion"}.issubset(cierres.columns):
            return cierre_pdi
        c = cierres.copy()
        c["Id"] = c["Id"].apply(_normalize_id_value)
        c = c[
            c["Id"].isin(IDS_INGRESOS_ACUMULADOS)
            & (pd.to_numeric(c["Mes"], errors="coerce") == 12)
            & pd.to_numeric(c["Anio"], errors="coerce").isin([int(a) for a in anios])
            & c["Meta"].notna()
            & c["Ejecucion"].notna()
        ].drop_duplicates(subset=["Id", "Anio"], keep="last")
        if c.empty:
            return cierre_pdi
        sumas = c.groupby("Id")[["Meta", "Ejecucion"]].sum()
        out = cierre_pdi.copy()
        for id_, row in sumas.iterrows():
            m = out["Id"] == id_
            if not m.any():
                continue
            out.loc[m, "Meta"] = row["Meta"]
            out.loc[m, "Ejecucion"] = row["Ejecucion"]
            sentido = out.loc[m, "Sentido"].iloc[0] if "Sentido" in out.columns else "Positivo"
            dec = recalcular_cumplimiento_faltante(row["Meta"], row["Ejecucion"], sentido, id_)
            out.loc[m, "cumplimiento_dec"] = dec
            out.loc[m, "cumplimiento_pct"] = dec * 100 if dec is not None and not pd.isna(dec) else pd.NA
            out.loc[m, "Nivel de cumplimiento"] = (
                categorizar_cumplimiento(dec, id_indicador=id_)
                if dec is not None and not pd.isna(dec)
                else PENDIENTE
            )
        return out

    def preparar_pdi_cierre_final(
        self, hoja: str = "Cierre PDI", anios: Sequence[int] | None = None
    ) -> pd.DataFrame:
        """Resultado final por indicador (hoja 'Cierre PDI'), para el rango
        "Cierre PDI 2022-2025" — a diferencia de preparar_pdi_con_cierre, no
        arrastra el ultimo valor disponible de anios anteriores cuando un
        indicador no tiene resultado final cargado."""
        base = self._loaders.load_worksheet_flags()
        catalog = self._loaders.load_pdi_catalog()
        cierre_pdi = self._loaders.load_cierre_pdi_final(hoja)
        if base.empty or cierre_pdi.empty:
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
        cierre_pdi = cierre_pdi.copy()
        cierre_pdi["Id"] = cierre_pdi["Id"].apply(_normalize_id_value)
        if anios is not None and len(anios) > 1:
            cierre_pdi = self._acumular_ingresos_ciclo(cierre_pdi, anios)

        # Solo indicadores con resultado final registrado en la hoja Cierre PDI
        # (inner join, no left) — evita mostrar indicadores sin cierre real.
        result = indicators[merge_cols].merge(
            cierre_pdi, on="Id", how="inner", suffixes=("", "_cierre")
        )
        if "Indicador_cierre" in result.columns:
            result["Indicador"] = result["Indicador"].where(
                result["Indicador"].notna() & (result["Indicador"].astype(str).str.strip() != ""),
                result["Indicador_cierre"],
            )
            result = result.drop(columns=["Indicador_cierre"])

        if not catalog.empty and "Linea" in result.columns and "Objetivo" in result.columns:
            result = result.merge(
                catalog, on=["Linea", "Objetivo"], how="left", suffixes=("", "_cat")
            )

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

        result = indicators[merge_cols].merge(
            cierres_cut, on="Id", how="left", suffixes=("", "_cierre")
        )
        if "Indicador_cierre" in result.columns:
            result["Indicador"] = result["Indicador"].where(
                result["Indicador"].notna() & (result["Indicador"].astype(str).str.strip() != ""),
                result["Indicador_cierre"],
            )
            result = result.drop(columns=["Indicador_cierre"])

        if not catalog.empty and "Factor" in result.columns and "Caracteristica" in result.columns:
            result = result.merge(
                catalog, on=["Factor", "Caracteristica"], how="left", suffixes=("", "_cat")
            )

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
