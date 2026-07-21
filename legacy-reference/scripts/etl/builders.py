"""
scripts/etl/builders.py
Constructores de registros para las hojas Histórico, Semestral y Cierres.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from .config import (
    AÑO_CIERRE_ACTUAL,
    _PARENT_SERIES_INDEX,
    _normalizar_nombre_serie,
    CRONOGRAMA_PADRES,
    _CRONOGRAMA_SERIES_FLAT,
)
from .extraccion import (
    _ejec_corrected_from_row, _meta_corrected_from_row, _extraer_registro,
    extraer_por_simbolo,
)
from .fuentes import cargar_estado_proyectos
from .normalizacion import _id_str, limpiar_html, make_llave, nan2none, parse_json_safe
from .periodos import _fecha_es_periodo_valido, ultimo_dia_mes

logger = logging.getLogger(__name__)


# Los proyectos (Proyecto=1 en el catálogo) reportan avance mensual, pero la
# Periodicidad mostrada en cada hoja refleja el nivel de agregación de esa
# hoja, no la cadencia de captura (feedback 2026-07-14).
_PERIODICIDAD_PROYECTO_POR_HOJA = {
    "historico": "Mensual",
    "semestral": "Semestral",
    "cierres":   "Anual",
}


def _es_proyecto(id_s: str, metadatos_cmi: Optional[Dict]) -> bool:
    if not metadatos_cmi:
        return False
    v = metadatos_cmi.get(id_s, {}).get("proyecto")
    try:
        return int(float(v)) == 1
    except (TypeError, ValueError):
        return False


def _resolver_periodicidad(
    id_s: str,
    año: Optional[int],
    valor_fuente,
    kawak_por_año: Optional[Dict] = None,
    metadatos_cmi: Optional[Dict] = None,
    hoja: str = "historico",
) -> str:
    """Periodicidad de un registro.

    Proyectos (Proyecto=1 en el catálogo): fija según la hoja de destino
    (Mensual/Semestral/Anual) — ver _PERIODICIDAD_PROYECTO_POR_HOJA.

    Resto de indicadores, en orden de precedencia:
    1. 'Indicadores Kawak.xlsx' (consolidado de Kawak/<año>.xlsx) para el
       (Id, Año) exacto del registro — fuente primaria.
    2. Periodicidad del catálogo maestro (Catalogo de Indicadores.xlsx).
    3. Valor que ya trae el propio registro fuente (Consolidado_API_Kawak),
       como último recurso para no dejar la celda vacía.
    """
    if _es_proyecto(id_s, metadatos_cmi):
        return _PERIODICIDAD_PROYECTO_POR_HOJA.get(hoja, "Mensual")
    if kawak_por_año and año is not None:
        v = kawak_por_año.get((id_s, int(año)))
        if v:
            return v
    if metadatos_cmi:
        v = str(metadatos_cmi.get(id_s, {}).get("periodicidad", "") or "").strip()
        if v and v.lower() != "nan":
            return v
    v = str(valor_fuente or "").strip()
    return v if v and v.lower() != "nan" else ""


# ── Histórico ─────────────────────────────────────────────────────

def construir_registros_historico(
    df_fuente: pd.DataFrame,
    llaves_existentes: Set[str],
    hist_escalas: Dict,
    config_patrones: Optional[Dict] = None,
    mapa_procesos: Optional[Dict] = None,
    kawak_validos: Optional[Set[Tuple[str, int]]] = None,
    extraccion_map: Optional[Dict] = None,
    api_kawak_lookup: Optional[Dict] = None,
    variables_campo_map: Optional[Dict] = None,
    tipo_indicador_map: Optional[Dict] = None,
    metadatos_cmi: Optional[Dict] = None,
    kawak_por_año: Optional[Dict] = None,
    hoja: str = "historico",
) -> Tuple[List[Dict], int, int]:
    """
    Genera registros nuevos para Consolidado Histórico.
    Retorna (registros, skipped, conteo_na).
    """
    registros = []
    skipped   = 0
    conteo_na = 0
    df = df_fuente[~df_fuente["LLAVE"].isin(llaves_existentes)].dropna(subset=["LLAVE"])

    for row in df.itertuples(index=False):
        id_s = _id_str(getattr(row, "Id", None) or getattr(row, "ID", ""))
        try:
            año = pd.to_datetime(getattr(row, "fecha", None)).year
        except Exception:
            año = None
        if kawak_validos is not None:
            if año is not None and (id_s, año) not in kawak_validos:
                skipped += 1
                continue

        meta, ejec, fuente, es_na = _extraer_registro(
            row, hist_escalas,
            config_patrones=config_patrones,
            extraccion_map=extraccion_map,
            api_kawak_lookup=api_kawak_lookup,
            variables_campo_map=variables_campo_map,
            tipo_indicador_map=tipo_indicador_map,
        )

        if fuente in ("skip", "sin_resultado"):
            skipped += 1
            continue

        periodicidad = _resolver_periodicidad(
            id_s, año, getattr(row, "Periodicidad", ""), kawak_por_año, metadatos_cmi, hoja
        )

        if es_na:
            try:
                fecha_ts = pd.to_datetime(getattr(row, "fecha", None))
            except Exception:
                fecha_ts = None
            if periodicidad and fecha_ts is not None:
                if not _fecha_es_periodo_valido(fecha_ts, periodicidad):
                    skipped += 1
                    continue
            conteo_na += 1

        registros.append({
            "Id":          getattr(row, "Id", None),
            "Indicador":   limpiar_html(str(getattr(row, "Indicador", ""))),
            "Proceso":     getattr(row, "Proceso", ""),
            "Periodicidad":periodicidad,
            "Sentido":     getattr(row, "Sentido", ""),
            "fecha":       getattr(row, "fecha", None),
            "Meta":        meta,
            "Ejecucion":   ejec,
            "LLAVE":       getattr(row, "LLAVE", None),
            "es_na":       es_na,
        })

    return registros, skipped, conteo_na


# ── Expansión de series como sub-indicadores ───────────────────────

# Símbolos de "% avance" (ejecución real) y "% esperado" (meta) por indicador
# padre de Plan Anual (Retos). Verificados contra las variables reales de
# data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx — varían por padre,
# no son un par fijo "PAGE"/"PEGE" global.
_SIMBOLOS_PLAN_ANUAL: Dict[str, Tuple[str, str]] = {
    "373": ("PAVAN", "PEAVAN"),
    "390": ("PAPRE", "PEPRE"),
    "414": ("PAVR",  "PERE"),
    "415": ("PAVE",  "PESVE"),
    "416": ("PAVC",  "PEVE"),
    "417": ("PAVF",  "PEVF"),
    "418": ("PAVA",  "PEVA"),
    "420": ("PAGE",  "PEGE"),
    "469": ("PARM",  "PAEM"),
    "470": ("PASAE", "PESAE"),
    "471": ("PAGTH", "PEGTH"),
}


def expandir_series_como_subindicadores(
    df_fuente: pd.DataFrame,
    llaves_existentes: Set[str],
    modo: str = "historico",
    metadatos_cmi: Optional[Dict] = None,
    kawak_por_año: Optional[Dict] = None,
) -> List[Dict]:
    """
    Expande las series JSON de indicadores padre en registros de sub-indicadores.

    Usa el índice _PARENT_SERIES_INDEX (cargado de config/series_subindicadores.toml)
    para mapear nombre de serie → ID decimal (ej. "SGC" → "420.1").

    Parámetros:
        df_fuente: DataFrame con todos los registros fuente (ya tiene columna 'fecha' parseada).
        llaves_existentes: Set de LLAVEs ya presentes en el consolidado.
        modo: "historico"  → todos los períodos
              "semestral"  → junio (S1) y diciembre (S2)
              "cierres"    → un registro por (sub_id, año): diciembre si existe, si no el último
    """
    if not _PARENT_SERIES_INDEX:
        return []

    registros: List[Dict] = []
    padres_en_fuente = set(_PARENT_SERIES_INDEX.keys())

    df_padres = df_fuente[
        df_fuente["Id"].map(lambda v: _id_str(v) if pd.notna(v) else "").isin(padres_en_fuente)
    ].copy()

    if df_padres.empty:
        return []

    df_padres["_id_s"] = df_padres["Id"].map(_id_str)
    df_padres["fecha"] = pd.to_datetime(df_padres["fecha"], errors="coerce")
    df_padres = df_padres.dropna(subset=["fecha", "series"])
    df_padres = df_padres[
        ~df_padres["series"].astype(str).str.strip().isin(["", "nan", "[]", "None"])
    ]

    if modo == "semestral":
        df_padres = df_padres[df_padres["fecha"].dt.month.isin([6, 12])]
    elif modo == "cierres":
        df_padres["_año"] = df_padres["fecha"].dt.year

    def _parse_series(val):
        from .normalizacion import parse_json_safe
        return parse_json_safe(val) or []

    if modo == "cierres":
        grupos = []
        for (id_s, año), grp in df_padres.groupby(["_id_s", "_año"]):
            dec_rows = grp[grp["fecha"].dt.month == 12]
            candidato = (dec_rows if not dec_rows.empty else grp).sort_values("fecha").tail(1)
            grupos.append(candidato)
        if not grupos:
            return []
        df_padres = pd.concat(grupos, ignore_index=True)

    for row in df_padres.itertuples(index=False):
        id_s: str = getattr(row, "_id_s", "") or _id_str(getattr(row, "Id", ""))
        serie_index = _PARENT_SERIES_INDEX.get(id_s, {})
        if not serie_index:
            continue

        series_list = _parse_series(getattr(row, "series", None))
        if not series_list:
            continue

        fecha = getattr(row, "fecha", None)
        indicador_padre = limpiar_html(str(getattr(row, "Indicador", "") or ""))
        proceso = getattr(row, "Proceso", "") or ""
        try:
            año_row = pd.to_datetime(fecha).year
        except Exception:
            año_row = None
        periodicidad = _resolver_periodicidad(
            id_s, año_row, getattr(row, "Periodicidad", ""), kawak_por_año, metadatos_cmi, modo
        )
        sentido = getattr(row, "Sentido", "") or ""

        for serie in series_list:
            if not isinstance(serie, dict):
                continue
            nombre_serie = str(serie.get("nombre", "")).strip()
            nombre_norm = _normalizar_nombre_serie(nombre_serie)
            sub_id = serie_index.get(nombre_norm)
            if sub_id is None:
                continue

            # Extraer avance real y esperado desde variables. Los símbolos
            # varían por indicador padre (ver _SIMBOLOS_PLAN_ANUAL); solo si
            # el padre no está en el mapa o las variables no existen se cae
            # a serie["resultado"]/serie["meta"] (que en la fuente NO son
            # avance real/esperado: "resultado" ya es un % de cumplimiento
            # pre-calculado y "meta" viene hardcodeado a 100).
            # Se almacenan en escala porcentual (0-100), igual que el resto del consolidado
            vars_dict = {
                v.get("simbolo", ""): v.get("valor")
                for v in serie.get("variables", [])
                if isinstance(v, dict)
            }
            simb_avance, simb_esperado = _SIMBOLOS_PLAN_ANUAL.get(id_s, ("PAGE", "PEGE"))
            avance = vars_dict.get(simb_avance)
            esperado = vars_dict.get(simb_esperado)
            try:
                ejec = float(avance) if avance is not None else (
                    float(serie["resultado"]) if serie.get("resultado") is not None else None
                )
            except (TypeError, ValueError):
                ejec = None
            try:
                meta = float(esperado) if esperado is not None else (
                    float(serie["meta"]) if serie.get("meta") is not None else None
                )
            except (TypeError, ValueError):
                meta = None

            llave = make_llave(sub_id, pd.Timestamp(fecha))
            if llave in llaves_existentes:
                continue

            registros.append({
                "Id":          sub_id,
                "Indicador":   f"{indicador_padre} — {nombre_serie}",
                "Proceso":     proceso,
                "Periodicidad":periodicidad,
                "Sentido":     sentido,
                "fecha":       fecha,
                "Meta":        meta,
                "Ejecucion":   ejec,
                "LLAVE":       llave,
                "es_na":       ejec is None,
            })

    return registros


# ── Proyectos cronograma (extrae series de padres 441/509/603) ─────

def extraer_cronograma_proyectos(
    df_fuente: pd.DataFrame,
    llaves_existentes: Set[str],
    modo: str = "historico",
    metadatos_cmi: Optional[Dict] = None,
    kawak_por_año: Optional[Dict] = None,
) -> List[Dict]:
    """
    Extrae ejecución y meta de los proyectos estratégicos desde las series
    del indicador padre correspondiente a cada año.

    Mapa en config/series_subindicadores.toml:
        [cronograma_proyectos.padres]   año → ID_padre   (441/509/603)
        [cronograma_proyectos.series]   nombre_serie → ID_proyecto

    Parámetros:
        modo: "historico"  → todos los meses del año de vigencia del padre
              "semestral"  → junio (S1) y diciembre (S2)
              "cierres"    → un registro por (padre, año): diciembre si existe, si no el último
    """
    if not CRONOGRAMA_PADRES or not _CRONOGRAMA_SERIES_FLAT:
        return []

    _padre_a_año: Dict[str, int] = {pid: yr for yr, pid in CRONOGRAMA_PADRES.items()}
    padres_ids = set(_padre_a_año.keys())

    df_proy = df_fuente[
        df_fuente["Id"].map(lambda v: _id_str(v) if pd.notna(v) else "").isin(padres_ids)
    ].copy()

    if df_proy.empty:
        return []

    df_proy["id_padre"] = df_proy["Id"].map(_id_str)
    df_proy["fecha"] = pd.to_datetime(df_proy["fecha"], errors="coerce")
    df_proy = df_proy.dropna(subset=["fecha", "series"])
    df_proy = df_proy[
        ~df_proy["series"].astype(str).str.strip().isin(["", "nan", "[]", "None"])
    ]

    # Filtrar filas al año de vigencia de su padre
    df_proy["año_padre"] = df_proy["fecha"].dt.year
    df_proy = df_proy[
        df_proy.apply(lambda r: _padre_a_año.get(r["id_padre"]) == r["año_padre"], axis=1)
    ]

    if df_proy.empty:
        return []

    # Aplicar filtro por modo
    if modo == "semestral":
        df_proy = df_proy[df_proy["fecha"].dt.month.isin([6, 12])]
    elif modo == "cierres":
        # Un registro por (padre_id, año): preferir diciembre, si no el último disponible
        seleccionados = []
        for (id_padre, año), grp in df_proy.groupby(["id_padre", "año_padre"]):
            dic_rows = grp[grp["fecha"].dt.month == 12]
            candidato = (dic_rows if not dic_rows.empty else grp).sort_values("fecha").tail(1)
            seleccionados.append(candidato)
        if not seleccionados:
            return []
        df_proy = pd.concat(seleccionados, ignore_index=True)

    def _parse_series(val):
        from .normalizacion import parse_json_safe
        return parse_json_safe(val) or []

    registros: List[Dict] = []

    for row in df_proy.itertuples(index=False):
        fecha = getattr(row, "fecha", None)
        if pd.isna(fecha):
            continue

        series_list = _parse_series(getattr(row, "series", None))
        if not series_list:
            continue

        proceso    = getattr(row, "Proceso", "") or ""
        periodicid = getattr(row, "Periodicidad", "") or ""
        sentido    = getattr(row, "Sentido", "") or ""
        try:
            año_row = pd.to_datetime(fecha).year
        except Exception:
            año_row = None

        for serie in series_list:
            if not isinstance(serie, dict):
                continue
            nombre_serie = str(serie.get("nombre", "")).strip()
            nombre_norm  = _normalizar_nombre_serie(nombre_serie)
            proj_id = _CRONOGRAMA_SERIES_FLAT.get(nombre_norm)
            if proj_id is None:
                continue
            if cargar_estado_proyectos().get(proj_id, "").lower() == "historico":
                continue

            # Extraer avance real (PARPR) y esperado (PAEPR) desde variables.
            # Se almacenan en escala porcentual (0-100), igual que el resto del consolidado.
            # No se cae a serie["resultado"]/serie["meta"] si faltan: "resultado" es
            # un % ya pre-calculado (no la ejecución real) y "meta" viene hardcodeado
            # a un valor fijo idéntico para todos los proyectos/meses (ej. 90) — usarlos
            # como sustituto produce Meta/Ejecución falsos en vez de marcar es_na
            # (feedback 2026-07-15).
            vars_dict = {
                v.get("simbolo", ""): v.get("valor")
                for v in serie.get("variables", [])
                if isinstance(v, dict)
            }
            parpr = vars_dict.get("PARPR")
            paepr = vars_dict.get("PAEPR")
            try:
                ejec = float(parpr) if parpr is not None else None
            except (TypeError, ValueError):
                ejec = None
            try:
                meta = float(paepr) if paepr is not None else None
            except (TypeError, ValueError):
                meta = None

            llave = make_llave(proj_id, pd.Timestamp(fecha))
            if llave in llaves_existentes:
                continue

            registros.append({
                "Id":           proj_id,
                "Indicador":    limpiar_html(nombre_serie),
                "Proceso":      proceso,
                "Periodicidad": _resolver_periodicidad(
                    proj_id, año_row, periodicid, kawak_por_año, metadatos_cmi, modo
                ),
                "Sentido":      sentido,
                "fecha":        fecha,
                "Meta":         meta,
                "Ejecucion":    ejec,
                "LLAVE":        llave,
                "es_na":        ejec is None,
            })

    return registros


# ── Población total (14, 14.1-14.4) ─────────────────────────────────

# Ninguno de estos 5 IDs tiene datos propios en Kawak/API: son derivados,
# calculados sumando matrículas nuevos (379, 381-384) y estudiantes antiguos
# (274). Fórmulas verificadas contra la columna "Asociacion" de la hoja
# "Catalogo Indicadores" (data/raw/Resultados_Consolidados_Fuente.xlsx) y
# contra docs/LOGICA_INDICADORES_ESPECIALES.md §2-3:
#   14   = Σ(379) + Σ(274)                        ("Suma de total de
#          indicador 379 y total indicador 274")
#   14.1-14.4 = "Suman Nuevos-Antiguos" por categoría (presencial/virtual/
#          pregrado/posgrado)
# Los símbolos de 379/381-384 dan conteos brutos (no porcentajes) de
# matrículas nuevos; TEMS/TEP dentro de cada serie de 274 dan los conteos
# brutos (matriculados/presupuestados) de estudiantes antiguos por
# modalidad — ver estructura de `series` documentada en el Grupo B.
_SIMBOLOS_MATRICULAS_NUEVOS: Dict[str, Tuple[str, str]] = {
    "379": ("NENTM",  "NTENMP"),   # Total estudiantes nuevos
    "381": ("ENMPP",  "TENPPP"),   # Pregrado presencial nuevos
    "382": ("ENMPV",  "TENPPV"),   # Pregrado virtual nuevos
    "383": ("NENMPV", "TEMPVP"),   # Posgrado virtual nuevos
    "384": ("NENMPP", "TENPPPR"),  # Posgrado presencial nuevos
}

_SERIES_ANTIGUOS_TODAS = [
    "Posgrado Presencial", "Pregrado Presencial", "Pregrado Virtual", "Posgrado Virtual",
]
_SERIES_ANTIGUOS_POR_CATEGORIA: Dict[str, List[str]] = {
    "presencial": ["Posgrado Presencial", "Pregrado Presencial"],
    "virtual":    ["Pregrado Virtual", "Posgrado Virtual"],
    "pregrado":   ["Pregrado Presencial", "Pregrado Virtual"],
    "posgrado":   ["Posgrado Presencial", "Posgrado Virtual"],
}
_NUEVOS_POR_CATEGORIA: Dict[str, List[str]] = {
    "presencial": ["381", "384"],
    "virtual":    ["382", "383"],
    "pregrado":   ["381", "382"],
    "posgrado":   ["384", "383"],
}

_ID_TOTAL_POBLACION = "14"
_SUB_POBLACION: Dict[str, Tuple[str, str]] = {
    "14.1": ("Estudiantes Presencial", "presencial"),
    "14.2": ("Estudiantes Virtual",    "virtual"),
    "14.3": ("Estudiantes Pregrado",   "pregrado"),
    "14.4": ("Estudiantes Posgrado",   "posgrado"),
}

# Metadatos fijos según hoja "Catalogo Indicadores" — id 14 y sus hijos
# tienen su propio Proceso/Sentido en el catálogo, distinto al de sus
# indicadores fuente (379/381-384/274).
_PROCESO_POBLACION = "Servicio"
_SENTIDO_POBLACION = "Positivo"


def construir_registros_poblacion(
    df_fuente: pd.DataFrame,
    llaves_existentes: Set[str],
    modo: str = "historico",
    metadatos_cmi: Optional[Dict] = None,
    kawak_por_año: Optional[Dict] = None,
) -> List[Dict]:
    """
    Construye el indicador 14 (Total Población) y sus sub-indicadores
    14.1-14.4, sumando matrículas nuevos (379, 381-384) y estudiantes
    antiguos (274). Ver docs/LOGICA_INDICADORES_ESPECIALES.md.

    Al igual que expandir_series_como_subindicadores(), no filtra por
    kawak_validos: estos IDs nunca aparecen en la fuente Kawak/API.
    """
    ids_fuente = set(_SIMBOLOS_MATRICULAS_NUEVOS.keys()) | {"274"}
    df = df_fuente[
        df_fuente["Id"].map(lambda v: _id_str(v) if pd.notna(v) else "").isin(ids_fuente)
    ].copy()
    if df.empty:
        return []

    df["_id_s"] = df["Id"].map(_id_str)
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])

    if modo == "semestral":
        df = df[df["fecha"].dt.month.isin([6, 12])]
    elif modo == "cierres":
        df["_año"] = df["fecha"].dt.year
        grupos = []
        for (_id_s, año), grp in df.groupby(["_id_s", "_año"]):
            dec_rows = grp[grp["fecha"].dt.month == 12]
            candidato = (dec_rows if not dec_rows.empty else grp).sort_values("fecha").tail(1)
            grupos.append(candidato)
        if not grupos:
            return []
        df = pd.concat(grupos, ignore_index=True)

    if df.empty:
        return []

    # Recopila valores por fecha: {fecha: {"381_ejec": .., "274_Pregrado Virtual_meta": .., ...}}
    valores: Dict[pd.Timestamp, Dict[str, float]] = {}

    for row in df.itertuples(index=False):
        id_s = _id_str(getattr(row, "Id", ""))
        fecha = getattr(row, "fecha", None)
        if pd.isna(fecha):
            continue
        fecha = pd.Timestamp(fecha)
        slot = valores.setdefault(fecha, {})

        if id_s in _SIMBOLOS_MATRICULAS_NUEVOS:
            vars_list = parse_json_safe(getattr(row, "variables", None)) or []
            simb_ejec, simb_meta = _SIMBOLOS_MATRICULAS_NUEVOS[id_s]
            ejec = extraer_por_simbolo(vars_list, simb_ejec)
            meta = extraer_por_simbolo(vars_list, simb_meta)
            if ejec is not None:
                slot[f"{id_s}_ejec"] = ejec
            if meta is not None:
                slot[f"{id_s}_meta"] = meta

        elif id_s == "274":
            series_list = parse_json_safe(getattr(row, "series", None)) or []
            for serie in series_list:
                if not isinstance(serie, dict):
                    continue
                nombre = str(serie.get("nombre", "")).strip()
                if nombre not in _SERIES_ANTIGUOS_TODAS:
                    continue
                vars_dict = {
                    v.get("simbolo", ""): v.get("valor")
                    for v in serie.get("variables", [])
                    if isinstance(v, dict)
                }
                ejec_v, meta_v = vars_dict.get("TEMS"), vars_dict.get("TEP")
                try:
                    if ejec_v is not None:
                        slot[f"274_{nombre}_ejec"] = float(ejec_v)
                    if meta_v is not None:
                        slot[f"274_{nombre}_meta"] = float(meta_v)
                except (TypeError, ValueError):
                    pass

    def _sum(slot: Dict[str, float], claves: List[str]) -> Optional[float]:
        vals = [slot[c] for c in claves if c in slot]
        return sum(vals) if len(vals) == len(claves) else None

    registros: List[Dict] = []

    for fecha, slot in valores.items():
        try:
            año = fecha.year
        except Exception:
            año = None
        periodicidad = _resolver_periodicidad(
            _ID_TOTAL_POBLACION, año, "Semestral", kawak_por_año, metadatos_cmi, modo
        )

        # ── Total (14) ──────────────────────────────────────────────
        claves_ejec_14 = ["379_ejec"] + [f"274_{s}_ejec" for s in _SERIES_ANTIGUOS_TODAS]
        claves_meta_14 = ["379_meta"] + [f"274_{s}_meta" for s in _SERIES_ANTIGUOS_TODAS]
        ejec_14 = _sum(slot, claves_ejec_14)
        if ejec_14 is not None:
            llave = make_llave(_ID_TOTAL_POBLACION, fecha)
            if llave not in llaves_existentes:
                registros.append({
                    "Id":          _ID_TOTAL_POBLACION,
                    "Indicador":   "Total Población",
                    "Proceso":     _PROCESO_POBLACION,
                    "Periodicidad":periodicidad,
                    "Sentido":     _SENTIDO_POBLACION,
                    "fecha":       fecha,
                    "Meta":        _sum(slot, claves_meta_14),
                    "Ejecucion":   ejec_14,
                    "LLAVE":       llave,
                    "es_na":       False,
                })

        # ── Sub-indicadores (14.1-14.4) ────────────────────────────
        for sub_id, (nombre_sub, categoria) in _SUB_POBLACION.items():
            claves_ejec = (
                [f"{nid}_ejec" for nid in _NUEVOS_POR_CATEGORIA[categoria]]
                + [f"274_{s}_ejec" for s in _SERIES_ANTIGUOS_POR_CATEGORIA[categoria]]
            )
            claves_meta = (
                [f"{nid}_meta" for nid in _NUEVOS_POR_CATEGORIA[categoria]]
                + [f"274_{s}_meta" for s in _SERIES_ANTIGUOS_POR_CATEGORIA[categoria]]
            )
            ejec = _sum(slot, claves_ejec)
            if ejec is None:
                continue
            llave = make_llave(sub_id, fecha)
            if llave in llaves_existentes:
                continue
            registros.append({
                "Id":          sub_id,
                "Indicador":   nombre_sub,
                "Proceso":     _PROCESO_POBLACION,
                "Periodicidad":periodicidad,
                "Sentido":     _SENTIDO_POBLACION,
                "fecha":       fecha,
                "Meta":        _sum(slot, claves_meta),
                "Ejecucion":   ejec,
                "LLAVE":       llave,
                "es_na":       False,
            })

    return registros


# ── Semestral ─────────────────────────────────────────────────────

def construir_registros_semestral(
    df_fuente: pd.DataFrame,
    llaves_existentes: Set[str],
    hist_escalas: Dict,
    config_patrones: Optional[Dict] = None,
    mapa_procesos: Optional[Dict] = None,
    kawak_validos: Optional[Set[Tuple[str, int]]] = None,
    extraccion_map: Optional[Dict] = None,
    api_kawak_lookup: Optional[Dict] = None,
    tipo_calculo_map: Optional[Dict] = None,
    variables_campo_map: Optional[Dict] = None,
    tipo_indicador_map: Optional[Dict] = None,
    metadatos_cmi: Optional[Dict] = None,
    kawak_por_año: Optional[Dict] = None,
) -> Tuple[List[Dict], int, int]:
    """
    Genera registros para Consolidado Semestral.

    TipoCalculo:
      Promedio  → promedio de meses del semestre
      Acumulado → suma de meses del semestre
      Cierre    → último período de cierre (jun/dic)
    """
    ids_avg: Set[str] = set()
    ids_sum: Set[str] = set()

    if config_patrones:
        for ids, cfg in config_patrones.items():
            if cfg["patron"] == "AVG":    ids_avg.add(ids)
            elif cfg["patron"] == "SUM":  ids_sum.add(ids)

    if tipo_calculo_map:
        for ids, tc in tipo_calculo_map.items():
            tc_n = tc.lower().strip()
            if tc_n == "promedio":   ids_avg.add(ids)
            elif tc_n == "acumulado": ids_sum.add(ids)

    df_base = df_fuente.copy()
    df_base["_ids"] = df_base["Id"].map(_id_str)
    df_base["_sem"] = (
        df_base["fecha"].dt.year.astype(int).astype(str)
        + "-"
        + (df_base["fecha"].dt.month <= 6).map({True: "1", False: "2"})
    )

    partes = []
    ids_agg = ids_avg | ids_sum

    # ── Indicadores Cierre/estándar ──────────────────────────────
    df_std = df_base[~df_base["_ids"].isin(ids_agg)].copy()
    df_std = df_std[df_std["fecha"].dt.month.isin([6, 12])]
    df_std = df_std[df_std["fecha"].dt.day == df_std["fecha"].dt.daysinmonth]
    partes.append(df_std)

    # ── Indicadores Promedio/Acumulado ───────────────────────────
    registros_agg: List[Dict] = []
    if ids_agg:
        df_agg_src = df_base[df_base["_ids"].isin(ids_agg)].copy()
        agg_records = df_agg_src.to_dict(orient="records")
        df_agg_src["_ejec_corr"] = [
            _ejec_corrected_from_row(
                rec, extraccion_map, api_kawak_lookup,
                variables_campo_map, tipo_indicador_map,
            )
            for rec in agg_records
        ]
        df_agg_src["_meta_corr"] = [
            _meta_corrected_from_row(
                rec, extraccion_map, api_kawak_lookup,
                variables_campo_map, tipo_indicador_map,
            )
            for rec in agg_records
        ]

        for (id_val, sem_label), grupo in df_agg_src.groupby(["Id", "_sem"]):
            ids = _id_str(id_val)
            patron = "AVG" if ids in ids_avg else "SUM"

            ejecs = pd.to_numeric(grupo["_ejec_corr"], errors="coerce").dropna()
            metas = pd.to_numeric(grupo["_meta_corr"], errors="coerce").dropna()
            if len(ejecs) == 0:
                continue

            ejec_agg = ejecs.mean() if patron == "AVG" else ejecs.sum()
            meta_agg = ((metas.mean() if patron == "AVG" else metas.sum())
                        if len(metas) > 0 else None)

            year, sem = int(sem_label.split("-")[0]), int(sem_label.split("-")[1])
            end_month = 6 if sem == 1 else 12
            end_fecha = pd.Timestamp(year, end_month, ultimo_dia_mes(year, end_month))
            llave = make_llave(id_val, end_fecha)

            if llave in llaves_existentes:
                continue
            if kawak_validos is not None and (ids, year) not in kawak_validos:
                continue

            last = grupo.sort_values("fecha").iloc[-1]
            registros_agg.append({
                "Id":          id_val,
                "Indicador":   limpiar_html(str(last.get("Indicador", ""))),
                "Proceso":     last.get("Proceso", ""),
                "Periodicidad":_resolver_periodicidad(
                    ids, year, last.get("Periodicidad", ""), kawak_por_año, metadatos_cmi, "semestral"
                ),
                "Sentido":     last.get("Sentido", ""),
                "fecha":       end_fecha,
                "Meta":        nan2none(pd.to_numeric(meta_agg, errors="coerce")) if meta_agg is not None else None,
                "Ejecucion":   nan2none(pd.to_numeric(ejec_agg, errors="coerce")),
                "LLAVE":       llave,
                "es_na":       False,
            })

    df_sem = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
    df_sem = df_sem.drop(
        columns=["_ids", "_sem", "_ejec_corr", "_meta_corr"], errors="ignore"
    )

    regs_std, skip_std, na_std = construir_registros_historico(
        df_sem, llaves_existentes, hist_escalas,
        config_patrones=config_patrones, mapa_procesos=mapa_procesos,
        kawak_validos=kawak_validos, extraccion_map=extraccion_map,
        api_kawak_lookup=api_kawak_lookup, variables_campo_map=variables_campo_map,
        tipo_indicador_map=tipo_indicador_map, metadatos_cmi=metadatos_cmi,
        kawak_por_año=kawak_por_año, hoja="semestral",
    )
    return regs_std + registros_agg, skip_std, na_std


# ── Cierres ───────────────────────────────────────────────────────

def construir_registros_cierres(
    df_fuente: pd.DataFrame,
    hist_escalas: Dict,
    config_patrones: Optional[Dict] = None,
    mapa_procesos: Optional[Dict] = None,
    kawak_validos: Optional[Set[Tuple[str, int]]] = None,
    extraccion_map: Optional[Dict] = None,
    api_kawak_lookup: Optional[Dict] = None,
    tipo_calculo_map: Optional[Dict] = None,
    variables_campo_map: Optional[Dict] = None,
    tipo_indicador_map: Optional[Dict] = None,
    metadatos_cmi: Optional[Dict] = None,
    kawak_por_año: Optional[Dict] = None,
) -> Tuple[List[Dict], int, int]:
    """
    Genera registros para Consolidado Cierres.

    TipoCalculo:
      Cierre    → último dic (o último mes si no hay dic)
      Promedio  → promedio de todos los meses del año
      Acumulado → suma de todos los meses del año
    """
    df = df_fuente.copy()
    df["año"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    registros: List[Dict] = []
    skipped   = 0
    conteo_na = 0

    ids_avg = {ids for ids, tc in (tipo_calculo_map or {}).items() if tc.lower() == "promedio"}
    ids_sum = {ids for ids, tc in (tipo_calculo_map or {}).items() if tc.lower() == "acumulado"}

    for (id_val, año), grupo in df.groupby(["Id", "año"]):
        id_s = _id_str(id_val)
        if kawak_validos is not None and (id_s, int(año)) not in kawak_validos:
            skipped += len(grupo)
            continue

        patron = ("AVG" if id_s in ids_avg else
                  "SUM" if id_s in ids_sum else
                  "LAST")

        if patron in ("AVG", "SUM"):
            grupo = grupo.sort_values("fecha")
            ejecs = []
            for _, r in grupo.iterrows():
                ev = _ejec_corrected_from_row(
                    r, extraccion_map, api_kawak_lookup,
                    variables_campo_map, tipo_indicador_map,
                )
                if ev is not None:
                    try:   ejecs.append(float(ev))
                    except: pass
            if not ejecs:
                skipped += 1
                continue
            ejec_agg = sum(ejecs) / len(ejecs) if patron == "AVG" else sum(ejecs)

            metas_corr = []
            for _, r in grupo.iterrows():
                mv = _meta_corrected_from_row(
                    r, extraccion_map, api_kawak_lookup,
                    variables_campo_map, tipo_indicador_map,
                )
                if mv is not None:
                    try:   metas_corr.append(float(mv))
                    except: pass
            meta_agg = (
                (sum(metas_corr) / len(metas_corr) if patron == "AVG"
                 else sum(metas_corr))
                if metas_corr else None
            )

            dic_rows = grupo[grupo["mes"] == 12]
            fecha_cierre = (dic_rows.iloc[-1]["fecha"] if len(dic_rows) > 0
                            else grupo.iloc[-1]["fecha"])
            last = grupo.iloc[-1]
            registros.append({
                "Id":          id_val,
                "Indicador":   limpiar_html(str(last.get("Indicador", ""))),
                "Proceso":     last.get("Proceso", ""),
                "Periodicidad":_resolver_periodicidad(
                    id_s, año, last.get("Periodicidad", ""), kawak_por_año, metadatos_cmi, "cierres"
                ),
                "Sentido":     last.get("Sentido", ""),
                "fecha":       fecha_cierre,
                "Meta":        meta_agg,
                "Ejecucion":   ejec_agg,
                "LLAVE":       make_llave(id_val, fecha_cierre),
                "es_na":       False,
            })
            continue

        # LAST (Cierre)
        if año > AÑO_CIERRE_ACTUAL:
            candidatos = grupo.sort_values("fecha").tail(1)
        else:
            dic = grupo[grupo["mes"] == 12]
            candidatos = (dic.sort_values("fecha").tail(1)
                          if len(dic) > 0
                          else grupo.sort_values("fecha").tail(1))

        for _, row in candidatos.iterrows():
            meta, ejec, fuente, es_na = _extraer_registro(
                row, hist_escalas,
                config_patrones=config_patrones,
                extraccion_map=extraccion_map,
                api_kawak_lookup=api_kawak_lookup,
                variables_campo_map=variables_campo_map,
                tipo_indicador_map=tipo_indicador_map,
            )
            if fuente in ("skip", "sin_resultado"):
                skipped += 1
                continue
            if es_na:
                conteo_na += 1
            registros.append({
                "Id":          id_val,
                "Indicador":   limpiar_html(str(row.get("Indicador", ""))),
                "Proceso":     row.get("Proceso", ""),
                "Periodicidad":_resolver_periodicidad(
                    id_s, año, row.get("Periodicidad", ""), kawak_por_año, metadatos_cmi, "cierres"
                ),
                "Sentido":     row.get("Sentido", ""),
                "fecha":       row["fecha"],
                "Meta":        meta,
                "Ejecucion":   ejec,
                "LLAVE":       row["LLAVE"],
                "es_na":       es_na,
            })

    return registros, skipped, conteo_na
