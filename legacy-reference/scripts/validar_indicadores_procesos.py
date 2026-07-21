"""Valida listado de indicadores y su cruce con procesos y unidades.

Este script inspecciona los indicadores CMI por procesos, los cruza con Kawak
si se provee año, y reporta con qué procesos y unidades está cruzando cada Id.

Uso:
    python scripts/validar_indicadores_procesos.py --year 2025
    python scripts/validar_indicadores_procesos.py --ids-file mis_ids.csv

Salida:
    artifacts/indicadores_procesos_cross_validation.xlsx
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Insert skill path for data_validation if available
SKILL_PATH = ROOT / ".github" / "skills" / "data-validation"
if SKILL_PATH.exists() and str(SKILL_PATH) not in sys.path:
    sys.path.insert(0, str(SKILL_PATH))

from services.data_loader import cargar_dataset
from services.cmi_filters import load_cmi_worksheet, get_cmi_procesos_ids, load_kawak_active_ids
from services.procesos import obtener_proceso_padre

try:
    from data_validation import enrich_with_process_hierarchy
except ImportError:
    enrich_with_process_hierarchy = None

OUT_DIR = ROOT / "artifacts"
OUT_FILE = OUT_DIR / "indicadores_procesos_cross_validation.xlsx"
RAW_CMI = ROOT / "data" / "raw" / "Catalogo de Indicadores.xlsx"  # hoja 'Catalogo Indicadores'
MASTER_PROCESOS = ROOT / "data" / "raw" / "Subproceso-Proceso-Area.xlsx"


def _normalize_id(value) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(value).strip()
    text = str(value).strip()
    try:
        num = float(text)
        if num.is_integer():
            return str(int(num))
    except Exception:
        pass
    return text


def _normalize_text(value) -> str:
    if not isinstance(value, str):
        value = str(value or "")
    value = value.strip().lower()
    return unicodedata.normalize("NFD", value)


def _load_master_process_map() -> pd.DataFrame:
    if not MASTER_PROCESOS.exists():
        raise FileNotFoundError(f"Master de procesos no encontrado: {MASTER_PROCESOS}")

    df = pd.read_excel(MASTER_PROCESOS, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _load_indicator_ids(path: Path) -> set[str]:
    if not path.exists():
        raise FileNotFoundError(f"IDs file not found: {path}")

    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path, engine="openpyxl")
    else:
        df = pd.read_csv(path)

    df.columns = [str(c).strip() for c in df.columns]
    id_col = None
    for candidate in ["Id", "ID", "id", "id_indicador", "Id indicador"]:
        if candidate in df.columns:
            id_col = candidate
            break
    if id_col is None:
        for col in df.columns:
            if str(col).strip().lower() == "id":
                id_col = col
                break

    if id_col is None:
        raise ValueError("No se encontró columna de Id en el archivo de entrada.")

    return { _normalize_id(v) for v in df[id_col].dropna().tolist() }


def build_cross_validation_table(
    dataset: pd.DataFrame,
    cmi_df: pd.DataFrame,
    master_df: pd.DataFrame,
    kawak_year: int | None = None,
    selected_ids: set[str] | None = None,
) -> pd.DataFrame:
    data = dataset.copy()
    data["Id_norm"] = data["Id"].apply(_normalize_id)
    data["Subproceso_norm"] = data["Subproceso"].astype(str).str.strip().str.lower()
    data["Proceso_norm"] = data["Proceso"].astype(str).str.strip().str.lower()

    cmi = cmi_df.copy()
    cmi["Id_norm"] = cmi["Id"].apply(_normalize_id)
    cmi["Subproceso_cmi"] = cmi.get("Subproceso", "")
    cmi["Subproceso_cmi_norm"] = cmi["Subproceso_cmi"].astype(str).str.strip().str.lower()
    cmi["Subprocesos_flag"] = pd.to_numeric(cmi.get("Subprocesos", 0), errors="coerce").fillna(0).astype(int)
    cmi = cmi[["Id_norm", "Indicador", "Subproceso_cmi", "Subproceso_cmi_norm", "Subprocesos_flag", "Linea", "Objetivo"]].drop_duplicates("Id_norm")

    merged = data.merge(cmi, on="Id_norm", how="left", suffixes=("", "_cmi"))

    if selected_ids is not None:
        merged = merged[merged["Id_norm"].isin(selected_ids)].copy()

    kawak_ids = set()
    if kawak_year is not None:
        kawak_ids = load_kawak_active_ids(kawak_year)
        merged["Kawak_active"] = merged["Id_norm"].isin(kawak_ids)
    else:
        merged["Kawak_active"] = False

    master = master_df.copy()
    master["Subproceso_norm"] = master["Subproceso"].astype(str).str.strip().str.lower()
    master["Proceso_norm"] = master["Proceso"].astype(str).str.strip().str.lower()

    master_sub = (
        master[
            ["Subproceso_norm", "Proceso", "Unidad", "Tipo de proceso"]
        ]
        .drop_duplicates(subset=["Subproceso_norm"], keep="first")
        .set_index("Subproceso_norm")
    )
    master_proc = (
        master[
            ["Proceso_norm", "Proceso", "Unidad", "Tipo de proceso"]
        ]
        .drop_duplicates(subset=["Proceso_norm"], keep="first")
        .set_index("Proceso_norm")
    )

    merged["Master_Proceso_by_Subproceso"] = merged["Subproceso_norm"].map(master_sub["Proceso"]).fillna("")
    merged["Master_Unidad_by_Subproceso"] = merged["Subproceso_norm"].map(master_sub["Unidad"]).fillna("")
    merged["Master_TipoProceso_by_Subproceso"] = merged["Subproceso_norm"].map(master_sub["Tipo de proceso"]).fillna("")

    merged["Master_Unidad_by_Proceso"] = merged["Proceso_norm"].map(master_proc["Unidad"]).fillna("")
    merged["Master_Proceso_by_Proceso"] = merged["Proceso_norm"].map(master_proc["Proceso"]).fillna("")
    merged["Master_TipoProceso_by_Proceso"] = merged["Proceso_norm"].map(master_proc["Tipo de proceso"]).fillna("")

    merged["Puede_cruzar_por_Subproceso"] = merged["Master_Proceso_by_Subproceso"].astype(bool)
    merged["Puede_cruzar_por_Proceso"] = merged["Master_Unidad_by_Proceso"].astype(bool)
    merged["Unidad_final"] = merged["Unidad"].fillna("")
    merged["Unidad_final"] = merged["Unidad_final"].mask(
        merged["Unidad_final"] == "", merged["Master_Unidad_by_Subproceso"]
    )
    merged["Unidad_final"] = merged["Unidad_final"].mask(
        merged["Unidad_final"] == "", merged["Master_Unidad_by_Proceso"]
    )

    merged["Proceso_final"] = merged["Proceso"].fillna("")
    merged["Proceso_final"] = merged["Proceso_final"].mask(
        merged["Proceso_final"] == "", merged["Master_Proceso_by_Subproceso"]
    )

    merged["Subproceso_match"] = merged["Subproceso_norm"] == merged["Subproceso_cmi_norm"]
    merged["Subproceso_missing"] = merged["Subproceso"].astype(str).str.strip() == ""
    merged["Unidad_missing"] = merged["Unidad"].astype(str).str.strip() == ""
    merged["Master_match"] = merged["Unidad_final"].astype(str).str.strip() != ""

    valid_cmi_ids = get_cmi_procesos_ids(year=kawak_year, omit_if_no_cross=False, use_kawak_cross=True)
    merged["CMI_por_procesos"] = merged["Id_norm"].isin(valid_cmi_ids)
    merged["CMI_por_procesos_base"] = merged["Subprocesos_flag"] == 1
    merged["Missing_unit_cmi"] = merged["CMI_por_procesos"] & (merged["Unidad_final"].astype(str).str.strip() == "")
    merged["Missing_master_cmi"] = merged["CMI_por_procesos"] & (~merged["Master_match"])

    cols = [
        "Id",
        "Indicador",
        "Id_norm",
        "Subproceso",
        "Subproceso_cmi",
        "Subprocesos_flag",
        "CMI_por_procesos",
        "Missing_unit_cmi",
        "Missing_master_cmi",
        "Subproceso_match",
        "Subproceso_missing",
        "Proceso",
        "Unidad",
        "Unidad_missing",
        "Tipo de proceso",
        "Proceso_final",
        "Unidad_final",
        "Master_Proceso_by_Subproceso",
        "Master_Unidad_by_Subproceso",
        "Master_Unidad_by_Proceso",
        "Master_match",
        "Kawak_active",
        "Linea",
        "Objetivo",
    ]

    for col in cols:
        if col not in merged.columns:
            merged[col] = ""

    return merged[cols]


def summarize(merged: pd.DataFrame, kawak_year: int | None) -> int:
    total = len(merged)
    cmi_procesos = merged[merged["CMI_por_procesos"]].shape[0]
    missing_unidad_cmi = merged[merged["Missing_unit_cmi"]].shape[0]
    missing_master_cmi = merged[merged["Missing_master_cmi"]].shape[0]
    kawak_cross = merged[merged["Kawak_active"]].shape[0]

    print(f"Total indicadores analizados: {total}")
    print(f"Indicadores CMI por procesos (Subprocesos==1): {cmi_procesos}")
    if kawak_year is not None:
        print(f"Indicadores activos en Kawak {kawak_year}: {kawak_cross}")
    print(f"Indicadores CMI por procesos sin Unidad final: {missing_unidad_cmi}")
    print(f"Indicadores CMI por procesos sin cruce maestro de unidad/proceso: {missing_master_cmi}")
    print("\nSubprocesos detectados que no cruzan correctamente con la maestra:")
    print(merged[merged["Missing_unit_cmi"]]["Subproceso"].astype(str).value_counts().to_string())

    return 1 if missing_unidad_cmi > 0 else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validar listados de indicadores y el cruce con procesos/unidades")
    parser.add_argument("--year", type=int, default=None, help="Año para cruzar con Kawak")
    parser.add_argument("--ids-file", type=Path, default=None, help="Archivo CSV/XLSX con IDs de indicadores a validar")
    parser.add_argument("--output", type=Path, default=OUT_FILE, help="Archivo de salida")
    parser.add_argument("--no-save", action="store_true", help="No guardar el resultado en disco")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        dataset = cargar_dataset()
        print(f"Cargado dataset con {len(dataset)} filas desde cargar_dataset().")
    except Exception as exc:
        print(f"Error cargando dataset con cargar_dataset(): {exc}")
        dataset = pd.DataFrame()

    if dataset.empty:
        source_path = ROOT / "data" / "output" / "Resultados Consolidados.xlsx"
        if not source_path.exists():
            raise FileNotFoundError("No se pudo cargar el dataset ni encontrar Resultados Consolidados.xlsx")
        dataset = pd.read_excel(source_path, sheet_name="Consolidado Semestral", engine="openpyxl")
        dataset.columns = [str(c).strip() for c in dataset.columns]
        print(f"Cargado dataset crudo desde {source_path} con {len(dataset)} filas.")

    if args.ids_file is not None:
        selected_ids = _load_indicator_ids(args.ids_file)
        print(f"Cargados {len(selected_ids)} IDs desde {args.ids_file}")
    else:
        selected_ids = None

    cmi_df = load_cmi_worksheet()
    if cmi_df.empty:
        raise ValueError(f"No se pudo cargar la hoja Worksheet desde {RAW_CMI}")

    master_df = _load_master_process_map()

    if enrich_with_process_hierarchy is not None:
        try:
            dataset = enrich_with_process_hierarchy(dataset, MASTER_PROCESOS)
            print("Dataset enriquecido con procesos/unidades desde el maestro.")
        except Exception as exc:
            print(f"Advertencia: no se pudo enriquecer dataset con la jerarquía de procesos: {exc}")

    merged = build_cross_validation_table(
        dataset=dataset,
        cmi_df=cmi_df,
        master_df=master_df,
        kawak_year=args.year,
        selected_ids=selected_ids,
    )

    exit_code = summarize(merged, args.year)

    if not args.no_save:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        merged.to_excel(args.output, index=False)
        print(f"Resultado guardado en: {args.output}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
