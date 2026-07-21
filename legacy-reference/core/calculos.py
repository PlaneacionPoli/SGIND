"""
core/calculos.py — Lógica de negocio: categorías, umbrales, salud institucional.

Sin dependencias de Streamlit → testeable con pytest directamente.
"""

import pandas as pd
import numpy as np

from core.config import (
    UMBRAL_PELIGRO,
    UMBRAL_ALERTA,
    UMBRAL_SOBRECUMPLIMIENTO,
    IDS_PLAN_ANUAL,
    UMBRAL_ALERTA_PA,
    UMBRAL_SOBRECUMPLIMIENTO_PA,
)
from core.domain import categorizar_cumplimiento as _categorizar_cumplimiento_oficial


def normalizar_cumplimiento(valor):
    """
    Valida que cumplimiento esté en rango esperado [0, 1.3].

    Notas:
    - Los datos ya vienen normalizados desde Excel (Consolidado Semestral)
    - Esta función es de VALIDACIÓN, no de conversión
    - Si valor está fuera de rango → log warning + retorna NaN
    - Rango: [0.0, 1.3] donde 1.3 = 130% (máximo capeado)

    Args:
        valor: número o string a validar

    Returns:
        valor validado ∈ [0, 1.3], o NaN si inválido
    """
    import logging

    logger = logging.getLogger(__name__)

    # Manejar NaN y tipos inválidos
    try:
        if pd.isna(valor):
            return np.nan
    except (ValueError, TypeError):
        # pd.isna falla con tipos complejos (arrays, dicts, etc)
        logger.warning(f"Tipo inválido para normalizar_cumplimiento: {type(valor)}")
        return np.nan

    # Convertir string a float si aplica
    if isinstance(valor, str):
        valor_clean = valor.replace("%", "").strip()
        # Formato latinoamericano: . para miles, , para decimales
        # Remover . (separador de miles), luego reemplazar , por . (decimal)
        valor_clean = valor_clean.replace(".", "").replace(",", ".")
        try:
            valor = float(valor_clean)
        except ValueError:
            logger.warning(f"No se puede convertir a float: '{valor}'")
            return np.nan

    # Convertir a float
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        logger.warning(f"Tipo inválido para normalizar_cumplimiento: {type(valor)} = {valor}")
        return np.nan

    # Validar que esté en rango esperado [0, 1.3]
    if not (0.0 <= valor <= 1.3):
        logger.warning(f"Cumplimiento fuera de rango [0.0, 1.3]: {valor}")
        return np.nan

    return valor


def categorizar_cumplimiento(cumplimiento, sentido="Positivo", id_indicador=None):
    """Wrapper de compatibilidad (delegación directa a core.domain).

    FUENTE ÚNICA OFICIAL: core/domain
    El parámetro `sentido` se ignora (se mantiene solo por compatibilidad hacia atrás).
    La categorización depende SOLO del valor numérico y del ID del indicador
    (Plan Anual / Negativo-Porcentual se auto-detectan por ID en core.domain).

    Retorna: 'Peligro' | 'Alerta' | 'Cumplimiento' | 'Sobrecumplimiento' | 'Sin dato'
    """
    return _categorizar_cumplimiento_oficial(cumplimiento, id_indicador=id_indicador)


def calcular_salud_institucional(df):
    """% promedio de cumplimiento agrupado por Fecha (para gráfico de tendencia)."""
    if "Fecha" not in df.columns or df.empty:
        return pd.DataFrame(columns=["Fecha", "Salud_pct"])
    result = (
        df.groupby("Fecha")["Cumplimiento_norm"]
        .mean()
        .reset_index()
        .assign(Salud_pct=lambda x: x["Cumplimiento_norm"] * 100)
    )
    return result


def calcular_tendencia(df_indicador):
    """Compara último vs penúltimo periodo. Retorna '↑' | '↓' | '→'"""
    if len(df_indicador) < 2:
        return "→"
    df_s = df_indicador.sort_values("Fecha")
    diff = df_s.iloc[-1]["Cumplimiento_norm"] - df_s.iloc[-2]["Cumplimiento_norm"]
    if pd.isna(diff):
        return "→"
    return "↑" if diff > 0.01 else "↓" if diff < -0.01 else "→"


def calcular_meses_en_peligro(df_indicador):
    """Periodos consecutivos en Peligro (desde el más reciente)."""
    df_s = df_indicador.sort_values("Fecha", ascending=False)
    conteo = 0
    for _, row in df_s.iterrows():
        if row.get("Categoria") == "Peligro":
            conteo += 1
        else:
            break
    return conteo


def generar_recomendaciones(categoria, cum_series):
    """
    Genera lista de recomendaciones según categoría y tendencia.
    Returns: (tendencia_str, [recomendaciones])
    """
    cum_series = cum_series.dropna()

    if len(cum_series) >= 3:
        ultima = float(cum_series.iloc[-1])
        anterior = float(cum_series.iloc[-3:-1].mean())
        if ultima > anterior + 2:
            tendencia = "Mejorando"
        elif ultima < anterior - 2:
            tendencia = "Empeorando"
        else:
            tendencia = "Estable"
    elif len(cum_series) == 2:
        delta = float(cum_series.iloc[-1]) - float(cum_series.iloc[-2])
        tendencia = "Mejorando" if delta > 2 else "Empeorando" if delta < -2 else "Estable"
    else:
        tendencia = "Sin datos suficientes"

    recs_base = {
        "Peligro": [
            "Convocar mesa de trabajo urgente con el responsable del proceso para identificar causas raíz.",
            "Revisar disponibilidad de recursos humanos, técnicos y financieros asignados al proceso.",
            "Establecer plan de acción con actividades concretas, responsables y fechas.",
            "Considerar apertura de una Oportunidad de Mejora (OM) si aún no existe.",
            "Incrementar frecuencia de seguimiento a monitoreo semanal o quincenal.",
        ],
        "Alerta": [
            "Analizar las causas que impiden alcanzar la meta del 100%.",
            "Verificar si existen acciones de mejora abiertas y revisar su avance.",
            "Implementar medidas preventivas antes de caer en zona de peligro.",
            "Revisar con el responsable los factores que pueden afectar el resultado.",
        ],
        "Cumplimiento": [
            "Documentar buenas prácticas que permiten el cumplimiento de la meta.",
            "Asegurar la continuidad de los factores que contribuyen al cumplimiento.",
            "Mantener el monitoreo periódico para detectar desviaciones a tiempo.",
        ],
        "Sobrecumplimiento": [
            "Evaluar si la meta actual es suficientemente retadora; considerar ajustarla.",
            "Documentar y socializar las buenas prácticas para replicarlas en otros procesos.",
            "Verificar que el sobrecumplimiento sea sostenible y no represente ineficiencia.",
            "Reportar el logro como caso de éxito en espacios de gestión institucional.",
        ],
    }

    recs = list(recs_base.get(categoria, ["Revisar con el responsable del proceso."]))

    if tendencia == "Empeorando" and categoria in ("Cumplimiento", "Sobrecumplimiento"):
        recs.append(
            "Aunque cumple la meta, se observa una tendencia decreciente — identificar causas antes de que impacte el resultado."
        )
    elif tendencia == "Mejorando" and categoria == "Peligro":
        recs.append(
            "El indicador muestra una tendencia creciente — continuar con las acciones implementadas."
        )
    elif tendencia == "Empeorando" and categoria == "Alerta":
        recs.append(
            "Se observa tendencia decreciente — priorizar medidas preventivas para evitar zona de peligro."
        )

    return tendencia, recs


def obtener_ultimo_registro(df):
    """
    Retorna un registro único por indicador para KPIs y tablas de resumen.
    Prioridad:
      1. Si existe 'Revisar', filtra Revisar == 1 y deduplica por Id.
      2. Si no, ordena por Fecha y toma el registro más reciente por Id.
    """
    if df.empty or "Id" not in df.columns:
        return df
    if "Revisar" in df.columns:
        revisar = pd.to_numeric(df["Revisar"], errors="coerce").fillna(0)
        return df[revisar == 1].drop_duplicates(subset="Id", keep="first").reset_index(drop=True)
    return df.sort_values("Fecha").drop_duplicates(subset="Id", keep="last").reset_index(drop=True)


def calcular_kpis(df_ultimo):
    """Calcula los 5 KPIs principales desde df_ultimo."""
    df_con_datos = df_ultimo[df_ultimo["Cumplimiento_norm"].notna()]
    total = len(df_con_datos)
    conteos = {}
    for cat in ["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento"]:
        n = (df_con_datos["Categoria"] == cat).sum()
        pct = (n / total * 100) if total > 0 else 0
        conteos[cat] = {"n": n, "pct": round(pct, 1)}
    return total, conteos


def estado_tiempo_acciones(df):
    """Aplica reglas Estado_Tiempo sobre df de acciones (in-place)."""
    df = df.copy()
    df["Estado_Tiempo"] = "A tiempo"
    if "DIAS_VENCIDA" in df.columns and "ESTADO" in df.columns:
        df.loc[df["DIAS_VENCIDA"] > 0, "Estado_Tiempo"] = "Vencida"
        df.loc[
            (df["DIAS_VENCIDA"] >= -30) & (df["DIAS_VENCIDA"] <= 0) & (df["ESTADO"] != "Cerrada"),
            "Estado_Tiempo",
        ] = "Por vencer"
        df.loc[df["ESTADO"] == "Cerrada", "Estado_Tiempo"] = "Cerrada"
    return df


def simple_categoria_desde_porcentaje(pct) -> str:
    """Categoriza valor en escala porcentual (0-100+) sin consideraciones especiales.

    Regla simple (sin Plan Anual ni IDS_TOPE_100):
      < 80%   → Peligro
      80-99%  → Alerta
      ≥ 100%  → Cumplimiento

    Args:
        pct: valor en rango 0-100+

    Returns:
        'Peligro' | 'Alerta' | 'Cumplimiento' | 'Sin dato'

    Nota: Para categorización completa con Plan Anual, usar categorizar_cumplimiento().

    Referencia histórica: Este patrón reemplaza a core/niveles.nivel_desde_pct() (deprecado).
    """
    try:
        c = float(pct)
    except (TypeError, ValueError):
        return "Sin dato"

    if c < UMBRAL_PELIGRO * 100:  # < 80%
        return "Peligro"
    if c < UMBRAL_ALERTA * 100:  # 80-99%
        return "Alerta"
    return "Cumplimiento"
