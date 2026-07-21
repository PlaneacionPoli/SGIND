"""
core/domain/__init__.py — DOMINIO DEL SISTEMA

Módulos de lógica de negocio (layer de dominio):
- categorization: Categorización de cumplimiento
- health_metrics: Cálculos de métricas de salud
- normalization: Normalización de valores

NOTA: No incluir lógica de presentación (UI, colores, íconos)
"""

from .categorization import (
    CategoriaCumplimiento,
    categorizar_cumplimiento,
    nivel_desde_cumplimiento,
)

from .health_metrics import recalcular_cumplimiento_faltante

from .normalization import (
    normalizar_valor_a_porcentaje,
    normalizar_y_categorizar,
)

__all__ = [
    "CategoriaCumplimiento",
    "categorizar_cumplimiento",
    "nivel_desde_cumplimiento",
    "recalcular_cumplimiento_faltante",
    "normalizar_valor_a_porcentaje",
    "normalizar_y_categorizar",
]
