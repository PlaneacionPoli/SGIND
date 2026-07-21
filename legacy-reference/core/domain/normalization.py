"""
core/domain/normalization.py — NORMALIZACIÓN DE VALORES DE CUMPLIMIENTO

PROPÓSITO:
  Lógica para normalizar valores de cumplimiento entre formatos
  (porcentaje ↔ decimal, con/sin símbolo %, latinoamericano).

  Centraliza la duplicación de normalizaciones manuales en dashboards.

IMPORTAR:
  from core.domain.normalization import (
      normalizar_valor_a_porcentaje,
      normalizar_y_categorizar,
  )
"""

import pandas as pd
import numpy as np
import math
import logging

# Importar categorización
from core.domain.categorization import categorizar_cumplimiento

logger = logging.getLogger(__name__)


def normalizar_valor_a_porcentaje(valor, tiene_porcentaje=None):
    """
    Normaliza un valor numérico a porcentaje (0-100, 0-130, etc).

    PROBLEMA #9 FIX: Detecta si el valor tiene símbolo % o no para normalizar.

    LÓGICA:
      - Si tiene_porcentaje=True: valor es porcentaje → retorna como está
      - Si tiene_porcentaje=False: valor es decimal (0-1.3) → multiplica por 100
      - Si tiene_porcentaje=None: intenta detectar automáticamente del string

    PARÁMETROS:
      valor: float, int, str, NaN
        Valor a normalizar
      tiene_porcentaje: None, True, False
        Si True: es porcentaje, mantener
        Si False: es decimal, multiplicar por 100
        Si None: detectar del string si tiene "%"

    RETORNA:
      float: Valor normalizado a porcentaje (0-130), o NaN si inválido

    EJEMPLOS:
      >>> normalizar_valor_a_porcentaje(0.95, tiene_porcentaje=False)  # decimal
      95.0

      >>> normalizar_valor_a_porcentaje(95.0, tiene_porcentaje=True)   # porcentaje
      95.0

      >>> normalizar_valor_a_porcentaje("85%")  # detecta % automáticamente
      85.0

      >>> normalizar_valor_a_porcentaje("0.85")  # sin %, es decimal
      85.0
    """
    # Manejo de NaN
    try:
        if pd.isna(valor):
            return np.nan
    except (ValueError, TypeError):
        return np.nan

    # Detectar % en string original si no se especifica tiene_porcentaje
    tiene_pct_detectado = False
    if isinstance(valor, str):
        valor_str = valor.strip()
        if valor_str.endswith("%"):
            tiene_pct_detectado = True
            valor_str = valor_str[:-1]
        try:
            valor = float(valor_str)
        except ValueError:
            return np.nan

    # Convertir a float
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return np.nan

    # Validar NaN
    if math.isnan(valor):
        return np.nan

    # Usar hint explícito si se proporciona, sino usar detección automática
    if tiene_porcentaje is None:
        tiene_porcentaje = tiene_pct_detectado

    # Aplicar lógica: si tiene %, mantener; si no, multiplicar por 100
    if tiene_porcentaje:
        return valor
    else:
        # Es decimal (0-1.3), convertir a porcentaje (0-130)
        return valor * 100.0


def normalizar_y_categorizar(valor, es_porcentaje=None, id_indicador=None, sentido="Positivo"):
    """
    Wrapper que combina normalización de cumplimiento + categorización en una sola función.

    PROPÓSITO:
      - Centralizar la lógica de conversión automática
      - Reemplazar conversiones manuales repetidas en dashboards
      - Garantizar consistencia en formato de entrada/salida

    PROBLEMA SOLUCIONADO:
      Reemplaza el antipatrón repetido en 4+ dashboards:

      ANTES (código duplicado):
          cumpl_decimal = pct / 100.0  # Conversión manual
          categoria = categorizar_cumplimiento(cumpl_decimal, id_indicador=id_ind)

      DESPUÉS (centralizado):
          categoria = normalizar_y_categorizar(pct, es_porcentaje=True, id_indicador=id_ind)

    PARÁMETROS
    ----------
    valor : float, str, NaN
        Valor de cumplimiento (puede ser porcentaje o decimal)

    es_porcentaje : None, True, False
        Hint sobre el formato del valor:
        - None: detectar automáticamente (si tiene "%" en string)
        - True: es porcentaje (0-130)
        - False: es decimal (0-1.3)

    id_indicador : str, int, opcional
        ID del indicador para auto-detectar Plan Anual

    sentido : str
        "Positivo" o "Negativo" (para futuros usos en recalcular_cumplimiento_faltante)

    RETORNA
    -------
    str
        Categoría: "Peligro" | "Alerta" | "Cumplimiento" | "Sobrecumplimiento" | "Sin dato"

    EJEMPLOS
    --------
    >>> normalizar_y_categorizar(95, es_porcentaje=True, id_indicador="373")
    'Cumplimiento'

    >>> normalizar_y_categorizar(0.95, es_porcentaje=False, id_indicador="123")
    'Alerta'

    >>> normalizar_y_categorizar("95%", id_indicador="373")
    'Cumplimiento'

    >>> normalizar_y_categorizar(105, es_porcentaje=True)
    'Sobrecumplimiento'
    """
    # Paso 1: Normalizar a decimal (0-1.3)
    valor_decimal = normalizar_valor_a_porcentaje(valor, tiene_porcentaje=es_porcentaje)

    # Si el valor normalizado es un porcentaje (0-130), convertir a decimal
    # Lógica: normalizar_valor_a_porcentaje retorna porcentaje (0-130)
    # categorizar_cumplimiento espera decimal (0-1.3)
    if pd.notna(valor_decimal) and valor_decimal > 1.3:
        # Es un porcentaje que necesita conversión a decimal
        valor_decimal = valor_decimal / 100.0

    # Paso 2: Categorizar usando lógica oficial
    categoria = categorizar_cumplimiento(valor_decimal, id_indicador=id_indicador)

    return categoria
