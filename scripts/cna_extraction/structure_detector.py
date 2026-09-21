"""
scripts/cna_extraction/structure_detector.py

Detector genérico de la geometría de cada hoja de datos del Anexo
Estadístico: localiza el bloque de encabezado (Tabla NO/Nombre), el eje de
periodos (horizontal, vertical o inexistente), las columnas/filas de
categoría (con forward-fill de etiquetas dispersas/mergeadas), y separa las
filas "Total" explícitas (que representan el valor del indicador principal)
de las filas de detalle (subindicadores).

Diseño: una cadena de funciones puras sobre listas de filas crudas
(`list[list[Any]]`), no una jerarquía de clases — cada hoja pasa por los
mismos pasos de descomposición geométrica, solo que con distintos puntos de
corte. Nunca lanza excepción por la forma de los datos: toda hoja produce un
SheetStructure con un `kind`, incluso "unresolved"/"event_log_atypical", para
que el reporte de diagnóstico quede completo.
"""

from __future__ import annotations

import re
from typing import Any

from scripts.cna_extraction.models import HeaderBlock, PeriodColumn, SheetStructure

NA_STRINGS = {"-", "", "\xa0", " ", " ", "n/a", "na", "nd"}

_YEAR_RE = re.compile(r"^(19|20)\d{2}$")
_SEMESTER_RE = re.compile(r"^(19|20)\d{2}-[12]$")
_HEADER_LABEL_RE = re.compile(r"^(tabla\s*n[oº°]?\.?|gr[aá]fico\s*n[oº°]?\.?|\*)$", re.IGNORECASE)
_NUM_RE = re.compile(r"(\d+)")


def normalize_missing(value: Any) -> Any:
    """Colapsa placeholders de 'sin dato' (guion, vacío, nbsp, espacios
    especiales, etc.) a None. Números/fechas pasan intactos."""
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if text == "" or text.lower() in NA_STRINGS:
            return None
        return value
    return value


def is_period_label(label: Any) -> str | None:
    """Devuelve el periodo normalizado ('YYYY' o 'YYYY-N') si `label` es un
    encabezado de periodo, o None si no lo es."""
    if label is None:
        return None
    text = str(label).strip()
    if _SEMESTER_RE.match(text):
        return text
    if _YEAR_RE.match(text):
        return text
    return None


def is_total_label(label: Any) -> bool:
    if label is None:
        return False
    return str(label).strip().lower().startswith("total")


def _row_is_blank(row: list[Any]) -> bool:
    return all(normalize_missing(v) is None for v in row)


def forward_fill(values: list[Any]) -> list[Any]:
    """Forward-fill genérico izquierda-a-derecha (o arriba-a-abajo, según
    cómo se le pase la secuencia): usado tanto para etiquetas de grupo en
    encabezados de 2 niveles como para columnas de categoría dispersas."""
    result: list[Any] = []
    last: Any = None
    for v in values:
        v = normalize_missing(v)
        if v is not None:
            last = v
        result.append(last)
    return result


def find_header_block(raw_rows: list[list[Any]]) -> HeaderBlock:
    """Localiza, dentro de las primeras filas, el número/nombre declarados
    de la tabla y la fila donde empiezan los datos reales (tolerante a la
    variación de 0-2 filas en blanco después de 'Nombre')."""
    numero: int | None = None
    nombre: str | None = None
    data_start_row = 0
    max_scan = min(len(raw_rows), 6)

    for idx in range(max_scan):
        row = raw_rows[idx]
        if not row:
            continue
        label = str(row[0] or "").strip()
        if _HEADER_LABEL_RE.match(label):
            candidate = row[1] if len(row) > 1 else None
            if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
                numero = int(candidate)
            elif isinstance(candidate, str):
                match = _NUM_RE.search(candidate)
                if match:
                    numero = int(match.group(1))
            data_start_row = idx + 1
        elif label.lower() == "nombre":
            candidate = row[1] if len(row) > 1 else None
            nombre = str(candidate) if candidate is not None else None
            data_start_row = idx + 1

    while data_start_row < len(raw_rows) and _row_is_blank(raw_rows[data_start_row]):
        data_start_row += 1

    return HeaderBlock(numero_declarado=numero, nombre=nombre, data_start_row=data_start_row)


def detect_event_log(raw_rows: list[list[Any]], data_start_row: int) -> bool:
    """Heurística para hojas tipo bitácora de eventos (columnas
    'Actividad'/'Población impactada' en texto libre) — se chequea ANTES de
    la detección de periodos para no forzar un ajuste incorrecto."""
    if data_start_row >= len(raw_rows):
        return False
    header_row = [str(v).strip().lower() if v is not None else "" for v in raw_rows[data_start_row]]
    has_actividad = any("actividad" in c for c in header_row)
    has_poblacion = any("poblaci" in c for c in header_row)
    return has_actividad and has_poblacion


def _extract_rows(
    raw_rows: list[list[Any]],
    data_row_start: int,
    category_columns: list[int],
    period_columns: list[PeriodColumn],
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    has_explicit_total = False
    state: dict[int, Any] = {}
    ambiguous_seen: dict[tuple[Any, ...], int] = {}

    for row in raw_rows[data_row_start:]:
        if _row_is_blank(row):
            break

        category_path: list[Any] = []
        row_has_raw_category = False
        for col in category_columns:
            val = normalize_missing(row[col]) if col < len(row) else None
            if val is not None:
                state[col] = val
                row_has_raw_category = True
            if state.get(col) is not None:
                category_path.append(state[col])

        row_is_total = any(is_total_label(v) for v in category_path)
        has_explicit_total = has_explicit_total or row_is_total
        row_kind = "total_explicito" if row_is_total else "detalle"

        # Fila sin ninguna etiqueta propia (todas las columnas de categoría
        # vacías en la fuente): el forward-fill la deja con el MISMO
        # category_path que la fila de detalle anterior, lo que colisiona su
        # Llave y provoca pérdida silenciosa de datos en la deduplicación de
        # escritura (ver caso real: Gráfico 19 "Proporción por tipo de
        # contrato" — una fila así trae valores ~1279/1234/... que NO suman
        # en el Total de la hoja, o sea es una categoría propia sin
        # etiqueta, no una continuación de "Medio tiempo - Anualizado").
        # Se distingue con un sufijo ordinal en vez de asumir en silencio
        # que es la misma categoría de la fila anterior.
        category_ambiguous = bool(category_path) and not row_has_raw_category and not row_is_total
        if category_ambiguous:
            key = tuple(category_path)
            ambiguous_seen[key] = ambiguous_seen.get(key, 0) + 1
            category_path = [*category_path, f"(sin etiqueta #{ambiguous_seen[key]})"]

        for pc in period_columns:
            value = normalize_missing(row[pc.col_index]) if pc.col_index < len(row) else None
            rows.append(
                {
                    "category_path": category_path,
                    "period": pc.period,
                    "value": value,
                    "row_kind": row_kind,
                    "category_ambiguous": category_ambiguous,
                }
            )

    return rows, has_explicit_total


def _extract_vertical_rows(raw_rows: list[list[Any]], header_row_idx: int) -> list[dict[str, Any]]:
    if header_row_idx >= len(raw_rows):
        return []
    header_row = raw_rows[header_row_idx]
    if is_period_label(header_row[0] if header_row else None):
        col_labels = {i: f"col_{i}" for i in range(1, len(header_row))}
        first_data_row = header_row_idx
    else:
        col_labels = {
            i: header_row[i]
            for i in range(1, len(header_row))
            if normalize_missing(header_row[i]) is not None
        }
        first_data_row = header_row_idx + 1

    rows: list[dict[str, Any]] = []
    for row in raw_rows[first_data_row:]:
        if _row_is_blank(row):
            break
        period = is_period_label(row[0] if row else None)
        if period is None:
            continue
        for col, label in col_labels.items():
            value = normalize_missing(row[col]) if col < len(row) else None
            row_kind = "total_explicito" if is_total_label(label) else "detalle"
            rows.append(
                {
                    "category_path": [label] if label else [],
                    "period": period,
                    "value": value,
                    "row_kind": row_kind,
                    "category_ambiguous": False,
                }
            )
    return rows


def _extract_snapshot_rows(raw_rows: list[list[Any]], header_row_idx: int) -> list[dict[str, Any]]:
    if header_row_idx >= len(raw_rows):
        return []
    header_row = raw_rows[header_row_idx]
    col_labels = {
        i: header_row[i]
        for i in range(1, len(header_row))
        if normalize_missing(header_row[i]) is not None
    }

    rows: list[dict[str, Any]] = []
    for row in raw_rows[header_row_idx + 1 :]:
        if _row_is_blank(row):
            break
        label = normalize_missing(row[0]) if row else None
        if label is None:
            continue
        row_kind = "total_explicito" if is_total_label(label) else "detalle"
        for col, sub_label in col_labels.items():
            value = normalize_missing(row[col]) if col < len(row) else None
            rows.append(
                {
                    "category_path": [label, sub_label],
                    "period": None,
                    "value": value,
                    "row_kind": row_kind,
                    "category_ambiguous": False,
                }
            )
    return rows


def detect_structure(raw_rows: list[list[Any]], catalog_numero: int | None) -> SheetStructure:
    """Orquesta la detección completa de geometría para una hoja. Nunca
    lanza excepción por forma de datos (solo `unresolved` cuando no hay
    filas de datos después del bloque de encabezado)."""
    raw_rows = [[normalize_missing(v) for v in row] for row in raw_rows]
    header = find_header_block(raw_rows)

    if detect_event_log(raw_rows, header.data_start_row):
        return SheetStructure(
            catalog_numero=catalog_numero,
            kind="event_log_atypical",
            header=header,
            issues=["Detectada estructura de bitácora de eventos (no periódica); requiere revisión manual."],
        )

    if header.data_start_row >= len(raw_rows):
        return SheetStructure(
            catalog_numero=catalog_numero,
            kind="unresolved",
            header=header,
            issues=["No se encontraron filas de datos después del bloque de encabezado."],
        )

    candidate_idx = header.data_start_row
    header_row_idx = candidate_idx
    group_row_idx: int | None = None

    row_at_candidate = raw_rows[candidate_idx]
    if not any(is_period_label(v) for v in row_at_candidate):
        next_idx = candidate_idx + 1
        if next_idx < len(raw_rows):
            row_at_next = raw_rows[next_idx]
            period_count_next = sum(1 for v in row_at_next if is_period_label(v))
            if period_count_next >= 2:
                header_row_idx = next_idx
                group_row_idx = candidate_idx

    header_row = raw_rows[header_row_idx]
    group_labels = forward_fill(raw_rows[group_row_idx]) if group_row_idx is not None else None

    period_columns: list[PeriodColumn] = []
    category_columns: list[int] = []
    excluded_columns: list[int] = []
    seen_first_period = False

    for col_idx, label in enumerate(header_row):
        period = is_period_label(label)
        if period is not None:
            seen_first_period = True
            group_label = group_labels[col_idx] if group_labels else None
            period_columns.append(PeriodColumn(col_index=col_idx, label=label, period=period, group_label=group_label))
        elif is_total_label(label):
            excluded_columns.append(col_idx)
        elif label is None:
            if seen_first_period:
                excluded_columns.append(col_idx)
            else:
                category_columns.append(col_idx)
        else:
            if seen_first_period:
                excluded_columns.append(col_idx)
            else:
                category_columns.append(col_idx)

    if period_columns:
        data_row_start = header_row_idx + 1
        rows, has_explicit_total = _extract_rows(raw_rows, data_row_start, category_columns, period_columns)
        if group_row_idx is not None:
            kind = "horizontal_periods_2level_header"
        elif len(category_columns) >= 2:
            kind = "horizontal_periods_2level_rows"
        else:
            kind = "horizontal_periods_flat"
        return SheetStructure(
            catalog_numero=catalog_numero,
            kind=kind,
            header=header,
            period_columns=period_columns,
            category_columns=category_columns,
            excluded_columns=excluded_columns,
            rows=rows,
            has_explicit_total=has_explicit_total,
        )

    # Sin periodos horizontales: intentar vertical, luego snapshot.
    vertical_candidates = [
        r for r in raw_rows[header_row_idx + 1 :] if r and is_period_label(r[0])
    ]
    if len(vertical_candidates) >= 2:
        rows = _extract_vertical_rows(raw_rows, header_row_idx)
        return SheetStructure(
            catalog_numero=catalog_numero,
            kind="vertical_periods",
            header=header,
            rows=rows,
        )

    rows = _extract_snapshot_rows(raw_rows, header_row_idx)
    return SheetStructure(
        catalog_numero=catalog_numero,
        kind="snapshot_no_period",
        header=header,
        rows=rows,
        issues=["No se detectó eje de periodos; tratada como tabla snapshot."],
    )
