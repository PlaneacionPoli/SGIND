"""Pipeline ETL 5 fases — portado desde services/loaders/pipeline.py."""

import pandas as pd

from app.domain.loader_utils import id_a_str, obtener_rename_map, renombrar_columnas
from app.services.excel_reader import ExcelReaderService

_CONSOLIDADO_CANDIDATES = [
    "output/Resultados Consolidados.xlsx",
    "output/Resultados Consolidados VALORES.xlsx",
]

# Desde la fusión 2026-07-14, la clasificación de negocio vive en la hoja
# "Catalogo Indicadores" del directorio maestro dedicado (Catalogo de
# Indicadores.xlsx), no en 'Indicadores por CMI.xlsx' (archivado en
# data/raw/_archivados/).
_CMI_CANDIDATES = [
    "raw/Catalogo de Indicadores.xlsx",
]
_CMI_SHEET = "Catalogo Indicadores"

_MESES_ES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


class ETLPipelineService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel

    def _resolve_consolidado(self) -> str:
        for candidate in _CONSOLIDADO_CANDIDATES:
            if (self._excel.data_root / candidate).exists():
                return candidate
        raise FileNotFoundError("No se encontró Resultados Consolidados.xlsx")

    def _resolve_cmi(self) -> str | None:
        for candidate in _CMI_CANDIDATES:
            if (self._excel.data_root / candidate).exists():
                return candidate
        return None

    def ejecutar(
        self,
        *,
        historico: bool = False,
        relative_path: str | None = None,
        sheet: str | None = None,
    ) -> pd.DataFrame:
        path = relative_path or self._resolve_consolidado()
        df = self._fase1_leer_path(path, historico=historico, sheet=sheet)
        df = self.fase2_clasificacion(df, path)
        df = self.fase3_cmi(df)
        df = self.fase4_fechas(df)
        from app.domain.calculos import aplicar_calculos_cumplimiento

        df = aplicar_calculos_cumplimiento(df)
        anio_col = "Anio" if "Anio" in df.columns else ("Año" if "Año" in df.columns else None)
        if anio_col:
            df["Anio"] = pd.to_numeric(df[anio_col], errors="coerce").astype("Int64")
        return df

    def leer_cierres(self) -> pd.DataFrame:
        return self.ejecutar(sheet="Consolidado Cierres")

    def _fase1_leer_path(self, relative: str, *, historico: bool, sheet: str | None = None) -> pd.DataFrame:
        if sheet is None:
            sheet = "Consolidado Historico" if historico else "Consolidado Semestral"
        try:
            df = self._excel.read_excel(relative, sheet_name=sheet)
        except (ValueError, KeyError):
            df = self._excel.read_excel(relative)
        df = renombrar_columnas(df, obtener_rename_map())
        if "Id" in df.columns:
            df["Id"] = df["Id"].apply(id_a_str)
        return df

    def fase2_clasificacion(self, df: pd.DataFrame, path: str) -> pd.DataFrame:
        if "Clasificacion" in df.columns:
            return df
        try:
            df_cat = self._excel.read_excel(path, sheet_name="Catalogo Indicadores")
            df_cat = renombrar_columnas(df_cat, obtener_rename_map())
            df_cat["Id"] = df_cat["Id"].apply(id_a_str)
            cols = ["Id"] + [c for c in ["Clasificacion"] if c in df_cat.columns]
            if len(cols) > 1:
                df = df.merge(df_cat[cols].drop_duplicates("Id"), on="Id", how="left")
        except Exception:
            pass
        return df

    def fase3_cmi(self, df: pd.DataFrame) -> pd.DataFrame:
        cmi_path = self._resolve_cmi()
        if not cmi_path:
            return df
        try:
            df_cmi = self._excel.read_excel(cmi_path, sheet_name=_CMI_SHEET)
            df_cmi = renombrar_columnas(df_cmi, obtener_rename_map())
            df_cmi = df_cmi.rename(columns={
                "Linea_Estrategica": "Linea", "Objetivo_Estrategico": "Objetivo",
            })
            if "Id" not in df_cmi.columns:
                return df
            df_cmi["Id"] = df_cmi["Id"].apply(id_a_str)
            cols = ["Id"] + [c for c in ["Subproceso", "Linea", "Objetivo"] if c in df_cmi.columns]
            if len(cols) > 1:
                df = df.merge(df_cmi[cols].drop_duplicates("Id"), on="Id", how="left")
        except Exception:
            pass
        return df

    def fase4_fechas(self, df: pd.DataFrame) -> pd.DataFrame:
        if "Fecha" not in df.columns:
            return df

        fecha = pd.to_datetime(df["Fecha"], errors="coerce")
        if "Anio" in df.columns:
            df["Anio"] = df["Anio"].fillna(fecha.dt.year)
        elif "Año" in df.columns:
            df["Año"] = df["Año"].fillna(fecha.dt.year)

        if "Mes" in df.columns:
            df["Mes"] = df["Mes"].where(
                df["Mes"].notna() & (df["Mes"] != ""),
                fecha.dt.month.map(_MESES_ES),
            )

        periodo_calc = (
            fecha.dt.year.astype("Int64").astype(str)
            + "-"
            + fecha.dt.month.apply(lambda m: "1" if m <= 6 else "2")
        )
        if "Periodo" in df.columns:
            df["Periodo"] = df["Periodo"].where(
                df["Periodo"].notna() & (df["Periodo"] != ""),
                periodo_calc,
            )
        else:
            df["Periodo"] = periodo_calc
        return df
