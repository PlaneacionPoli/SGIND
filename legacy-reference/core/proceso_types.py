"""
core/proceso_types.py — Constantes y paleta de colores para tipos de proceso.

Define los 4 tipos de proceso del sistema y sus colores asociados para
visualizaciones consistentes en el dashboard.
"""

# ── Tipos de Proceso (valores exactos como aparecen en Excel) ─────────────────
TIPOS_PROCESO = ["APOYO", "ESTRATÉGICO", "EVALUACIÓN Y MEJORA", "MISIONAL"]

# ── Paleta de colores por tipo de proceso ─────────────────────────────────────
# Colores institucionales diferenciados para cada tipo
TIPO_PROCESO_COLORS = {
    "APOYO": "#42A5F5",  # Azul claro - soporte
    "ESTRATÉGICO": "#1A3A5C",  # Azul oscuro institucional - estrategia
    "EVALUACIÓN Y MEJORA": "#FB8C00",  # Naranja - evaluación/mejora continua
    "MISIONAL": "#43A047",  # Verde - core/misión
}

# Versiones claras para fondos de tarjetas
TIPO_PROCESO_COLORS_LIGHT = {
    "APOYO": "#E3F2FD",  # Azul muy claro
    "ESTRATÉGICO": "#D0E4FF",  # Azul claro institucional
    "EVALUACIÓN Y MEJORA": "#FFF3E0",  # Naranja claro
    "MISIONAL": "#E8F5E9",  # Verde claro
}

# ── Íconos/emojis por tipo (opcional, para UI) ────────────────────────────────
TIPO_PROCESO_ICONS = {
    "APOYO": "🔧",
    "ESTRATÉGICO": "🎯",
    "EVALUACIÓN Y MEJORA": "📊",
    "MISIONAL": "⭐",
}


def get_tipo_color(tipo: str, light: bool = False) -> str:
    """
    Obtiene el color asociado a un tipo de proceso.

    Args:
        tipo: Nombre del tipo de proceso
        light: Si True, devuelve versión clara para fondos

    Returns:
        Código de color hexadecimal. Si no se encuentra, retorna gris.
    """
    tipo_upper = str(tipo or "").strip().upper()

    # Normalizar variaciones comunes
    if "EVALUACION" in tipo_upper or "EVALUACIÓN" in tipo_upper:
        tipo_upper = "EVALUACIÓN Y MEJORA"

    palette = TIPO_PROCESO_COLORS_LIGHT if light else TIPO_PROCESO_COLORS
    return palette.get(tipo_upper, "#BDBDBD")  # Gris por defecto
