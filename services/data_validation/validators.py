"""
services/data_validation/validators.py
======================================

Core validation functions for checking data against contracts.

Responsibility: Implement data validation rules (columns, types, categories, nulls, ranges).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from .models import ValidationIssue
from .utils import (
    find_matching_column,
    iter_hojas,
    normalize_allowed_values,
    normalize_series_values,
)

# ============================================================================
# VALIDATORS
# ============================================================================


def validate_required_columns(
    df: pd.DataFrame,
    contract: Dict[str, Any],
    target_sheet: Optional[str] = None,
) -> List[ValidationIssue]:
    """Check that required columns exist."""
    issues = []

    for hoja_name, hoja_spec in iter_hojas(contract, target_sheet):
        columnas = hoja_spec.get("columnas", {})

        for col_name, col_spec in columnas.items():
            if col_spec.get("requerida", False):
                actual_col = find_matching_column(df.columns, col_name)
                if actual_col is None:
                    issues.append(
                        ValidationIssue(
                            level="error",
                            rule="Required Column Missing",
                            sheet=hoja_name,
                            column=col_name,
                            description=f"Required column '{col_name}' not found",
                        )
                    )

    return issues


def validate_column_types(
    df: pd.DataFrame,
    contract: Dict[str, Any],
    target_sheet: Optional[str] = None,
) -> List[ValidationIssue]:
    """Check data types match contract."""
    issues = []

    for hoja_name, hoja_spec in iter_hojas(contract, target_sheet):
        columnas = hoja_spec.get("columnas", {})

        for col_name, col_spec in columnas.items():
            actual_col = find_matching_column(df.columns, col_name)
            if actual_col is None:
                continue

            col_type = col_spec.get("tipo", "string")
            col_data = df[actual_col].dropna()

            # Type check (basic)
            if col_type == "integer":
                non_int = col_data[~col_data.astype(str).str.match(r"^-?\d+$")]
                if len(non_int) > 0:
                    issues.append(
                        ValidationIssue(
                            level="warning",
                            rule="Type Mismatch",
                            sheet=hoja_name,
                            column=col_name,
                            row_count=len(non_int),
                            description=f"Column '{col_name}' should be integer but found non-integers",
                            values_sample=non_int.unique()[:3].tolist(),
                        )
                    )

            elif col_type == "float":
                try:
                    col_data.astype(float)
                except (ValueError, TypeError):
                    non_float = col_data[pd.to_numeric(col_data, errors="coerce").isna()]
                    issues.append(
                        ValidationIssue(
                            level="warning",
                            rule="Type Mismatch",
                            sheet=hoja_name,
                            column=col_name,
                            row_count=len(non_float),
                            description=f"Column '{col_name}' should be float but found non-floats",
                            values_sample=non_float.unique()[:3].tolist(),
                        )
                    )

    return issues


def validate_categorical_values(
    df: pd.DataFrame,
    contract: Dict[str, Any],
    target_sheet: Optional[str] = None,
) -> List[ValidationIssue]:
    """Check categorical values are in allowed set."""
    issues = []

    for hoja_name, hoja_spec in iter_hojas(contract, target_sheet):
        columnas = hoja_spec.get("columnas", {})

        for col_name, col_spec in columnas.items():
            actual_col = find_matching_column(df.columns, col_name)
            if actual_col is None:
                continue

            if col_spec.get("tipo") != "categorical":
                continue

            valores_permitidos = col_spec.get("valores_permitidos", [])
            if not valores_permitidos:
                continue

            normalized_allowed = normalize_allowed_values(valores_permitidos)
            col_data = df[actual_col].dropna()
            normalized_data = normalize_series_values(col_data)
            invalid_mask = ~normalized_data.isin(normalized_allowed)
            invalid_values = col_data[invalid_mask]

            if len(invalid_values) > 0:
                issues.append(
                    ValidationIssue(
                        level="warning",
                        rule="Invalid Categorical Value",
                        sheet=hoja_name,
                        column=col_name,
                        row_count=len(invalid_values),
                        description=f"Column '{col_name}' has values outside allowed set: {valores_permitidos}",
                        values_sample=invalid_values.unique()[:3].tolist(),
                    )
                )

    return issues


def validate_null_constraints(
    df: pd.DataFrame,
    contract: Dict[str, Any],
    target_sheet: Optional[str] = None,
) -> List[ValidationIssue]:
    """Check null value constraints."""
    issues = []

    for hoja_name, hoja_spec in iter_hojas(contract, target_sheet):
        columnas = hoja_spec.get("columnas", {})

        for col_name, col_spec in columnas.items():
            actual_col = find_matching_column(df.columns, col_name)
            if actual_col is None:
                continue

            if col_spec.get("requerida", False):
                null_count = df[actual_col].isna().sum()
                if null_count > 0:
                    issues.append(
                        ValidationIssue(
                            level="error",
                            rule="Null in Required Column",
                            sheet=hoja_name,
                            column=col_name,
                            row_count=null_count,
                            description=f"Column '{col_name}' has {null_count} null values but is required",
                        )
                    )

    return issues


def validate_numeric_ranges(
    df: pd.DataFrame,
    contract: Dict[str, Any],
    target_sheet: Optional[str] = None,
) -> List[ValidationIssue]:
    """Check minimum/maximum value constraints."""
    issues = []

    for hoja_name, hoja_spec in iter_hojas(contract, target_sheet):
        columnas = hoja_spec.get("columnas", {})

        for col_name, col_spec in columnas.items():
            actual_col = find_matching_column(df.columns, col_name)
            if actual_col is None:
                continue

            col_data = pd.to_numeric(df[actual_col], errors="coerce").dropna()

            # Min check
            min_val = col_spec.get("min")
            if min_val is not None:
                below_min = col_data[col_data < min_val]
                if len(below_min) > 0:
                    issues.append(
                        ValidationIssue(
                            level="warning",
                            rule="Value Below Minimum",
                            sheet=hoja_name,
                            column=col_name,
                            row_count=len(below_min),
                            description=f"Column '{col_name}' has {len(below_min)} values < {min_val}",
                            values_sample=below_min.unique()[:3].tolist(),
                        )
                    )

            # Max check
            max_val = col_spec.get("max")
            if max_val is not None:
                above_max = col_data[col_data > max_val]
                if len(above_max) > 0:
                    issues.append(
                        ValidationIssue(
                            level="warning",
                            rule="Value Above Maximum",
                            sheet=hoja_name,
                            column=col_name,
                            row_count=len(above_max),
                            description=f"Column '{col_name}' has {len(above_max)} values > {max_val}",
                            values_sample=above_max.unique()[:3].tolist(),
                        )
                    )

    return issues
