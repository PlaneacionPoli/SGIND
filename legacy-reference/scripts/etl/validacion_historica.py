"""
scripts/etl/validacion_historica.py
Validación de coherencia histórica en datos ETL.

PROPÓSITO:
  Detectar anomalías en series de tiempo de indicadores antes de escribir
  al consolidado. Garantiza que los datos nuevos sean coherentes con el
  histórico existente.

VALIDACIONES IMPLEMENTADAS:
  1. Cambio retroactivo de Sentido (Positivo ↔ Negativo)
  2. Caída brusca de Meta (>50% respecto al último valor)
  3. Caída brusca de Ejecución (>80% respecto al promedio reciente)

USO:
  from scripts.etl.validacion_historica import validar_coherencia_historica

  alertas = validar_coherencia_historica(df_nuevo, df_historico)
  for alerta in alertas:
      logger.warning(alerta)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class AlertaCoherencia:
    """Representa una anomalía detectada en la coherencia histórica."""

    id_indicador: str
    tipo: str          # "cambio_sentido" | "caida_meta" | "caida_ejecucion"
    severidad: str     # "ERROR" | "WARNING"
    mensaje: str
    valor_anterior: Optional[float] = None
    valor_nuevo: Optional[float] = None


def validar_coherencia_historica(
    df_nuevo: pd.DataFrame,
    df_historico: pd.DataFrame,
    umbral_caida_meta: float = 0.50,
    umbral_caida_ejec: float = 0.80,
    periodos_referencia: int = 3,
) -> List[AlertaCoherencia]:
    """
    Detecta incoherencias entre datos nuevos y el histórico existente.

    PARÁMETROS
    ----------
    df_nuevo : pd.DataFrame
        Registros nuevos a ingresar. Requiere columnas: Id, Sentido, Meta, Ejecucion.
    df_historico : pd.DataFrame
        Registros históricos consolidados. Mismas columnas + Fecha.
    umbral_caida_meta : float
        Fracción de caída en Meta que dispara WARNING (default 0.50 = 50%).
    umbral_caida_ejec : float
        Fracción de caída en Ejecución que dispara WARNING (default 0.80 = 80%).
    periodos_referencia : int
        Cantidad de períodos históricos para calcular el promedio de referencia.

    RETORNA
    -------
    List[AlertaCoherencia]
        Lista de alertas (vacía si no hay anomalías).
    """
    alertas: List[AlertaCoherencia] = []

    if df_nuevo.empty or df_historico.empty:
        return alertas

    # Normalizar columnas mínimas requeridas
    cols_requeridas = {"Id", "Sentido"}
    if not cols_requeridas.issubset(df_nuevo.columns) or not cols_requeridas.issubset(df_historico.columns):
        logger.debug("validar_coherencia_historica: columnas insuficientes, se omite validación.")
        return alertas

    # Agrupar histórico por Id para comparación
    hist_por_id = df_historico.copy()
    if "Fecha" in hist_por_id.columns:
        hist_por_id["Fecha"] = pd.to_datetime(hist_por_id["Fecha"], errors="coerce")
        hist_por_id = hist_por_id.sort_values("Fecha", ascending=True)

    for _, fila in df_nuevo.iterrows():
        id_str = str(fila.get("Id", "")).strip()
        if not id_str:
            continue

        hist_ind = hist_por_id[hist_por_id["Id"].astype(str).str.strip() == id_str]

        if hist_ind.empty:
            continue  # indicador nuevo, no hay histórico para comparar

        # ── 1. Cambio retroactivo de Sentido ─────────────────────────────────
        sentido_nuevo = str(fila.get("Sentido", "")).strip()
        sentidos_hist = hist_ind["Sentido"].dropna().astype(str).str.strip().unique()
        if len(sentidos_hist) > 0:
            sentido_hist = sentidos_hist[-1]  # último sentido registrado
            if sentido_nuevo and sentido_hist and sentido_nuevo != sentido_hist:
                alertas.append(AlertaCoherencia(
                    id_indicador=id_str,
                    tipo="cambio_sentido",
                    severidad="ERROR",
                    mensaje=(
                        f"Indicador {id_str}: Sentido cambió de '{sentido_hist}' "
                        f"a '{sentido_nuevo}'. Cambio retroactivo invalida histórico."
                    ),
                ))

        # ── 2. Caída brusca de Meta ───────────────────────────────────────────
        if "Meta" in df_nuevo.columns and "Meta" in hist_ind.columns:
            meta_nueva = _to_float(fila.get("Meta"))
            metas_hist = hist_ind["Meta"].dropna().map(_to_float).dropna()
            if meta_nueva is not None and len(metas_hist) >= 1:
                meta_ref = metas_hist.iloc[-periodos_referencia:].mean()
                if meta_ref > 0:
                    caida = (meta_ref - meta_nueva) / meta_ref
                    if caida > umbral_caida_meta:
                        alertas.append(AlertaCoherencia(
                            id_indicador=id_str,
                            tipo="caida_meta",
                            severidad="WARNING",
                            mensaje=(
                                f"Indicador {id_str}: Meta nueva ({meta_nueva:.2f}) "
                                f"cayó {caida:.0%} respecto al promedio histórico ({meta_ref:.2f})."
                            ),
                            valor_anterior=meta_ref,
                            valor_nuevo=meta_nueva,
                        ))

        # ── 3. Caída brusca de Ejecución ─────────────────────────────────────
        if "Ejecucion" in df_nuevo.columns and "Ejecucion" in hist_ind.columns:
            ejec_nueva = _to_float(fila.get("Ejecucion"))
            ejec_hist = hist_ind["Ejecucion"].dropna().map(_to_float).dropna()
            if ejec_nueva is not None and len(ejec_hist) >= periodos_referencia:
                ejec_ref = ejec_hist.iloc[-periodos_referencia:].mean()
                if ejec_ref > 0:
                    caida = (ejec_ref - ejec_nueva) / ejec_ref
                    if caida > umbral_caida_ejec:
                        alertas.append(AlertaCoherencia(
                            id_indicador=id_str,
                            tipo="caida_ejecucion",
                            severidad="WARNING",
                            mensaje=(
                                f"Indicador {id_str}: Ejecución nueva ({ejec_nueva:.2f}) "
                                f"cayó {caida:.0%} respecto al promedio reciente ({ejec_ref:.2f}). "
                                "Verificar si es dato real o error de carga."
                            ),
                            valor_anterior=ejec_ref,
                            valor_nuevo=ejec_nueva,
                        ))

    logger.info(
        f"validar_coherencia_historica: {len(df_nuevo)} registros nuevos, "
        f"{len(alertas)} alertas generadas."
    )
    return alertas


def _to_float(val: object) -> Optional[float]:
    """Convierte un valor a float, retorna None si no es posible."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
