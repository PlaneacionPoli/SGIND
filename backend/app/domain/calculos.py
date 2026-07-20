"""Lógica de negocio — portado desde core/calculos.py y services/loaders/pipeline.py fase5."""

import logging

import numpy as np
import pandas as pd

from app.domain.categorization import categorizar_cumplimiento
from app.domain.constants import RANGO_CUMPLIMIENTO_MAX, RANGO_CUMPLIMIENTO_MIN
from app.domain.health_metrics import recalcular_cumplimiento_faltante
from app.domain.loader_utils import find_col

logger = logging.getLogger(__name__)


def normalizar_cumplimiento(valor) -> float:
    try:
        if pd.isna(valor):
            return np.nan
    except (ValueError, TypeError):
        return np.nan

    if isinstance(valor, str):
        valor_clean = valor.replace("%", "").strip()
        if "," in valor_clean:
            valor_clean = valor_clean.replace(".", "").replace(",", ".")
        try:
            valor = float(valor_clean)
        except ValueError:
            return np.nan

    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return np.nan

    # Escala porcentaje 0–100 → decimal
    if valor > RANGO_CUMPLIMIENTO_MAX and valor <= 100:
        valor = valor / 100.0

    if not (RANGO_CUMPLIMIENTO_MIN <= valor <= RANGO_CUMPLIMIENTO_MAX):
        return np.nan

    return valor


def obtener_ultimo_registro(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Id" not in df.columns:
        return df

    if "Revisar" in df.columns:
        revisar = pd.to_numeric(df["Revisar"], errors="coerce").fillna(0)
        activos = df[revisar == 1]
        if not activos.empty:
            return activos.drop_duplicates(subset="Id", keep="first").reset_index(drop=True)

    if "Fecha" in df.columns:
        return (
            df.sort_values("Fecha")
            .drop_duplicates(subset="Id", keep="last")
            .reset_index(drop=True)
        )
    return df.drop_duplicates(subset="Id", keep="last").reset_index(drop=True)


def calcular_kpis(df_ultimo: pd.DataFrame) -> tuple[int, dict]:
    if "Cumplimiento_norm" not in df_ultimo.columns:
        return 0, {}

    df_con_datos = df_ultimo[df_ultimo["Cumplimiento_norm"].notna()]
    total = len(df_con_datos)
    conteos: dict = {}
    for cat in ["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento"]:
        n = int((df_con_datos["Categoria"] == cat).sum()) if "Categoria" in df_con_datos.columns else 0
        pct = round(n / total * 100, 1) if total > 0 else 0
        conteos[cat] = {"n": n, "pct": pct}
    return total, conteos


def _resolver_columna_cumplimiento(df: pd.DataFrame) -> str | None:
    for candidate in (
        "Cumplimiento",
        "cumplimiento",
        "cumplimiento_dec",
        "cumplimiento_pct",
        "Cumplimiento Real",
        "CumplReal",
        "Cumplimiento_norm",
    ):
        if candidate in df.columns:
            return candidate
    return find_col(
        df,
        [
            "Cumplimiento",
            "cumplimiento_dec",
            "cumplimiento_pct",
            "Cumplimiento Real",
            "CumplReal",
        ],
    )


def aplicar_calculos_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    """Fase 5 completa: normalizar, recalcular y categorizar."""
    if df.empty:
        return df

    out = df.copy()
    if "Id" not in out.columns and "id" in out.columns:
        out["Id"] = out["id"]

    col_tipo_reg = next((c for c in ["TipoRegistro", "Tipo_Registro"] if c in out.columns), None)
    col_ejec_signo = next((c for c in ["EjecS", "Ejecucion_Signo"] if c in out.columns), None)

    if col_tipo_reg:
        mask_metrica = out[col_tipo_reg].astype(str).str.strip().str.lower() == "metrica"
    elif "Indicador" in out.columns:
        mask_metrica = out["Indicador"].astype(str).str.lower().str.contains(r"\bmetrica\b", na=False)
    else:
        mask_metrica = pd.Series(False, index=out.index)

    mask_sin_meta = (
        (pd.to_numeric(out["Meta"], errors="coerce").isna() | (pd.to_numeric(out["Meta"], errors="coerce") == 0))
        if "Meta" in out.columns
        else pd.Series(False, index=out.index)
    )

    if col_tipo_reg:
        mask_no_aplica = out[col_tipo_reg].astype(str).str.strip().str.lower().eq("no aplica")
    elif col_ejec_signo:
        mask_no_aplica = out[col_ejec_signo].astype(str).str.strip().str.lower().eq("no aplica")
    else:
        mask_no_aplica = pd.Series(False, index=out.index)

    mask_sin_reporte = (~mask_metrica) & (mask_sin_meta | mask_no_aplica)

    cumpl_col = _resolver_columna_cumplimiento(out)
    if cumpl_col and cumpl_col != "cumplimiento_pct":
        out["Cumplimiento_norm"] = out[cumpl_col].apply(normalizar_cumplimiento)
    elif cumpl_col == "cumplimiento_pct":
        out["Cumplimiento_norm"] = pd.to_numeric(out[cumpl_col], errors="coerce") / 100.0
    else:
        out["Cumplimiento_norm"] = float("nan")

    out.loc[mask_metrica | mask_sin_reporte, "Cumplimiento_norm"] = float("nan")

    col_ejec = "Ejecucion" if "Ejecucion" in out.columns else find_col(out, ["Ejecución", "Ejecucion"])
    col_sentido = "Sentido" if "Sentido" in out.columns else find_col(out, ["Sentido"])

    if col_ejec and "Meta" in out.columns:
        calcular_mask = out["Cumplimiento_norm"].isna() & out["Meta"].notna() & out[col_ejec].notna()
        if calcular_mask.any():

            def _calcular_fila(row):
                sentido = row[col_sentido] if col_sentido and col_sentido in row.index else "Positivo"
                return recalcular_cumplimiento_faltante(
                    row["Meta"],
                    row[col_ejec],
                    sentido=sentido,
                    id_indicador=row.get("Id"),
                )

            out.loc[calcular_mask, "Cumplimiento_norm"] = out.loc[calcular_mask].apply(_calcular_fila, axis=1)

    out["Categoria"] = out.apply(
        lambda r: categorizar_cumplimiento(
            r.get("Cumplimiento_norm"),
            id_indicador=r.get("Id"),
        ),
        axis=1,
    )

    if "Anio" not in out.columns:
        anio_col = find_col(out, ["Anio", "Año"])
        if anio_col:
            out["Anio"] = pd.to_numeric(out[anio_col], errors="coerce")

    return out


def enriquecer_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Alias de fase 5 para compatibilidad."""
    return aplicar_calculos_cumplimiento(df)
