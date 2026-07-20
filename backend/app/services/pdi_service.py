"""Servicio PDI/Acreditación — paridad streamlit_app/pages/pdi_acreditacion.py."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.domain.categorization import categorizar_cumplimiento
from app.domain.linea_order import linea_sort_key
from app.services.excel_reader import ExcelReaderService
from app.services.tracking_cache import get_tracking_dataframe

NIVEL_COLOR: dict[str, str] = {
    "Sobrecumplimiento": "#3b82f6",
    "Cumplimiento": "#22c55e",
    "Alerta": "#f59e0b",
    "Peligro": "#ef4444",
    "Sin dato": "#94a3b8",
}

ESTADOS_DEFAULT = ["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"]
MACROS_DEFAULT = ["Docencia", "Investigación", "Extensión", "Gobierno"]
HORIZONTES_DEFAULT = ["2026-1", "2026-2", "2027-1"]

# Desde la fusión 2026-07-14, el catálogo de clasificación vive en la hoja
# "Catalogo Indicadores" del directorio maestro dedicado (Catalogo de
# Indicadores.xlsx), no en 'Indicadores por CMI.xlsx' (archivado en
# data/raw/_archivados/).
_CNA_PATHS = [
    "raw/Catalogo de Indicadores.xlsx",
]
_CNA_SHEET = "Catalogo Indicadores"


def _classify_estado(cumpl_pct: float | None, id_indicador: Any = None) -> str:
    fraccion = cumpl_pct / 100 if pd.notna(cumpl_pct) else cumpl_pct
    return categorizar_cumplimiento(fraccion, id_indicador=id_indicador)


class PDIService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel

    def _load_df(self) -> pd.DataFrame:
        try:
            df = get_tracking_dataframe(self._excel)
        except Exception:
            return pd.DataFrame()
        if df.empty:
            return df

        if "Clasificacion" not in df.columns:
            return pd.DataFrame()
        df = df[df["Clasificacion"].str.contains("acredit", case=False, na=False)].copy()
        if df.empty:
            return df

        # Enrich with directorio maestro (Catalogo Indicadores) for Linea/Objetivo columns
        for path in _CNA_PATHS:
            try:
                df_cna = self._excel.read_excel(path, sheet_name=_CNA_SHEET)
                df_cna = df_cna.rename(columns={
                    "Linea_Estrategica": "Linea", "Objetivo_Estrategico": "Objetivo",
                })
                for col in ["Linea", "Objetivo"]:
                    if col not in df.columns and col in df_cna.columns and "Id" in df_cna.columns:
                        df = df.merge(df_cna[["Id", col]].drop_duplicates("Id"), on="Id", how="left")
                break
            except Exception:
                continue

        # Compute cumplimiento_pct
        col_cumpl = None
        for c in ["Cumplimiento_norm", "Cumplimiento", "cumplimiento_norm", "cumplimiento"]:
            if c in df.columns:
                col_cumpl = c
                break
        if col_cumpl:
            raw = pd.to_numeric(df[col_cumpl], errors="coerce")
            if raw.dropna().max() <= 1.5:
                df["cumplimiento_pct"] = (raw * 100).round(1)
            else:
                df["cumplimiento_pct"] = raw.round(1)
        else:
            df["cumplimiento_pct"] = None

        # Brecha
        if "Meta" in df.columns and "Ejecucion" in df.columns:
            df["brecha"] = (
                pd.to_numeric(df["Meta"], errors="coerce")
                - pd.to_numeric(df["Ejecucion"], errors="coerce")
            )
        else:
            df["brecha"] = None

        # Classify estado (misma escala/umbrales que categorizar_cumplimiento central)
        id_col = df["Id"] if "Id" in df.columns else pd.Series([None] * len(df), index=df.index)
        df["Estado"] = [
            _classify_estado(cumpl, id_ind) for cumpl, id_ind in zip(df["cumplimiento_pct"], id_col)
        ]

        return df

    def get_filtros(self) -> dict[str, Any]:
        try:
            df = self._load_df()
        except Exception:
            df = pd.DataFrame()

        horizontes = (
            sorted(df["Periodo"].dropna().astype(str).unique().tolist())
            if not df.empty and "Periodo" in df.columns
            else HORIZONTES_DEFAULT
        )
        macros = (
            sorted(df["Linea"].dropna().astype(str).unique().tolist(), key=linea_sort_key)
            if not df.empty and "Linea" in df.columns
            else MACROS_DEFAULT
        )
        return {
            "estados": ESTADOS_DEFAULT,
            "macros": macros or MACROS_DEFAULT,
            "horizontes": horizontes or HORIZONTES_DEFAULT,
            "horizonte_default": horizontes[0] if horizontes else "2026-1",
        }

    def get_dashboard(
        self,
        *,
        estado: str | None = None,
        macro: str | None = None,
        horizonte: str | None = None,
    ) -> dict[str, Any]:
        filtros_vacio: dict[str, Any] = {
            "estados": ESTADOS_DEFAULT,
            "macros": MACROS_DEFAULT,
            "horizontes": HORIZONTES_DEFAULT,
            "horizonte_default": "2026-1",
        }

        try:
            df = self._load_df()
        except Exception as exc:
            return {
                "error": f"Error cargando datos: {exc}",
                "filtros": filtros_vacio,
                "kpis": {"total": 0, "cumplimiento_promedio": None, "brecha_promedio": None},
                "treemap": [],
                "benchmark": [],
                "evolucion_brechas": [],
                "tabla": [],
            }

        if df.empty:
            return {
                "error": "No hay datos de acreditación disponibles.",
                "filtros": filtros_vacio,
                "kpis": {"total": 0, "cumplimiento_promedio": None, "brecha_promedio": None},
                "treemap": [],
                "benchmark": [],
                "evolucion_brechas": [],
                "tabla": [],
            }

        filtros = self.get_filtros()

        # Apply filters
        df_f = df.copy()
        if estado and estado != "Todos":
            df_f = df_f[df_f["Estado"] == estado]
        if macro and macro != "Todos" and "Linea" in df_f.columns:
            df_f = df_f[df_f["Linea"].astype(str) == macro]
        if horizonte and "Periodo" in df_f.columns:
            df_f = df_f[df_f["Periodo"].astype(str) == horizonte]

        # KPIs
        cumpl_s = pd.to_numeric(df_f.get("cumplimiento_pct", pd.Series(dtype=float)), errors="coerce")
        brecha_s = pd.to_numeric(df_f.get("brecha", pd.Series(dtype=float)), errors="coerce")
        kpis: dict[str, Any] = {
            "total": len(df_f),
            "cumplimiento_promedio": round(float(cumpl_s.mean()), 1) if cumpl_s.notna().any() else None,
            "brecha_promedio": round(float(brecha_s.mean()), 1) if brecha_s.notna().any() else None,
        }

        # Treemap: Macrolinea → Objetivo → Indicador
        treemap: list[dict[str, Any]] = []
        has_linea = "Linea" in df_f.columns
        has_obj = "Objetivo" in df_f.columns
        if has_linea and has_obj:
            for macro_val, gm in df_f.groupby("Linea", dropna=True):
                treemap.append({"id": str(macro_val), "label": str(macro_val), "parent": "", "value": len(gm)})
                for obj_val, go in gm.groupby("Objetivo", dropna=True):
                    node_id = f"{macro_val}||{obj_val}"
                    treemap.append(
                        {"id": node_id, "label": str(obj_val)[:60], "parent": str(macro_val), "value": len(go)}
                    )
                    for _, row in go.iterrows():
                        ind_id = str(row.get("Id", ""))
                        ind_label = f"{ind_id}: {str(row.get('Indicador', ''))[:40]}"
                        cumpl_val = row.get("cumplimiento_pct")
                        estado_str = str(row.get("Estado", "Sin dato"))
                        treemap.append({
                            "id": ind_id or f"{node_id}||{ind_label}",
                            "label": ind_label,
                            "parent": node_id,
                            "value": 1,
                            "color": NIVEL_COLOR.get(estado_str, "#94a3b8"),
                            "color_value": (
                                round(float(cumpl_val), 1)
                                if cumpl_val is not None and not (isinstance(cumpl_val, float) and pd.isna(cumpl_val))
                                else None
                            ),
                        })

        # Benchmark by Proceso
        benchmark: list[dict[str, Any]] = []
        proc_col = "Proceso" if "Proceso" in df_f.columns else None
        if proc_col and "cumplimiento_pct" in df_f.columns:
            for proc, gp in df_f.groupby(proc_col, dropna=True):
                c_series = pd.to_numeric(gp["cumplimiento_pct"], errors="coerce")
                if c_series.notna().any():
                    c_mean = round(float(c_series.mean()), 1)
                    benchmark.append({
                        "proceso": str(proc),
                        "cumplimiento": c_mean,
                        "benchmark": round(c_mean - 5, 1),
                    })

        # Evolución brechas
        evolucion: list[dict[str, Any]] = []
        if "Periodo" in df_f.columns and proc_col and "brecha" in df_f.columns:
            for (per, proc), g in df_f.groupby(["Periodo", proc_col], dropna=True):
                b_series = pd.to_numeric(g["brecha"], errors="coerce")
                if b_series.notna().any():
                    evolucion.append({
                        "periodo": str(per),
                        "proceso": str(proc),
                        "brecha": round(float(b_series.mean()), 1),
                    })

        # Tabla
        tabla_cols = ["Id", "Indicador", "Linea", "Objetivo", "cumplimiento_pct", "Meta", "Ejecucion", "Meta_Signo", "Ejecucion_s", "EjecS", "Decimales_Meta", "Decimales_Ejecucion", "Estado", "brecha"]
        tabla: list[dict[str, Any]] = []
        for _, row in df_f.iterrows():
            rec: dict[str, Any] = {}
            for c in tabla_cols:
                v = row.get(c)
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    rec[c] = None
                elif isinstance(v, float):
                    rec[c] = round(v, 2)
                elif isinstance(v, int):
                    rec[c] = v
                else:
                    rec[c] = str(v)
            rec["estado_color"] = NIVEL_COLOR.get(str(row.get("Estado", "Sin dato")), "#94a3b8")
            tabla.append(rec)

        return {
            "error": None,
            "filtros": filtros,
            "filtros_aplicados": {
                "estado": estado or "Todos",
                "macro": macro or "Todos",
                "horizonte": horizonte or "",
            },
            "kpis": kpis,
            "treemap": treemap,
            "benchmark": benchmark,
            "evolucion_brechas": evolucion,
            "tabla": tabla,
        }
