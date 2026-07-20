"""Cargadores estratégicos — portado desde services/strategic_indicators/loaders.py."""

from __future__ import annotations

import pandas as pd

from app.domain.categorization import categorizar_cumplimiento
from app.domain.health_metrics import recalcular_cumplimiento_faltante
from app.domain.loader_utils import find_col, id_a_str, repair_linea_encoding
from app.services.excel_reader import ExcelReaderService

PENDIENTE = "Pendiente de reporte"
NO_APLICA = "No aplica"
METRICA = "metrica"

# Desde la fusión 2026-07-14, la clasificación de negocio vive en la hoja
# "Catalogo Indicadores" del directorio maestro dedicado (Catalogo de
# Indicadores.xlsx), no en 'Indicadores por CMI.xlsx' (archivado en
# data/raw/_archivados/).
_CMI_PATHS = [
    "raw/Catalogo de Indicadores.xlsx",
]
_CMI_SHEET = "Catalogo Indicadores"
_CONSOLIDADO_PATHS = [
    "output/Resultados Consolidados.xlsx",
    "output/Resultados Consolidados VALORES.xlsx",
]
# El ETL de output/ excluye IDs de proyectos; la fuente raw los conserva (legacy loaders.py).
_PROYECTOS_CONSOLIDADO_PATHS = [
    "raw/Resultados_Consolidados_Fuente.xlsx",
    *_CONSOLIDADO_PATHS,
]


class StrategicLoaders:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel
        self._cache: dict[str, pd.DataFrame] = {}

    def _resolve_cmi(self) -> str | None:
        for p in _CMI_PATHS:
            if (self._excel.data_root / p).exists():
                return p
        return None

    def _resolve_consolidado(self) -> str | None:
        for p in _CONSOLIDADO_PATHS:
            if (self._excel.data_root / p).exists():
                return p
        return None

    def _resolve_proyectos_consolidado(self) -> str | None:
        for p in _PROYECTOS_CONSOLIDADO_PATHS:
            if (self._excel.data_root / p).exists():
                return p
        return None

    def _cached(self, key: str, loader) -> pd.DataFrame:
        if key not in self._cache:
            self._cache[key] = loader()
        return self._cache[key]

    def load_worksheet_flags(self) -> pd.DataFrame:
        def _load() -> pd.DataFrame:
            path = self._resolve_cmi()
            if not path:
                return pd.DataFrame()
            try:
                df = self._excel.read_excel(path, sheet_name=_CMI_SHEET)
            except Exception:
                return pd.DataFrame()
            df.columns = [str(c).strip() for c in df.columns]
            c_id = find_col(df, ["Id", "ID"])
            c_ind = find_col(df, ["Indicador"])
            c_linea = find_col(df, ["Linea", "Línea", "LINEA", "LÍNEA", "Linea estrategica", "Linea_Estrategica"])
            c_obj = find_col(df, ["Objetivo", "OBJETIVO", "Objetivo_Estrategico"])
            c_plan = find_col(df, ["Indicadores Plan estrategico", "Indicadores_Plan_Estrategico"])
            c_proyecto = find_col(df, ["Proyecto", "PROYECTO"])
            c_factor = find_col(df, ["FACTOR", "Factor"])
            c_car = find_col(df, ["CARACTERISTICA", "Caracteristica", "CARACTERÍSTICA"])
            c_cna = find_col(df, ["Indicadores CNA", "FlagCNA", "CNA", "CNA_SNIES"])
            if not c_id:
                return pd.DataFrame()
            cols = [c for c in [c_id, c_ind, c_linea, c_obj, c_plan, c_proyecto, c_factor, c_car, c_cna] if c]
            out = df[cols].copy()
            rename = {c_id: "Id", c_ind: "Indicador", c_linea: "Linea", c_obj: "Objetivo"}
            if c_plan:
                rename[c_plan] = "FlagPlanEstrategico"
            if c_proyecto:
                rename[c_proyecto] = "Proyecto"
            if c_factor:
                rename[c_factor] = "Factor"
            if c_car:
                rename[c_car] = "Caracteristica"
            if c_cna:
                rename[c_cna] = "FlagCNA"
            out = out.rename(columns=rename)
            if "Linea" in out.columns:
                out["Linea"] = repair_linea_encoding(out["Linea"])
            return out

        return self._cached("worksheet_flags", _load)

    def load_cna_catalog(self) -> pd.DataFrame:
        def _load() -> pd.DataFrame:
            path = self._resolve_cmi()
            if not path:
                return pd.DataFrame(columns=["Factor", "Caracteristica"])
            try:
                df = self._excel.read_excel(path, sheet_name=_CMI_SHEET)
            except Exception:
                return pd.DataFrame(columns=["Factor", "Caracteristica"])
            df.columns = [str(c).strip() for c in df.columns]
            c_factor = find_col(df, ["FACTOR", "Factor"])
            c_car = find_col(df, ["CARACTERISTICA", "Caracteristica", "CARACTERÍSTICA"])
            if not c_factor or not c_car:
                return pd.DataFrame(columns=["Factor", "Caracteristica"])
            out = df[[c_factor, c_car]].copy().rename(columns={c_factor: "Factor", c_car: "Caracteristica"})
            out["Factor"] = out["Factor"].astype(str).str.strip()
            out["Caracteristica"] = out["Caracteristica"].astype(str).str.strip()
            out = out[(out["Factor"] != "") & (out["Caracteristica"] != "")]
            out["Caracteristica"] = out["Caracteristica"].replace("nan", "")
            return out.drop_duplicates().reset_index(drop=True)

        return self._cached("cna_catalog", _load)

    def load_pdi_catalog(self) -> pd.DataFrame:
        def _load() -> pd.DataFrame:
            path = self._resolve_cmi()
            if not path:
                return pd.DataFrame(columns=["Linea", "Objetivo", "Meta_Estrategica"])
            try:
                df = self._excel.read_excel(path, sheet_name=_CMI_SHEET)
            except Exception:
                return pd.DataFrame(columns=["Linea", "Objetivo", "Meta_Estrategica"])
            df.columns = [str(c).strip() for c in df.columns]
            c_linea = find_col(df, ["Linea", "Línea", "LINEA", "Linea_Estrategica"])
            c_obj = find_col(df, ["Objetivo", "OBJETIVO", "Objetivo_Estrategico"])
            c_meta = find_col(df, ["Meta Estratégica", "META ESTRATEGICA", "Meta estrategica", "Meta_Estrategica"])
            if not c_linea or not c_obj:
                return pd.DataFrame(columns=["Linea", "Objetivo", "Meta_Estrategica"])
            cols = [c_linea, c_obj] + ([c_meta] if c_meta else [])
            out = df[cols].copy().rename(columns={c_linea: "Linea", c_obj: "Objetivo"})
            if c_meta:
                out = out.rename(columns={c_meta: "Meta_Estrategica"})
            else:
                out["Meta_Estrategica"] = ""
            out["Linea"] = repair_linea_encoding(out["Linea"].astype(str).str.strip())
            out["Objetivo"] = out["Objetivo"].astype(str).str.strip()
            return out.drop_duplicates(subset=["Linea", "Objetivo"])

        return self._cached("pdi_catalog", _load)

    def load_cierres(self) -> pd.DataFrame:
        def _load() -> pd.DataFrame:
            path = self._resolve_consolidado()
            if not path:
                return pd.DataFrame()
            for sheet in ("Cierre historico", "Consolidado Cierres"):
                try:
                    df = self._excel.read_excel(path, sheet_name=sheet)
                    break
                except (ValueError, KeyError):
                    df = None
            if df is None:
                return pd.DataFrame()

            df.columns = [str(c).strip() for c in df.columns]
            c_id = find_col(df, ["Id", "ID"])
            if not c_id:
                return pd.DataFrame()

            out = pd.DataFrame()
            out["Id"] = df[c_id].apply(id_a_str)
            for src, dst, transform in [
                (find_col(df, ["Indicador"]), "Indicador", lambda s: s.astype(str).str.strip()),
                (find_col(df, ["Fecha"]), "Fecha", lambda s: pd.to_datetime(s, errors="coerce")),
                (find_col(df, ["Año", "Anio"]), "Anio", lambda s: pd.to_numeric(s, errors="coerce")),
                (find_col(df, ["Mes"]), "Mes", lambda s: pd.to_numeric(s, errors="coerce")),
                (find_col(df, ["Meta"]), "Meta", lambda s: pd.to_numeric(s, errors="coerce")),
                (find_col(df, ["Ejecucion", "Ejecución"]), "Ejecucion", lambda s: pd.to_numeric(s, errors="coerce")),
                (find_col(df, ["Sentido"]), "Sentido", lambda s: s.astype(str).str.strip()),
                (find_col(df, ["Tipo_Registro", "Tipo Registro"]), "Tipo_Registro", lambda s: s.astype(str).str.strip()),
                (find_col(df, ["Linea", "Línea"]), "Linea", lambda s: repair_linea_encoding(s.astype(str).str.strip())),
                (find_col(df, ["Objetivo"]), "Objetivo", lambda s: s.astype(str).str.strip()),
                (find_col(df, ["Meta_Signo", "MetaS", "meta_signo"]), "Meta_Signo", lambda s: s.astype(str).str.strip()),
                (find_col(df, ["Ejecucion_Signo", "Ejecucion_s", "EjecS", "ejec_signo"]), "Ejecucion_s", lambda s: s.astype(str).str.strip()),
                (find_col(df, ["Decimales_Meta"]), "Decimales_Meta", lambda s: pd.to_numeric(s, errors="coerce")),
                (find_col(df, ["Decimales_Ejecucion"]), "Decimales_Ejecucion", lambda s: pd.to_numeric(s, errors="coerce")),
            ]:
                if src:
                    out[dst] = transform(df[src])
            out = out[out["Id"] != ""].copy()
            if "Fecha" in out.columns:
                out.loc[out["Anio"].isna(), "Anio"] = out.loc[out["Anio"].isna(), "Fecha"].dt.year
                out.loc[out["Mes"].isna(), "Mes"] = out.loc[out["Mes"].isna(), "Fecha"].dt.month

            c_cumpl = find_col(df, ["Cumplimiento", "cumplimiento_dec"])
            out["cumplimiento_dec"] = pd.to_numeric(df[c_cumpl], errors="coerce") if c_cumpl else pd.NA
            mask = out["cumplimiento_dec"].isna() & out["Meta"].notna() & out["Ejecucion"].notna()
            if mask.any():
                out.loc[mask, "cumplimiento_dec"] = out.loc[mask].apply(
                    lambda r: recalcular_cumplimiento_faltante(
                        r["Meta"], r["Ejecucion"], r.get("Sentido", "Positivo"), r.get("Id")
                    ),
                    axis=1,
                )
            out["cumplimiento_pct"] = pd.to_numeric(out["cumplimiento_dec"], errors="coerce") * 100
            if "Tipo_Registro" in out.columns:
                es_metrica = out["Tipo_Registro"].astype(str).str.lower() == METRICA
            else:
                es_metrica = pd.Series(False, index=out.index)
            out["Nivel de cumplimiento"] = out.apply(
                lambda r: categorizar_cumplimiento(r["cumplimiento_dec"], id_indicador=r.get("Id")),
                axis=1,
            )
            out.loc[es_metrica, "Nivel de cumplimiento"] = NO_APLICA
            out.loc[out["cumplimiento_pct"].isna() & ~es_metrica, "Nivel de cumplimiento"] = PENDIENTE
            return out.reset_index(drop=True)

        return self._cached("cierres", _load)

    def load_proyectos_consolidados(self) -> pd.DataFrame:
        """Consolidado Cierres con IDs de proyectos (fuente raw, no output ETL)."""

        def _load() -> pd.DataFrame:
            path = self._resolve_proyectos_consolidado()
            if not path:
                return pd.DataFrame()
            try:
                df = self._excel.read_excel(path, sheet_name="Consolidado Cierres")
            except (ValueError, KeyError):
                return pd.DataFrame()

            df.columns = [str(c).strip() for c in df.columns]
            c_id = find_col(df, ["Id", "ID"])
            if not c_id:
                return pd.DataFrame()

            out = pd.DataFrame()
            out["Id"] = df[c_id].apply(id_a_str)
            for src, dst, transform in [
                (find_col(df, ["Indicador"]), "Indicador", lambda s: s.astype(str).str.strip()),
                (find_col(df, ["Linea", "Línea"]), "Linea", lambda s: repair_linea_encoding(s.astype(str).str.strip())),
                (find_col(df, ["Objetivo"]), "Objetivo", lambda s: s.astype(str).str.strip()),
                (find_col(df, ["Fecha"]), "Fecha", pd.to_datetime),
                (find_col(df, ["Año", "Anio"]), "Anio", lambda s: pd.to_numeric(s, errors="coerce")),
                (find_col(df, ["Mes"]), "Mes", lambda s: pd.to_numeric(s, errors="coerce")),
                (find_col(df, ["Meta"]), "Meta", lambda s: pd.to_numeric(s, errors="coerce")),
                (find_col(df, ["Ejecucion", "Ejecución"]), "Ejecucion", lambda s: pd.to_numeric(s, errors="coerce")),
                (find_col(df, ["Sentido"]), "Sentido", lambda s: s.astype(str).str.strip()),
                (find_col(df, ["Tipo_Registro", "Tipo Registro"]), "Tipo_Registro", lambda s: s.astype(str).str.strip()),
            ]:
                if src:
                    out[dst] = transform(df[src])

            c_cumpl = find_col(df, ["Cumplimiento", "cumplimiento_dec"])
            out["cumplimiento_dec"] = pd.to_numeric(df[c_cumpl], errors="coerce") if c_cumpl else pd.NA
            mask = out["cumplimiento_dec"].isna() & out["Meta"].notna() & out["Ejecucion"].notna()
            if mask.any():
                out.loc[mask, "cumplimiento_dec"] = out.loc[mask].apply(
                    lambda r: recalcular_cumplimiento_faltante(
                        r["Meta"], r["Ejecucion"], r.get("Sentido", "Positivo"), r.get("Id")
                    ),
                    axis=1,
                )
            out["cumplimiento_pct"] = pd.to_numeric(out["cumplimiento_dec"], errors="coerce") * 100
            out["Nivel de cumplimiento"] = out.apply(
                lambda r: categorizar_cumplimiento(r["cumplimiento_dec"], id_indicador=r.get("Id")),
                axis=1,
            )
            if "Tipo_Registro" in out.columns:
                es_metrica = out["Tipo_Registro"].astype(str).str.lower() == METRICA
                out.loc[es_metrica, "Nivel de cumplimiento"] = NO_APLICA
                pend_mask = out["cumplimiento_pct"].isna() & ~es_metrica
            else:
                pend_mask = out["cumplimiento_pct"].isna()
            out.loc[pend_mask, "Nivel de cumplimiento"] = PENDIENTE
            return out[out["Id"] != ""].reset_index(drop=True)

        return self._cached("proyectos_consolidados", _load)

    def load_proyectos(self) -> pd.DataFrame:
        consolidado = self.load_proyectos_consolidados()
        if consolidado.empty:
            consolidado = self.load_cierres()
        if consolidado.empty:
            return consolidado
        from app.domain.cmi_filters import CMIFilterService

        df = CMIFilterService(self._excel).filter_proyectos(consolidado)
        return self._enrich_with_worksheet(df)

    def _enrich_with_worksheet(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "Id" not in df.columns:
            return df
        ws = self.load_worksheet_flags()
        if ws.empty or "Linea" not in ws.columns:
            return df
        merge_cols = ["Id"] + [c for c in ["Linea", "Objetivo", "Indicador"] if c in ws.columns]
        base = ws[merge_cols].drop_duplicates("Id")
        out = df.copy()
        out["Id"] = out["Id"].apply(id_a_str)
        base["Id"] = base["Id"].apply(id_a_str)
        out = out.merge(base, on="Id", how="left", suffixes=("_src", "_cmi"))
        for col in ["Linea", "Objetivo", "Indicador"]:
            src_col = f"{col}_src"
            cmi_col = f"{col}_cmi"
            if cmi_col not in out.columns:
                continue
            if src_col in out.columns:
                mask = out[cmi_col].notna() & (out[cmi_col].astype(str).str.strip() != "")
                out.loc[mask, src_col] = out.loc[mask, cmi_col]
                out[col] = out[src_col]
                out = out.drop(columns=[src_col, cmi_col])
            else:
                out[col] = out[cmi_col]
                out = out.drop(columns=[cmi_col])
        for col in list(out.columns):
            if col.endswith("_cmi") or col.endswith("_src"):
                out = out.drop(columns=[col])
        return out
