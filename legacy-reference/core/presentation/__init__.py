"""
core/presentation/__init__.py — LAYER DE PRESENTACIÓN

Módulos de lógica de presentación (UI, visualización):
- visual_mapping: Mapeo visual de categorías (colores, íconos)

NOTA: Solo contiene lógica de UI, no incluir lógica de negocio
"""

from .visual_mapping import (
    obtener_color_categoria,
    obtener_icono_categoria,
)

__all__ = [
    "obtener_color_categoria",
    "obtener_icono_categoria",
]
