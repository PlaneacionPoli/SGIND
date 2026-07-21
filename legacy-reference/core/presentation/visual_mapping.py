"""
core/presentation/visual_mapping.py — MAPEO VISUAL DE CATEGORÍAS

PROPÓSITO:
  Lógica de presentación: colores e íconos para categorías de cumplimiento.
  Separado de la lógica de dominio por SRP.

IMPORTAR:
  from core.presentation.visual_mapping import (
      obtener_color_categoria,
      obtener_icono_categoria,
  )
"""

import logging

logger = logging.getLogger(__name__)


def obtener_color_categoria(categoria):
    """
    Retorna el color hex para una categoría.

    RESPONSABILIDAD:
      Presentación (UI) - mapeo visual de categorías
      No contiene lógica de negocio, solo configuración de colores.

    Parámetros
    ----------
    categoria : str
        Una de: "Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"

    Retorna
    -------
    str
        Color hex (ej: "#D32F2F")

    Ejemplos
    --------
    >>> obtener_color_categoria("Peligro")
    '#D32F2F'

    >>> obtener_color_categoria("Cumplimiento")
    '#4CAF50'
    """
    from core.config import COLOR_CATEGORIA

    return COLOR_CATEGORIA.get(categoria, COLOR_CATEGORIA.get("Sin dato"))


def obtener_icono_categoria(categoria):
    """
    Retorna el ícono (emoji) para una categoría.

    RESPONSABILIDAD:
      Presentación (UI) - mapeo visual de categorías
      No contiene lógica de negocio, solo configuración de íconos.

    Parámetros
    ----------
    categoria : str
        Una de: "Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"

    Retorna
    -------
    str
        Emoji (ej: "🔴")

    Ejemplos
    --------
    >>> obtener_icono_categoria("Peligro")
    '🔴'

    >>> obtener_icono_categoria("Cumplimiento")
    '✅'
    """
    from core.config import ICONOS_CATEGORIA

    return ICONOS_CATEGORIA.get(categoria, "⚪")
