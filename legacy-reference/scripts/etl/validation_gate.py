"""
scripts/etl/validation_gate.py
Validación centralizada de contratos de datos en pipeline ETL.

RESPONSABILIDAD: Verificar que datos cumplen especificación ANTES de procesarlos.
PRINCIPIO: "No procesar garbage" — bloquear pipeline si hay errores críticos.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Resultado de validación de contrato."""

    status: str  # "ok" | "warning" | "error"
    error_count: int = 0
    warning_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [f"Status: {self.status}"]
        if self.error_count:
            lines.append(f"  Errors ({self.error_count}):")
            for err in self.errors[:5]:  # mostrar máximo 5
                lines.append(f"    - {err}")
            if len(self.errors) > 5:
                lines.append(f"    ... y {len(self.errors) - 5} más")
        if self.warning_count:
            lines.append(f"  Warnings ({self.warning_count}):")
            for warn in self.warnings[:5]:
                lines.append(f"    - {warn}")
            if len(self.warnings) > 5:
                lines.append(f"    ... y {len(self.warnings) - 5} más")
        return "\n".join(lines)


def validar_consolidado_api_entrada(
    df: pd.DataFrame, min_rows: int = 100, verbose: bool = True
) -> ValidationResult:
    """
    VALIDACIÓN GATE LAYER 1: Contrato de datos de entrada.

    Valida que Consolidado_API_Kawak.xlsx cumple especificación mínima.
    Si devuelve status="error", el pipeline debe bloquearse.

    Args:
        df: DataFrame cargado desde Consolidado_API_Kawak.xlsx
        min_rows: Mínimo de filas esperadas (default 100)
        verbose: Loguear resultado (default True)

    Returns:
        ValidationResult con status, errores y warnings.
    """
    result = ValidationResult(status="ok")

    # 1. COLUMNAS REQUERIDAS (notar que ID se renombra a Id en cargar_fuente_consolidada)
    cols_requeridas = {"Id", "fecha", "resultado"}
    cols_disponibles = set(df.columns)
    cols_faltantes = cols_requeridas - cols_disponibles

    if cols_faltantes:
        result.errors.append(f"Columnas faltantes: {', '.join(sorted(cols_faltantes))}")
        result.error_count += 1

    # 2. NULOS EN CRÍTICAS (bloquear si hay)
    if not result.errors:  # solo si pasó validación de columnas
        for col in ["Id", "fecha"]:
            if col in df.columns:
                nulos = df[col].isnull().sum()
                if nulos > 0:
                    result.errors.append(f"{nulos} nulos en columna requerida '{col}'")
                    result.error_count += 1

    # 3. CARDINALIDAD: Id-fecha única (warning, no error)
    if "Id" in df.columns and "fecha" in df.columns:
        duplicados = df.groupby(["Id", "fecha"]).size()
        dup_count = (duplicados > 1).sum()
        if dup_count > 0:
            result.warnings.append(
                f"{dup_count} combinaciones ID-fecha duplicadas (se procesa primera)"
            )
            result.warning_count += 1

    # 4. RANGO DE FECHAS
    if "fecha" in df.columns:
        try:
            fechas = pd.to_datetime(df["fecha"], errors="coerce")
            fecha_invalidas = fechas.isna().sum()

            if fecha_invalidas > 0:
                result.warnings.append(f"{fecha_invalidas} fechas no convertibles")
                result.warning_count += 1

            # Solo revisar rango si hay fechas válidas
            fechas_validas = fechas[fechas.notna()]
            if len(fechas_validas) > 0:
                fecha_min = fechas_validas.min()
                fecha_max = fechas_validas.max()

                if fecha_min < pd.Timestamp("2020-01-01"):
                    result.warnings.append(f"Fecha mínima muy antigua: {fecha_min.date()}")
                    result.warning_count += 1

                if fecha_max > pd.Timestamp("2030-12-31"):
                    result.warnings.append(f"Fecha máxima futura: {fecha_max.date()}")
                    result.warning_count += 1

        except Exception as e:
            result.errors.append(f"Error procesando fechas: {e}")
            result.error_count += 1

    # 5. CARDINALIDAD TOTAL
    if len(df) < min_rows:
        result.warnings.append(f"Dataset pequeño ({len(df)} < {min_rows} mínimo esperado)")
        result.warning_count += 1

    if len(df) == 0:
        result.errors.append("DataFrame vacío (0 filas)")
        result.error_count += 1

    # 6. TIPOS DE DATO (validación suave)
    if "resultado" in df.columns:
        try:
            pd.to_numeric(df["resultado"], errors="coerce")
            non_numeric = df["resultado"].apply(
                lambda x: not pd.isna(x) and pd.isna(pd.to_numeric(x, errors="coerce"))
            ).sum()
            if non_numeric > 0:
                result.warnings.append(f"{non_numeric} valores no numéricos en 'resultado'")
                result.warning_count += 1
                
            # 7. RANGO DE RESULTADOS (0-1.3 según reglas de negocio)
            numeric_results = pd.to_numeric(df["resultado"], errors="coerce")
            valid_results = numeric_results[numeric_results.notna()]
            
            if len(valid_results) > 0:
                min_val = valid_results.min()
                max_val = valid_results.max()
                
                # Valores negativos (warning, puede haber datos válidos)
                negative_count = (valid_results < 0).sum()
                if negative_count > 0:
                    result.warnings.append(
                        f"{negative_count} resultados negativos en 'resultado' (mínimo: {min_val})"
                    )
                    result.warning_count += 1
                
                # Valores mayores a 1.3 (130%)
                over_max = (valid_results > 1.3).sum()
                if over_max > 0:
                    result.warnings.append(
                        f"{over_max} resultados > 1.3 (130%) en 'resultado' (máximo: {max_val})"
                    )
                    result.warning_count += 1
                    
        except Exception:
            pass

    # Determinar status final
    if result.error_count > 0:
        result.status = "error"
    elif result.warning_count > 0:
        result.status = "warning"
    else:
        result.status = "ok"

    # Loguear resultado
    if verbose:
        if result.status == "ok":
            logger.info(f"✅ Validación OK: {len(df)} registros pasaron contrato")
        elif result.status == "warning":
            logger.warning(f"⚠️ Validación con warnings ({result.warning_count}):")
            for warn in result.warnings:
                logger.warning(f"   {warn}")
        else:
            logger.error(f"❌ Validación FALLIDA ({result.error_count} errores):")
            for err in result.errors:
                logger.error(f"   {err}")

    return result


def validar_consolidado_salida(
    df: pd.DataFrame, min_rows: int = 100
) -> ValidationResult:
    """
    VALIDACIÓN GATE LAYER 2: Contrato de datos de salida.

    Valida que consolidado ANTES de escribir a Excel.

    Args:
        df: DataFrame a escribir en Resultados_Consolidados.xlsx
        min_rows: Mínimo de filas esperadas

    Returns:
        ValidationResult con status, errores y warnings.
    """
    result = ValidationResult(status="ok")

    # 1. Columnas esperadas en salida
    cols_esperadas = {
        "Id",
        "Fecha",
        "Meta",
        "Ejecucion",
        "Cumplimiento",
        "Categoria",
        "Anio",
        "Mes",
    }
    cols_faltantes = cols_esperadas - set(df.columns)

    if cols_faltantes:
        result.errors.append(f"Columnas faltantes en salida: {', '.join(sorted(cols_faltantes))}")
        result.error_count += 1

    # 2. Integridad referencial: todo Id debe ser válido
    if "Id" in df.columns:
        nulos_id = df["Id"].isnull().sum()
        if nulos_id > 0:
            result.errors.append(f"{nulos_id} nulos en 'Id' (requerido)")
            result.error_count += 1

    # 3. Tamaño mínimo
    if len(df) < min_rows:
        result.errors.append(f"Consolidado muy pequeño ({len(df)} < {min_rows})")
        result.error_count += 1
    
    # 4. RANGOS DE CAMPOS NUMÉRICOS
    for col in ["Meta", "Ejecucion"]:
        if col in df.columns:
            numeric_vals = pd.to_numeric(df[col], errors="coerce")
            valid_vals = numeric_vals[numeric_vals.notna()]
            
            if len(valid_vals) > 0:
                # Valores negativos
                negative_count = (valid_vals < 0).sum()
                if negative_count > 0:
                    result.warnings.append(
                        f"{negative_count} valores negativos en '{col}'"
                    )
                    result.warning_count += 1
                
                # Valores mayores a 1.3 (130%)
                over_max = (valid_vals > 1.3).sum()
                if over_max > 0:
                    result.warnings.append(
                        f"{over_max} valores > 1.3 (130%) en '{col}'"
                    )
                    result.warning_count += 1
    
    # 5. CUMPLIMIENTO EN RANGO VÁLIDO (0-1 o vacío)
    if "Cumplimiento" in df.columns:
        # El cumplimiento debe ser 0-1 o vacío
        numeric_cum = pd.to_numeric(df["Cumplimiento"], errors="coerce")
        valid_cum = numeric_cum[numeric_cum.notna()]
        
        if len(valid_cum) > 0:
            invalid_range = ((valid_cum < 0) | (valid_cum > 1)).sum()
            if invalid_range > 0:
                result.warnings.append(
                    f"{invalid_range} valores fuera de rango [0,1] en 'Cumplimiento'"
                )
                result.warning_count += 1

    # Determinar status
    if result.error_count > 0:
        result.status = "error"
    else:
        result.status = "ok"

    return result
