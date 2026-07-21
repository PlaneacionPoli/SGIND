"""
core/config.py — Constantes globales del dashboard.

Fuente única de verdad para colores, umbrales, rutas y columnas de visualización.
Importar SIEMPRE desde aquí: `from core.config import ...`
"""

from pathlib import Path

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent  # raíz del proyecto
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_OUTPUT = BASE_DIR / "data" / "output"
DATA_DB = BASE_DIR / "data" / "db"
DB_PATH = DATA_DB / "registros_om.db"

# ── Paleta de colores institucional ───────────────────────────────────────────
COLORES = {
    "peligro": "#D32F2F",
    "peligro_claro": "#FFCDD2",
    "alerta": "#FBAF17",
    "alerta_claro": "#FEF3D0",
    "cumplimiento": "#43A047",
    "cumplimiento_claro": "#E8F5E9",
    "sobrecumplimiento": "#6699FF",
    "sobrecumplimiento_claro": "#DCE6FF",
    "sin_dato": "#BDBDBD",
    "primario": "#1A3A5C",
    "secundario": "#1565C0",
    "fondo": "#F4F6F9",
    "texto": "#212121",
}

COLOR_CATEGORIA = {
    "Peligro": COLORES["peligro"],
    "Alerta": COLORES["alerta"],
    "Cumplimiento": COLORES["cumplimiento"],
    "Sobrecumplimiento": COLORES["sobrecumplimiento"],
    "Sin dato": COLORES["sin_dato"],
}

COLOR_CATEGORIA_CLARO = {
    "Peligro": COLORES["peligro_claro"],
    "Alerta": COLORES["alerta_claro"],
    "Cumplimiento": COLORES["cumplimiento_claro"],
    "Sobrecumplimiento": COLORES["sobrecumplimiento_claro"],
    "Sin dato": "#EEEEEE",
}

# Colores específicos por Unidad / Vicerrectoría. Definir colores fijos
# para vicerrectorías clave y dejar un color por defecto para las demás.
VICERRECTORIA_COLORS = {
    # Vicerrectorías solicitadas con color fijo
    "Calidad": "#1A3A5C",
    "Expansión": "#1565C0",
    "Experiencia": "#43A047",
    # Puede ampliarse con más mapeos explícitos según se requiera
}

# ── Umbrales de cumplimiento ───────────────────────────────────────────────────
# Generales:  0–79.9% Peligro | 80–99.9% Alerta | 100–104.99% Cumplimiento | ≥105% Sobrecumplimiento
UMBRAL_PELIGRO = 0.80
UMBRAL_ALERTA = 1.00
UMBRAL_SOBRECUMPLIMIENTO = 1.05

# Régimen Negativo-Porcentual: indicadores de sentido Negativo cuya meta y/o
# ejecución están en escala 0-100. < 102% Cumplimiento | 102-110% Alerta | > 110% Peligro
UMBRAL_ALERTA_NEG_PCT = 1.02
UMBRAL_PELIGRO_NEG_PCT = 1.10

# ── Rango válido para Cumplimiento (normalizado) ───────────────────────────
# Los datos de Cumplimiento deben estar en rango [0.0, 1.3]
# donde 1.3 = 130% (máximo permitido tras cappeo)
RANGO_CUMPLIMIENTO_MIN = 0.0
RANGO_CUMPLIMIENTO_MAX = 1.3
RANGO_CUMPLIMIENTO = (RANGO_CUMPLIMIENTO_MIN, RANGO_CUMPLIMIENTO_MAX)

# ── Indicadores Plan Anual (PA) — umbrales especiales ─────────────────────────
# GENERADOS DINÁMICAMENTE desde "Indicadores por CMI.xlsx"
#
# Cumplen desde 95% y su tope de cumplimiento es 100%.
# Un indicador es Plan Anual si en el Excel:
#   - Columna "Plan anual" = 1
#   - O columna "Proyecto" = 1
#
# Función que extrae IDs dinámicamente (sin hardcoding):


def _cargar_ids_plan_anual():
    """
    Extrae dinámicamente IDs de Plan Anual desde la hoja 'Catalogo Indicadores'
    del directorio maestro (antes 'Indicadores por CMI.xlsx').

    NO hardcodea. Se actualiza automáticamente si el Excel cambia.

    Criterio: Un indicador es Plan Anual si:
      - Columna "Plan anual" = 1, O
      - Columna "Proyecto" = 1

    Retorna: frozenset de strings (IDs)
    Fallback: set vacío si Excel no existe o error
    """
    import pandas as pd
    import logging

    logger = logging.getLogger(__name__)

    # Desde la fusión 2026-07-14, vive en la hoja "Catalogo Indicadores" del
    # directorio maestro dedicado 'Catalogo de Indicadores.xlsx' (antes
    # 'Indicadores por CMI.xlsx', archivado en data/raw/_archivados/).
    xlsx_path = DATA_RAW / "Catalogo de Indicadores.xlsx"

    # Si no existe, fallar explícitamente (FALLA SEGURA)
    if not xlsx_path.exists():
        logger.error(f"ARCHIVO REQUERIDO FALTA: {xlsx_path}")
        raise FileNotFoundError(
            f"No se puede cargar IDS_PLAN_ANUAL: {xlsx_path} no existe. "
            f"Verificar que 'Catalogo de Indicadores.xlsx' esté en {DATA_RAW}"
        )

    try:
        # Leer Excel
        df = pd.read_excel(xlsx_path, sheet_name="Catalogo Indicadores", engine="openpyxl")

        # Normalizar nombres de columnas (minúsculas, sin espacios)
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        # Buscar columnas relevantes (con flexibilidad en nombres)
        col_id = None
        col_plan_anual = None
        col_proyecto = None

        for col in df.columns:
            if col in ["id", "id_indicador", "indicador_id"]:
                col_id = col
            if col in ["plan_anual", "plan anual", "plan_anuales"]:
                col_plan_anual = col
            if col in ["proyecto", "proyecto_id"]:
                col_proyecto = col

        # Si no encuentra columnas necesarias, fallar explícitamente
        if col_id is None or (col_plan_anual is None and col_proyecto is None):
            logger.error(
                f"ESQUEMA INCORRECTO en {xlsx_path}. "
                f"Esperado: 'id' (o similar) + 'plan_anual' o 'proyecto' (o similares). "
                f"Encontrado: {list(df.columns)}"
            )
            raise ValueError(
                f"Columnas requeridas no encontradas en {xlsx_path}. "
                f"Esperado: id, plan_anual (o proyecto). "
                f"Columnas encontradas: {list(df.columns)}"
            )

        # Extraer IDs donde (Plan anual=1) OR (Proyecto=1)
        mascara = pd.Series([False] * len(df))

        if col_plan_anual:
            mascara |= df[col_plan_anual] == 1

        if col_proyecto:
            mascara |= df[col_proyecto] == 1

        ids = df.loc[mascara, col_id].astype(str).tolist()
        ids_plan_anual = frozenset(ids)

        logger.info(f"Cargados {len(ids_plan_anual)} indicadores Plan Anual: {ids_plan_anual}")

        return ids_plan_anual

    except Exception as e:
        logger.critical(f"FALLO CRÍTICO al cargar IDS_PLAN_ANUAL: {type(e).__name__}: {e}")
        raise RuntimeError(
            f"No se puede inicializar el sistema sin IDS_PLAN_ANUAL. "
            f"Error: {type(e).__name__}: {e}"
        ) from e


# Cargar dinámicamente (se ejecuta en tiempo de importación)
IDS_PLAN_ANUAL = _cargar_ids_plan_anual()

# Validación: IDS_PLAN_ANUAL nunca debe estar vacío
if not IDS_PLAN_ANUAL:
    raise RuntimeError(
        "FALLO CRÍTICO: IDS_PLAN_ANUAL está vacío después de cargar. "
        "Verificar que 'Catalogo Indicadores' (Catalogo de Indicadores.xlsx) "
        "contiene indicadores con columna 'Plan_Anual'=1 o 'Proyecto'=1"
    )

UMBRAL_ALERTA_PA = 0.95  # PA cumple desde 95%
UMBRAL_SOBRECUMPLIMIENTO_PA = 1.00  # tope 100%

# ── Indicadores con tope de cumplimiento 100% (no sobrecumplimiento) ──────────
# Indicadores de sentido Negativo cuyo cumplimiento no debe superar el 100%.
IDS_TOPE_100 = {"208", "218", "92", "104", "106", "124", "125", "126", "127", "128", "272"}

# ── Indicadores Negativo-Porcentual (régimen 102%/110%) ───────────────────────
# Lista curada (jul-2026): < 102% Cumplimiento | 102-110% Alerta | > 110% Peligro
IDS_NEGATIVO_PCT = {"121", "207", "377", "561"}

# ── Aliases de colores para compatibilidad heredada ──────────────────────────
# (core/niveles.py usaba estos nombres)
NIVEL_COLOR = COLOR_CATEGORIA
NIVEL_BG = COLOR_CATEGORIA_CLARO

NIVEL_ICON = {
    "Peligro": "🔴",
    "Alerta": "🟡",
    "Cumplimiento": "🟢",
    "Sobrecumplimiento": "🟢",  # compat con datos históricos (antes usaba 🔵)
    "Sin dato": "⚪",
}

# ── Orden y visualización de categorías ───────────────────────────────────────
ORDEN_CATEGORIAS = ["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento", "Sin dato"]

ICONOS_CATEGORIA = {
    "Peligro": "🔴",
    "Alerta": "🟡",
    "Cumplimiento": "🟢",
    "Sobrecumplimiento": "🔵",
}

# ── Alias para compatibilidad ──────────────────────────────────────────────────
NIVEL_ORDEN = ORDEN_CATEGORIAS

# ── Columnas de visualización por página ──────────────────────────────────────
COLS_TABLA_RESUMEN = [
    "Id",
    "Indicador",
    "Proceso",
    "Subproceso",
    "Cumplimiento%",
    "Categoria",
    "Clasificacion",
    "Periodicidad",
]

COLS_TABLA_RIESGO = [
    "Id",
    "Indicador",
    "Proceso",
    "Subproceso",
    "Periodicidad",
    "Periodo",
    "Cumplimiento%",
    "Categoria",
]

COLS_TABLA_OM = [
    "id_indicador",
    "nombre_indicador",
    "proceso",
    "periodo",
    "anio",
    "tiene_om",
    "numero_om",
    "comentario",
    "fecha_registro",
]

# ── Cache TTL (segundos) ───────────────────────────────────────────────────────
CACHE_TTL = 300

# ── Strings de estado / dominio — FUENTE ÚNICA DE VERDAD ──────────────────────
# Usar siempre estas constantes; nunca strings literales en el código.
ESTADO_NO_APLICA = "No Aplica"
ESTADO_PENDIENTE = "Pendiente de reporte"
ESTADO_SIN_DATO = "Sin dato"

SENTIDO_POSITIVO = "Positivo"
SENTIDO_NEGATIVO = "Negativo"

TIPO_METRICA = "metrica"
TIPO_NO_APLICA = "no aplica"
