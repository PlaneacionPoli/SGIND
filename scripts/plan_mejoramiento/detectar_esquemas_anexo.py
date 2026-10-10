"""Detecta el patrón de cada hoja del Anexo Estadístico y genera esquemas borrador.

Uso:
    python scripts/plan_mejoramiento/detectar_esquemas_anexo.py [ruta_xlsx] [dir_salida]

Salida (dir_salida, por defecto data/processed/anexo_esquemas/):
    esquemas_borrador.json   un esquema por hoja (insumo de la definición de tablas)
    resumen_patrones.csv     una fila por hoja, para revisión en Excel
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_XLSX = ROOT / "data/raw/Plan de mejoramiento/Anexo Estadístico Dcto. Autoevaluacion.xlsx"
DEFAULT_OUT = ROOT / "data/processed/anexo_esquemas"

PERIODO_RE = re.compile(r"^\s*((19|20)\d{2})(\s*[-/.]\s*([12I]{1,2}))?\s*$")
META_KEYS = ("tabla no", "gráfico no", "grafico no", "nombre", "*")


def _txt(v) -> str:
    return "" if v is None else str(v).strip()


def _es_periodo(v) -> bool:
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return 1990 <= v <= 2040 and float(v).is_integer()
    return bool(PERIODO_RE.match(_txt(v)))


def _es_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _tipo_hoja(nombre: str) -> str:
    n = nombre.lower()
    if n.startswith("gr"):
        return "grafico"
    if n.startswith("ilus"):
        return "ilustracion"
    return "tabla"


def _clasificar_formula(f: str) -> str:
    u = f.upper()
    if "SUM(" in u or re.fullmatch(r"=\+?[A-Z]+\d+(\+[A-Z]+\d+)+", u.replace(" ", "")):
        return "suma"
    if "/" in u:
        return "razon"
    if "AVERAGE(" in u or "PROMEDIO(" in u:
        return "promedio"
    return "otra"


def analizar_hoja(ws, ws_f) -> dict:
    grid = [[c.value for c in row] for row in ws.iter_rows()]
    n_rows = len(grid)
    n_cols = max((len(r) for r in grid), default=0)

    # meta: número y nombre de la tabla (primeras filas)
    meta_nombre = ""
    for r in grid[:4]:
        if r and _txt(r[0]).lower() == "nombre":
            meta_nombre = _txt(r[1]) if len(r) > 1 else ""

    # fila de encabezado: la de mayor cantidad de periodos; si no hay, primera fila
    # con >=2 textos tras las filas meta.
    mejor, hdr_row, per_cols = 0, None, []
    for i, r in enumerate(grid[:60]):
        cols = [j for j, v in enumerate(r) if _es_periodo(v)]
        if len(cols) > mejor:
            mejor, hdr_row, per_cols = len(cols), i, cols
    periodos_en = "columnas" if mejor >= 2 else None

    if hdr_row is None:
        for i, r in enumerate(grid[:15]):
            if _txt(r[0] if r else "").lower() in META_KEYS:
                continue
            if sum(1 for v in r if isinstance(v, str) and v.strip()) >= 2:
                hdr_row = i
                break

    # periodos en filas: primera columna con años en la mayoría de las filas de datos
    col0 = [r[0] for r in grid[(hdr_row or 0) + 1:] if r and r[0] is not None]
    if periodos_en is None and len(col0) >= 3 and sum(map(_es_periodo, col0)) / len(col0) >= 0.5:
        periodos_en = "filas"

    header = grid[hdr_row] if hdr_row is not None else []
    data = grid[hdr_row + 1:] if hdr_row is not None else grid
    data = [r for r in data if any(v is not None for v in r)]

    nums = sum(_es_num(v) for r in data for v in r)
    textos = sum(isinstance(v, str) and v.strip() != "" for r in data for v in r)
    celdas = nums + textos or 1
    ratio_num = nums / celdas

    # fórmulas
    forms = Counter()
    for row in ws_f.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith("="):
                forms[_clasificar_formula(c.value)] += 1

    # subtotales/total: filas cuya primera celda dice "total"
    filas_total = sum(
        1 for r in data if any(isinstance(v, str) and v.strip().lower().startswith("total") for v in r[:2])
    )
    n_dim = 0
    if hdr_row is not None:
        limite = per_cols[0] if per_cols else len(header)
        n_dim = max(1, sum(1 for v in header[:limite] if _txt(v)))

    tipo = _tipo_hoja(ws.title)
    # patrón
    if tipo != "tabla":
        patron = "grafico_ilustracion"
    elif len(data) == 0:
        patron = "vacia"
    elif periodos_en == "columnas":
        patron = "matriz_periodo_columnas"
    elif periodos_en == "filas":
        patron = "serie_periodo_filas"
    elif len(data) >= 12 and ratio_num < 0.45:
        patron = "listado_registros"
    elif ratio_num >= 0.45:
        patron = "matriz_sin_periodo"  # cruces categoría x métrica (p. ej. admisión)
    else:
        patron = "otro_manual"

    # dificultad / automatizabilidad
    marcas = []
    if len(ws.merged_cells.ranges) > 0:
        marcas.append("celdas_combinadas")
    if len(ws_f._charts) or len(ws_f._images):
        marcas.append("grafico_o_imagen")
    if sum(1 for r in grid[:60] if r and _txt(r[0]).lower() in ("nombre",)) > 1:
        marcas.append("bloques_multiples")
    if forms.get("otra"):
        marcas.append("formulas_complejas")
    if filas_total:
        marcas.append("subtotales")

    columnas = []
    for j, v in enumerate(header):
        t = _txt(v)
        if not t:
            continue
        if j in per_cols:
            rol = "periodo"
        elif j < (per_cols[0] if per_cols else len(header)) and not _es_num(v):
            rol = "dimension"
        else:
            rol = "metrica"
        muestra = [r[j] for r in data[:30] if j < len(r) and r[j] is not None]
        tipo_col = "numero" if muestra and sum(map(_es_num, muestra)) / len(muestra) > 0.6 else "texto"
        columnas.append({"col": j + 1, "nombre": t, "rol": rol, "tipo": tipo_col})

    return {
        "hoja": ws.title,
        "tipo_hoja": tipo,
        "nombre_en_hoja": meta_nombre,
        "patron": patron,
        "periodos_en": periodos_en,
        "periodos": [_txt(header[j]) for j in per_cols] if per_cols else [],
        "fila_encabezado": None if hdr_row is None else hdr_row + 1,
        "filas_datos": len(data),
        "columnas_total": n_cols,
        "n_dimensiones": n_dim,
        "ratio_numerico": round(ratio_num, 2),
        "filas_total": filas_total,
        "formulas": dict(forms),
        "marcas": marcas,
        "columnas": columnas,
        "nivel_sugerido": (
            "C_manual_formulario" if patron == "listado_registros"
            else "manual_adjunto" if (patron in ("otro_manual", "vacia") or len(marcas) >= 3)
            else "B_plantilla"
        ),
    }


def cargar_indice(wb) -> dict:
    """Mapa hoja -> metadatos del índice (fuente, responsable, enlace, factor)."""
    ws = next(s for s in wb if s.title.lower().startswith("índice") or s.title.lower().startswith("indice"))
    hdr = [_txt(c.value) for c in ws[1]]
    ix = {h: i for i, h in enumerate(hdr)}
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        t, g = row[ix["Tabla No"]], row[ix["Gráfico"]]
        if t:
            clave = f"Tabla {_txt(t)}"
        elif g:
            clave = _txt(g) if _txt(g).lower().startswith("ilus") else f"Gráfico {_txt(g)}"
        else:
            continue
        out[clave] = {
            "factor": _txt(row[ix["Factor"]]),
            "caracteristica": _txt(row[ix["SUBCAPÍTULO/CARACTERÍSTICA"]]),
            "nombre": _txt(row[ix["Nombre"]]),
            "fuente": _txt(row[ix["Fuente"]]),
            "responsable": _txt(row[ix["Responsable Información"]]),
            "enlace": _txt(row[ix["Enlace"]]),
            "observaciones": _txt(row[ix["Observaciones"]]) if "Observaciones" in ix else "",
        }
    return out


def main() -> None:
    xlsx = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_XLSX
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.load_workbook(xlsx, data_only=True)
    wf = openpyxl.load_workbook(xlsx)
    indice = cargar_indice(wb)

    esquemas, sin_indice = [], []
    for ws in wb:
        t = ws.title.lower()
        if t == "respaldo" or t.startswith("índice") or t.startswith("indice"):
            continue
        e = analizar_hoja(ws, wf[ws.title])
        meta = indice.get(ws.title)
        if meta is None:
            sin_indice.append(ws.title)
        e["indice"] = meta or {}
        esquemas.append(e)

    en_hojas = {e["hoja"] for e in esquemas}
    sin_hoja = sorted(k for k in indice if k not in en_hojas)

    (out / "esquemas_borrador.json").write_text(
        json.dumps(
            {"origen": xlsx.name, "hojas_sin_indice": sin_indice, "indice_sin_hoja": sin_hoja, "esquemas": esquemas},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )

    cols = ["hoja", "patron", "nivel_sugerido", "periodos_en", "n_periodos", "ultimo_periodo", "filas_datos",
            "n_dimensiones", "marcas", "fuente", "responsable", "enlace", "nombre"]
    with (out / "resumen_patrones.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for e in esquemas:
            ix = e["indice"]
            w.writerow([
                e["hoja"], e["patron"], e["nivel_sugerido"], e["periodos_en"] or "", len(e["periodos"]),
                e["periodos"][-1] if e["periodos"] else "", e["filas_datos"], e["n_dimensiones"],
                ";".join(e["marcas"]), ix.get("fuente", ""), ix.get("responsable", ""),
                ix.get("enlace", ""), ix.get("nombre", "") or e["nombre_en_hoja"],
            ])

    print(f"Hojas analizadas: {len(esquemas)}")
    for k, v in Counter(e["patron"] for e in esquemas).most_common():
        print(f"  {k:28s} {v}")
    print("Nivel sugerido:", dict(Counter(e["nivel_sugerido"] for e in esquemas)))
    print("Marcas:", dict(Counter(m for e in esquemas for m in e["marcas"])))
    print("Hojas sin entrada en índice:", sin_indice)
    print("Entradas del índice sin hoja:", sin_hoja)
    print("Salida en", out)


if __name__ == "__main__":
    main()
