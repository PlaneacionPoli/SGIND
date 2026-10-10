#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/generar_seguimiento.py
==============================
Genera data/output/Seguimiento_Reporte.xlsx (hoja "Tracking Mensual" + hojas de cierres).

Cierra el hueco G-06: hasta ahora ningún paso del pipeline regeneraba este archivo (el
generador vivía solo en Sistema_Indicadores_Poli/generar_reporte.py, fuera del pipeline).

FUENTES (el LMI ya NO se usa)
─────────────────────────────
  1. data/raw/Kawak/<año>.xlsx          Fuente vigente por año. Define los indicadores activos
                                        de cada año, su periodicidad y, por las columnas
                                        fechadas ("2026-09-30 Periodo 40"), qué periodos ya
                                        traen resultado.
  2. data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx
                                        Resultados históricos de la API (generado por
                                        consolidar_api.py).
  3. data/output/Resultados Consolidados.xlsx  (solo hoja "Consolidado Cierres", para las
                                        hojas de cierres y la matriz de calor)

Un (indicador, mes) es "Reportado" si la API o el archivo anual de Kawak traen resultado para
el periodo de cierre que le corresponde por su periodicidad. Si no: "Pendiente" (o "No aplica"
para los procesos configurados).

Calendario: de FECHA_INICIO al último día del mes anterior a la ejecución (o --fecha-ref).

Uso:
    python scripts/generar_seguimiento.py
    python scripts/generar_seguimiento.py --fecha-ref 2026-09-30 --salida ruta/Seguimiento_Reporte.xlsx
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import openpyxl
import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# stdout en UTF-8 (consola de Windows) sin envolver el buffer: el orquestador captura la salida.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
os.environ.setdefault("SGIND_DATA_PATH", os.path.join(BASE_DIR, "data"))

# Lógica de categorización: fuente única del backend (misma que usa la aplicación).
from app.domain.categorization import categorizar_cumplimiento  # noqa: E402

# ── Rutas ─────────────────────────────────────────────────────────────────────
RUTA_SALIDA = os.path.join(BASE_DIR, "data", "output", "Seguimiento_Reporte.xlsx")
RUTA_KAWAK_API = os.path.join(BASE_DIR, "data", "raw", "Fuentes Consolidadas", "Consolidado_API_Kawak.xlsx")
RUTA_KAWAK_DIR = os.path.join(BASE_DIR, "data", "raw", "Kawak")
RUTA_CONSOLIDADOS = os.path.join(BASE_DIR, "data", "output", "Resultados Consolidados.xlsx")

# ── Reglas de negocio (heredadas del generador original, validadas) ───────────
# ── Configuración dinámica de fechas ──────────────────────────────────────────
# None = automático: último día del mes anterior al mes actual.
# Fijarlo manualmente si se necesita un corte específico.
FECHA_REFERENCIA_MANUAL: Optional[date] = None

# Inicio del calendario histórico para el "Tracking Mensual"
FECHA_INICIO = date(2025, 1, 1)

# Indicadores que reportan en "año vencido":
# Su dato del año N (en Kawak) cuenta como "Reportado" para el año N+1.
# Ej: dato 2024 en Kawak → Reportado en dic-2025 del tracking.
IDS_AÑO_VENCIDO: set = {"226", "227", "228"}

# Indicadores con vigencia parcial: solo aplican desde la fecha indicada.
# Meses anteriores a esa fecha se omiten del tracking (no generan fila).
IDS_VIGENCIA_DESDE: Dict[str, date] = {
    "515": date(2025, 7, 1),
    "516": date(2025, 7, 1),
    "526": date(2025, 7, 1),
    "530": date(2025, 7, 1),
    "531": date(2025, 7, 1),
    "538": date(2025, 7, 1),
    "539": date(2025, 7, 1),
    "554": date(2025, 7, 1),
    "555": date(2025, 7, 1),
}

# Procesos cuyos indicadores muestran "No aplica" cuando no tienen reporte
# (en lugar de "Pendiente").  Comparación case-insensitive, coincidencia parcial.
PROCESOS_NO_APLICA_SIN_REPORTE: List[str] = [
    "Gestión de Unidades Académicas",
]

# ── Paleta de colores ──────────────────────────────────────────────────────────
C_HEADER    = "1F4E79"

C_SI        = "C6EFCE"

C_NO        = "FFCCCC"

C_PENDIENTE = "FFEB9C"

C_REVISAR1  = "DDEEFF"

C_NO_APLICA = "EEEEEE"

# Fondos para niveles de cumplimiento (matriz de calor)
C_NIVEL_BG = {
    "Sobrecumplimiento": "D0E4FF",
    "Cumplimiento":      "E8F5E9",
    "Alerta":            "FEF3D0",
    "Peligro":           "FFCDD2",
    "Sin dato":          "F0F0F0",
}

# Nombres de meses en español para la columna Mes_Nombre
_MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


# ══════════════════════════════════════════════════════════════════════════════
#  FUNCIONES (copiadas del generador original; sin dependencia del LMI)
# ══════════════════════════════════════════════════════════════════════════════

def _calcular_fecha_ref() -> date:
    """Retorna el último día del mes anterior al mes actual."""
    hoy = date.today()
    return hoy.replace(day=1) - timedelta(days=1)


def get_fecha_referencia() -> date:
    """Punto de acceso único para la fecha de referencia."""
    return FECHA_REFERENCIA_MANUAL or _calcular_fecha_ref()


def _ultimo_dia(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _tiene_dato(v) -> bool:
    if v is None:
        return False
    s = str(v).strip()
    return s not in ("", "-", "nan", "NaN", "None")


def _tiene_dato_kawak(v) -> bool:
    try:
        if pd.isna(v):
            return False
    except (TypeError, ValueError):
        pass
    s = str(v).strip()
    return s not in ("", "-", "nan", "NaN", "None")


def _id_normalizar(x) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except (TypeError, ValueError):
        pass
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else str(f)
    except (ValueError, TypeError):
        return str(x).strip()


def _detectar_col(df: pd.DataFrame, candidatos: list) -> Optional[str]:
    """Detección dinámica de columna: busca por nombre exacto, luego case-insensitive."""
    # Búsqueda exacta primero
    for cand in candidatos:
        if cand in df.columns:
            return cand
    # Fallback case-insensitive
    col_lower = {c.lower(): c for c in df.columns}
    for cand in candidatos:
        found = col_lower.get(cand.lower())
        if found:
            return found
    return None


def leer_kawak_api(ruta: str) -> Dict:
    """
    Lee Consolidado_API_Kawak.xlsx y retorna {(id_str, year, month): resultado}.

    Estructura esperada (generada por consolidar_api.py PARTE 2):
      Columnas: ID | fecha | resultado | ... (minúsculas, origen API)
    Si el mismo (id, year, month) aparece varias veces conserva el último
    registro no vacío (el archivo ya está ordenado por ID + fecha).
    """
    if not os.path.exists(ruta):
        print(f"    INFO: {ruta} no encontrado — se omite lookup Kawak.")
        return {}

    try:
        df = pd.read_excel(ruta, engine="openpyxl",
                           keep_default_na=False, na_values=[""])
    except Exception as exc:
        print(f"    ADVERTENCIA Kawak API: no se pudo leer: {exc}")
        return {}

    df.columns = [str(c).strip() for c in df.columns]

    # Columnas del Consolidado_API_Kawak: "ID" (mayús.), "fecha", "resultado"
    col_id  = _detectar_col(df, ["ID", "Id", "id", "Codigo", "Código"])
    col_fec = _detectar_col(df, ["fecha", "Fecha", "FechaPeriodo", "Periodo", "Mes"])
    col_res = _detectar_col(df, ["resultado", "Resultado", "Valor", "valor", "Result"])

    if not col_id or not col_fec or not col_res:
        print(f"    ADVERTENCIA Kawak API: columnas no encontradas.\n"
              f"    Disponibles: {df.columns.tolist()}")
        return {}

    lookup: Dict = {}
    omitidas = 0
    for _, row in df.iterrows():
        kid = _id_normalizar(row[col_id])
        if not kid:
            continue

        fecha_raw = row[col_fec]
        resultado = row[col_res]

        try:
            if isinstance(fecha_raw, (pd.Timestamp, date)):
                ts = pd.Timestamp(fecha_raw)
            elif isinstance(fecha_raw, (int, float)) and not pd.isna(fecha_raw):
                ts = pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(fecha_raw))
            else:
                ts = pd.Timestamp(str(fecha_raw).strip())

            if pd.isna(resultado):
                continue
            # El archivo está ordenado por fecha → el último registro gana
            lookup[(kid, ts.year, ts.month)] = resultado
        except Exception:
            omitidas += 1

    if omitidas:
        print(f"    INFO Kawak API: {omitidas} filas con fecha no parseable omitidas.")

    print(f"    Kawak API cargado: {len(lookup)} registros (Id × período).")
    return lookup


def leer_catalogo_por_anio(kawak_dir: str, year: int) -> Tuple[Dict[str, str], Dict[str, dict]]:
    """
    Lee data/raw/Kawak/{year}.xlsx — fuente autoritativa de IDs activos para ese año.
    Retorna:
      catalogo : {id_str: periodicidad}
      meta     : {id_str: {col: valor, ...}}  (metadata descriptiva sin Id/Periodicidad)

    Si el archivo no existe, retorna ({}, {}) sin error fatal.
    """
    ruta = os.path.join(kawak_dir, f"{year}.xlsx")
    if not os.path.exists(ruta):
        print(f"    INFO: {ruta} no encontrado — año {year} omitido del tracking.")
        return {}, {}

    try:
        df = pd.read_excel(ruta, engine="openpyxl", keep_default_na=False, na_values=[""])
    except Exception as exc:
        print(f"    ADVERTENCIA catálogo {year}: {exc}")
        return {}, {}

    df.columns = [str(c).strip() for c in df.columns]
    col_id  = _detectar_col(df, ["Id", "ID", "id"])
    col_per = _detectar_col(df, ["Periodicidad", "periodicidad", "frecuencia"])

    if not col_id or not col_per:
        print(f"    ADVERTENCIA: columnas Id/Periodicidad no encontradas en {ruta}\n"
              f"    Disponibles: {df.columns.tolist()}")
        return {}, {}

    # Columnas de metadata (todo excepto Id y Periodicidad)
    excluir_meta = {col_id, col_per}
    meta_cols = [c for c in df.columns if c not in excluir_meta]

    catalogo: Dict[str, str] = {}
    meta: Dict[str, dict] = {}

    for _, row in df.iterrows():
        kid = _id_normalizar(row[col_id])
        if not kid:
            continue
        perio = str(row.get(col_per, "")).strip()
        if perio and perio not in ("nan", "NaN", "None", ""):
            catalogo[kid] = perio
            if kid not in meta:
                meta[kid] = {c: row.get(c) for c in meta_cols}

    print(f"    Kawak {year}: {len(catalogo)} indicadores activos.")
    return catalogo, meta


def _mes_cierre_periodo(month: int, periodicidad: str) -> int:
    """
    Dado un mes calendario cualquiera, retorna el mes de CIERRE del período
    al que pertenece según la periodicidad del indicador.

    Ejemplos:
      Trimestral: Feb (2) → 3  |  May (5) → 6  |  Oct (10) → 12
      Bimestral:  Mar (3) → 4  |  Nov (11) → 12
      Semestral:  Abr (4) → 6  |  Sep (9)  → 12
      Anual:      cualquier mes → 12
      Mensual:    mes → mismo mes
    """
    perio = str(periodicidad).strip()
    if perio == "Mensual":
        return month
    if perio == "Bimestral":
        return month if month % 2 == 0 else month + 1
    if perio == "Trimestral":
        if month <= 3:  return 3
        if month <= 6:  return 6
        if month <= 9:  return 9
        return 12
    if perio == "Semestral":
        return 6 if month <= 6 else 12
    if perio == "Anual":
        return 12
    return month  # periodicidad desconocida → sin normalizar


def normalizar_kawak_lookup(kawak_raw: Dict,
                             catalogo: Dict[str, str]) -> Dict:
    """
    Re-mapea las claves del lookup Kawak al mes de CIERRE del período
    correspondiente según la periodicidad de cada indicador.

    Problema que resuelve:
      La API Kawak almacena el dato con la fecha real del reporte
      (ej: 2025-02-10 para un Trimestral de Q1).
      El tracking busca por el mes de cierre del período (2025-03 para Q1).
      Sin normalizar, la búsqueda falla y el indicador aparece como Pendiente.

    Regla de precedencia:
      Si dos fechas distintas del mismo indicador cierran al mismo período,
      se conserva el último valor encontrado (el más reciente en el archivo).
    """
    normalizado: Dict = {}
    for (kid, year, month), valor in kawak_raw.items():
        perio = catalogo.get(kid, "Mensual")
        mes_norm = _mes_cierre_periodo(month, perio)
        normalizado[(kid, year, mes_norm)] = valor  # último gana
    return normalizado


def aplica_periodicidad(periodicidad: str, mes: int) -> bool:
    """
    Determina si un mes calendario aplica según la periodicidad del indicador.
      Mensual    → todos los meses
      Bimestral  → meses pares (2, 4, 6, 8, 10, 12)
      Trimestral → 3, 6, 9, 12
      Semestral  → 6, 12
      Anual      → 12
    Periodicidad desconocida → False (conservador: no marcar como Pendiente).
    """
    perio = str(periodicidad).strip()
    if perio == "Mensual":
        return True
    if perio == "Bimestral":
        return mes % 2 == 0
    if perio == "Trimestral":
        return mes in (3, 6, 9, 12)
    if perio == "Semestral":
        return mes in (6, 12)
    if perio == "Anual":
        return mes == 12
    return False


def generar_calendario(fecha_inicio: date, fecha_fin: date) -> List[Tuple[int, int]]:
    """Genera lista ordenada de (año, mes) desde fecha_inicio hasta fecha_fin inclusive."""
    calendario: List[Tuple[int, int]] = []
    y, m = fecha_inicio.year, fecha_inicio.month
    fin_y, fin_m = fecha_fin.year, fecha_fin.month
    while (y < fin_y) or (y == fin_y and m <= fin_m):
        calendario.append((y, m))
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return calendario


def _proceso_es_no_aplica(proceso: str) -> bool:
    """Retorna True si el proceso del indicador usa 'No aplica' en lugar de 'Pendiente'."""
    proceso_norm = str(proceso or "").strip().lower()
    for p in PROCESOS_NO_APLICA_SIN_REPORTE:
        if p.lower() in proceso_norm:
            return True
    return False


def _parsear_vigencia_desde(v) -> Optional[date]:
    """Parsea la columna 'Vigencia Desde' de Kawak a date, o None si vacía/no parseable."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    s = str(v).strip()
    if s in ("", "-", "nan", "NaN", "None"):
        return None
    try:
        return pd.Timestamp(v).date()
    except (ValueError, TypeError):
        return None


def construir_tracking_largo(
    catalogo_por_anio: Dict[int, Dict[str, str]],
    kawak_lookup: Dict,
    kawak_anual_lookup: Dict,
    calendario: List[Tuple[int, int]],
    meta_por_anio: Optional[Dict[int, Dict[str, dict]]] = None,
) -> pd.DataFrame:
    """
    Genera DataFrame en FORMATO LARGO (long) filtrable mes a mes.
    Una fila por (Id × período que APLICA según periodicidad).

    El catálogo de IDs activos es AÑO-ESPECÍFICO:
      catalogo_por_anio[2025] = IDs activos en 2025 (data/raw/Kawak/2025.xlsx)
      catalogo_por_anio[2026] = IDs activos en 2026 (data/raw/Kawak/2026.xlsx)
    Esto permite que indicadores se activen o inactiven entre años.

    Columnas: Id | <meta Kawak> | Periodicidad | Año | Mes | Mes_Nombre | Periodo | Estado | Fuente

    Reglas de negocio:
      1. IDS_AÑO_VENCIDO    → busca también en año anterior de Kawak.
      2. IDS_VIGENCIA_DESDE → omite meses anteriores a la fecha de inicio.
      3. PROCESOS_NO_APLICA → sin dato = "No aplica" en vez de "Pendiente".
    """
    if not catalogo_por_anio:
        return pd.DataFrame()

    meta_por_anio = meta_por_anio or {}

    def _sort_key(kid: str) -> tuple:
        try:
            return (0, int(kid), kid)
        except (ValueError, TypeError):
            return (1, 0, kid)

    # Orden de columnas de metadata (unión de todos los años)
    prioridad = ["Indicador", "Nombre", "Proceso", "Subproceso", "Linea",
                 "Clasificacion", "Tipo", "Sentido", "Área", "Area"]
    todas_meta_cols: set = set()
    for meta_year in meta_por_anio.values():
        for m in meta_year.values():
            todas_meta_cols.update(m.keys())
    meta_cols_order = [c for c in prioridad if c in todas_meta_cols]
    meta_cols_order += [c for c in sorted(todas_meta_cols) if c not in meta_cols_order]

    rows = []
    for (year, month) in calendario:
        catalogo_year = catalogo_por_anio.get(year, {})
        meta_year     = meta_por_anio.get(year, {})

        for kid in sorted(catalogo_year.keys(), key=_sort_key):
            perio   = catalogo_year[kid]
            meta    = meta_year.get(kid, {})
            proceso = str(meta.get("Proceso", "") or "").strip()

            # ── Regla base: mes debe aplicar según periodicidad ──────────
            if not aplica_periodicidad(perio, month):
                continue

            # ── Regla 2: vigencia parcial ────────────────────────────────
            # Fuente primaria: columna "Vigencia Desde" que trae Kawak por
            # indicador (data/raw/Kawak/<año>.xlsx) — ya presente en meta.
            # IDS_VIGENCIA_DESDE queda como respaldo manual solo para IDs
            # donde Kawak no trae la fecha (columna vacía).
            vigencia_desde = _parsear_vigencia_desde(meta.get("Vigencia Desde"))
            if vigencia_desde is None:
                vigencia_desde = IDS_VIGENCIA_DESDE.get(kid)
            if vigencia_desde and date(year, month, 1) < vigencia_desde:
                continue

            # ── Regla 1: año vencido ─────────────────────────────────────
            if kid in IDS_AÑO_VENCIDO:
                en_kawak = (
                    (kid, year,     month) in kawak_lookup or
                    (kid, year - 1, month) in kawak_lookup
                )
            else:
                en_kawak = (kid, year, month) in kawak_lookup

            en_anual = (kid, year, month) in kawak_anual_lookup

            # ── Estado y fuente ──────────────────────────────────────────
            if en_kawak:
                estado, fuente = "Reportado", "Kawak"
            elif en_anual:
                estado, fuente = "Reportado", "Kawak anual"
            else:
                estado = "No aplica" if _proceso_es_no_aplica(proceso) else "Pendiente"
                fuente = "—"

            row_data: Dict = {"Id": kid}
            for col in meta_cols_order:
                row_data[col] = meta.get(col)
            row_data["Periodicidad"] = perio
            row_data["Año"]          = year
            row_data["Mes"]          = month
            row_data["Mes_Nombre"]   = _MESES_ES.get(month, str(month))
            row_data["Periodo"]      = f"{month}/{year}"
            row_data["Estado"]       = estado
            row_data["Fuente"]       = fuente
            rows.append(row_data)

    return pd.DataFrame(rows)


def _estilo_header(cell):
    cell.font = Font(bold=True, color="FFFFFF", size=10)
    cell.fill = PatternFill("solid", fgColor=C_HEADER)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    borde = Side(style="thin", color="FFFFFF")
    cell.border = Border(left=borde, right=borde, bottom=borde)


def escribir_tracking_mensual(ws, df: pd.DataFrame):
    """
    Escribe la hoja "Tracking Mensual" en FORMATO LARGO con código de colores:
      Verde    → Reportado
      Amarillo → Pendiente
    Todas las columnas tienen filtro automático.
    Congela hasta la columna "Periodicidad" inclusive.
    """
    if df.empty:
        ws.cell(row=1, column=1, value="Sin datos — verifica las fuentes.")
        return

    fill_reportado = PatternFill("solid", fgColor=C_SI)
    fill_pendiente = PatternFill("solid", fgColor=C_PENDIENTE)

    # Anchos sugeridos por tipo de columna
    ANCHOS = {
        "Id": 8, "Periodicidad": 14, "Año": 7, "Mes": 6,
        "Mes_Nombre": 13, "Periodo": 10, "Estado": 13, "Fuente": 10,
    }

    # Encabezados
    for ci, col in enumerate(df.columns, 1):
        cell = ws.cell(row=1, column=ci, value=col)
        _estilo_header(cell)
        ws.column_dimensions[get_column_letter(ci)].width = ANCHOS.get(
            col, min(max(len(str(col)) + 4, 14), 40)
        )

    # Identificar índice de columna "Periodicidad" para congelar hasta ahí
    cols_list = list(df.columns)
    try:
        col_freeze = cols_list.index("Periodicidad") + 2  # columna siguiente a Periodicidad
    except ValueError:
        col_freeze = 2
    ws.freeze_panes = f"{get_column_letter(col_freeze)}2"

    # Datos
    for ri, row in enumerate(df.itertuples(index=False), 2):
        estado_val = None
        for ci, val in enumerate(row, 1):
            col_name = cols_list[ci - 1]
            cell = ws.cell(row=ri, column=ci, value=val)
            cell.alignment = Alignment(horizontal="center", vertical="center")

            if col_name == "Estado":
                estado_val = val

        # Colorear fila completa según Estado
        if estado_val in ("Reportado", "Pendiente"):
            fill = fill_reportado if estado_val == "Reportado" else fill_pendiente
            col_estado = cols_list.index("Estado") + 1
            ws.cell(row=ri, column=col_estado).fill = fill

    ws.auto_filter.ref = f"A1:{get_column_letter(len(df.columns))}1"


def _nivel_cumplimiento(c, id_indicador=None) -> str:
    """Clasifica un valor de cumplimiento decimal en nivel de semáforo.
    
    Usa core.semantica para consistencia con el resto del sistema.
    """
    categoria = categorizar_cumplimiento(c, id_indicador=id_indicador)
    return categoria


def leer_consolidado_cierres(ruta: str, ids_activos: set) -> pd.DataFrame:
    """
    Lee la hoja 'Consolidado Cierres' de Resultados Consolidados.xlsx.
    Filtra a los IDs activos indicados, normaliza columnas clave y agrega
    la columna 'Nivel' calculada desde 'Cumplimiento'.
    """
    if not os.path.exists(ruta):
        print(f"    INFO: {ruta} no encontrado — hojas de cierres omitidas.")
        return pd.DataFrame()
    try:
        df = pd.read_excel(ruta, sheet_name="Consolidado Cierres", engine="openpyxl")
    except Exception as exc:
        print(f"    ADVERTENCIA Consolidado Cierres: {exc}")
        return pd.DataFrame()

    df.columns = [str(c).strip() for c in df.columns]

    # Normalizar Id
    col_id = _detectar_col(df, ["Id", "ID", "id"])
    if col_id:
        df[col_id] = df[col_id].apply(_id_normalizar)
        if col_id != "Id":
            df = df.rename(columns={col_id: "Id"})

    # Normalizar Fecha
    col_fec = _detectar_col(df, ["Fecha", "fecha"])
    if col_fec:
        df[col_fec] = pd.to_datetime(df[col_fec], errors="coerce")
        if col_fec != "Fecha":
            df = df.rename(columns={col_fec: "Fecha"})

    # Normalizar columnas de cumplimiento
    for col in ["Cumplimiento", "Cumplimiento Real"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Filtrar a IDs activos
    if ids_activos and "Id" in df.columns:
        df = df[df["Id"].isin(ids_activos)].copy()

    # Agregar columna Nivel
    if "Cumplimiento" in df.columns:
        df["Nivel"] = df["Cumplimiento"].apply(_nivel_cumplimiento)

    # Ordenar Id numérico → Fecha ascendente
    if "Fecha" in df.columns:
        df = df.sort_values(
            ["Id", "Fecha"],
            key=lambda s: pd.to_numeric(s, errors="coerce") if s.name == "Id" else s
        ).reset_index(drop=True)

    return df


def escribir_consolidado_cierres(ws, df: pd.DataFrame):
    """
    Escribe la hoja 'Consolidado Cierres' con color en columna Nivel
    y formato porcentual en Cumplimiento.
    """
    if df.empty:
        ws.cell(row=1, column=1, value="Sin datos de cierres históricos.")
        return

    # Columnas a mostrar (priorizadas + resto)
    prio = ["Id", "Indicador", "Proceso", "Periodicidad", "Sentido",
            "Fecha", "Periodo", "Meta", "Ejecucion",
            "Cumplimiento", "Cumplimiento Real", "Nivel"]
    cols = [c for c in prio if c in df.columns]
    cols += [c for c in df.columns if c not in cols and c not in
             {"Llave", "Meta_Signo", "Ejecucion_Signo",
              "Decimales_Meta", "Decimales_Ejecucion", "Tipo_Registro"}]
    df_out = df[cols].copy()

    # Encabezados
    for ci, col in enumerate(df_out.columns, 1):
        cell = ws.cell(row=1, column=ci, value=col)
        _estilo_header(cell)
        ws.column_dimensions[get_column_letter(ci)].width = max(len(str(col)) + 4, 12)

    col_nivel_idx = df_out.columns.tolist().index("Nivel") + 1 if "Nivel" in df_out.columns else None
    col_cum_idx   = df_out.columns.tolist().index("Cumplimiento") + 1 if "Cumplimiento" in df_out.columns else None

    for ri, row in enumerate(df_out.itertuples(index=False), 2):
        for ci, val in enumerate(row, 1):
            col_name = df_out.columns[ci - 1]
            # Fecha → objeto date nativo para que Excel la reconozca
            if col_name == "Fecha" and pd.notna(val):
                try:
                    val = pd.Timestamp(val).date()
                except Exception:
                    pass
            cell = ws.cell(row=ri, column=ci, value=val)
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Color Nivel
        if col_nivel_idx:
            nivel_val = str(row[col_nivel_idx - 1])
            bg = C_NIVEL_BG.get(nivel_val)
            if bg:
                ws.cell(row=ri, column=col_nivel_idx).fill = PatternFill("solid", fgColor=bg)

        # Color Cumplimiento (degradado por nivel)
        if col_cum_idx:
            cum_val = row[col_cum_idx - 1]
            nivel_c = _nivel_cumplimiento(cum_val)
            bg_c = C_NIVEL_BG.get(nivel_c)
            if bg_c:
                ws.cell(row=ri, column=col_cum_idx).fill = PatternFill("solid", fgColor=bg_c)

    ws.freeze_panes = "G2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(df_out.columns))}1"


def escribir_matriz_calor(ws, df_cierres: pd.DataFrame):
    """
    Escribe la hoja 'Matriz Calor': indicadores (filas) × períodos de cierre (columnas).
    Cada celda muestra el % de cumplimiento con color de fondo según nivel.
    Columnas fijas izquierda: Id | Indicador | Proceso | Periodicidad
    Columnas dinámicas: una por Fecha de cierre (dd/mm/AAAA), ordenadas ascendente.
    """
    if df_cierres.empty or "Fecha" not in df_cierres.columns or "Id" not in df_cierres.columns:
        ws.cell(row=1, column=1, value="Sin datos para la matriz de calor.")
        return

    # ── Metadata fija por indicador (primera aparición) ──────────────────────
    META_COLS = [c for c in ["Indicador", "Proceso", "Periodicidad"] if c in df_cierres.columns]
    meta = (df_cierres.drop_duplicates(subset=["Id"], keep="first")
            .set_index("Id")[META_COLS])

    # ── Pivot Id × Fecha → Cumplimiento (último valor si hay duplicados) ──────
    pivot = (df_cierres.dropna(subset=["Fecha", "Cumplimiento"])
             .pivot_table(index="Id", columns="Fecha",
                          values="Cumplimiento", aggfunc="last"))
    pivot.columns = pd.to_datetime(pivot.columns)
    pivot = pivot.sort_index(axis=1)  # fechas ascendente

    # ── Unir metadata + pivot ─────────────────────────────────────────────────
    result = meta.join(pivot, how="outer").reset_index()

    # Ordenar filas por Id numérico
    result["_sort"] = pd.to_numeric(result["Id"], errors="coerce")
    result = result.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

    # ── Columnas del Excel ────────────────────────────────────────────────────
    fixed_cols = ["Id"] + META_COLS
    date_cols  = [c for c in result.columns if isinstance(c, pd.Timestamp)]
    all_cols   = fixed_cols + date_cols

    # ── Encabezados ───────────────────────────────────────────────────────────
    ANCHOS_FIJOS = {"Id": 8, "Indicador": 40, "Proceso": 28, "Periodicidad": 14}
    for ci, col in enumerate(all_cols, 1):
        if isinstance(col, pd.Timestamp):
            label = col.strftime("%d/%m/%Y")
            ancho = 13
        else:
            label = col
            ancho = ANCHOS_FIJOS.get(col, max(len(str(col)) + 3, 12))
        cell = ws.cell(row=1, column=ci, value=label)
        _estilo_header(cell)
        ws.column_dimensions[get_column_letter(ci)].width = ancho

    # ── Datos ─────────────────────────────────────────────────────────────────
    n_fixed = len(fixed_cols)
    for ri, row in enumerate(result.itertuples(index=False), 2):
        row_dict = dict(zip(all_cols, row))
        for ci, col in enumerate(all_cols, 1):
            val = row_dict.get(col)
            if ci <= n_fixed:
                # Columnas fijas: texto plano
                cell = ws.cell(row=ri, column=ci, value=val if pd.notna(val) else "")
                cell.alignment = Alignment(horizontal="left" if ci > 1 else "center",
                                           vertical="center")
            else:
                # Columna de cumplimiento: mostrar como % y colorear
                if pd.notna(val):
                    pct_str = f"{float(val) * 100:.1f}%"
                    nivel   = _nivel_cumplimiento(val)
                    bg      = C_NIVEL_BG.get(nivel, "FFFFFF")
                    cell = ws.cell(row=ri, column=ci, value=pct_str)
                    cell.fill = PatternFill("solid", fgColor=bg)
                else:
                    cell = ws.cell(row=ri, column=ci, value="")
                    cell.fill = PatternFill("solid", fgColor="F5F5F5")
                cell.alignment = Alignment(horizontal="center", vertical="center")

    # ── Formato final ─────────────────────────────────────────────────────────
    freeze_col = get_column_letter(n_fixed + 1)
    ws.freeze_panes = f"{freeze_col}2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(all_cols))}1"


# ══════════════════════════════════════════════════════════════════════════════
#  ARCHIVOS ANUALES DE KAWAK → periodos con resultado (columnas fechadas)
# ══════════════════════════════════════════════════════════════════════════════

_PAT_PERIODO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\s+Periodo\s+(\d+)$")


def leer_kawak_anual(kawak_dir: str, years: List[int]) -> Tuple[Dict, Dict[int, Optional[date]]]:
    """
    Lee data/raw/Kawak/<año>.xlsx y devuelve:
      lookup  : {(id_str, año, mes): True} para cada periodo fechado con resultado
      ultimo  : {año: fecha del último periodo (columna) que trae resultado para algún indicador}

    Usa solo las filas consolidadas ("Nombre variable/consolidado" contiene "Consolidado"): las
    filas de variables pueden traer valores parciales aunque el indicador no esté calculado.
    El encabezado de cada columna lleva su fecha real ("2026-09-30 Periodo 40"), por lo que no
    se deduce nada por posición.
    """
    lookup: Dict = {}
    ultimo: Dict[int, Optional[date]] = {}
    for year in years:
        ruta = os.path.join(kawak_dir, f"{year}.xlsx")
        ultimo[year] = None
        if not os.path.exists(ruta):
            continue
        try:
            df = pd.read_excel(ruta, engine="openpyxl", dtype=object)
        except Exception as exc:  # noqa: BLE001
            print(f"    ADVERTENCIA Kawak {year}: no se pudo leer: {exc}")
            continue
        df.columns = [str(c).strip() for c in df.columns]
        col_id = _detectar_col(df, ["Id", "ID", "id"])
        if not col_id:
            continue
        col_var = _detectar_col(df, ["Nombre variable/consolidado"])
        if col_var:
            df = df[df[col_var].astype(str).str.contains("Consolidado", case=False, na=False)]
        columnas = []
        for c in df.columns:
            m = _PAT_PERIODO.match(c)
            if m and int(m.group(1)) >= year - 1:
                columnas.append((c, int(m.group(1)), int(m.group(2)), int(m.group(3))))
        for _, fila in df.iterrows():
            kid = _id_normalizar(fila[col_id])
            if not kid:
                continue
            for c, a, mes, dia in columnas:
                if _tiene_dato_kawak(fila[c]):
                    lookup[(kid, a, mes)] = True
                    f = date(a, mes, dia)
                    if f.year == year and (ultimo[year] is None or f > ultimo[year]):
                        ultimo[year] = f
        print(f"    Kawak {year}: periodos con resultado hasta {ultimo[year] or 'ninguno'}")
    return lookup, ultimo


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def _sin_columnas_de_periodo(meta_por_anio: Dict[int, Dict[str, dict]]) -> Dict[int, Dict[str, dict]]:
    """Quita de la metadata las columnas "Periodo N" / "AAAA-MM-DD Periodo N" del archivo de Kawak.

    Son resultados por indicador y periodo; en el tracking (una fila por indicador y mes) solo
    inflan el archivo (72 columnas) sin aportar: el estado ya sale de leer_kawak_anual().
    """
    return {
        anio: {kid: {c: v for c, v in meta.items() if not re.search(r"Periodo\s+\d+$", str(c))} for kid, meta in metas.items()}
        for anio, metas in meta_por_anio.items()
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Genera Seguimiento_Reporte.xlsx (sin LMI).")
    parser.add_argument("--salida", default=RUTA_SALIDA, help="Archivo de salida (.xlsx).")
    parser.add_argument("--fecha-ref", default=None, help="Último día del calendario (AAAA-MM-DD). Por defecto: fin del mes anterior.")
    args = parser.parse_args(argv)

    fecha_ref = date.fromisoformat(args.fecha_ref) if args.fecha_ref else get_fecha_referencia()
    sep = "=" * 66
    print(sep)
    print("  generar_seguimiento.py → Seguimiento_Reporte.xlsx  (fuente: Kawak anual + API)")
    print(sep)
    print(f"  Fecha de ejecución : {date.today().strftime('%d/%m/%Y')}")
    print(f"  Fecha de referencia: {fecha_ref.strftime('%d/%m/%Y')}")
    print(f"  Inicio calendario  : {FECHA_INICIO.strftime('%m/%Y')}")

    calendario = generar_calendario(FECHA_INICIO, fecha_ref)
    years = sorted({y for y, _ in calendario})
    print(f"\n[1] Calendario: {calendario[0][1]}/{calendario[0][0]} → {calendario[-1][1]}/{calendario[-1][0]}  ({len(calendario)} meses)")

    # Catálogos año-específicos: un indicador inactivo en 2026 no genera filas para 2026.
    print("\n[2] Catálogos anuales de Kawak (indicadores activos y periodicidad)...")
    catalogo_por_anio: Dict[int, Dict[str, str]] = {}
    meta_por_anio: Dict[int, Dict[str, dict]] = {}
    for year in years:
        cat, met = leer_catalogo_por_anio(RUTA_KAWAK_DIR, year)
        if cat:
            catalogo_por_anio[year], meta_por_anio[year] = cat, met
        else:
            print(f"    ADVERTENCIA: sin catálogo para {year} — meses de ese año omitidos.")
    if not catalogo_por_anio:
        print("    ERROR: no hay catálogos de Kawak; no se genera el archivo.")
        return 2
    meta_por_anio = _sin_columnas_de_periodo(meta_por_anio)
    # El catálogo del año más reciente manda (la periodicidad puede cambiar entre años).
    catalogo_unificado: Dict[str, str] = {}
    for year in sorted(catalogo_por_anio):
        catalogo_unificado.update(catalogo_por_anio[year])

    print("\n[3] Resultados: API de Kawak + periodos fechados de los archivos anuales...")
    kawak_lookup = normalizar_kawak_lookup(leer_kawak_api(RUTA_KAWAK_API), catalogo_unificado)
    anual_raw, ultimo = leer_kawak_anual(RUTA_KAWAK_DIR, years)
    kawak_anual_lookup = normalizar_kawak_lookup(anual_raw, catalogo_unificado)
    print(f"    API (normalizada a mes de cierre): {len(kawak_lookup)} | archivos anuales: {len(kawak_anual_lookup)}")

    print("\n[4] Tracking Mensual...")
    tracking_df = construir_tracking_largo(catalogo_por_anio, kawak_lookup, kawak_anual_lookup, calendario, meta_por_anio)
    if tracking_df.empty:
        print("    ERROR: el tracking quedó vacío; no se sobrescribe el archivo.")
        return 2
    vc = tracking_df["Estado"].value_counts().to_dict()
    por_fuente = tracking_df["Fuente"].value_counts().to_dict()
    print(f"    Filas: {len(tracking_df):,} ({tracking_df['Id'].nunique()} indicadores) | estados: {vc} | fuente: {por_fuente}")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    escribir_tracking_mensual(wb.create_sheet(title="Tracking Mensual"), tracking_df)

    print("\n[5] Hojas de cierres históricos...")
    df_cierres = leer_consolidado_cierres(RUTA_CONSOLIDADOS, set(catalogo_unificado.keys()))
    if not df_cierres.empty:
        escribir_consolidado_cierres(wb.create_sheet(title="Consolidado Cierres"), df_cierres)
        escribir_matriz_calor(wb.create_sheet(title="Matriz Calor"), df_cierres)
        print(f"    Consolidado Cierres: {len(df_cierres)} registros | Matriz Calor OK")
    else:
        print("    ADVERTENCIA: sin datos de cierres — hojas omitidas.")

    # Escritura atómica: un fallo a medias no deja un archivo corrupto en data/output/.
    destino = os.path.abspath(args.salida)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".xlsx", dir=os.path.dirname(destino))
    os.close(fd)
    try:
        wb.save(tmp)
        os.replace(tmp, destino)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    print(f"\n[6] Guardado: {destino}")
    print(sep)
    print("  Proceso completado exitosamente.")
    print(sep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
