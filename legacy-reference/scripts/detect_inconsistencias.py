"""Detecta inconsistencias de unidades/signos en cierres de indicadores.

Genera un CSV con indicadores cuyo signo de Meta o Ejecucion cambia entre periodos,
lo que puede indicar mezcla de unidades (p. ej. $ y % para el mismo Id).
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.strategic_indicators import load_cierres

OUT_DIR = ROOT / "artifacts"
OUT_FILE = OUT_DIR / "indicadores_inconsistentes.xlsx"


def _clean_sign(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _sign_set(series: pd.Series) -> list[str]:
    signs = sorted({s for s in series.map(_clean_sign).tolist() if s != ""})
    return signs


def detectar_inconsistencias() -> pd.DataFrame:
    df = load_cierres()
    if df.empty:
        return pd.DataFrame(
            columns=[
                "Id",
                "Indicador",
                "n_registros",
                "meta_signos",
                "ejec_signos",
                "meta_mixto",
                "ejec_mixto",
                "meta_min",
                "meta_max",
                "ejec_min",
                "ejec_max",
            ]
        )

    cols = ["Id", "Indicador", "Meta_Signo", "Ejecucion_Signo", "Meta", "Ejecucion"]
    data = df[[c for c in cols if c in df.columns]].copy()

    grouped = (
        data.groupby("Id", dropna=False)
        .agg(
            Indicador=("Indicador", "first"),
            n_registros=("Id", "size"),
            meta_signos=("Meta_Signo", _sign_set),
            ejec_signos=("Ejecucion_Signo", _sign_set),
            meta_min=("Meta", "min"),
            meta_max=("Meta", "max"),
            ejec_min=("Ejecucion", "min"),
            ejec_max=("Ejecucion", "max"),
        )
        .reset_index()
    )

    grouped["meta_mixto"] = grouped["meta_signos"].map(lambda signs: len(signs) > 1)
    grouped["ejec_mixto"] = grouped["ejec_signos"].map(lambda signs: len(signs) > 1)

    inconsistentes = grouped[(grouped["meta_mixto"]) | (grouped["ejec_mixto"])].copy()
    inconsistentes = inconsistentes.sort_values(["n_registros", "Id"], ascending=[False, True])

    # Convertir listas a texto para exportacion tabular
    inconsistentes["meta_signos"] = inconsistentes["meta_signos"].map(lambda vals: " | ".join(vals))
    inconsistentes["ejec_signos"] = inconsistentes["ejec_signos"].map(lambda vals: " | ".join(vals))

    return inconsistentes


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    inconsistentes = detectar_inconsistencias()
    inconsistentes.to_excel(OUT_FILE, index=False)

    total = len(inconsistentes)
    print(f"Archivo generado: {OUT_FILE}")
    print(f"Indicadores inconsistentes: {total}")

    # Visibilidad rápida del caso reportado por negocio
    if "Id" in inconsistentes.columns:
        hit_204 = inconsistentes[inconsistentes["Id"].astype(str).str.strip() == "204"]
        if not hit_204.empty:
            print("Se detecto inconsistencia para Id 204.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
