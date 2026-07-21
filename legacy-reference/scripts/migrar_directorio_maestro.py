"""Migración de una sola pasada: fusiona 'Indicadores por CMI.xlsx' y
'Ficha_Tecnica_Indicadores.xlsx' dentro de la hoja 'Catalogo Indicadores' de
data/raw/Resultados_Consolidados_Fuente.xlsx (INPUT_FILE del pipeline ETL),
convirtiéndola en el directorio maestro único de indicadores.

Qué hace:
  1. Backup de los 3 archivos (.bak_pre_fusion).
  2. Lee los 3 con pandas, normaliza Id con la misma regla que
     scripts/etl/normalizacion.py::_id_str (quita sufijo ".0").
  3. Amplía 'Catalogo Indicadores' (549 filas, 14 columnas actuales sin tocar)
     con columnas nuevas de clasificación (CMI) y ficha técnica resumida.
     Además agrega como filas nuevas los Id que solo existen en CMI o Ficha
     (unión de los 3 universos → 752 Id).
  4. Escribe una hoja nueva 'Ficha Tecnica Detalle' con el resto de columnas
     de la ficha técnica (variables, semáforo por serie, aprobación, etc.),
     indexada por Id, que el pipeline NO regenera.

Precedencia cuando dos fuentes traen el mismo campo conceptual:
  CMI > Ficha (para los campos nuevos; los 14 campos ya existentes en
  Catalogo Indicadores — Indicador, Clasificacion, Proceso, Periodicidad,
  Sentido, etc. — NO se tocan, siguen viniendo de Kawak/API vía el pipeline).

Uso: python scripts/migrar_directorio_maestro.py
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
CMI_FILE = ROOT / "data" / "raw" / "Indicadores por CMI.xlsx"
FICHA_FILE = ROOT / "data" / "raw" / "Ficha_Tecnica_Indicadores.xlsx"

CATALOGO_COLS_ACTUALES = [
    "Id", "Indicador", "Clasificacion", "Proceso", "Periodicidad", "Sentido",
    "Tipo_API", "Estado", "Fuente", "Extraccion", "TipoCalculo",
    "Asociacion", "Formato_Valores", "Tipo de indicador",
]

COLUMNAS_NUEVAS = [
    "Subproceso", "Linea_Estrategica", "Objetivo_Estrategico",
    "Meta_Estrategica", "Proyecto", "Orden_CMI", "Plan_Anual",
    "Formula", "Descripcion", "Unidad", "Responsable_Calculo",
    "Responsable_Analisis", "Deficiente", "Alerta", "Satisfactorio",
    "Sobresaliente", "ID_Kawak", "CNA_SNIES",
]


def _id_str(v) -> str:
    s = str(v).strip()
    return s[:-2] if s.endswith(".0") else s


def _backup(path: Path) -> None:
    bak = path.with_name(path.stem + ".bak_pre_fusion" + path.suffix)
    if not bak.exists():
        shutil.copy2(path, bak)
        print(f"  backup -> {bak.name}")


def main() -> None:
    for p in (CAT_FILE, CMI_FILE, FICHA_FILE):
        _backup(p)

    df_cat = pd.read_excel(CAT_FILE, sheet_name="Catalogo Indicadores")
    df_cmi = pd.read_excel(CMI_FILE, sheet_name="Worksheet")
    df_ficha = pd.read_excel(FICHA_FILE, sheet_name="query (1)")

    df_cat["_id"] = df_cat["Id"].map(_id_str)
    df_cmi["_id"] = df_cmi["Id"].map(_id_str)
    df_ficha["_id"] = df_ficha["Id Ind"].map(_id_str)

    df_cmi = df_cmi.drop_duplicates("_id", keep="last").set_index("_id")
    df_ficha = df_ficha.drop_duplicates("_id", keep="last").set_index("_id")

    n_antes = len(df_cat)
    ids_union = set(df_cat["_id"]) | set(df_cmi.index) | set(df_ficha.index)
    ids_nuevos = sorted(ids_union - set(df_cat["_id"]))
    print(f"Catalogo actual: {n_antes} filas. Ids solo en CMI/Ficha (nuevos): {len(ids_nuevos)}")

    filas_nuevas = []
    for id_s in ids_nuevos:
        cmi_row = df_cmi.loc[id_s] if id_s in df_cmi.index else None
        ficha_row = df_ficha.loc[id_s] if id_s in df_ficha.index else None
        nombre = ""
        if cmi_row is not None and pd.notna(cmi_row.get("Indicador")):
            nombre = str(cmi_row["Indicador"])
        elif ficha_row is not None and pd.notna(ficha_row.get("Nombre del indicador")):
            nombre = str(ficha_row["Nombre del indicador"])
        fila = {c: None for c in CATALOGO_COLS_ACTUALES}
        fila["Id"] = id_s
        fila["Indicador"] = nombre
        fila["Fuente"] = "CMI/Ficha (sin Kawak)"
        filas_nuevas.append(fila)

    if filas_nuevas:
        df_cat = pd.concat([df_cat.drop(columns=["_id"]), pd.DataFrame(filas_nuevas)], ignore_index=True)
        df_cat["_id"] = df_cat["Id"].map(_id_str)

    # ── Poblar columnas nuevas con precedencia CMI > Ficha ─────────────
    for col in COLUMNAS_NUEVAS:
        df_cat[col] = None

    n_sin_ficha_proyecto = 0
    for i, row in df_cat.iterrows():
        id_s = row["_id"]
        cmi_row = df_cmi.loc[id_s] if id_s in df_cmi.index else None
        ficha_row = df_ficha.loc[id_s] if id_s in df_ficha.index else None

        def cmi_val(col):
            return cmi_row.get(col) if cmi_row is not None and pd.notna(cmi_row.get(col)) else None

        def ficha_val(col):
            return ficha_row.get(col) if ficha_row is not None and pd.notna(ficha_row.get(col)) else None

        df_cat.at[i, "Subproceso"] = cmi_val("Subproceso")
        df_cat.at[i, "Linea_Estrategica"] = cmi_val("Linea") or ficha_val("Linea_Estrategica")
        df_cat.at[i, "Objetivo_Estrategico"] = cmi_val("Objetivo") or ficha_val("Objetivo_Estrategico")
        df_cat.at[i, "Meta_Estrategica"] = cmi_val("Meta Estratégica")
        df_cat.at[i, "Proyecto"] = cmi_val("Proyecto")
        df_cat.at[i, "Orden_CMI"] = cmi_val("Orden CMI")
        df_cat.at[i, "Plan_Anual"] = cmi_val("Plan anual")
        df_cat.at[i, "Formula"] = ficha_val("Formula")
        df_cat.at[i, "Descripcion"] = ficha_val("Descripción del indicador")
        df_cat.at[i, "Unidad"] = ficha_val("Unidad")
        df_cat.at[i, "Responsable_Calculo"] = ficha_val("Responsable del calculo")
        df_cat.at[i, "Responsable_Analisis"] = ficha_val("Responsable del analisis")
        df_cat.at[i, "Deficiente"] = ficha_val("Deficiente")
        df_cat.at[i, "Alerta"] = ficha_val("Alerta")
        df_cat.at[i, "Satisfactorio"] = ficha_val("Satisfactorio")
        df_cat.at[i, "Sobresaliente"] = ficha_val("Sobresaliente")
        df_cat.at[i, "ID_Kawak"] = ficha_val("ID Kawak")
        df_cat.at[i, "CNA_SNIES"] = cmi_val("CNA") or ficha_val("CNA/SNIES")

        if cmi_val("Proyecto") == 1 and ficha_row is None:
            n_sin_ficha_proyecto += 1

    print(f"  Proyectos (Proyecto=1) sin fila en Ficha técnica: {n_sin_ficha_proyecto} (esperado: 54, gap ya conocido)")

    df_cat_final = df_cat.drop(columns=["_id"])
    n_despues = len(df_cat_final)
    print(f"Catalogo Indicadores: {n_antes} -> {n_despues} filas | {len(CATALOGO_COLS_ACTUALES)} -> {len(df_cat_final.columns)} columnas")

    # ── Hoja "Ficha Tecnica Detalle" (todas las columnas originales de Ficha) ──
    df_ficha_detalle = df_ficha.reset_index().rename(columns={"_id": "Id"})
    cols_orden = ["Id"] + [c for c in df_ficha_detalle.columns if c != "Id"]
    df_ficha_detalle = df_ficha_detalle[cols_orden]

    wb = openpyxl.load_workbook(CAT_FILE)
    escribir_hoja_nueva(wb, "Catalogo Indicadores", df_cat_final)
    escribir_hoja_nueva(wb, "Ficha Tecnica Detalle", df_ficha_detalle)
    wb.save(CAT_FILE)
    print(f"\nGuardado: {CAT_FILE}")
    print(f"  Catalogo Indicadores: {n_despues} filas, {len(df_cat_final.columns)} columnas")
    print(f"  Ficha Tecnica Detalle: {len(df_ficha_detalle)} filas, {len(df_ficha_detalle.columns)} columnas")


if __name__ == "__main__":
    main()
