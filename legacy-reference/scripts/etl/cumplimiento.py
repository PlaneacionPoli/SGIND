"""
scripts/etl/cumplimiento.py
Cálculo de cumplimiento (lógica de negocio pura, sin I/O).

DOCUMENTACIÓN:
  - Cumplimiento (col L): Decimal normalizado con TOPE [0.0, 1.0] PA o [0.0, 1.3] regular
  - CumplReal (col M): Decimal con TOPE [0.0, 1.0] PA/tope-100, SIN TOPE [0.0, ∞) regular

CASOS ESPECIALES (Problema #4 fixes):
  1. Meta=0 Y Ejecución=0 → 1.0 (100% éxito, no error)
     Ejemplo: Mortalidad laboral con meta=0, ejecutado=0 → perfecto

  2. Sentido Negativo Y Ejecución=0 (Meta>0) → 1.0 (100% éxito)
     Ejemplo: Accidentalidad con meta=1.6, ejecutado=0 → cero accidentes es perfecto

  3. Tope aplicado:
     - SIEMPRE 1.0 máximo en Cumplimiento (capped)
     - CumplReal: también acotado a 1.0 para Plan Anual/IDS_TOPE_100 (la meta
       es un techo real, no tiene sentido "sobrecumplir"); sin límite para
       indicadores regulares (tope=1.3)
"""
from __future__ import annotations

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def _calc_cumpl(
    meta: object,
    ejec: object,
    sentido: str,
    tope: float = 1.3,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calcula (cumpl_capped, cumpl_real) a partir de meta, ejec y sentido.
    
    RETORNA:
      (cumpl_capped, cumpl_real) ambos en rango [0.0, ∞)
        - cumpl_capped: acotado a tope (130% regular, 100% Plan Anual)
        - cumpl_real: sin acotamiento
      
      (None, None) si no se puede calcular
    
    CASOS ESPECIALES (Problem #4 - Nuevos):
      ✓ Meta=0 AND Ejecución=0 → (1.0, 1.0) [100% perfecto]
      ✓ Sentido Negativo AND Ejecución=0 AND Meta>0 → (1.0, 1.0) [cero es perfecto]
    """
    # ── Validar entrada ───────────────────────────────────────────
    if meta is None or ejec is None:
        return None, None
    
    try:
        m, e = float(meta), float(ejec)
    except (TypeError, ValueError):
        logger.debug(f"No se pudo convertir meta={meta} o ejec={ejec} a float")
        return None, None
    
    # ── CASO ESPECIAL 1: Meta=0 y Ejecución=0 ────────────────────
    # Interpretación: meta de 0 muertes, 0 accidentes, etc. lograda perfectamente
    # Ejemplo: Mortalidad laboral: meta=0 (cero muertes), ejecutado=0
    if m == 0 and e == 0:
        logger.debug("Caso especial: Meta=0 y Ejec=0 → 100% (éxito perfecto)")
        return 1.0, 1.0
    
    # ── CASO ESPECIAL 2: Sentido Negativo y Ejecución=0 ──────────
    # Interpretación: indicador que menos es mejor (gastos, accidentes)
    # Si ejecutó 0 (cero gastos, cero accidentes), es perfecto
    # Ejemplo: Accidentalidad: meta=1.6, ejecutado=0 → 100%
    if sentido.strip().lower() == "negativo" and e == 0 and m > 0:
        logger.debug("Caso especial Negativo: Ejec=0 y Meta>0 → 100% (cero es perfecto)")
        return 1.0, 1.0
    
    # ── Validación standard: Meta no puede ser 0 (división por cero) ─────────────
    if m == 0:
        logger.debug(f"Meta es 0 (no se puede dividir): meta={m}, ejec={e}")
        return None, None
    
    # ── Cálculo según Sentido ──────────────────────────────────────
    if sentido.strip().lower() == "positivo":
        # Más es mejor: cumplimiento = ejecución / meta
        raw = e / m
    else:
        # Menos es mejor (Negativo): cumplimiento = meta / ejecución
        # Pero si ejec=0 ya fue manejado arriba como éxito
        if e == 0:
            logger.debug(f"Sentido Negativo con Ejec=0: meta={m}, ejec={e}")
            return None, None
        raw = m / e
    
    # ── Normalizar: asegurar mínimo 0 ──────────────────────────────
    raw = max(raw, 0.0)
    
    # ── Aplicar tope ─────────────────────────────────────────────────
    # cumpl_capped siempre acotado a [0, tope].
    # cumpl_real solo se acota cuando tope <= 1.0 (Plan Anual / IDS_TOPE_100),
    # donde la meta es un techo real y no tiene sentido "sobrecumplir".
    # Para indicadores regulares (tope=1.3) cumpl_real queda sin límite.
    cumpl_capped = min(raw, tope)
    cumpl_real = min(raw, tope) if tope <= 1.0 else raw
    
    logger.debug(
        f"Calc cumpl: meta={m}, ejec={e}, sentido={sentido}, raw={raw:.4f}, "
        f"tope={tope}, capped={cumpl_capped:.4f}"
    )
    
    return cumpl_capped, cumpl_real


# Alias público con nombre más descriptivo
calcular_cumplimiento = _calc_cumpl


def obtener_tope_cumplimiento(id_indicador: object, ids_plan_anual=None, ids_tope_100=None) -> float:
    """
    Determina el tope dinámico para un indicador según tipo.
    
    LÓGICA:
      - Plan Anual (PA): tope = 1.0 (100%)
      - IDS_TOPE_100: tope = 1.0 (100%)
      - Regular: tope = 1.3 (130%)
    
    PARÁMETROS:
      id_indicador: ID del indicador (se convierte a string)
      ids_plan_anual: set/frozenset con IDs Plan Anual (default: desde config)
      ids_tope_100: set/frozenset con IDs tope 100% (default: desde config)
    
    RETORNA:
      1.0 si es PA o está en IDS_TOPE_100
      1.3 si es regular
    """
    # Importar desde config si no se proporciona
    if ids_plan_anual is None:
        try:
            from .config import IDS_PLAN_ANUAL
            ids_plan_anual = IDS_PLAN_ANUAL
        except (ImportError, NameError):
            ids_plan_anual = frozenset()
    
    if ids_tope_100 is None:
        try:
            from .config import IDS_TOPE_100
            ids_tope_100 = IDS_TOPE_100
        except (ImportError, NameError):
            ids_tope_100 = frozenset()
    
    # Convertir ID a string
    id_str = str(id_indicador).strip() if id_indicador is not None else ""
    
    # Chequear si está en listas especiales
    if id_str in (ids_plan_anual or frozenset()) or id_str in (ids_tope_100 or frozenset()):
        logger.debug(f"ID {id_str} está en PA o TOPE_100 → tope = 1.0")
        return 1.0
    
    logger.debug(f"ID {id_str} es regular → tope = 1.3")
    return 1.3


def _calc_cumpl_con_tope_dinamico(
    meta: object,
    ejec: object,
    sentido: str,
    id_indicador: object = None,
    ids_plan_anual=None,
    ids_tope_100=None,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Versión de _calc_cumpl que determina el tope dinámicamente según el indicador.
    
    PARÁMETROS:
      meta, ejec, sentido: igual que _calc_cumpl
      id_indicador: ID del indicador para determinar tope
      ids_plan_anual: set con IDs Plan Anual
      ids_tope_100: set con IDs tope 100%
    
    RETORNA:
      (cumpl_capped, cumpl_real)
    """
    # Determinar tope dinámicamente
    tope = obtener_tope_cumplimiento(id_indicador, ids_plan_anual, ids_tope_100)
    
    # Usar función principal con tope calculado
    return _calc_cumpl(meta, ejec, sentido, tope)
