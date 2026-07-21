"""
core/semantica.py — MÓDULO FACADE (COMPATIBILIDAD HACIA ATRÁS)

PROPÓSITO:
  Re-export de módulos refactorizados para mantener compatibilidad
  con código existente que importa desde core.semantica.

REFACTORIZACIÓN (PHASE 2):
  Código original (523L) dividido en 4 módulos enfocados:
  - core/domain/categorization.py (150L)
  - core/domain/health_metrics.py (93L)
  - core/domain/normalization.py (200L)
  - core/presentation/visual_mapping.py (80L)

IMPORTAR:
  # Opción 1: Desde facade (compatibilidad)
  from core.semantica import categorizar_cumplimiento, CategoriaCumplimiento

  # Opción 2: Desde módulos específicos (recomendado)
  from core.domain import categorizar_cumplimiento, CategoriaCumplimiento
  from core.domain import recalcular_cumplimiento_faltante
  from core.domain import normalizar_valor_a_porcentaje, normalizar_y_categorizar
  from core.presentation import obtener_color_categoria, obtener_icono_categoria
"""

# Re-export de dominio
from core.domain import (
    CategoriaCumplimiento,
    categorizar_cumplimiento,
    nivel_desde_cumplimiento,
    recalcular_cumplimiento_faltante,
    normalizar_valor_a_porcentaje,
    normalizar_y_categorizar,
)

# Re-export de presentación
from core.presentation import (
    obtener_color_categoria,
    obtener_icono_categoria,
)


# Explicit public API
__all__ = [
    # Categorización
    "CategoriaCumplimiento",
    "categorizar_cumplimiento",
    "nivel_desde_cumplimiento",
    # Métricas de salud
    "recalcular_cumplimiento_faltante",
    # Normalización
    "normalizar_valor_a_porcentaje",
    "normalizar_y_categorizar",
    # Presentación
    "obtener_color_categoria",
    "obtener_icono_categoria",
]
