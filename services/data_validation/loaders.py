"""
services/data_validation/loaders.py
===================================

Source file validation and data freshness checking.

Responsibility: Load and validate source files; check data freshness.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from .models import ValidationIssue, ValidationReport
from .utils import load_contracts
from .validators import (
    validate_required_columns,
    validate_column_types,
    validate_categorical_values,
    validate_null_constraints,
    validate_numeric_ranges,
)


# ============================================================================
# PUBLIC API
# ============================================================================


def validate_dataset(
    df: pd.DataFrame,
    source_name: str,
    sheet_name: Optional[str] = None,
) -> ValidationReport:
    """
    Validate a dataset against its data contract.

    Args:
        df: DataFrame to validate
        source_name: Name of data source (key in data_contracts.yaml)
        sheet_name: Optional sheet name for Excel files

    Returns:
        ValidationReport with all issues found
    """
    contracts = load_contracts()

    if source_name not in contracts:
        report = ValidationReport(
            source_name=source_name,
            dataset_shape=df.shape,
        )
        report.add_issue(
            ValidationIssue(
                level="warning",
                rule="No Contract Found",
                description=f"No contract defined for '{source_name}' in data_contracts.yaml",
            )
        )
        return report

    contract = contracts[source_name]
    report = ValidationReport(
        source_name=source_name,
        dataset_shape=df.shape,
    )

    # Run all validators
    all_issues = []
    all_issues.extend(validate_required_columns(df, contract, target_sheet=sheet_name))
    all_issues.extend(validate_column_types(df, contract, target_sheet=sheet_name))
    all_issues.extend(validate_categorical_values(df, contract, target_sheet=sheet_name))
    all_issues.extend(validate_null_constraints(df, contract, target_sheet=sheet_name))
    all_issues.extend(validate_numeric_ranges(df, contract, target_sheet=sheet_name))

    for issue in all_issues:
        report.add_issue(issue)

    return report


def validate_source_file(
    source_name: str,
    file_path: Optional[Path] = None,
) -> ValidationReport:
    """Validate a configured source file, including every declared sheet."""
    contracts = load_contracts()

    if source_name not in contracts:
        raise KeyError(f"No contract defined for '{source_name}'")

    contract = contracts[source_name]
    aggregate = ValidationReport(source_name=source_name, dataset_shape=(0, 0))

    if file_path is not None:
        source_paths = [Path(file_path)]
    else:
        configured = str(contract["archivo"])
        base_dir = Path(__file__).parent.parent.parent
        if "*" in configured or "?" in configured:
            configured_path = Path(configured)
            source_paths = sorted((base_dir / configured_path.parent).glob(configured_path.name))
        else:
            source_paths = [base_dir / configured]

    if not source_paths:
        aggregate.add_issue(
            ValidationIssue(
                level="error",
                rule="Source File Missing",
                description=f"Configured file not found: {base_dir / contract['archivo']}",
            )
        )
        return aggregate

    total_rows = 0
    total_cols = 0

    for source_path in source_paths:
        source_path = Path(source_path)

        if not source_path.exists():
            aggregate.add_issue(
                ValidationIssue(
                    level="error",
                    rule="Source File Missing",
                    description=f"Configured file not found: {source_path}",
                )
            )
            continue

        if contract.get("tipo") == "excel":
            workbook = pd.ExcelFile(source_path)
            declared_sheets = contract.get("hojas", {})
            for sheet_name, sheet_spec in declared_sheets.items():
                if sheet_name not in workbook.sheet_names:
                    aggregate.add_issue(
                        ValidationIssue(
                            level="error",
                            rule="Required Sheet Missing",
                            sheet=sheet_name,
                            description=f"Sheet '{sheet_name}' not found in {source_path.name}",
                        )
                    )
                    continue

                df = pd.read_excel(source_path, sheet_name=sheet_name)
                total_rows += len(df)
                total_cols = max(total_cols, len(df.columns))
                sheet_report = validate_dataset(df, source_name, sheet_name=sheet_name)
                for issue in sheet_report.issues:
                    aggregate.add_issue(issue)
        else:
            df = pd.read_csv(source_path)
            total_rows += len(df)
            total_cols = max(total_cols, len(df.columns))
            sheet_report = validate_dataset(df, source_name)
            for issue in sheet_report.issues:
                aggregate.add_issue(issue)

    aggregate.dataset_shape = (total_rows, total_cols)
    return aggregate


def validate_all_sources() -> Dict[str, ValidationReport]:
    """Validate every configured source and return reports keyed by source name."""
    contracts = load_contracts()
    reports: Dict[str, ValidationReport] = {}
    for source_name, contract in contracts.items():
        if not isinstance(contract, dict) or "archivo" not in contract:
            continue
        reports[source_name] = validate_source_file(source_name)
    return reports


def check_data_freshness(
    df: pd.DataFrame,
    max_age_days: int = 7,
) -> bool:
    """
    Simple freshness check — look for date column and ensure not too old.

    Args:
        df: DataFrame to check
        max_age_days: Maximum allowed age in days

    Returns:
        True if data is fresh, False otherwise
    """
    # Look for datetime columns
    date_cols = df.select_dtypes(include=["datetime64"]).columns

    if len(date_cols) == 0:
        return True  # No date column, assume fresh

    latest_date = df[date_cols[0]].max()
    age = (datetime.now() - latest_date).days

    return age <= max_age_days
