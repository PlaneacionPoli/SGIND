"""Agrega al directorio maestro (data/raw/Catalogo de Indicadores.xlsx) una hoja
INDEPENDIENTE por PDI — impact_report.md §4.1:

  PDI_2022_2026   Indicadores de ese PDI, con su columna PDI (1/0), línea, objetivo y meta.
                  Se migra UNA vez desde las columnas heredadas del catálogo y queda
                  congelada (si la hoja ya existe, no se toca).
  PDI_2026_2030   Ídem para el PDI vigente. Se precarga con los indicadores activos, los
                  proyectos del PDI anterior que NO han cerrado (mismo Id) y los proyectos
                  nuevos del ciclo. Planeación la diligencia; el script nunca pisa lo
                  diligenciado, solo agrega los indicadores que falten.
  Listas_PDI_*    Jerarquía oficial de cada PDI (qué objetivos tiene cada línea y qué metas
                  cada objetivo) y los bloques de los desplegables en cascada (se regeneran).
  Taxonomia_Marco Líneas/objetivos/metas de todas las versiones (derivada).

Cada hoja de PDI tiene una sola columna PDI:
  1 = indicador estratégico del PDI (incluye proyectos; EXIGE meta estratégica)
  0 = de proceso (NO puede tener meta estratégica) | vacío = sin definir.
Línea, Objetivo y Meta se eligen por nombre en listas desplegables EN CASCADA: el
objetivo solo ofrece los de la línea elegida y la meta solo las del objetivo elegido.

La hoja "Catalogo Indicadores" no se modifica (se retiran las columnas Tipo_/Estrategico_ por
PDI y las hojas de diseños anteriores). Uso:
    backend/.venv312/Scripts/python.exe scripts/agregar_hojas_marco_catalogo.py
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import openpyxl
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))
os.environ.setdefault("SGIND_DATA_PATH", str(BASE_DIR / "data"))  # el default "../data" depende del cwd

from app.domain.marcos import Marco, get_marco, get_marcos, marco_activo  # noqa: E402
from app.domain.taxonomia import load_taxonomia, norm_texto  # noqa: E402

CATALOGO_FILE = BASE_DIR / "data" / "raw" / "Catalogo de Indicadores.xlsx"
HOJA_CATALOGO = "Catalogo Indicadores"
HOJA_TAXONOMIA = "Taxonomia_Marco"
# Hojas/columnas de diseños anteriores que se retiran (Codigos_PDI_* se detecta por prefijo).
HOJAS_OBSOLETAS = ("Indicador_Marco", "Listas_Marco", "Codigos_PDI")
PREFIJO_HOJAS_OBSOLETAS = "Codigos_PDI_"
PREFIJOS_COLUMNAS_OBSOLETAS = ("Tipo_PDI_", "Estrategico_PDI_")
COLS_CODIGO_OBSOLETAS = ("Linea_Cod", "Objetivo_Cod", "Meta_Cod")

COLS_CONTEXTO = ["Id", "Indicador", "Proceso", "Clasificacion", "Estado", "Origen"]
COL_ANTERIOR = "Linea_PDI_anterior"  # solo en el PDI vigente: referencia de la línea del PDI cerrado
COLS_ENTRADA = ["PDI", "Linea", "Objetivo", "Meta", "Observaciones"]

HEADER_FILL = PatternFill("solid", fgColor="1D3557")
ENTRADA_FILL = PatternFill("solid", fgColor="FFF8DC")
HEADER_FONT = Font(bold=True, color="FFFFFF")
FILAS_VALIDACION_EXTRA = 600

# Proyectos del ciclo anterior (PRY-1..44, ProyectosOficialesService.PROYECTO_MAX):
# los de estado PMO distinto de "Cerrado" continúan en el ciclo nuevo.
ESTADOS_CERRADOS = {"cerrado", "finalizado"}
PROYECTO_MAX_CICLO_ANTERIOR = 44
ORIGEN_ACTIVO = "Indicador activo"
ORIGEN_PROYECTO_CONTINUA = "Proyecto en curso (continúa)"
ORIGEN_PROYECTO_NUEVO = "Proyecto nuevo del ciclo"
ORIGEN_MIGRADO = "Migrado del catálogo"
_PLACEHOLDERS = {"seleccione", "nan", "none", ""}


def hoja_pdi(marco: Marco) -> str:
    return marco.version_id.replace("-", "_")  # PDI_2026_2030


def hoja_listas(marco: Marco) -> str:
    return "Listas_" + hoja_pdi(marco)


def columnas(marco: Marco) -> list[str]:
    extra = [COL_ANTERIOR] if marco.estado == "activo" else []
    return COLS_CONTEXTO + extra + COLS_ENTRADA


def _estilo_encabezado(ws, n_cols: int) -> None:
    for c in range(1, n_cols + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"


def _reemplazar_hoja(wb, nombre: str):
    if nombre in wb.sheetnames:
        del wb[nombre]
    return wb.create_sheet(nombre)


def _num_pry(valor: object) -> int | None:
    m = re.match(r"^PRY-(\d+)$", str(valor).strip(), re.IGNORECASE)
    return int(m.group(1)) if m else None


def _marca_plan(row: pd.Series) -> bool:
    return str(row.get("Indicadores_Plan_Estrategico")).strip() in ("1", "1.0")


def _limpio(valor: object, *, guion_bajo: bool = False) -> str | None:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).replace("_", " ") if guion_bajo else str(valor)
    return None if norm_texto(texto) in _PLACEHOLDERS else texto.strip()


def _v(valor: object) -> object:
    return None if valor is None or (isinstance(valor, float) and pd.isna(valor)) else valor


# ── Limpieza de diseños anteriores ───────────────────────────────────────────

def _hoja_con_codigos(ws) -> tuple[bool, bool]:
    """(tiene el diseño con códigos, tiene códigos diligenciados)."""
    enc = [c.value for c in ws[1]]
    idx = [enc.index(c) for c in COLS_CODIGO_OBSOLETAS if c in enc]
    if not idx:
        return False, False
    return True, any(any(r[i].value not in (None, "") for i in idx) for r in ws.iter_rows(min_row=2))


def retirar_obsoletos(wb, cerrado: Marco, vigente: Marco) -> list[str]:
    """Quita hojas y columnas de diseños anteriores. Las hojas de PDI con el diseño de códigos
    se regeneran: la del PDI cerrado siempre (es una migración); la vigente solo si no tiene
    códigos diligenciados (si los tiene, se aborta para no perder trabajo)."""
    quitados: list[str] = []
    if "Indicador_Marco" in wb.sheetnames:
        ws = wb["Indicador_Marco"]
        enc = [c.value for c in ws[1]]
        idx = [enc.index(c) for c in ("Linea", "Objetivo", "Meta") if c in enc]
        if any(any(r[i].value not in (None, "") for i in idx) for r in ws.iter_rows(min_row=2)):
            raise SystemExit("Indicador_Marco ya tiene asociaciones diligenciadas; no se elimina. Avísame para migrarlas.")
    for marco in (cerrado, vigente):
        if hoja_pdi(marco) in wb.sheetnames:
            con_codigos, diligenciados = _hoja_con_codigos(wb[hoja_pdi(marco)])
            if con_codigos:
                if diligenciados and marco is vigente:
                    raise SystemExit(f"{hoja_pdi(marco)} tiene códigos diligenciados; avísame para migrarlos a nombres.")
                del wb[hoja_pdi(marco)]
                quitados.append(f"hoja {hoja_pdi(marco)} (diseño con códigos)")
    for nombre in list(wb.sheetnames):
        if nombre in HOJAS_OBSOLETAS or nombre.startswith(PREFIJO_HOJAS_OBSOLETAS):
            del wb[nombre]
            quitados.append(f"hoja {nombre}")
    ws = wb[HOJA_CATALOGO]
    for col in range(ws.max_column, 0, -1):
        enc = ws.cell(row=1, column=col).value
        if isinstance(enc, str) and enc.startswith(PREFIJOS_COLUMNAS_OBSOLETAS):
            ws.delete_cols(col)
            quitados.append(f"columna {enc}")
    return quitados


# ── Hojas derivadas de la taxonomía ──────────────────────────────────────────

def escribir_taxonomia(wb) -> None:
    ws = _reemplazar_hoja(wb, HOJA_TAXONOMIA)
    ws.append(["version_id", "linea_id", "Linea", "objetivo_id", "Objetivo", "meta_id", "Meta"])
    for marco in get_marcos("PDI"):
        if not marco.taxonomia:
            continue
        for linea, obj, meta in load_taxonomia(marco.taxonomia).iter_metas():
            ws.append([marco.version_id, linea.id, linea.nombre, obj.id, obj.nombre, meta.id, meta.nombre])
    _estilo_encabezado(ws, 7)
    for col, w in zip("ABCDEFG", (16, 34, 34, 40, 70, 44, 80), strict=True):
        ws.column_dimensions[col].width = w


def escribir_listas(wb, marco: Marco) -> dict:
    """Hoja Listas_<PDI> con la jerarquía visible y los bloques que alimentan los desplegables
    en cascada. Devuelve la información que necesitan las validaciones.

      A:C   Jerarquía legible: cada línea con sus objetivos y cada objetivo con sus metas
            (la línea y el objetivo solo se escriben en la primera fila de su grupo).
      Bloque "Objetivos por línea": una columna por línea (encabezado = nombre de la línea)
            con sus objetivos debajo.
      Bloque "Metas por objetivo": una columna por objetivo con sus metas debajo.
    """
    nombre = hoja_listas(marco)
    ws = _reemplazar_hoja(wb, nombre)
    tax = load_taxonomia(marco.taxonomia)
    n_lin = len(tax.lineas)
    n_obj = sum(len(ln.objetivos) for ln in tax.lineas)
    max_obj = max(len(ln.objetivos) for ln in tax.lineas)
    max_meta = max(len(o.metas) for ln in tax.lineas for o in ln.objetivos)

    # A:C jerarquía legible
    ws.append(["Linea", "Objetivo", "Meta"])
    fila = 2
    negrita = Font(bold=True)
    fondo_linea = PatternFill("solid", fgColor="DCE6F1")
    fondo_obj = PatternFill("solid", fgColor="F2F2F2")
    for ln in tax.lineas:
        for k, ob in enumerate(ln.objetivos):
            for m, meta in enumerate(ob.metas or [None]):
                ws.cell(row=fila, column=1, value=ln.nombre if (k == 0 and m == 0) else None)
                ws.cell(row=fila, column=2, value=ob.nombre if m == 0 else None)
                ws.cell(row=fila, column=3, value=meta.nombre if meta else None)
                if k == 0 and m == 0:
                    for c in (1, 2, 3):
                        ws.cell(row=fila, column=c).fill = fondo_linea
                    ws.cell(row=fila, column=1).font = negrita
                elif m == 0:
                    for c in (2, 3):
                        ws.cell(row=fila, column=c).fill = fondo_obj
                fila += 1

    # Bloque B: objetivos por línea (encabezado = línea)
    col_b = 5
    for j, ln in enumerate(tax.lineas):
        ws.cell(row=1, column=col_b + j, value=ln.nombre)
        for i, ob in enumerate(ln.objetivos):
            ws.cell(row=2 + i, column=col_b + j, value=ob.nombre)
    # Bloque C: metas por objetivo (encabezado = objetivo)
    col_c = col_b + n_lin + 1
    j = 0
    for ln in tax.lineas:
        for ob in ln.objetivos:
            ws.cell(row=1, column=col_c + j, value=ob.nombre)
            for i, meta in enumerate(ob.metas):
                ws.cell(row=2 + i, column=col_c + j, value=meta.nombre)
            j += 1

    _estilo_encabezado(ws, col_c + n_obj - 1)
    ws.cell(row=1, column=4).fill = PatternFill(fill_type=None)  # separadores sin estilo
    ws.cell(row=1, column=col_b + n_lin).fill = PatternFill(fill_type=None)
    for col, w in zip("ABC", (36, 70, 80), strict=True):
        ws.column_dimensions[col].width = w
    for c in range(col_b, col_c + n_obj):
        ws.column_dimensions[get_column_letter(c)].width = 46

    def rango(col_ini: int, n: int) -> str:
        return f"${get_column_letter(col_ini)}$1:${get_column_letter(col_ini + n - 1)}$1"

    return {
        "hoja": nombre,
        "lin_hdr": rango(col_b, n_lin),
        "lin_ancla": f"${get_column_letter(col_b)}$1",
        "obj_hdr": rango(col_c, n_obj),
        "obj_ancla": f"${get_column_letter(col_c)}$1",
        "max_obj": max_obj,
        "max_meta": max_meta,
    }


def _formula_cascada(info: dict, ancla: str, hdr: str, col_padre: str, filas: int) -> str:
    """Lista dependiente: las opciones son la columna cuyo encabezado coincide con el valor
    elegido en `col_padre` (p. ej. los objetivos de la línea elegida)."""
    h = info["hoja"]
    idx = f"MATCH(${col_padre}2,{h}!{hdr},0)"
    base = f"{h}!{ancla}"
    return f"=OFFSET({base},1,{idx}-1,COUNTA(OFFSET({base},1,{idx}-1,{filas},1)),1)"


# ── Migración del PDI cerrado (desde las columnas heredadas del catálogo) ────

def migrar_pdi_cerrado(df_cat: pd.DataFrame, marco: Marco) -> pd.DataFrame:
    """Filas de la hoja del PDI cerrado a partir de Linea_Estrategica / Objetivo_Estrategico /
    Meta_Estrategica / Indicadores_Plan_Estrategico del catálogo.

    PDI = 1 si Indicadores_Plan_Estrategico = 1, si no 0. Línea, objetivo y meta quedan con el
    NOMBRE OFICIAL cuando coinciden con la taxonomía (ignorando tildes, mayúsculas y
    puntuación); si no, se conserva el texto original tal cual, sin adivinar el equivalente.
    Se excluyen los PRY posteriores al 44 (son del ciclo nuevo) y las filas sin línea.
    """
    tax = load_taxonomia(marco.taxonomia)
    lineas = {norm_texto(ln.nombre): ln for ln in tax.lineas}
    filas = []
    for _, r in df_cat.iterrows():
        n = _num_pry(r["Id"])
        if n is not None and n > PROYECTO_MAX_CICLO_ANTERIOR:
            continue
        linea_t = _limpio(r.get("Linea_Estrategica"), guion_bajo=True)
        if linea_t is None:
            continue
        ln = lineas.get(norm_texto(linea_t))
        linea = ln.nombre if ln else linea_t
        obj_t = _limpio(r.get("Objetivo_Estrategico"))
        meta_t = _limpio(r.get("Meta_Estrategica"))
        objetivo, meta = obj_t, meta_t
        if ln is not None and obj_t:
            ob = next((o for o in ln.objetivos if norm_texto(o.nombre) == norm_texto(obj_t)), None)
            if ob is not None:
                objetivo = ob.nombre
                if meta_t:
                    m = next((m for m in ob.metas if norm_texto(m.nombre) == norm_texto(meta_t)), None)
                    meta = m.nombre if m else meta_t
        filas.append({
            "Id": r["Id"], "Indicador": r.get("Indicador"), "Proceso": r.get("Proceso"),
            "Clasificacion": r.get("Clasificacion"), "Estado": r.get("Estado"), "Origen": ORIGEN_MIGRADO,
            "PDI": 1 if _marca_plan(r) else 0,
            "Linea": linea, "Objetivo": objetivo, "Meta": meta, "Observaciones": None,
        })
    return pd.DataFrame(filas)


# ── Candidatos del PDI vigente ───────────────────────────────────────────────

def estados_proyectos_ciclo_anterior() -> dict[str, str]:
    """Id -> estado PMO de los 44 proyectos del PDI anterior (misma fuente que
    el Resumen General: ProyectosOficialesService)."""
    from app.api.deps import get_excel_service
    from app.core.config import get_settings
    from app.services.proyectos_oficiales_service import ProyectosOficialesService

    df = ProyectosOficialesService(get_excel_service(get_settings())).load()
    if df.empty:
        raise SystemExit("No se pudo leer el estado de los proyectos (ProyectosOficialesService vacío).")
    return dict(zip(df["Id"].astype(str), df["estado"].astype(str), strict=True))


def candidatos_vigente(df_cat: pd.DataFrame, estados_proyectos: dict[str, str]) -> pd.DataFrame:
    """Filas a precargar para el PDI vigente (activos + proyectos en curso + proyectos nuevos).

    Un proyecto es "en curso" si su estado PMO no es Cerrado/Finalizado: los "Stand by"
    siguen abiertos y por eso continúan. PDI se sugiere con la marca actual del plan
    estratégico (los proyectos siempre 1); Planeación debe revisarlo.
    """
    df = df_cat.copy()
    df["Origen"] = None
    num = df["Id"].map(_num_pry)
    es_pry = num.notna()
    activo = df["Estado"].astype(str).str.strip().str.lower() == "activo"
    df.loc[activo, "Origen"] = ORIGEN_ACTIVO
    for pos, row in df[es_pry].iterrows():
        n = int(num[pos])
        if n > PROYECTO_MAX_CICLO_ANTERIOR:
            df.at[pos, "Origen"] = ORIGEN_PROYECTO_NUEVO
        else:
            estado = estados_proyectos.get(str(row["Id"]).strip())
            if estado is not None and estado.strip().lower() not in ESTADOS_CERRADOS:
                df.at[pos, "Origen"] = f"{ORIGEN_PROYECTO_CONTINUA} · PMO: {estado}"
    out = df[df["Origen"].notna()].copy()
    out[COL_ANTERIOR] = out["Linea_Estrategica"]
    out["PDI"] = [1 if (_num_pry(i) is not None or _marca_plan(r)) else 0
                  for i, (_, r) in zip(out["Id"], out.iterrows(), strict=True)]
    return out


# ── Escritura de la hoja de cada PDI ─────────────────────────────────────────

def aplicar_validaciones(ws, cols: list[str], marco: Marco, listas: dict) -> None:
    """PDI solo 1/0; Linea de la lista oficial; Objetivo solo los de la línea elegida y Meta
    solo las del objetivo elegido (listas en cascada). No toca los valores ya escritos."""
    ultima = ws.max_row + FILAS_VALIDACION_EXTRA
    ws.data_validations.dataValidation = []
    letra = {c: get_column_letter(cols.index(c) + 1) for c in ("PDI", "Linea", "Objetivo", "Meta")}
    h = listas["hoja"]

    def agregar(formula: str, columna: str, titulo: str, error: str, prompt: str | None = None) -> None:
        dv = DataValidation(type="list", formula1=formula, allow_blank=True, showErrorMessage=True)
        dv.errorTitle, dv.error = titulo, error
        if prompt:
            dv.showInputMessage, dv.promptTitle, dv.prompt = True, columna, prompt
        ws.add_data_validation(dv)
        dv.add(f"{letra[columna]}2:{letra[columna]}{ultima}")

    agregar('"1,0"', "PDI", "Valor no válido",
            "1 = estratégico del PDI (exige meta) | 0 = de proceso (sin meta) | vacío = sin definir")
    agregar(f"={h}!{listas['lin_hdr']}", "Linea", "Línea fuera de la taxonomía", f"Elige una línea de {marco.nombre}.")
    agregar(_formula_cascada(listas, listas["lin_ancla"], listas["lin_hdr"], letra["Linea"], listas["max_obj"]),
            "Objetivo", "Objetivo no válido", "Elige un objetivo de la línea seleccionada (primero elige la Línea).",
            "Elige primero la Línea: solo se listan sus objetivos.")
    agregar(_formula_cascada(listas, listas["obj_ancla"], listas["obj_hdr"], letra["Objetivo"], listas["max_meta"]),
            "Meta", "Meta no válida", "Elige una meta del objetivo seleccionado (primero elige el Objetivo).",
            "Elige primero el Objetivo: solo se listan sus metas.")


def escribir_hoja_pdi(wb, marco: Marco, filas: pd.DataFrame, listas: dict) -> tuple[int, int]:
    """Crea/actualiza la hoja del PDI sin pisar filas existentes. Devuelve (existentes, nuevas)."""
    cols = columnas(marco)
    nombre = hoja_pdi(marco)
    if nombre in wb.sheetnames:
        ws = wb[nombre]
        if [c.value for c in ws[1]] != cols:
            raise SystemExit(f"{nombre} tiene columnas inesperadas {[c.value for c in ws[1]]}; revisar a mano.")
        existentes = {str(r[0].value).strip() for r in ws.iter_rows(min_row=2) if r[0].value is not None}
    else:
        ws = wb.create_sheet(nombre)
        ws.append(cols)
        existentes = set()

    nuevas = 0
    for _, row in filas.iterrows():
        if str(row["Id"]).strip() in existentes:
            continue
        ws.append([_v(row.get(c)) for c in cols])
        nuevas += 1

    _estilo_encabezado(ws, len(cols))
    anchos = {"Id": 12, "Indicador": 50, "Proceso": 36, "Clasificacion": 14, "Estado": 11, "Origen": 38,
              COL_ANTERIOR: 26, "PDI": 7, "Linea": 34, "Objetivo": 70, "Meta": 80, "Observaciones": 40}
    for i, c in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = anchos[c]

    aplicar_validaciones(ws, cols, marco, listas)
    i_ent = cols.index(COLS_ENTRADA[0]) + 1
    for r in range(2, ws.max_row + 1):
        for c in range(i_ent, i_ent + len(COLS_ENTRADA)):
            ws.cell(row=r, column=c).fill = ENTRADA_FILL
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"
    return len(existentes), nuevas


def main() -> None:
    if not CATALOGO_FILE.exists():
        raise SystemExit(f"No existe {CATALOGO_FILE}")
    vigente = marco_activo("PDI")
    cerrado = get_marco("PDI-2022-2026")
    wb = openpyxl.load_workbook(CATALOGO_FILE)
    quitados = retirar_obsoletos(wb, cerrado, vigente)
    if quitados:
        print("Retirado de diseños anteriores:", "; ".join(quitados))
    df_cat = pd.read_excel(CATALOGO_FILE, sheet_name=HOJA_CATALOGO)
    df_cat = df_cat[[c for c in df_cat.columns if not str(c).startswith(PREFIJOS_COLUMNAS_OBSOLETAS)]]

    escribir_taxonomia(wb)
    for marco in (cerrado, vigente):
        listas = escribir_listas(wb, marco)
        if marco.version_id == cerrado.version_id:
            if hoja_pdi(marco) in wb.sheetnames:
                aplicar_validaciones(wb[hoja_pdi(marco)], columnas(marco), marco, listas)
                print(f"{hoja_pdi(marco)}: ya existe, congelada (solo se actualizan las listas desplegables)")
                continue
            filas = migrar_pdi_cerrado(df_cat, marco)
        else:
            filas = candidatos_vigente(df_cat, estados_proyectos_ciclo_anterior())
        existentes, nuevas = escribir_hoja_pdi(wb, marco, filas, listas)
        print(f"{hoja_pdi(marco)}: {existentes} filas previas conservadas, {nuevas} agregadas")

    try:
        wb.save(CATALOGO_FILE)
    except PermissionError:
        raise SystemExit(f"No se pudo guardar: cierra {CATALOGO_FILE.name} en Excel y reintenta.") from None
    print(f"OK {CATALOGO_FILE.name}")


if __name__ == "__main__":
    main()
