"""Umbrales y constantes de negocio — portados desde core/config.py."""

from enum import Enum

UMBRAL_PELIGRO = 0.80
UMBRAL_ALERTA = 1.00
UMBRAL_SOBRECUMPLIMIENTO = 1.05
UMBRAL_ALERTA_PA = 0.95
UMBRAL_SOBRECUMPLIMIENTO_PA = 1.00

# Régimen Negativo-Porcentual: indicadores de sentido Negativo cuya meta y/o
# ejecución están en escala 0-100. < 102% Cumplimiento | 102-110% Alerta | > 110% Peligro
UMBRAL_ALERTA_NEG_PCT = 1.02
UMBRAL_PELIGRO_NEG_PCT = 1.10

# Fallback desde settings.toml [business] si no se carga Excel
IDS_PLAN_ANUAL_DEFAULT = frozenset(
    {"373", "390", "414", "415", "416", "417", "418", "420", "469", "470", "471"}
)
IDS_TOPE_100 = frozenset({"208", "218"})

# Régimen Negativo-Porcentual (102%/110%): lista curada (jul-2026)
IDS_NEGATIVO_PCT = frozenset({"121", "207", "377", "561"})

RANGO_CUMPLIMIENTO_MIN = 0.0
RANGO_CUMPLIMIENTO_MAX = 1.3

# Paleta oficial confirmada con negocio 2026-09-20 (Oleada 2) — debe coincidir
# exactamente con frontend/src/lib/design-tokens.ts (SEMAFORO), fuente única
# de color en toda la app. Peligro se mantiene en el rojo institucional
# existente; Alerta/Cumplimiento/Sobrecumplimiento adoptan la paleta Tailwind
# que el frontend ya usaba en sus gráficos Plotly/Recharts.
COLOR_CATEGORIA = {
    "Peligro": "#D32F2F",
    "Alerta": "#f59e0b",
    "Cumplimiento": "#22c55e",
    "Sobrecumplimiento": "#3b82f6",
    "Sin dato": "#BDBDBD",
}


class CategoriaCumplimiento(str, Enum):
    PELIGRO = "Peligro"
    ALERTA = "Alerta"
    CUMPLIMIENTO = "Cumplimiento"
    SOBRECUMPLIMIENTO = "Sobrecumplimiento"
    SIN_DATO = "Sin dato"
