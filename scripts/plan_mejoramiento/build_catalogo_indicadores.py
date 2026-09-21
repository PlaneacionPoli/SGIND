"""
scripts/plan_mejoramiento/build_catalogo_indicadores.py — Genera el borrador del
catálogo Signo/Decimales para los indicadores del Plan de Mejoramiento CNA.

Lee `data/raw/Plan de mejoramiento/Indicadores Plan de Mejoramiento.xlsx` y
escribe `data/raw/Plan de mejoramiento/Catalogo_Indicadores_Plan_Mejoramiento.xlsx`
con Factor/Caracteristica/Accion_Mejora/Indicador/Formula/Fuente/Periodicidad
(copiados, solo para trazabilidad) + Signo/Decimales/Decimales_Cump (NUEVO).

Signo/Decimales son un PRIMER BORRADOR heurístico — este script NO adivina con
certeza la unidad real de cada indicador (eso requiere criterio de negocio).
Revisar y corregir el Excel generado fila por fila antes de usarlo en
producción; ver services/plan_mejoramiento_loader.py::load_catalogo_plan_indicadores.

Uso: python scripts/plan_mejoramiento/build_catalogo_indicadores.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.config import DATA_RAW  # noqa: E402

SOURCE_XLSX = DATA_RAW / "Plan de mejoramiento" / "Indicadores Plan de Mejoramiento.xlsx"
OUTPUT_XLSX = DATA_RAW / "Plan de mejoramiento" / "Catalogo_Indicadores_Plan_Mejoramiento.xlsx"
SHEET_SOURCE = "Indicadores Plan de Mejor"

_RENAME = {
    "FACTOR": "Factor",
    "CARACTERÍSTICA": "Caracteristica",
    "ACCIÓN DE MEJORA": "Accion_Mejora",
    "INDICADOR DE RESULTADO O IMPACTO": "Indicador",
    "Fórmula": "Formula",
    "Fuente": "Fuente",
    "PERIODICIDAD DE MEDICIÓN": "Periodicidad",
    "Meta 2025": "Meta_2025",
    "Ejecución 2025": "Ejecucion_2025",
    "Meta 2026": "Meta_2026",
    "Ejecución 2026": "Ejecucion_2026",
}

_TEXTOS_SIN_REPORTE = {"linea base", "pendiente", "n/a", "na", ""}


def _to_num(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("$", "").replace("%", "").replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def _es_texto_sin_reporte(value) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    text = str(value).strip().lower()
    if text in _TEXTOS_SIN_REPORTE:
        return True
    return "definir" in text or "pendiente" in text


def _clasificar_signo(row: pd.Series) -> tuple[str, int, int]:
    """Heurística de primer borrador -> (Signo, Decimales, Decimales_Cump).

    Devuelve SIEMPRE Decimales_Cump=1 (el % de Cumplimiento es porcentaje por
    definición, independiente de la unidad de Meta/Ejecución).

    Distingue DOS variantes de porcentaje porque el Excel fuente NO es
    consistente en cómo guarda Meta/Ejecución de indicadores tipo "%":
      - "%FRAC": el valor crudo es una fracción 0–1 (ej. 0.95 = 95%) — la capa
        de presentación debe multiplicar por 100 antes de mostrar
        (ver streamlit_app/pages/plan_mejoramiento_utils.py::fmt_valor_plan).
      - "%": el valor crudo YA es el número de porcentaje (ej. 86.1 = 86,1%),
        igual que el resto de la app — se muestra tal cual.
    Esta distinción es la que el usuario pidió revisar caso por caso: la
    heurística es un punto de partida, no la verdad final.
    """
    valores_num = [
        v
        for v in (_to_num(row.get(c)) for c in ("Meta_2025", "Ejecucion_2025", "Meta_2026", "Ejecucion_2026"))
        if v is not None
    ]
    textos_crudos = [row.get(c) for c in ("Meta_2025", "Meta_2026")]

    if not valores_num and all(_es_texto_sin_reporte(t) for t in textos_crudos):
        return "Sin reporte", 0, 1

    formula = str(row.get("Formula") or "").lower()
    parece_proporcion = "%" in formula or "*100" in formula.replace(" ", "") or "* 100" in formula

    if valores_num and all(0 <= v <= 2 for v in valores_num) and (parece_proporcion or all(v <= 1 for v in valores_num)):
        return "%FRAC", 1, 1

    if valores_num and parece_proporcion and all(2 < v <= 150 for v in valores_num):
        return "%", 1, 1

    if valores_num and all(v == int(v) and abs(v) > 2 for v in valores_num):
        return "ENT", 0, 1

    if valores_num:
        return "DEC", 2, 1

    return "DEC", 2, 1


def main() -> None:
    if not SOURCE_XLSX.exists():
        raise SystemExit(f"No existe el archivo fuente: {SOURCE_XLSX}")

    df = pd.read_excel(SOURCE_XLSX, sheet_name=SHEET_SOURCE, header=1, engine="openpyxl")
    df.columns = [str(c).replace("\n", " ").strip() for c in df.columns]
    df = df.rename(columns={k: v for k, v in _RENAME.items() if k in df.columns})

    for col in ("Factor", "Caracteristica", "Accion_Mejora", "Indicador", "Formula", "Fuente", "Periodicidad"):
        if col not in df.columns:
            df[col] = ""

    clasificacion = df.apply(_clasificar_signo, axis=1)
    df["Signo"] = [c[0] for c in clasificacion]
    df["Decimales"] = [c[1] for c in clasificacion]
    df["Decimales_Cump"] = [c[2] for c in clasificacion]

    cols_salida = [
        "Factor", "Caracteristica", "Accion_Mejora", "Indicador", "Formula", "Fuente",
        "Periodicidad", "Signo", "Decimales", "Decimales_Cump",
    ]
    salida = df[cols_salida].copy()

    OUTPUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    salida.to_excel(OUTPUT_XLSX, sheet_name="Catalogo", index=False, engine="openpyxl")

    print(f"Catálogo generado: {OUTPUT_XLSX}")
    print(f"Total indicadores: {len(salida)}")
    print("\nDistribución de Signo asignado (revisar cada uno en el Excel):")
    print(salida["Signo"].value_counts().to_string())


if __name__ == "__main__":
    main()
