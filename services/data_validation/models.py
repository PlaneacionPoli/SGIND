"""
services/data_validation/models.py
==================================

Data models for validation reports: ValidationIssue, ValidationReport.

Responsibility: Define data structures for validation results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ValidationIssue:
    """Single data quality issue found during validation."""

    level: str  # "error" | "warning" | "info"
    rule: str  # Name of rule that failed
    sheet: Optional[str] = None
    column: Optional[str] = None
    row_count: int = 0
    description: str = ""
    values_sample: List[Any] = field(default_factory=list)  # Problematic values

    def __str__(self) -> str:
        level_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[self.level]
        sheet_info = f" [{self.sheet}]" if self.sheet else ""
        col_info = f" [{self.column}]" if self.column else ""
        sample_info = f" | Examples: {self.values_sample[:3]}" if self.values_sample else ""
        return (
            f"{level_icon} {self.rule}{sheet_info}{col_info} — {self.description} "
            f"({self.row_count} rows){sample_info}"
        )


@dataclass
class ValidationReport:
    """Report of all validation issues for a dataset."""

    source_name: str
    dataset_shape: tuple
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """True if no errors (warnings ok)."""
        return not any(i.level == "error" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "warning")

    def add_issue(self, issue: ValidationIssue) -> None:
        """Register an issue."""
        self.issues.append(issue)

    def print_issues(self, level_filter: Optional[str] = None) -> None:
        """Print all issues (optionally filtered by level)."""
        print(f"\n📋 DataValidation Report — {self.source_name}")
        print(f"   Shape: {self.dataset_shape}")
        print(f"   Issues: {self.error_count} errors, {self.warning_count} warnings")
        print()

        for issue in self.issues:
            if level_filter and issue.level != level_filter:
                continue
            print(f"   {issue}")

        print()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (for JSON export)."""
        return {
            "source_name": self.source_name,
            "timestamp": self.timestamp,
            "dataset_shape": self.dataset_shape,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "is_valid": self.is_valid,
            "issues": [
                {
                    "level": i.level,
                    "rule": i.rule,
                    "sheet": i.sheet,
                    "column": i.column,
                    "row_count": int(i.row_count),
                    "description": i.description,
                }
                for i in self.issues
            ],
        }
