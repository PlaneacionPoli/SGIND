"""
scripts/cna_extraction/writer.py

Fase 2 — escritura incremental del consolidado CNA a data/output/. Sigue el
patrón canónico ya usado en scripts/etl/escritura.py: calcular las Llaves ya
existentes, filtrar solo los registros nuevos, y nunca tocar los registros
históricos. Antes de escribir, crea un backup versionado con
scripts/etl/versioning.py si el archivo de salida ya existe.

El archivo de salida es nuevo (data/output/Resultados_Consolidados_CNA.xlsx)
y nunca se escribe dentro de data/raw/ — Resultados_Consolidados_CNA_actualizado.xlsx
(la referencia legacy) no se toca.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import DATA_OUTPUT
from scripts.etl.versioning import VersionManager

OUTPUT_FILE = DATA_OUTPUT / "Resultados_Consolidados_CNA.xlsx"
SHEET_METRICAS = "Metricas"
SHEET_FACTOR_CARACTERISTICA = "Factor- Caracteristica"

# Mismo orden/conjunto que METRICAS_COLS en services/plan_mejoramiento_loader.py
# (+ Decimales, que ese loader ignora pero no le molesta que exista). Proceso,
# Periodicidad, Sentido y Meta no son derivables del Anexo — quedan en None,
# igual que ya son "prácticamente vacíos" en la fuente legacy (ver docstring
# del loader), así que el loader sigue funcionando sin cambios.
METRICAS_COLUMNS = [
    "Id",
    "Indicador",
    "Subindicador",
    "Factor",
    "Caracteristica",
    "Proceso",
    "Periodicidad",
    "Sentido",
    "Fecha",
    "Año",
    "Mes",
    "Periodo",
    "Meta",
    "Ejecución",
    "Ejecución s",
    "Decimales",
    "DecimalesEje",
    "Proyecto",
    "Llave",
]


def load_existing_llaves(output_file: Path = OUTPUT_FILE) -> set[str]:
    if not output_file.exists():
        return set()
    df = pd.read_excel(output_file, sheet_name=SHEET_METRICAS)
    if "Llave" not in df.columns:
        return set()
    return set(df["Llave"].dropna().astype(str))


def write_full(
    records: list[dict[str, Any]],
    output_file: Path = OUTPUT_FILE,
    factor_caracteristica_rows: list[dict[str, str]] | None = None,
) -> dict[str, int]:
    """Reescribe `output_file` desde cero con `records` (sin conservar filas
    existentes). A diferencia de `write_incremental`, no es apto para correr
    periódicamente sobre un archivo con datos manuales mezclados — está
    pensado para reconstruir el consolidado íntegro a partir del Anexo tras
    un fix de extracción (ej. el diferenciador de tipo tabla/gráfico/
    ilustración), donde las filas viejas quedaron mal etiquetadas y deben
    descartarse, no acumularse. Crea backup versionado antes de escribir si
    el archivo ya existe."""
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.exists():
        VersionManager(base_file=output_file).crear_version(tag="pre_cna_rebuild")

    combined = pd.DataFrame(records, columns=METRICAS_COLUMNS).drop_duplicates(subset=["Llave"])

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        combined.to_excel(writer, sheet_name=SHEET_METRICAS, index=False)
        if factor_caracteristica_rows is not None:
            pd.DataFrame(factor_caracteristica_rows, columns=["Factor", "Caracteristica"]).to_excel(
                writer, sheet_name=SHEET_FACTOR_CARACTERISTICA, index=False
            )

    return {
        "registros_existentes": 0,
        "registros_nuevos_candidatos": len(records),
        "registros_nuevos_insertados": len(combined),
        "registros_totales": len(combined),
    }


def write_incremental(
    records: list[dict[str, Any]],
    output_file: Path = OUTPUT_FILE,
    factor_caracteristica_rows: list[dict[str, str]] | None = None,
) -> dict[str, int]:
    """Agrega `records` a `output_file` (por Llave), sin tocar los
    registros existentes. Crea un backup versionado antes de escribir si el
    archivo ya existe. Si se pasa `factor_caracteristica_rows`, (re)escribe
    también la hoja 'Factor- Caracteristica' (catálogo Factor→Característica
    que usa el filtro dependiente del loader)."""
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    existing_llaves = load_existing_llaves(output_file)

    new_df = pd.DataFrame(records, columns=METRICAS_COLUMNS)
    if not new_df.empty:
        new_df = new_df[~new_df["Llave"].isin(existing_llaves)]
        new_df = new_df.drop_duplicates(subset=["Llave"])

    if output_file.exists():
        VersionManager(base_file=output_file).crear_version(tag="pre_cna_extraction")
        existing_df = pd.read_excel(output_file, sheet_name=SHEET_METRICAS)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        combined.to_excel(writer, sheet_name=SHEET_METRICAS, index=False)
        if factor_caracteristica_rows is not None:
            pd.DataFrame(factor_caracteristica_rows, columns=["Factor", "Caracteristica"]).to_excel(
                writer, sheet_name=SHEET_FACTOR_CARACTERISTICA, index=False
            )

    return {
        "registros_existentes": len(existing_llaves),
        "registros_nuevos_candidatos": len(records),
        "registros_nuevos_insertados": len(new_df),
        "registros_totales": len(combined),
    }
