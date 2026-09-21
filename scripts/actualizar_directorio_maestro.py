"""
scripts/actualizar_directorio_maestro.py

Complementa los huecos de Periodicidad/Sentido/Clasificacion en el
directorio maestro (data/raw/Catalogo de Indicadores.xlsx, hoja
"Catalogo Indicadores") usando dos fuentes de respaldo, EN ESTE ORDEN
de prioridad (solo se usa una fuente si el directorio maestro ya no
resolvio el dato con la fuente anterior):

  1. data/raw/Ficha_Tecnica_Indicadores.xlsx (local a este repo).
  2. data/raw/Indicadores por CMI.xlsx (copiado desde el repo
     Sistema_Indicadores_Poli por el workflow de CI antes de este paso;
     en corridas locales, el usuario debe copiarlo a mano si quiere
     usar esta fuente).

Politica de fusion: SOLO llena celdas vacias, nunca sobrescribe un
valor ya presente en el directorio maestro (decision de negocio,
2026-09-20) — evita que un dato desactualizado de una fuente externa
reemplace un valor ya corregido en SGING.

Uso:
  python scripts/actualizar_directorio_maestro.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional

import openpyxl
import pandas as pd

BASE_DIR = Path(__file__).parent.parent.resolve()
_SCRIPTS_DIR = Path(__file__).parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from etl.normalizacion import id_str  # noqa: E402

CATALOGO_MAESTRO_FILE = BASE_DIR / "data" / "raw" / "Catalogo de Indicadores.xlsx"
FICHA_TECNICA_FILE = BASE_DIR / "data" / "raw" / "Ficha_Tecnica_Indicadores.xlsx"
CMI_EXTERNO_FILE = BASE_DIR / "data" / "raw" / "Indicadores por CMI.xlsx"

CATALOGO_SHEET = "Catalogo Indicadores"

# Mapa de valores de "Tipo de Indicador" (Ficha Tecnica) -> "Clasificacion"
# (directorio maestro). Confirmado con negocio 2026-09-20: "Gestion" y
# "Operativo" son el mismo concepto.
_MAPA_TIPO_INDICADOR_A_CLASIFICACION = {
    "gestion": "Operativo",
    "gestión": "Operativo",
    "operativo": "Operativo",
    "estrategico": "Estratégico",
    "estratégico": "Estratégico",
}


def _clean(v) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() in ("nan", "none", "seleccione"):
        return None
    return s


def _cargar_ficha_tecnica() -> Dict[str, Dict[str, Optional[str]]]:
    """{id_str: {periodicidad, sentido, clasificacion}} desde Ficha Tecnica."""
    if not FICHA_TECNICA_FILE.exists():
        print(f"[actualizar_directorio_maestro] No existe {FICHA_TECNICA_FILE.name}, se omite esta fuente.")
        return {}
    df = pd.read_excel(FICHA_TECNICA_FILE, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    result: Dict[str, Dict[str, Optional[str]]] = {}
    for _, row in df.iterrows():
        for id_col in ("Id Ind", "ID Kawak"):
            if id_col not in df.columns:
                continue
            ids = id_str(row.get(id_col))
            if not ids or ids.lower() == "nan":
                continue
            tipo_ind = _clean(row.get("Tipo de Indicador"))
            clasificacion = None
            if tipo_ind:
                clasificacion = _MAPA_TIPO_INDICADOR_A_CLASIFICACION.get(tipo_ind.strip().lower())
            entry = {
                "periodicidad": _clean(row.get("Frecuencia")),
                "sentido": _clean(row.get("Sentido")),
                "clasificacion": clasificacion,
            }
            # No sobrescribir si ya existe una entrada con mas datos (Id Ind e ID Kawak
            # suelen coincidir; si difieren, se queda con la primera coincidencia util).
            if ids not in result:
                result[ids] = entry
    return result


def _cargar_cmi_externo() -> Dict[str, Dict[str, Optional[str]]]:
    """{id_str: {periodicidad, sentido, clasificacion}} desde el catalogo CMI
    de Sistema_Indicadores_Poli (copiado por CI o manualmente)."""
    if not CMI_EXTERNO_FILE.exists():
        print(f"[actualizar_directorio_maestro] No existe {CMI_EXTERNO_FILE.name}, se omite esta fuente.")
        return {}
    df = pd.read_excel(CMI_EXTERNO_FILE, sheet_name="Worksheet", engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    clas_col = next((c for c in df.columns if "Clasificaci" in c), None)
    result: Dict[str, Dict[str, Optional[str]]] = {}
    for _, row in df.iterrows():
        ids = id_str(row.get("Id"))
        if not ids or ids.lower() == "nan":
            continue
        result[ids] = {
            "periodicidad": _clean(row.get("Periodicidad")),
            "sentido": _clean(row.get("Sentido")),
            "clasificacion": _clean(row.get(clas_col)) if clas_col else None,
        }
    return result


def main() -> int:
    if not CATALOGO_MAESTRO_FILE.exists():
        print(f"[ERROR] No existe {CATALOGO_MAESTRO_FILE}")
        return 2

    ficha_tecnica = _cargar_ficha_tecnica()
    cmi_externo = _cargar_cmi_externo()
    print(f"[actualizar_directorio_maestro] Ficha Tecnica: {len(ficha_tecnica)} ids. "
          f"CMI externo: {len(cmi_externo)} ids.")

    wb = openpyxl.load_workbook(CATALOGO_MAESTRO_FILE)
    if CATALOGO_SHEET not in wb.sheetnames:
        print(f"[ERROR] La hoja '{CATALOGO_SHEET}' no existe en {CATALOGO_MAESTRO_FILE.name}")
        return 3
    ws = wb[CATALOGO_SHEET]

    header = [str(c.value).strip() if c.value is not None else "" for c in next(ws.iter_rows(min_row=1, max_row=1))]
    try:
        idx_id = header.index("Id") + 1
        idx_periodicidad = header.index("Periodicidad") + 1
        idx_sentido = header.index("Sentido") + 1
        idx_clasificacion = header.index("Clasificacion") + 1
    except ValueError as exc:
        print(f"[ERROR] Columna esperada no encontrada en el encabezado: {exc}")
        return 4

    campos = [
        ("periodicidad", idx_periodicidad),
        ("sentido", idx_sentido),
        ("clasificacion", idx_clasificacion),
    ]

    n_llenados = {"periodicidad": 0, "sentido": 0, "clasificacion": 0}
    ids_aun_incompletos: list[str] = []

    for row in ws.iter_rows(min_row=2):
        id_cell = row[idx_id - 1]
        if id_cell.value is None:
            continue
        ids = id_str(id_cell.value)

        sigue_incompleto = False
        for campo, idx in campos:
            celda = row[idx - 1]
            if _clean(celda.value) is not None:
                continue  # ya tiene valor: no se sobrescribe (solo llenar vacios)
            valor_nuevo = None
            for fuente in (ficha_tecnica, cmi_externo):
                entry = fuente.get(ids)
                if entry and entry.get(campo):
                    valor_nuevo = entry[campo]
                    break
            if valor_nuevo:
                celda.value = valor_nuevo
                n_llenados[campo] += 1
            else:
                sigue_incompleto = True

        if sigue_incompleto:
            ids_aun_incompletos.append(ids)

    wb.save(CATALOGO_MAESTRO_FILE)

    print(f"[actualizar_directorio_maestro] Celdas llenadas: {n_llenados}")
    if ids_aun_incompletos:
        print(
            f"[actualizar_directorio_maestro] {len(ids_aun_incompletos)} ids siguen con "
            f"Periodicidad/Sentido/Clasificacion incompletos tras el merge "
            f"(ninguna fuente los cubre): {', '.join(ids_aun_incompletos)}"
        )
    else:
        print("[actualizar_directorio_maestro] Directorio maestro completo, sin huecos restantes.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
