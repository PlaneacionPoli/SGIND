"""
core/db/data_normalizer.py — Normalización de datos temporales.

Responsabilidad única: Convertir diferentes formatos de mes/período/año
a formato estándar esperado por la aplicación.

Sin lógica de BD, conexiones o CRUD.
"""

import re
import logging
from typing import Any, Tuple

logger = logging.getLogger(__name__)

# Meses en español (índices 1-12)
MESES_ESPANOL = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# Mapeo de variaciones de nombres de mes
MESES_NORMALIZACION_MAP = {
    "ene": "Enero", "ene.": "Enero", "enero": "Enero",
    "feb": "Febrero", "feb.": "Febrero", "febrero": "Febrero",
    "mar": "Marzo", "mar.": "Marzo", "marzo": "Marzo",
    "abr": "Abril", "abr.": "Abril", "abril": "Abril",
    "may": "Mayo", "mayo": "Mayo",
    "jun": "Junio", "jun.": "Junio", "junio": "Junio",
    "jul": "Julio", "jul.": "Julio", "julio": "Julio",
    "ago": "Agosto", "ago.": "Agosto", "agosto": "Agosto",
    "sep": "Septiembre", "sep.": "Septiembre", "sept": "Septiembre", 
    "sept.": "Septiembre", "septiembre": "Septiembre",
    "oct": "Octubre", "oct.": "Octubre", "octubre": "Octubre",
    "nov": "Noviembre", "nov.": "Noviembre", "noviembre": "Noviembre",
    "dic": "Diciembre", "dic.": "Diciembre", "diciembre": "Diciembre",
}


def numero_mes_a_nombre(numero: int) -> str:
    """Convierte número de mes (1-12) a nombre en español.
    
    Args:
        numero: Mes como número (1-12)
        
    Returns:
        Nombre del mes en español (ej: "Enero"), o string del número si inválido
    """
    try:
        if 1 <= numero <= 12:
            return MESES_ESPANOL[numero - 1]
    except (TypeError, IndexError):
        pass
    return str(numero)


def normalizar_nombre_mes(mes: Any) -> str:
    """Normaliza diferentes variaciones de nombre de mes a formato estándar.
    
    Acepta:
    - "Enero", "enero", "ene", "ene.", "ENE"
    - "1" (número como string) → "Enero"
    - Nombres en español
    
    Args:
        mes: Mes en cualquier formato
        
    Returns:
        Nombre de mes normalizado (ej: "Enero"), o string original si no reconocido
    """
    texto = str(mes or "").strip()
    if not texto:
        return ""
    
    texto_lower = texto.lower()
    
    # Buscar en mapeo de normalización
    if texto_lower in MESES_NORMALIZACION_MAP:
        return MESES_NORMALIZACION_MAP[texto_lower]
    
    # Si es número, convertir
    if texto.isdigit():
        return numero_mes_a_nombre(int(texto))
    
    # Si no coincide, capitalizar y retornar
    return texto.capitalize()


def normalizar_periodo_anio(
    periodo: Any, anio: Any = None
) -> Tuple[str, int]:
    """Normaliza periodo y año a formato (mes_nombre: str, año: int).
    
    Acepta múltiples formatos:
    - periodo="2024-01", anio=None → ("Enero", 2024)
    - periodo="Enero", anio=2024 → ("Enero", 2024)
    - periodo="1", anio=2024 → ("Enero", 2024)
    - periodo="2024/01", anio=None → ("Enero", 2024)
    
    Args:
        periodo: Mes/período en varios formatos
        anio: Año (int o string), usa año de periodo si no presente
        
    Returns:
        Tupla (mes_nombre, año): (str, int) normalizado
    """
    periodo_str = str(periodo or "").strip()
    anio_int = 0
    
    # Parsear año si es int
    if isinstance(anio, int):
        anio_int = anio
    else:
        anio_text = str(anio or "").strip()
        if anio_text.isdigit():
            anio_int = int(anio_text)
    
    # Si período vacío, retornar defaults
    if not periodo_str:
        return "", anio_int
    
    # Patrón YYYY-MM o YYYY/MM (extrae año y mes)
    match = re.match(r"^(\d{4})[-/](\d{1,2})$", periodo_str)
    if match:
        anio_int = int(match.group(1))
        mes_num = int(match.group(2))
        return numero_mes_a_nombre(mes_num), anio_int
    
    # Si es número puro, tratar como mes
    if periodo_str.isdigit():
        numero = int(periodo_str)
        if 1 <= numero <= 12:
            return numero_mes_a_nombre(numero), anio_int
    
    # Normalizar como nombre de mes
    return normalizar_nombre_mes(periodo_str), anio_int
