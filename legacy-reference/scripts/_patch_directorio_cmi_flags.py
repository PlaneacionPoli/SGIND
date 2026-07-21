"""Parche de una sola pasada: agrega al directorio maestro ('Catalogo
Indicadores' en Resultados_Consolidados_Fuente.xlsx) las columnas de CMI que
la fusión inicial (migrar_directorio_maestro.py) no había incluido pero que
sí consume el backend (cmi_filters.py, strategic_loaders.py):
FACTOR, CARACTERÍSTICA, Indicadores Clave, Indicadores Plan estrategico,
Indicadores Vicerrectoria, Subprocesos (flag), General, Meta General, Ind act.

Lee del backup pre-fusión de 'Indicadores por CMI.xlsx' (no del archivo
original, que ya puede estar archivado).

Uso: python scripts/_patch_directorio_cmi_flags.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from etl.escritura import escribir_hoja_nueva  # noqa: E402

CAT_FILE = ROOT / "data" / "raw" / "Resultados_Consolidados_Fuente.xlsx"
CMI_BACKUP = ROOT / "data" / "raw" / "Indicadores por CMI.bak_pre_fusion.xlsx"

MAPA_COLUMNAS = {
    "FACTOR": "Factor",
    "CARACTERÍSTICA": "Caracteristica",
    "Indicadores Clave": "Indicadores_Clave",
    "Indicadores Plan estrategico": "Indicadores_Plan_Estrategico",
    "Indicadores Vicerrectoria": "Indicadores_Vicerrectoria",
    "Subprocesos": "Subprocesos",
    "General": "General",
    "Meta General": "Meta_General",
    "Ind act": "Ind_Act",
}


def _id_str(v) -> str:
    s = str(v).strip()
    return s[:-2] if s.endswith(".0") else s


def main() -> None:
    if not CMI_BACKUP.exists():
        print(f"ERROR: no existe {CMI_BACKUP}")
        return

    bak = CAT_FILE.with_name(CAT_FILE.stem + ".bak_pre_patch_flags" + CAT_FILE.suffix)
    if not bak.exists():
        shutil.copy2(CAT_FILE, bak)
        print(f"backup -> {bak.name}")

    df_cmi = pd.read_excel(CMI_BACKUP, sheet_name="Worksheet")
    df_cmi["_id"] = df_cmi["Id"].map(_id_str)
    df_cmi = df_cmi.drop_duplicates("_id", keep="last").set_index("_id")

    df_cat = pd.read_excel(CAT_FILE, sheet_name="Catalogo Indicadores")
    df_cat["_id"] = df_cat["Id"].map(_id_str)

    for col_nuevo in MAPA_COLUMNAS.values():
        if col_nuevo not in df_cat.columns:
            df_cat[col_nuevo] = None

    n = 0
    for i, row in df_cat.iterrows():
        id_s = row["_id"]
        if id_s not in df_cmi.index:
            continue
        cmi_row = df_cmi.loc[id_s]
        for col_origen, col_nuevo in MAPA_COLUMNAS.items():
            if col_origen in cmi_row.index and pd.notna(cmi_row[col_origen]):
                df_cat.at[i, col_nuevo] = cmi_row[col_origen]
        n += 1

    df_cat_final = df_cat.drop(columns=["_id"])
    print(f"Filas actualizadas con flags CMI: {n} de {len(df_cat_final)}")

    wb = openpyxl.load_workbook(CAT_FILE)
    escribir_hoja_nueva(wb, "Catalogo Indicadores", df_cat_final)
    wb.save(CAT_FILE)
    print(f"Guardado: {CAT_FILE} — {len(df_cat_final.columns)} columnas")


if __name__ == "__main__":
    main()
