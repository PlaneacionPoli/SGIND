"""
scripts/cna_extraction/catalog.py

Parser de la hoja "Índice Tablas" del Anexo Estadístico Dcto. Autoevaluacion.xlsx.
Es el catálogo maestro: para cada Tabla/Gráfico define su Factor,
Característica, Nombre y número identificador.

Reutiliza las convenciones de parsing de Factor de
services/plan_mejoramiento_loader.py (_factor_num/_factor_nombre) para que
el Factor quede consistente con el resto de la app — ver
scripts/cna_extraction/_factor_utils.py para por qué se duplican en vez de
importar ese módulo directamente (dependencia de streamlit).
"""

from __future__ import annotations

import re
from pathlib import Path

import openpyxl

from scripts.cna_extraction._factor_utils import _factor_nombre, _factor_num
from scripts.cna_extraction.models import CatalogRecord

SHEET_INDICE = "Índice Tablas"

_NUM_RE = re.compile(r"(\d+)")


def _to_int(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except (ValueError, OverflowError):
            return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _extract_numero(raw: object) -> int | None:
    """Extrae la parte numérica de un valor de columna Tabla No/Gráfico,
    tolerando tanto enteros como strings tipo 'Ilustración 20'."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return int(raw)
    match = _NUM_RE.search(str(raw))
    return int(match.group(1)) if match else None


def load_catalog(xlsx_path: Path, sheet_name: str = SHEET_INDICE) -> list[CatalogRecord]:
    """Lee 'Índice Tablas' y devuelve un registro por fila con datos, unificando
    Tabla No/Gráfico en (tipo, numero). Filas sin ningún identificador se
    conservan con numero=None para que el reporte de diagnóstico las liste
    en vez de descartarlas silenciosamente."""
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    try:
        ws = wb[sheet_name]
        records: list[CatalogRecord] = []

        for row in ws.iter_rows(min_row=2, values_only=True):
            factor_raw = row[0] if len(row) > 0 else None
            caracteristica = row[1] if len(row) > 1 else None
            orden = row[2] if len(row) > 2 else None
            tabla_no_raw = row[3] if len(row) > 3 else None
            grafico_raw = row[4] if len(row) > 4 else None
            nombre = row[5] if len(row) > 5 else None
            fuente = row[6] if len(row) > 6 else None
            responsable = row[7] if len(row) > 7 else None
            enlace = row[8] if len(row) > 8 else None
            observaciones = row[9] if len(row) > 9 else None

            if all(v is None for v in (factor_raw, caracteristica, tabla_no_raw, grafico_raw, nombre)):
                continue

            tabla_no = _to_int(tabla_no_raw)

            if tabla_no is not None:
                tipo = "tabla"
                numero = tabla_no
                grafico_no = None
                id_hint = f"Tabla {tabla_no}"
            else:
                # La columna "Gráfico" del catálogo mezcla dos series
                # independientes: "Gráfico N" e "Ilustración N", cada una con
                # su propia numeración reiniciada en 1. Si ambas se tratan
                # como tipo="grafico", un "Gráfico 21" y una "Ilustración 21"
                # quedan indistinguibles por (tipo, numero) más adelante
                # (sheet_resolver.by_key, Id/Llave en normalize.py) y sus
                # datos terminan mezclados bajo el mismo Id — confirmado con
                # el caso real Gráfico 21 "Evolución Bilingüismo..." vs
                # Ilustración 21 "Medios destacados para el Poli".
                tipo = "ilustracion" if isinstance(grafico_raw, str) and "ilustra" in grafico_raw.lower() else "grafico"
                numero = _extract_numero(grafico_raw)
                grafico_no = grafico_raw
                if isinstance(grafico_raw, str) and grafico_raw.strip():
                    id_hint = grafico_raw.strip()
                elif numero is not None:
                    id_hint = f"Gráfico {numero}"
                else:
                    id_hint = ""

            records.append(
                CatalogRecord(
                    orden=_to_int(orden),
                    factor_raw=str(factor_raw or ""),
                    factor_num=_factor_num(factor_raw),
                    factor_nombre=_factor_nombre(factor_raw),
                    caracteristica=str(caracteristica or ""),
                    tabla_no=tabla_no,
                    grafico_no=grafico_no,
                    nombre=str(nombre or ""),
                    fuente=str(fuente or ""),
                    responsable=str(responsable or ""),
                    enlace=str(enlace or ""),
                    observaciones=str(observaciones or ""),
                    tipo=tipo,
                    numero=numero,
                    id_hint=id_hint,
                )
            )

        return records
    finally:
        wb.close()


def build_factor_caracteristica_rows(catalog: list[CatalogRecord]) -> list[dict[str, str]]:
    """Pares únicos (Factor, Caracteristica) del catálogo, para la hoja
    'Factor- Caracteristica' del consolidado — insumo del filtro dependiente
    Factor→Característica que ya usa services/plan_mejoramiento_loader.py."""
    seen: set[tuple[str, str]] = set()
    rows: list[dict[str, str]] = []
    for rec in catalog:
        key = (rec.factor_raw, rec.caracteristica)
        if not rec.factor_raw or not rec.caracteristica or key in seen:
            continue
        seen.add(key)
        rows.append({"Factor": rec.factor_raw, "Caracteristica": rec.caracteristica})
    return rows
