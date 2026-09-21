"""
scripts/cna_extraction/models.py

Dataclasses compartidas entre el catálogo, el resolver de hojas y el
detector de estructura (Fase 1 — solo lectura/diagnóstico).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

TipoRegistro = Literal["tabla", "grafico", "ilustracion"]

SheetKind = Literal[
    "horizontal_periods_flat",
    "horizontal_periods_2level_rows",
    "horizontal_periods_2level_header",
    "vertical_periods",
    "snapshot_no_period",
    "event_log_atypical",
    "unresolved",
]

RowKind = Literal["detalle", "total_explicito"]


@dataclass
class CatalogRecord:
    """Un registro de la hoja 'Índice Tablas'."""

    orden: int | None
    factor_raw: str
    factor_num: int | None
    factor_nombre: str
    caracteristica: str
    tabla_no: int | None
    grafico_no: int | str | None
    nombre: str
    fuente: str
    responsable: str
    enlace: str
    observaciones: str
    tipo: TipoRegistro
    numero: int | None
    id_hint: str


@dataclass
class ResolvedSheet:
    """Resultado de emparejar un registro de catálogo con una hoja real."""

    catalog_record: CatalogRecord | None
    sheet_name: str | None
    declared_number: int | None
    match_method: Literal["declared_number", "tab_name_fallback", "unmatched"]


@dataclass
class HeaderBlock:
    """Bloque de encabezado (Tabla NO/Nombre) al inicio de cada hoja de datos."""

    numero_declarado: int | None
    nombre: str | None
    data_start_row: int


@dataclass
class PeriodColumn:
    col_index: int
    label: Any
    period: str | None
    group_label: Any | None = None
    # Subvariable de un encabezado de 2 niveles con el periodo ARRIBA y la variable
    # ABAJO (Tabla 40: 2025|2026 sobre Títulos|Volúmenes).
    variable: str | None = None


@dataclass
class SheetStructure:
    """Resultado del detector genérico de estructura para una hoja."""

    catalog_numero: int | None
    kind: SheetKind
    header: HeaderBlock
    period_columns: list[PeriodColumn] = field(default_factory=list)
    category_columns: list[int] = field(default_factory=list)
    excluded_columns: list[int] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    has_explicit_total: bool | None = None
