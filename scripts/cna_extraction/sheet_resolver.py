"""
scripts/cna_extraction/sheet_resolver.py

Empareja cada registro del catálogo ("Índice Tablas") con la hoja real del
workbook que contiene sus datos.

Regla clave (confirmada en el archivo real): el nombre de la pestaña NO
siempre coincide con el número de tabla/gráfico declarado DENTRO de la hoja
(ej. la pestaña "Tabla 127" declara internamente "Tabla NO 130"). Por eso el
match primario usa el número declarado dentro de la hoja; el nombre de la
pestaña solo se usa como respaldo.
"""

from __future__ import annotations

import re

from scripts.cna_extraction.models import CatalogRecord, ResolvedSheet

SKIP_SHEETS = {"Índice Tablas", "Respaldo"}

_HEADER_LABEL_RE = re.compile(r"^(tabla\s*n[oº°]?\.?|gr[aá]fico\s*n[oº°]?\.?|\*)$", re.IGNORECASE)
_TAB_NAME_RE = re.compile(r"(Tabla|Gr[aá]fico|Ilustraci[oó]n)\s+(\d+)", re.IGNORECASE)
_NUM_RE = re.compile(r"(\d+)")


def _tipo_from_sheet_name(sheet_name: str) -> str:
    lowered = sheet_name.strip().lower()
    if lowered.startswith("tabla"):
        return "tabla"
    if lowered.startswith("ilustra"):
        return "ilustracion"
    # "Gráfico N" e "Ilustración N" son series de numeración independientes
    # en el Anexo (ambas reinician en 1) — deben distinguirse aquí igual que
    # en catalog.py, o dos hojas con el mismo número (ej. Gráfico 21 vs
    # Ilustración 21) colisionan en `by_key` más abajo y una pisa a la otra.
    return "grafico"


def read_sheet_header_number(ws) -> tuple[int | None, str | None]:
    """Escanea las primeras filas buscando la celda de etiqueta ('Tabla NO',
    '*', 'Gráfico No', ...) y el número declarado junto a ella, además del
    'Nombre' asociado. Tolerante a variaciones de mayúsculas/espacios."""
    numero: int | None = None
    nombre: str | None = None

    for row in ws.iter_rows(min_row=1, max_row=3, values_only=True):
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
        elif label.strip().lower() == "nombre":
            candidate = row[1] if len(row) > 1 else None
            nombre = str(candidate) if candidate is not None else None

    return numero, nombre


def resolve_sheets(
    catalog: list[CatalogRecord], wb
) -> tuple[list[ResolvedSheet], list[str]]:
    """Empareja cada hoja de datos del workbook con su registro de catálogo.

    Devuelve (resolved, unreferenced_sheets):
      - resolved: una entrada por cada hoja de datos (matched o no) MÁS una
        entrada adicional por cada registro de catálogo que no encontró
        ninguna hoja (sheet_name=None) — ninguno de los dos casos se descarta
        silenciosamente.
      - unreferenced_sheets: nombres de hoja que no calzaron con ningún
        registro de catálogo (ej. hojas huérfanas como "Tabla 81").
    """
    by_key: dict[tuple[str, int], CatalogRecord] = {}
    for rec in catalog:
        if rec.numero is not None:
            by_key[(rec.tipo, rec.numero)] = rec

    data_sheets = [name for name in wb.sheetnames if name not in SKIP_SHEETS]

    resolved: list[ResolvedSheet] = []
    matched_keys: set[tuple[str, int]] = set()

    for sheet_name in data_sheets:
        ws = wb[sheet_name]
        declared_number, _ = read_sheet_header_number(ws)
        tipo = _tipo_from_sheet_name(sheet_name)

        record = by_key.get((tipo, declared_number)) if declared_number is not None else None
        match_method = "declared_number" if record else None

        if record is None:
            tab_match = _TAB_NAME_RE.search(sheet_name)
            if tab_match:
                tab_numero = int(tab_match.group(2))
                record = by_key.get((tipo, tab_numero))
                if record:
                    match_method = "tab_name_fallback"

        if record is not None:
            matched_keys.add((record.tipo, record.numero))  # type: ignore[arg-type]
            resolved.append(
                ResolvedSheet(
                    catalog_record=record,
                    sheet_name=sheet_name,
                    declared_number=declared_number,
                    match_method=match_method or "declared_number",
                )
            )
        else:
            resolved.append(
                ResolvedSheet(
                    catalog_record=None,
                    sheet_name=sheet_name,
                    declared_number=declared_number,
                    match_method="unmatched",
                )
            )

    unreferenced_sheets = [r.sheet_name for r in resolved if r.match_method == "unmatched"]  # type: ignore[misc]

    for rec in catalog:
        if rec.numero is not None and (rec.tipo, rec.numero) not in matched_keys:
            resolved.append(
                ResolvedSheet(
                    catalog_record=rec,
                    sheet_name=None,
                    declared_number=None,
                    match_method="unmatched",
                )
            )

    return resolved, unreferenced_sheets
