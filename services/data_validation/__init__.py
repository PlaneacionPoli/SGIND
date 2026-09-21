"""
services/data_validation/ — Data quality validation service

Refactorización PHASE 2 (495L → 4 módulos):
  - models.py: Data structures for validation results (99L)
  - utils.py: Text normalization and contract loading (115L)
  - validators.py: Core validation rules (220L)
  - loaders.py: Source file and freshness validation (40L)

Responsibility unique per module:
  - models: Define ValidationIssue, ValidationReport data classes
  - utils: Load contracts, normalize text, find columns
  - validators: Implement 5 validation rule types
  - loaders: Orchestrate validation across source files

Usage:
    from services.data_validation import validate_dataset, ValidationReport

    report = validate_dataset(df, source_name="resultados_consolidados")
    if not report.is_valid:
        report.print_issues()
"""

# Re-export for backward compatibility
from .loaders import (
    check_data_freshness,
    validate_all_sources,
    validate_dataset,
    validate_source_file,
)
from .models import ValidationIssue, ValidationReport

__all__ = [
    "ValidationIssue",
    "ValidationReport",
    "validate_dataset",
    "validate_source_file",
    "validate_all_sources",
    "check_data_freshness",
]
