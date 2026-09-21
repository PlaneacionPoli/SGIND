"""
services/data_validation/utils.py
=================================

Utility functions for text normalization, column finding, and data loading.

Responsibility: Support text normalization, column matching, and contract loading.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import yaml

# ============================================================================
# CONSTANTS
# ============================================================================

COLUMN_ALIASES: Dict[str, Set[str]] = {
    "ano": {"ano", "año", "a�o", "anio", "ano_archivo", "año_archivo", "a�o_archivo"},
    "anio": {"ano", "año", "a�o", "anio", "ano_archivo", "año_archivo", "a�o_archivo"},
    "id": {"id"},
    "fecha": {"fecha", "fecha_corte"},
    "valor": {"valor", "resultado"},
}

CATEGORICAL_SYNONYMS: Dict[str, str] = {
    "positivo": "ascendente",
    "negativo": "descendente",
    "gestion": "gestion",
    "gesti n": "gestion",
    "estrat gico": "estrategico",
    "estrat eacute gico": "estrategico",
}

# ============================================================================
# PUBLIC FUNCTIONS
# ============================================================================


def load_contracts() -> Dict[str, Any]:
    """Load data contracts from config/data_contracts.yaml."""
    contracts_path = Path(__file__).parent.parent.parent / "config" / "data_contracts.yaml"
    if not contracts_path.exists():
        raise FileNotFoundError(f"Data contracts not found: {contracts_path}")

    with open(contracts_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def normalize_text(value: Any) -> str:
    """Normalize text for tolerant comparisons across headers and categorical values."""
    if value is None:
        return ""

    text = str(value).strip()
    text = (
        text.replace("A�o", "Año")
        .replace("a�o", "año")
        .replace("Gesti�n", "Gestión")
        .replace("gesti�n", "gestión")
        .replace("&eacute;", "é")
        .replace("&Eacute;", "É")
    )
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def find_matching_column(columns: pd.Index, contract_column: str) -> Optional[str]:
    """Find a dataframe column matching a contract column using normalized names and aliases."""
    normalized_contract = normalize_text(contract_column)
    aliases = {normalized_contract}
    aliases.update(
        normalize_text(alias) for alias in COLUMN_ALIASES.get(normalized_contract, set())
    )

    for column in columns:
        normalized_column = normalize_text(column)
        if normalized_column in aliases:
            return str(column)

    return None


def normalize_allowed_values(values: List[Any]) -> Set[str]:
    """Normalize categorical allowed values for comparison."""
    normalized_values: Set[str] = set()
    for value in values:
        normalized = normalize_text(value)
        normalized_values.add(CATEGORICAL_SYNONYMS.get(normalized, normalized))
    return normalized_values


def normalize_series_values(series: pd.Series) -> pd.Series:
    """Normalize all values in a Series."""
    return series.astype(str).map(
        lambda value: CATEGORICAL_SYNONYMS.get(normalize_text(value), normalize_text(value))
    )


def iter_hojas(
    contract: Dict[str, Any],
    target_sheet: Optional[str] = None,
) -> List[tuple[str, Dict[str, Any]]]:
    """Iterate over sheet specifications in a contract."""
    hojas = contract.get("hojas", {})
    if target_sheet is not None:
        hoja_spec = hojas.get(target_sheet)
        return [(target_sheet, hoja_spec or {})]
    return list(hojas.items())
