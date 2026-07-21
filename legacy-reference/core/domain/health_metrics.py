"""
core/domain/health_metrics.py — CÁLCULOS DE MÉTRICAS DE SALUD

PROPÓSITO:
  Lógica de recálculo de cumplimiento cuando faltan datos.
  Centraliza la duplicación que existía en 3 módulos diferentes.

PROBLEMA SOLUCIONADO (#2):
  Antes: 3 implementaciones divergentes
  - services/data_loader.py líneas 248-276 (defectuosa)
  - services/strategic_indicators.py load_cierres() (defectuosa)
  - scripts/etl/cumplimiento.py (CORRECTA)
  
  Ahora: 1 lógica oficial global

IMPORTAR:
  from core.domain.health_metrics import recalcular_cumplimiento_faltante
"""

import pandas as pd
import logging

# Importar configuración
from core.config import (
    IDS_PLAN_ANUAL,
    IDS_TOPE_100,
)

logger = logging.getLogger(__name__)


def recalcular_cumplimiento_faltante(meta, ejecucion, sentido="Positivo", id_indicador=None):
    """
    Recalcula cumplimiento cuando falta: ejecución / meta (o meta / ejecución según sentido).

    PROPÓSITO:
        Centralizar la lógica de recálculo que estaba duplicada en 3 lugares.

    CASOS ESPECIALES (PROBLEMA #2):
        - Meta=0 & Ejec=0 → 1.0 (éxito perfecto, cero es logro)
        - Negativo & Ejec=0 → 1.0 (cero es perfecto en indicadores de "menos es mejor")

    LÓGICA:
        1. Validar meta y ejecucion no sean None
        2. Convertir a float
        3. CASOS ESPECIALES:
           - Si Meta=0 y Ejec=0: retorna 1.0 (éxito)
           - Si Sentido=Negativo y Ejec=0 (Meta>0): retorna 1.0 (perfecto)
        4. Cálculo estándar:
           - Si sentido="Positivo": cumplimiento = ejecucion / meta
           - Si sentido="Negativo": cumplimiento = meta / ejecucion
        5. Aplicar tope según tipo de indicador:
           - Plan Anual: [0, 1.0]
           - Regular: [0, 1.3]

    Parámetros
    ----------
    meta : float, int, str
        Meta del período

    ejecucion : float, int, str
        Ejecución del período

    sentido : str, default "Positivo"
        "Positivo": más es mejor (cumpl = ejec/meta)
        "Negativo": menos es mejor (cumpl = meta/ejec)

    id_indicador : str, int, optional
        ID del indicador para detectar Plan Anual y aplicar tope correcto

    Retorna
    -------
    float
        Cumplimiento recalculado: [0, 1.0] para PA, [0, 1.3] para regular
        Retorna NaN si no se puede calcular (entrada inválida, meta=0 pero ejec≠0, etc.)

    Ejemplos
    --------
    >>> recalcular_cumplimiento_faltante(100, 50)  # Regular, Positivo
    0.5

    >>> recalcular_cumplimiento_faltante(100, 150, sentido="Positivo")  # Sobrecump
    1.3  # Tope aplicado

    >>> recalcular_cumplimiento_faltante(100, 150, sentido="Positivo", id_indicador="45")  # PA
    1.0  # Tope PA más restrictivo

    >>> recalcular_cumplimiento_faltante(0, 0, sentido="Positivo")  # CASO ESPECIAL
    1.0  # Meta=0 & Ejec=0 = éxito perfecto

    >>> recalcular_cumplimiento_faltante(1.6, 0, sentido="Negativo")  # CASO ESPECIAL
    1.0  # Negativo & Ejec=0 = cero es perfecto
    """
    # Validar entradas
    if meta is None or ejecucion is None:
        logger.debug(f"Meta o Ejecucion es None: meta={meta}, ejec={ejecucion}")
        return float("nan")

    # Convertir a float
    try:
        m = float(meta)
        e = float(ejecucion)
    except (TypeError, ValueError):
        logger.debug(f"No se pudo convertir meta={meta} o ejecucion={ejecucion} a float")
        return float("nan")

    # Validar no sean NaN
    if pd.isna(m) or pd.isna(e):
        logger.debug(f"Meta o Ejecucion es NaN: meta={m}, ejec={e}")
        return float("nan")

    # Normalizar sentido
    sentido_str = str(sentido).strip().lower() if sentido else "positivo"

    # ════════════════════════════════════════════════════════════════════════════
    # CASOS ESPECIALES (PROBLEMA #2)
    # ════════════════════════════════════════════════════════════════════════════

    # CASO ESPECIAL 1: Meta=0 & Ejecución=0 → 1.0 (100% éxito perfecto)
    # Interpretación: "Meta de cero logros (muertes, accidentes), cero logrados = perfecto"
    # Ejemplo: Mortalidad Laboral (meta=0 muertes, ejecutado=0 muertes)
    if m == 0 and e == 0:
        logger.debug("CASO ESPECIAL: Meta=0 y Ejec=0 → 100% (éxito perfecto)")
        return 1.0

    # CASO ESPECIAL 2: Sentido Negativo & Ejecución=0 (Meta>0) → 1.0 (100% perfecto)
    # Interpretación: "Indicador donde menos es mejor, cero logrado es perfecto"
    # Ejemplo: Accidentalidad (meta=1.6 accidentes permitidos, ejecutado=0 accidentes = perfecto)
    if sentido_str == "negativo" and e == 0 and m > 0:
        logger.debug("CASO ESPECIAL Negativo: Ejec=0 y Meta>0 → 100% (cero es perfecto)")
        return 1.0

    # ════════════════════════════════════════════════════════════════════════════
    # CÁLCULO ESTÁNDAR
    # ════════════════════════════════════════════════════════════════════════════

    try:
        if sentido_str == "positivo":
            # Más es mejor: cumplimiento = ejecución / meta
            if m == 0:
                logger.debug("Positivo & Meta=0 & Ejec≠0: no se puede dividir")
                return float("nan")
            raw = e / m
        elif sentido_str == "negativo":
            # Menos es mejor: cumplimiento = meta / ejecución
            if e == 0:
                logger.debug("Negativo & Ejec=0 & Meta=0: ya fue manejado como caso especial")
                return float("nan")
            raw = m / e
        else:
            logger.warning(f"Sentido desconocido: {sentido}, asumiendo Positivo")
            if m == 0:
                return float("nan")
            raw = e / m
    except ZeroDivisionError:
        logger.debug(f"División por cero: meta={m}, ejecucion={e}")
        return float("nan")

    # Validar resultado
    if pd.isna(raw):
        return float("nan")

    # Aplicar tope según tipo de indicador
    es_plan_anual = False
    es_tope_100 = False
    if id_indicador is not None:
        id_str = str(id_indicador).strip()
        es_plan_anual = id_str in IDS_PLAN_ANUAL
        es_tope_100 = id_str in IDS_TOPE_100

    tope = 1.0 if (es_plan_anual or es_tope_100) else 1.3

    # Retornar acotado [0, tope]
    resultado = min(max(raw, 0.0), tope)
    logger.debug(
        f"Recalc cumpl: meta={m}, ejec={e}, sentido={sentido_str}, "
        f"PA={es_plan_anual}, raw={raw:.3f}, resultado={resultado:.3f}"
    )

    return resultado
