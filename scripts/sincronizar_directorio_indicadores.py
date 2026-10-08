"""Detecta indicadores NUEVOS en las fuentes Kawak/API que aún no están en el directorio
maestro (data/raw/Catalogo de Indicadores.xlsx), los agrega y SOLICITA su asignación
estratégica en cada PDI activo (marcador PDI 1/0, línea, objetivo y meta).

Qué actualiza (todos los catálogos activos):
  1. "Catalogo Indicadores"  → una fila por Id nuevo, con lo inferible de Kawak/API
                               (nombre, proceso, clasificación, periodicidad, sentido).
  2. Hoja de cada PDI activo (PDI_2026_2030, …) → una fila por cada indicador activo que
                               falte en ella, con las listas desplegables en cascada.
  3. Listas_PDI_* / Taxonomia_Marco → se regeneran desde la taxonomía oficial.
  Los PDI cerrados (PDI_2022_2026) NO se tocan: son una foto histórica.

Qué se considera "nuevo": Id presente en el año más reciente del catálogo Kawak o en el
consolidado API y ausente de "Catalogo Indicadores". Los Ids que solo aparecen en años
anteriores de Kawak son históricos: se informan pero no se agregan.

Asignación estratégica:
  - Con terminal interactiva el script PREGUNTA, por cada indicador pendiente de cada PDI
    activo: ¿es estratégico del PDI? (1/0) → línea → objetivo → meta (solo si es 1). Los
    menús salen de la taxonomía del PDI, así que solo se pueden elegir valores oficiales.
    Enter omite el indicador (queda pendiente); `q` deja de preguntar.
  - Sin terminal (pipeline/CI) no pregunta: deja las filas pendientes y emite un
    "[AVISO]" para que Planeación las complete en el Excel o corriendo este script a mano.
  Regla de meta: estratégico (1) EXIGE meta; de proceso (0) no puede tenerla.

Orden en el pipeline: DESPUÉS de consolidar_api (regenera las fuentes) y ANTES de
actualizar_directorio_maestro (que completa periodicidad/sentido de las filas nuevas).

Uso:
    backend/.venv312/Scripts/python.exe scripts/sincronizar_directorio_indicadores.py
    ... --dry-run          (solo informa, no escribe)
    ... --no-interactivo   (no pregunta aunque haya terminal)
    ... --catalogo RUTA    (probar sobre una copia)
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
sys.path.insert(0, str(BASE_DIR / "backend"))
os.environ.setdefault("SGIND_DATA_PATH", str(BASE_DIR / "data"))  # el default "../data" depende del cwd

import agregar_hojas_marco_catalogo as hojas  # noqa: E402
from app.domain.marcos import Marco, get_marcos  # noqa: E402
from app.domain.taxonomia import Taxonomia, load_taxonomia, parse_flag01, regla_meta  # noqa: E402
from etl.config import CATALOGO_MAESTRO_FILE, CONSOLIDADO_API_KW, KAWAK_CAT_FILE  # noqa: E402
from etl.normalizacion import id_str, limpiar_clasificacion, limpiar_html  # noqa: E402

HOJA_CATALOGO = "Catalogo Indicadores"
FUENTE_NUEVO = "Nuevo Kawak/API (pendiente clasificar)"
ORIGEN_NUEVO = "Indicador nuevo (Kawak/API)"
ESTADO_ACTIVO = "Activo"
BACKUPS_DIR = BASE_DIR / "data" / "raw" / "_backups_fusion"


# ── Lectura de fuentes y detección ───────────────────────────────────────────

def _texto(valor: object) -> str:
    return "" if valor is None or (isinstance(valor, float) and pd.isna(valor)) else str(valor).strip()


def leer_kawak(path: Path = KAWAK_CAT_FILE) -> tuple[dict[str, dict], set[str]]:
    """(metadatos de los Ids del año más reciente, Ids que solo están en años anteriores)."""
    if not path.exists():
        return {}, set()
    df = pd.read_excel(path)
    df.columns = [str(c).strip() for c in df.columns]
    col_anio = next((c for c in df.columns if c.lower() in ("año", "ano", "anio")), df.columns[0])
    df["_id"] = df["Id"].map(lambda v: id_str(v) if pd.notna(v) else "")
    df = df[df["_id"] != ""]
    df["_anio"] = pd.to_numeric(df[col_anio], errors="coerce")
    ultimo = df["_anio"].max()
    vigentes = df[df["_anio"] == ultimo].drop_duplicates("_id", keep="last")
    meta = {
        r["_id"]: {
            "Indicador": limpiar_html(_texto(r.get("Indicador"))),
            "Clasificacion": limpiar_clasificacion(_texto(r.get("Clasificacion"))),
            "Proceso": limpiar_html(_texto(r.get("Proceso"))),
            "Periodicidad": _texto(r.get("Periodicidad")),
            "Sentido": _texto(r.get("Sentido")),
            "Tipo_API": _texto(r.get("Tipo")),
            "Estado": ESTADO_ACTIVO,
        }
        for _, r in vigentes.iterrows()
    }
    historicos = set(df["_id"]) - set(meta)
    return meta, historicos


def leer_api(path: Path = CONSOLIDADO_API_KW) -> dict[str, dict]:
    """Metadatos de la última fila de cada Id del consolidado API."""
    if not path.exists():
        return {}
    df = pd.read_excel(path)
    col_id = next((c for c in df.columns if str(c).upper() == "ID"), None)
    if col_id is None:
        return {}
    df["_id"] = df[col_id].map(lambda v: id_str(v) if pd.notna(v) else "")
    df = df[df["_id"] != ""]
    if "fecha" in df.columns:
        df = df.sort_values("fecha")
    ultimo = df.groupby("_id").last()
    return {
        ids: {
            "Indicador": limpiar_html(_texto(r.get("nombre"))),
            "Clasificacion": limpiar_clasificacion(_texto(r.get("clasificacion"))),
            "Proceso": limpiar_html(_texto(r.get("proceso"))),
            "Periodicidad": _texto(r.get("frecuencia")),
            "Sentido": _texto(r.get("sentido")),
            "Tipo_API": _texto(r.get("Tipo")),
            "Estado": _texto(r.get("estado")) or ESTADO_ACTIVO,
        }
        for ids, r in ultimo.iterrows()
    }


def detectar_nuevos(
    ids_catalogo: set[str], kawak: dict[str, dict], api: dict[str, dict]
) -> dict[str, dict]:
    """Ids de las fuentes vigentes que el catálogo no tiene. La API gana sobre Kawak en
    estado/tipo, pero Kawak gana en nombre y periodicidad (fuente de la ficha)."""
    nuevos: dict[str, dict] = {}
    for ids in sorted((set(kawak) | set(api)) - ids_catalogo, key=_orden_id):
        base = {**api.get(ids, {}), **{k: v for k, v in kawak.get(ids, {}).items() if v}}
        base["Estado"] = api.get(ids, {}).get("Estado") or ESTADO_ACTIVO
        nuevos[ids] = base
    return nuevos


def _orden_id(ids: str) -> tuple[int, float, str]:
    try:
        return (0, float(ids), ids)
    except ValueError:
        return (1, 0.0, ids)


# ── Catálogo maestro ─────────────────────────────────────────────────────────

def agregar_al_catalogo(wb, nuevos: dict[str, dict]) -> None:
    ws = wb[HOJA_CATALOGO]
    header = {cell.value: cell.column for cell in ws[1] if cell.value}
    for ids, datos in nuevos.items():
        fila: list[object] = [None] * ws.max_column
        for col, val in {"Id": ids, **{k: v for k, v in datos.items() if k in header}, "Fuente": FUENTE_NUEVO}.items():
            if col in header:
                fila[header[col] - 1] = val or None
        ws.append(fila)


def activos_del_catalogo(wb, vigentes: set[str] = frozenset()) -> dict[str, dict]:
    """Id → datos de contexto de los indicadores activos del catálogo (ya con los nuevos).

    Activo = Estado «Activo» O presente en el año vigente de Kawak / en la API: el Estado del
    catálogo puede estar vacío en indicadores que sí se reportan, y no por eso deben quedar
    fuera del PDI. A esos se les completa el Estado con «Activo»."""
    ws = wb[HOJA_CATALOGO]
    enc = [c.value for c in ws[1]]
    ix = {c: enc.index(c) for c in ("Id", "Indicador", "Proceso", "Clasificacion", "Estado", "Linea_Estrategica") if c in enc}
    out: dict[str, dict] = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[ix["Id"]] is None:
            continue
        ids = id_str(row[ix["Id"]])
        if _texto(row[ix["Estado"]]).lower() != ESTADO_ACTIVO.lower() and ids not in vigentes:
            continue
        out[ids] = {c: row[i] for c, i in ix.items()}
    return out


CAMPOS_FUENTE = ("Indicador", "Clasificacion", "Proceso", "Periodicidad", "Sentido", "Tipo_API")


def completar_datos(wb, fuente: dict[str, dict]) -> int:
    """Llena SOLO las celdas vacías de «Catalogo Indicadores» con lo que dicen Kawak/API
    (nombre, clasificación, proceso, periodicidad, sentido, tipo). Nunca pisa un valor."""
    ws = wb[HOJA_CATALOGO]
    enc = [c.value for c in ws[1]]
    i_id = enc.index("Id")
    cols = {c: enc.index(c) for c in CAMPOS_FUENTE if c in enc}
    n = 0
    for row in ws.iter_rows(min_row=2):
        if row[i_id].value is None:
            continue
        datos = fuente.get(id_str(row[i_id].value))
        if not datos:
            continue
        for campo, i in cols.items():
            if not _texto(row[i].value) and datos.get(campo):
                row[i].value = datos[campo]
                n += 1
    return n


def completar_contexto_hoja(wb, marco: Marco) -> int:
    """Llena las celdas vacías de contexto (Indicador, Proceso, Clasificación, Estado) de la hoja
    del PDI con lo que dice el catálogo. No toca PDI/Línea/Objetivo/Meta."""
    cat = wb[HOJA_CATALOGO]
    enc = [c.value for c in cat[1]]
    ix = {c: enc.index(c) for c in ("Id", "Indicador", "Proceso", "Clasificacion", "Estado")}
    por_id = {id_str(r[ix["Id"]]): r for r in cat.iter_rows(min_row=2, values_only=True) if r[ix["Id"]] is not None}
    ws = wb[hojas.hoja_pdi(marco)]
    cols = [c.value for c in ws[1]]
    n = 0
    for row in ws.iter_rows(min_row=2):
        fuente = por_id.get(id_str(row[0].value)) if row[0].value is not None else None
        if fuente is None:
            continue
        for campo in ("Indicador", "Proceso", "Clasificacion", "Estado"):
            celda = row[cols.index(campo)]
            if not _texto(celda.value) and _texto(fuente[ix[campo]]):
                celda.value = fuente[ix[campo]]
                n += 1
    return n


def completar_estado(wb, vigentes: set[str]) -> int:
    """Estado vacío → «Activo» para los Ids vigentes en Kawak/API. Devuelve cuántos."""
    ws = wb[HOJA_CATALOGO]
    enc = [c.value for c in ws[1]]
    i_id, i_est = enc.index("Id"), enc.index("Estado")
    n = 0
    for row in ws.iter_rows(min_row=2):
        if row[i_id].value is not None and not _texto(row[i_est].value) and id_str(row[i_id].value) in vigentes:
            row[i_est].value = ESTADO_ACTIVO
            n += 1
    return n


# ── Hoja de cada PDI activo ──────────────────────────────────────────────────

def pdi_activos() -> list[Marco]:
    return [m for m in get_marcos("PDI") if m.estado == "activo" and m.taxonomia]


def faltantes_en_hoja(wb, marco: Marco, activos: dict[str, dict]) -> dict[str, dict]:
    """Indicadores activos del catálogo que la hoja del PDI aún no tiene."""
    nombre = hojas.hoja_pdi(marco)
    if nombre not in wb.sheetnames:
        return activos  # la hoja se crea con todos (normalmente ya existe)
    ws = wb[nombre]
    presentes = {id_str(r[0].value) for r in ws.iter_rows(min_row=2) if r[0].value is not None}
    return {i: d for i, d in activos.items() if i not in presentes}


def pendientes_de_asignar(wb, marco: Marco) -> list[int]:
    """Filas (de la hoja del PDI) de indicadores nuevos que siguen sin línea asignada (el
    marcador PDI arranca en 0 = de proceso; solo cambia si Planeación lo marca como 1)."""
    ws = wb[hojas.hoja_pdi(marco)]
    cols = [c.value for c in ws[1]]
    i_lin, i_origen = cols.index("Linea"), cols.index("Origen")
    return [
        r[0].row
        for r in ws.iter_rows(min_row=2)
        if r[0].value is not None and r[i_origen].value == ORIGEN_NUEVO and r[i_lin].value in (None, "")
    ]


def escribir_filas_nuevas(wb, marco: Marco, faltantes: dict[str, dict], nuevos: frozenset[str] = frozenset()) -> int:
    """Agrega a la hoja del PDI los indicadores que faltan (sin tocar lo ya diligenciado) y
    regenera las listas desplegables. Devuelve cuántas filas agregó."""
    filas = pd.DataFrame([
        {
            "Id": ids, "Indicador": d.get("Indicador"), "Proceso": d.get("Proceso"),
            "Clasificacion": d.get("Clasificacion"), "Estado": d.get("Estado") or ESTADO_ACTIVO,
            "Origen": ORIGEN_NUEVO if ids in nuevos else hojas.ORIGEN_ACTIVO, hojas.COL_ANTERIOR: d.get("Linea_Estrategica"),
            "PDI": 0, "Linea": None, "Objetivo": None, "Meta": None, "Observaciones": None,
        }
        for ids, d in faltantes.items()
    ], columns=hojas.columnas(marco))
    listas = hojas.escribir_listas(wb, marco)
    _, nuevas = hojas.escribir_hoja_pdi(wb, marco, filas, listas)
    return nuevas


# ── Solicitud de la asignación estratégica ───────────────────────────────────

class Salir(Exception):
    """El usuario escribió `q`: se deja de preguntar."""


def elegir(titulo: str, opciones: list[str]) -> str | None:
    """Menú numerado. Enter = omitir (None); `q` = dejar de preguntar."""
    print(f"\n  {titulo}")
    for n, op in enumerate(opciones, 1):
        print(f"    {n:>2}. {op}")
    while True:
        r = input("  Número (Enter = omitir, q = terminar): ").strip().lower()
        if r == "":
            return None
        if r == "q":
            raise Salir
        if r.isdigit() and 1 <= int(r) <= len(opciones):
            return opciones[int(r) - 1]
        print("  Opción no válida.")


def preguntar_asignacion(tax: Taxonomia, ids: str, indicador: str, proceso: str) -> dict | None:
    """Pide marcador, línea, objetivo y meta de UN indicador. None = lo omitió."""
    print(f"\n── {ids} · {indicador}  [{proceso}] " + "─" * 10)
    marcador = elegir("¿Es indicador ESTRATÉGICO del PDI?", ["1 = Sí (estratégico del PDI, exige meta)", "0 = No (de proceso)"])
    if marcador is None:
        return None
    pdi = int(marcador[0])
    linea = elegir("Línea estratégica", [ln.nombre for ln in tax.lineas])
    if linea is None:
        return {"PDI": pdi}
    ln = next(x for x in tax.lineas if x.nombre == linea)
    objetivo = elegir(f"Objetivo de «{linea}»", [o.nombre for o in ln.objetivos])
    meta = None
    if objetivo is not None and pdi == 1:
        ob = next(o for o in ln.objetivos if o.nombre == objetivo)
        meta = elegir(f"Meta estratégica de «{objetivo[:60]}»", [m.nombre for m in ob.metas])
    return {"PDI": pdi, "Linea": linea, "Objetivo": objetivo, "Meta": meta}


def aplicar_asignacion(ws, fila: int, valores: dict) -> None:
    cols = [c.value for c in ws[1]]
    for col, val in valores.items():
        ws.cell(row=fila, column=cols.index(col) + 1, value=val)


def incumple_regla(ws, fila: int, version_id: str) -> str | None:
    cols = [c.value for c in ws[1]]
    pdi = parse_flag01(ws.cell(row=fila, column=cols.index("PDI") + 1).value)
    meta = _texto(ws.cell(row=fila, column=cols.index("Meta") + 1).value)
    if pdi is None and not meta:
        return None  # sin asignar todavía: ya se informa como pendiente
    return regla_meta(pdi, bool(meta), version_id)


def hay_terminal() -> bool:
    """Solo se pregunta con terminal real (en el pipeline la salida va capturada)."""
    return sys.stdin.isatty() and sys.stdout.isatty()


# ── Principal ────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="solo informa; no escribe nada")
    ap.add_argument("--no-interactivo", action="store_true", help="no pregunta aunque haya terminal")
    ap.add_argument("--catalogo", type=Path, default=CATALOGO_MAESTRO_FILE, help="catálogo a actualizar (p. ej. una copia)")
    args = ap.parse_args(argv)
    catalogo: Path = args.catalogo

    if not catalogo.exists():
        print(f"[ERROR] No existe {catalogo}")
        return 2
    interactivo = not args.no_interactivo and hay_terminal()

    kawak, historicos = leer_kawak()
    api = leer_api()
    wb = openpyxl.load_workbook(catalogo)
    ids_catalogo = {id_str(r[0]) for r in wb[HOJA_CATALOGO].iter_rows(min_row=2, values_only=True) if r[0] is not None}
    nuevos = detectar_nuevos(ids_catalogo, kawak, api)
    print(
        f"[sincronizar_directorio] Fuentes vigentes (Kawak+API): {len(set(kawak) | set(api))} Ids | "
        f"catálogo: {len(ids_catalogo)} | nuevos: {len(nuevos)} | históricos sin catalogar (no se agregan): "
        f"{len(historicos - ids_catalogo - set(api))}"
    )
    if nuevos:
        print("  Nuevos:", ", ".join(f"{i} ({d.get('Indicador', '')[:40]})" for i, d in nuevos.items()))

    agregar_al_catalogo(wb, nuevos)
    vigentes = set(kawak) | set(api)
    activos = activos_del_catalogo(wb, vigentes)

    plan: list[tuple[Marco, dict[str, dict]]] = []
    for marco in pdi_activos():
        faltan = faltantes_en_hoja(wb, marco, activos)
        plan.append((marco, faltan))
        print(f"  {hojas.hoja_pdi(marco)} ({marco.nombre}): {len(faltan)} indicadores activos por agregar")

    if args.dry_run:
        print("[sincronizar_directorio] --dry-run: no se escribió nada.")
        return 0

    n_datos = completar_datos(wb, {**api, **kawak})
    if n_datos:
        print(f"  Catalogo Indicadores: {n_datos} celdas vacias completadas desde Kawak/API")
    n_estado = completar_estado(wb, vigentes)
    if n_estado:
        print(f"  Estado vacio a Activo en {n_estado} indicadores vigentes en Kawak/API")
    hojas.escribir_taxonomia(wb)
    pendientes_total: list[dict] = []
    incumplimientos: list[str] = []
    detenido = False
    for marco, faltan in plan:
        agregadas = escribir_filas_nuevas(wb, marco, faltan, frozenset(nuevos))
        n_ctx = completar_contexto_hoja(wb, marco)
        if n_ctx:
            print(f"  {hojas.hoja_pdi(marco)}: {n_ctx} celdas de contexto completadas desde el catalogo")
        ws = wb[hojas.hoja_pdi(marco)]
        tax = load_taxonomia(marco.taxonomia)
        filas = pendientes_de_asignar(wb, marco)
        cols = [c.value for c in ws[1]]
        print(f"  {hojas.hoja_pdi(marco)}: {agregadas} agregadas, {len(filas)} pendientes de asignar")
        if interactivo and filas and not detenido:
            print(f"\n=== Asignación estratégica · {marco.nombre} ({len(filas)} indicadores) ===")
            for fila in filas:
                ids = id_str(ws.cell(row=fila, column=1).value)
                try:
                    valores = preguntar_asignacion(
                        tax, ids, _texto(ws.cell(row=fila, column=2).value), _texto(ws.cell(row=fila, column=3).value)
                    )
                except Salir:
                    detenido = True
                    break
                if valores:
                    aplicar_asignacion(ws, fila, valores)
        for fila in pendientes_de_asignar(wb, marco):
            pendientes_total.append({
                "PDI": marco.version_id, "Id": id_str(ws.cell(row=fila, column=1).value),
                "Indicador": _texto(ws.cell(row=fila, column=2).value),
                "Proceso": _texto(ws.cell(row=fila, column=3).value),
            })
        for r in range(2, ws.max_row + 1):
            if ws.cell(row=r, column=1).value is None or ws.cell(row=r, column=cols.index("Origen") + 1).value != ORIGEN_NUEVO:
                continue
            motivo = incumple_regla(ws, r, marco.version_id)
            if motivo:
                incumplimientos.append(f"{marco.version_id} · {id_str(ws.cell(row=r, column=1).value)}: {motivo}")

    bak = BACKUPS_DIR / f"{catalogo.stem}.{datetime.now():%Y%m%d_%H%M%S}.pre_sync{catalogo.suffix}"
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(catalogo, bak)
    print(f"  Respaldo: {bak.name}")
    try:
        wb.save(catalogo)
    except PermissionError:
        print(f"[ERROR] No se pudo guardar: cierra {catalogo.name} en Excel y reintenta.")
        return 3

    if pendientes_total:
        ids = ", ".join(p["Id"] for p in pendientes_total[:30])
        print(
            f"[AVISO] {len(pendientes_total)} asignación(es) de línea estratégica pendientes en "
            f"{', '.join(sorted({p['PDI'] for p in pendientes_total}))} (Ids: {ids}"
            f"{'…' if len(pendientes_total) > 30 else ''}). Complétalas en las hojas PDI_* de "
            f"'{catalogo.name}' (filas con Origen «{ORIGEN_NUEVO}»; columnas PDI/Linea/Objetivo/Meta) "
            f"o corre este script en una terminal."
        )
    for texto in incumplimientos:
        print(f"[AVISO] Regla de meta: {texto}")
    if not pendientes_total and not incumplimientos:
        print("[sincronizar_directorio] Catálogos activos al día, sin asignaciones pendientes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
