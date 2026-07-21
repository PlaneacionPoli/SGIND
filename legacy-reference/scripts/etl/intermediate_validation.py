"""
scripts/etl/intermediate_validation.py
Validación en capas intermedias del pipeline ETL.

Proporciona validaciones específicas para cada paso del ETL:
- Después de consolidar_api.py
- Después de construir registros
- Antes de escribir a Excel
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class LayerValidationResult:
    """Resultado de validación de capa intermedia."""
    
    layer: str
    status: str  # "ok" | "warning" | "error"
    checks_passed: int = 0
    checks_failed: int = 0
    warnings: List[str] = None
    errors: List[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []
        if self.metrics is None:
            self.metrics = {}


def validate_after_consolidar_api(
    df_api: pd.DataFrame,
    df_kawak: Optional[pd.DataFrame] = None
) -> LayerValidationResult:
    """
    LAYER 1.5: Validación post-consolidación de API.
    
    Se ejecuta después de consolidar_api.py y antes de actualizar_consolidado.py.
    
    Args:
        df_api: DataFrame del consolidado API
        df_kawak: DataFrame del catálogo Kawak (opcional)
    
    Returns:
        LayerValidationResult con status y métricas
    """
    result = LayerValidationResult(layer="post_consolidar_api", status="ok")
    
    # Check 1: Tamaño mínimo
    if len(df_api) < 1000:
        result.warnings.append(f"Consolidado API pequeño ({len(df_api)} registros)")
    else:
        result.checks_passed += 1
    
    result.metrics["total_registros"] = len(df_api)
    
    # Check 2: IDs únicos
    if "ID" in df_api.columns:
        unique_ids = df_api["ID"].nunique()
        result.metrics["ids_unicos"] = unique_ids
        
        if unique_ids < 50:
            result.warnings.append(f"Pocos IDs únicos ({unique_ids})")
        else:
            result.checks_passed += 1
    
    # Check 3: Rango de fechas
    if "fecha" in df_api.columns:
        try:
            fechas = pd.to_datetime(df_api["fecha"], errors="coerce")
            fecha_min = fechas.min()
            fecha_max = fechas.max()
            
            result.metrics["fecha_min"] = str(fecha_min.date()) if pd.notna(fecha_min) else None
            result.metrics["fecha_max"] = str(fecha_max.date()) if pd.notna(fecha_max) else None
            
            # Verificar que hay datos de al menos 1 año
            if pd.notna(fecha_min) and pd.notna(fecha_max):
                dias = (fecha_max - fecha_min).days
                if dias < 365:
                    result.warnings.append(f"Rango de fechas menor a 1 año ({dias} días)")
                else:
                    result.checks_passed += 1
        except Exception as e:
            result.errors.append(f"Error procesando fechas: {e}")
            result.checks_failed += 1
    
    # Check 4: Campos requeridos
    required_cols = {"ID", "fecha", "resultado"}
    missing = required_cols - set(df_api.columns)
    if missing:
        result.errors.append(f"Campos faltantes: {missing}")
        result.checks_failed += 1
    else:
        result.checks_passed += 1
    
    # Check 5: Valores nulos en críticas
    for col in ["ID", "fecha"]:
        if col in df_api.columns:
            nulos = df_api[col].isnull().sum()
            if nulos > 0:
                result.warnings.append(f"{nulos} nulos en '{col}'")
            else:
                result.checks_passed += 1
    
    # Determinar status final
    if result.checks_failed > 0:
        result.status = "error"
    elif result.warnings:
        result.status = "warning"
    
    return result


def validate_after_build_records(
    records: List[Dict],
    layer_name: str = "unknown"
) -> LayerValidationResult:
    """
    LAYER 2: Validación post-construcción de registros.
    
    Se ejecuta después de construir_registros_* y antes de escribir.
    
    Args:
        records: Lista de dicts con los registros construidos
        layer_name: Nombre de la capa (historico, semestral, cierres)
    
    Returns:
        LayerValidationResult con status y métricas
    """
    result = LayerValidationResult(layer=f"post_build_{layer_name}", status="ok")
    
    if not records:
        result.warnings.append("Sin registros construidos")
        result.metrics["total_registros"] = 0
        return result
    
    df = pd.DataFrame(records)
    result.metrics["total_registros"] = len(df)
    
    # Check 1: Llaves únicas
    if "LLAVE" in df.columns:
        duplicados = df["LLAVE"].duplicated().sum()
        if duplicados > 0:
            result.warnings.append(f"{duplicados} llaves duplicadas")
        else:
            result.checks_passed += 1
        
        result.metrics["llaves_unicas"] = df["LLAVE"].nunique()
    
    # Check 2: Campos requeridos por capa
    required_by_layer = {
        "historico": ["Id", "Fecha", "Meta", "Ejecucion"],
        "semestral": ["Id", "Fecha", "Meta", "Ejecucion"],
        "cierres": ["Id", "Fecha", "Meta", "Ejecucion"]
    }
    
    required = required_by_layer.get(layer_name, ["Id", "Fecha"])
    missing = set(required) - set(df.columns)
    if missing:
        result.errors.append(f"Campos faltantes en {layer_name}: {missing}")
        result.checks_failed += 1
    else:
        result.checks_passed += 1
    
    # Check 3: Rangos de valores
    for col in ["Meta", "Ejecucion"]:
        if col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            valid = numeric[numeric.notna()]
            
            if len(valid) > 0:
                min_val = valid.min()
                max_val = valid.max()
                
                result.metrics[f"{col}_min"] = float(min_val)
                result.metrics[f"{col}_max"] = float(max_val)
                
                if min_val < 0:
                    result.warnings.append(f"Valores negativos en '{col}'")
                elif max_val > 1.3:
                    result.warnings.append(f"Valores > 1.3 en '{col}'")
                else:
                    result.checks_passed += 1
    
    # Check 4: Sin registros vacíos
    empty_rows = df.isnull().all(axis=1).sum()
    if empty_rows > 0:
        result.warnings.append(f"{empty_rows} filas completamente vacías")
    else:
        result.checks_passed += 1
    
    # Determinar status final
    if result.checks_failed > 0:
        result.status = "error"
    elif result.warnings:
        result.status = "warning"
    
    return result


def validate_before_write(
    df: pd.DataFrame,
    sheet_name: str = "unknown"
) -> LayerValidationResult:
    """
    LAYER 3: Validación pre-escritura a Excel.
    
    Se ejecuta justo antes de escribir al consolidado final.
    
    Args:
        df: DataFrame a escribir
        sheet_name: Nombre de la hoja destino
    
    Returns:
        LayerValidationResult con status y métricas
    """
    result = LayerValidationResult(layer=f"pre_write_{sheet_name}", status="ok")
    
    if df.empty:
        result.errors.append("DataFrame vacío")
        result.checks_failed += 1
        return result
    
    result.metrics["total_registros"] = len(df)
    
    # Check 1: Columnas esperadas
    expected_cols = {"Id", "Fecha", "Meta", "Ejecucion"}
    missing = expected_cols - set(df.columns)
    if missing:
        result.errors.append(f"Columnas faltantes: {missing}")
        result.checks_failed += 1
    else:
        result.checks_passed += 1
    
    # Check 2: Integridad referencial
    if "Id" in df.columns:
        nulos_id = df["Id"].isnull().sum()
        if nulos_id > 0:
            result.errors.append(f"{nulos_id} IDs nulos")
            result.checks_failed += 1
        else:
            result.checks_passed += 1
    
    # Check 3: Fechas válidas
    if "Fecha" in df.columns:
        try:
            fechas = pd.to_datetime(df["Fecha"], errors="coerce")
            invalidas = fechas.isnull().sum()
            if invalidas > 0:
                result.warnings.append(f"{invalidas} fechas inválidas")
            else:
                result.checks_passed += 1
        except Exception:
            result.warnings.append("Error procesando fechas")
    
    # Check 4: Sin duplicados exactos
    duplicados = df.duplicated().sum()
    if duplicados > 0:
        result.warnings.append(f"{duplicados} filas duplicadas exactas")
    else:
        result.checks_passed += 1
    
    # Check 5: Tamaño razonable
    if len(df) > 50000:
        result.warnings.append(f"Dataset muy grande ({len(df)} registros)")
    elif len(df) < 10:
        result.warnings.append(f"Dataset muy pequeño ({len(df)} registros)")
    else:
        result.checks_passed += 1
    
    # Determinar status final
    if result.checks_failed > 0:
        result.status = "error"
    elif result.warnings:
        result.status = "warning"
    
    return result


def log_validation_result(result: LayerValidationResult) -> None:
    """Loguear resultado de validación de forma legible."""
    
    status_icons = {
        "ok": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    icon = status_icons.get(result.status, "❓")
    logger.info(f"{icon} Validación {result.layer}: {result.status.upper()}")
    logger.info(f"   Checks pasados: {result.checks_passed}")
    
    if result.warnings:
        logger.warning(f"   Warnings ({len(result.warnings)}):")
        for warn in result.warnings[:3]:  # Mostrar máximo 3
            logger.warning(f"     - {warn}")
    
    if result.errors:
        logger.error(f"   Errors ({len(result.errors)}):")
        for err in result.errors[:3]:
            logger.error(f"     - {err}")
    
    if result.metrics:
        logger.info(f"   Métricas: {result.metrics}")
