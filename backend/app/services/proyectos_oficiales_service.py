"""Lista oficial de proyectos del ciclo PDI 2022-2025.

Fuente de verdad confirmada con negocio (2026-09-29/30):
  - El UNIVERSO de proyectos y su línea son los del catálogo (Catalogo de
    Indicadores.xlsx, columna Proyecto=1), acotado a Id PRY-1..PRY-44 (44
    proyectos — PRY-45 en adelante son de un ciclo posterior).
  - Las CIFRAS (Meta/Ejecución/Cumplimiento) SIEMPRE vienen de Resultados
    Consolidados (hoja "Cierre PDI", con "Consolidado Cierres" como
    respaldo) — nunca del Centro de Proyectos PMO.
  - Las FECHAS (para el Gantt) y la información CUALITATIVA (objetivo,
    entregables, impactos) vienen del Centro de Proyectos PMO
    (centroDeProyectos_PMO_2026.xlsx).

El cruce entre el catálogo y las hojas de cierre/PMO es por NOMBRE
normalizado, no por Id: una migración renombró los proyectos a "PRY-XX"
en el catálogo sin propagar el cambio a "Cierre PDI" (que conserva Ids
numéricos antiguos, ej. Proyecto Silver = 908) ni completamente al PMO.
Los 16 casos donde el nombre no coincide textualmente con el PMO, y el 1
caso donde no coincide con Cierre PDI, se resolvieron a mano — ver
_ALIAS_CIERRE_ID / _ALIAS_PMO_NOMBRE abajo. No usar fuzzy-matching
automático aquí: ya produjo pares incorrectos en una iteración anterior.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd

from app.domain.resumen_builders import _ESTADO_MAP_PMO, norm_key
from app.services.etl_pipeline import ETLPipelineService
from app.services.excel_reader import ExcelReaderService
from app.services.proyectos_pmo_loader import ProyectosPmoLoader
from app.services.strategic_loaders import StrategicLoaders

PROYECTO_MAX = 44


def _norm(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^0-9a-z]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# "PRY-11" en el catálogo es "Acreditación Institucional - Fase I", pero en
# Cierre PDI el mismo proyecto está registrado con Id "10.1" y el nombre
# "Acreditación Institucional Sede Bogotá - Fase I" (no matchea por nombre).
_ALIAS_CIERRE_ID: dict[str, str] = {
    "PRY-11": "10.1",
}

# Sin cierre cargado en ninguna hoja — estado real a cierre 2025 confirmado
# con negocio 2026-09-30.
_OVERRIDE_CIFRA: dict[str, tuple[float, float]] = {
    "PRY-33": (100.0, 100.0),  # Ilumno Self Service S&P: completado
    "PRY-43": (100.0, 0.0),  # Sistema de medición de resultados de aprendizaje: en Planeación
    "PRY-44": (100.0, 0.0),  # Fortalecimiento visibilidad nacional e internacional: en Planeación
}

# La fila 901 (Centro de Idiomas Fase I) SÍ existe en Cierre PDI pero sin
# Meta/Ejecución — es un proyecto en stand by real, no un vacío de carga.
_SIN_CIFRA_STANDBY = {"PRY-17"}

# Catálogo (nombre normalizado) -> PMO (nombre normalizado), para los
# proyectos donde el nombre no coincide exacto con el Centro de Proyectos.
_ALIAS_PMO_NOMBRE: dict[str, str] = {
    _norm("Innovación curricular - Fase I"): _norm("Innovación Curricular"),
    _norm("Portal Universitario"): _norm("Portal Web Universitario"),
    _norm("Data Lake Institucional"): _norm("Datalake"),
    _norm(
        "Acreditación Institucional Sede Bogotá - Fase II - Condiciones iniciales"
    ): _norm("Acreditación Institucional Fase II"),
    _norm("Acreditación Institucional - Fase I"): _norm(
        "Acreditación Institucional Sede Bogotá-Fase I"
    ),
    _norm(
        "Creación del Instituto de Educación para el trabajo y el desarrollo humano - Stand By"
    ): _norm("Institución de educación para el trabajo y desarrollo humano IETDH"),
    _norm("Creación del colegio de educación media virtual  - Stand By"): _norm(
        "Colegio Virtual"
    ),
    _norm("Diseño del Modelo de Experiencia Institucional - Fase 2"): _norm(
        "Experiencia Institucional Fase II"
    ),
    _norm("Diseño del Modelo de Experiencia Institucional - Fase 1"): _norm(
        "Experiencia Institucional fase I"
    ),
    _norm("Experiencia Institucional - Fase 3- Hub de experiencia"): _norm(
        "Experiencia Institucional fase III - Hub de Experiencia y agilismo"
    ),
    _norm("Centro de Idiomas Fase I - Stand By"): _norm("Centro de Idiomas POLI"),
    _norm(
        "Acreditación Institucional  Fase III - Etapa de evaluación externa"
    ): _norm(
        "Acreditación Institucional fase III – Etapa de evaluación externa o evaluación por pares"
    ),
    _norm("Plataforma de gestión de la información curricular Fase I"): _norm(
        "Plataforma de gestión de información curricular Fase 1"
    ),
    _norm("Ilumno Self Service S&P"): _norm("Proyectos Ilumno Self Service S&P"),
    _norm(
        "SOPHIA Sistema de optimización y programación horaria institucional"
    ): _norm(
        "SOPHIA Sistema de Optimización y Programación Horaria Institucional Académica  I Fase"
    ),
    _norm("Modelo de seguimiento al graduado"): _norm(
        "Redefinición de Modelo de seguimiento y acompañamiento al Graduado"
    ),
}


class ProyectosOficialesService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel
        self._strategic_loaders = StrategicLoaders(excel)
        self._etl = ETLPipelineService(excel)
        self._pmo = ProyectosPmoLoader(excel)

    def _load_catalogo_44(self) -> pd.DataFrame:
        wf = self._strategic_loaders.load_worksheet_flags()
        if wf.empty or "Proyecto" not in wf.columns:
            return pd.DataFrame(columns=["Id", "Indicador", "Linea"])
        proy = wf[wf["Proyecto"].astype(str).isin(["1", "1.0", "True", "true"])][
            ["Id", "Indicador", "Linea"]
        ].copy()
        rx = re.compile(r"PRY-(\d+)", re.IGNORECASE)

        def _num(pid: str) -> int | None:
            m = rx.search(str(pid))
            return int(m.group(1)) if m else None

        proy["_num"] = proy["Id"].astype(str).apply(_num)
        proy = proy[proy["_num"].notna() & (proy["_num"] <= PROYECTO_MAX)]
        return proy.sort_values("_num").drop(columns=["_num"]).reset_index(drop=True)

    def load(self) -> pd.DataFrame:
        """Id, Indicador, Linea, Meta, Ejecucion, cumplimiento_pct, estado,
        anio_inicio, anio_fin, objetivo_proyecto, entregables, impactos —
        una fila por cada uno de los 44 proyectos oficiales del ciclo."""
        catalogo = self._load_catalogo_44()
        if catalogo.empty:
            return catalogo

        cierre_pdi = self._strategic_loaders.load_cierre_pdi_final()
        cierre_pdi["_norm"] = cierre_pdi["Indicador"].apply(_norm)
        cierre_con_dato = cierre_pdi[
            cierre_pdi["Meta"].notna() | cierre_pdi["Ejecucion"].notna()
        ]
        cierre_by_norm = cierre_con_dato.drop_duplicates("_norm", keep="last").set_index(
            "_norm"
        )
        cierre_by_id = cierre_con_dato.drop_duplicates("Id", keep="last").set_index("Id")

        cons = self._etl.leer_cierres()
        cons["_norm"] = cons["Indicador"].apply(_norm)
        cons_con_dato = cons[cons["Meta"].notna() | cons["Ejecucion"].notna()]
        cons_latest = (
            cons_con_dato.sort_values("Anio")
            .drop_duplicates("_norm", keep="last")
            .set_index("_norm")
            if not cons_con_dato.empty
            else cons_con_dato.set_index("_norm")
        )

        pmo_df = self._pmo.load()
        pmo_df["_norm"] = pmo_df["Indicador"].apply(_norm)
        pmo_by_norm = pmo_df.drop_duplicates("_norm", keep="last").set_index("_norm")

        pmo_qual = self._pmo.load_cualitativo()
        pmo_qual["_norm"] = pmo_qual["nombre"].apply(_norm)
        pmo_qual_by_norm = pmo_qual.drop_duplicates("_norm", keep="last").set_index("_norm")

        rows: list[dict[str, Any]] = []
        for _, row in catalogo.iterrows():
            pid = str(row["Id"])
            nombre = str(row["Indicador"])
            linea = str(row["Linea"])
            norm_nombre = _norm(nombre)

            meta = ejecucion = cumplimiento = None
            estado_manual: str | None = None

            if pid in _OVERRIDE_CIFRA:
                meta, ejecucion = _OVERRIDE_CIFRA[pid]
                cumplimiento = round(ejecucion / meta * 100, 1) if meta else 0.0
                if ejecucion == 0.0:
                    estado_manual = "Planeación"
            elif pid in _SIN_CIFRA_STANDBY:
                estado_manual = "Stand by"
            else:
                alias_id = _ALIAS_CIERRE_ID.get(pid)
                cierre_row = None
                if alias_id is not None and alias_id in cierre_by_id.index:
                    cierre_row = cierre_by_id.loc[alias_id]
                elif norm_nombre in cierre_by_norm.index:
                    cierre_row = cierre_by_norm.loc[norm_nombre]
                if cierre_row is not None:
                    meta = cierre_row.get("Meta")
                    ejecucion = cierre_row.get("Ejecucion")
                    cumplimiento = cierre_row.get("cumplimiento_pct")
                elif norm_nombre in cons_latest.index:
                    cons_row = cons_latest.loc[norm_nombre]
                    meta = cons_row.get("Meta")
                    ejecucion = cons_row.get("Ejecucion")
                    cumplimiento = cons_row.get("Cumplimiento")
                    if pd.notna(cumplimiento) and cumplimiento <= 2:
                        cumplimiento = cumplimiento * 100

            pmo_key = _ALIAS_PMO_NOMBRE.get(norm_nombre, norm_nombre)
            gantt_row = pmo_by_norm.loc[pmo_key] if pmo_key in pmo_by_norm.index else None
            qual_row = (
                pmo_qual_by_norm.loc[pmo_key] if pmo_key in pmo_qual_by_norm.index else None
            )

            if estado_manual:
                estado = estado_manual
            elif gantt_row is not None:
                estado_raw = str(gantt_row.get("estado") or "")
                estado = _ESTADO_MAP_PMO.get(norm_key(estado_raw), estado_raw or "Planeación")
            else:
                estado = "Sin medición"
            cumplimiento_val = (
                round(float(cumplimiento), 1)
                if cumplimiento is not None and pd.notna(cumplimiento)
                else None
            )

            rows.append(
                {
                    "Id": pid,
                    "Indicador": nombre,
                    "Linea": linea,
                    "Meta": meta if meta is not None and pd.notna(meta) else None,
                    "Ejecucion": (
                        ejecucion if ejecucion is not None and pd.notna(ejecucion) else None
                    ),
                    "cumplimiento_pct": cumplimiento_val,
                    "estado": estado,
                    "anio_inicio": (
                        int(gantt_row.get("anio_inicio"))
                        if gantt_row is not None and pd.notna(gantt_row.get("anio_inicio"))
                        else None
                    ),
                    "anio_fin": (
                        int(gantt_row.get("anio_fin"))
                        if gantt_row is not None and pd.notna(gantt_row.get("anio_fin"))
                        else None
                    ),
                    "objetivo_proyecto": (
                        str(qual_row.get("objetivo_proyecto")) if qual_row is not None else ""
                    ),
                    "entregables": str(qual_row.get("entregables")) if qual_row is not None else "",
                    "impactos": str(qual_row.get("impactos")) if qual_row is not None else "",
                }
            )

        return pd.DataFrame(rows)
