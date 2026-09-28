"""Cargador del Centro de Proyectos PMO — fuente OFICIAL de proyectos para
el cronograma "PROYECTOS PMO" del Informe Ejecutivo y de la hoja de línea
(Comienzo/Fin/% completado reales por proyecto), distinta de
Cierres/Consolidado (build_proyectos_gantt), que solo cubre proyectos con
cierre cargado. Confirmado con negocio, 2026-09-27.

Produce las columnas que build_proyectos_pmo_gantt (resumen_builders.py)
espera: Id, Indicador, Linea, anio_inicio, anio_fin, cumplimiento_pct,
estado.

cumplimiento_pct evalúa avance real frente a avance ESPERADO a la fecha
(igual que Retos), no el avance ejecutado a secas — confirmado con negocio,
2026-09-28. Prioridad por proyecto (ver _cumplimiento_consolidado_por_nombre):
  1. Resultados Consolidados (Meta/Ejecución del cierre oficial más
     reciente, vía StrategicLoaders.load_cierres filtrado a Ids PRY-*)
     cuando el proyecto tiene cierre cargado ahí — es la cifra auditada.
  2. "Ind. cumplimiento PWA" del propio Centro de Proyectos (% completado /
     % Esperado centro de proyectos) cuando el proyecto no tiene cierre en
     Resultados Consolidados — cubre a los que solo viven en el PMO (ej.
     PRICING, Proyecto Silver).
  3. "% completado" crudo si ninguna de las dos anteriores viene poblada.
Confirmado con negocio, 2026-09-28: Resultados Consolidados no cubre todo
el maestro PMO (por eso PMO es la fuente oficial de QUÉ proyectos y sus
fechas), pero cuando SÍ trae un proyecto, su Cumplimiento (Ejecución/Meta)
es la cifra oficial, no el "% completado" ni el PWA calculados aparte."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

from app.services.excel_reader import ExcelReaderService
from app.services.strategic_loaders import StrategicLoaders

PMO_PATH = "raw/Proyectos/centroDeProyectos_PMO_2026.xlsx"
PMO_SHEET = "centroDeProyectos"

_COLS = {
    "Nombre del proyecto": "Indicador",
    "0. Estado del proyecto": "estado",
    "% completado": "_pct_completado",
    "Ind. cumplimiento PWA": "cumplimiento_pct",
    "4. Líneas estratégicas": "Linea",
    "Comienzo": "_fecha_inicio",
    "Fin": "_fecha_fin",
}

_SUFIJOS_NOMBRE = (" stand by", " - stand by")


def _norm_nombre(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^0-9a-z]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for sufijo in _SUFIJOS_NOMBRE:
        sufijo_norm = re.sub(r"[^0-9a-z]+", " ", sufijo).strip()
        if text.endswith(sufijo_norm):
            text = text[: -len(sufijo_norm)].strip()
    return text


_OUT_COLS = ["Id", "Indicador", "Linea", "anio_inicio", "anio_fin", "cumplimiento_pct", "estado"]


def _parse_pct(value) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, int | float):
        num = float(value)
        return round(num * 100, 1) if num <= 1 else round(num, 1)
    text = str(value).strip().replace("%", "").replace(",", ".")
    try:
        return round(float(text), 1)
    except ValueError:
        return None


def _parse_fecha(value) -> pd.Timestamp | None:
    if pd.isna(value) or value in ("", None):
        return None
    if isinstance(value, pd.Timestamp):
        return value
    try:
        parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
        return None if pd.isna(parsed) else parsed
    except (ValueError, TypeError):
        return None


class ProyectosPmoLoader:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel
        self._strategic_loaders = StrategicLoaders(excel)

    def _exists(self) -> bool:
        return (self._excel.data_root / PMO_PATH).exists()

    def _cumplimiento_consolidado_por_nombre(self) -> dict[str, float]:
        """nombre normalizado -> cumplimiento_pct (Ejecución/Meta) del cierre
        MÁS RECIENTE en Resultados Consolidados, solo para Ids de proyecto
        (PRY-*). Ausente para proyectos que solo viven en el PMO."""
        # load_proyectos() reescribe Indicador con el nombre del catálogo CMI
        # (p.ej. PRY-36 -> "Hubspot CRM"), que ya no calza con el nombre del
        # PMO ("Implementación de Hubspot Eduvida"). load_cierres() trae el
        # Indicador tal como viene en la hoja "Consolidado Cierres" — se
        # filtra aquí a Ids de proyecto (PRY-*) en vez de usar
        # load_proyectos_consolidados(), que hoy no encuentra esa hoja en
        # raw/Resultados_Consolidados_Fuente.xlsx (solo tiene "Catalogo
        # Indicadores") y devuelve vacío.
        consolidado = self._strategic_loaders.load_cierres()
        if (
            consolidado.empty
            or "Id" not in consolidado.columns
            or "Indicador" not in consolidado.columns
            or "cumplimiento_pct" not in consolidado.columns
        ):
            return {}
        consolidado = consolidado[consolidado["Id"].astype(str).str.startswith("PRY-")]
        work = consolidado.dropna(subset=["cumplimiento_pct"]).copy()
        if work.empty:
            return {}
        work["_nombre_norm"] = work["Indicador"].apply(_norm_nombre)
        work = work[work["_nombre_norm"] != ""]
        if "Fecha" in work.columns:
            work = work.sort_values("Fecha", na_position="first")
        return (
            work.drop_duplicates(subset=["_nombre_norm"], keep="last")
            .set_index("_nombre_norm")["cumplimiento_pct"]
            .to_dict()
        )

    def load(self) -> pd.DataFrame:
        """Id, Indicador, Linea, anio_inicio, anio_fin, cumplimiento_pct,
        estado — una fila por proyecto del Centro de Proyectos PMO
        (raw/Proyectos/centroDeProyectos_PMO_2026.xlsx)."""
        empty = pd.DataFrame(columns=_OUT_COLS)
        if not self._exists():
            return empty
        try:
            df = self._excel.read_excel(PMO_PATH, sheet_name=PMO_SHEET)
        except Exception:
            return empty
        df.columns = [str(c).strip() for c in df.columns]
        available = {src: dst for src, dst in _COLS.items() if src in df.columns}
        if "Nombre del proyecto" not in available:
            return empty

        out = df[list(available.keys())].rename(columns=available)
        out = out[
            out["Indicador"].notna() & (out["Indicador"].astype(str).str.strip() != "")
        ].copy()
        out = out.reset_index(drop=True)
        out["Id"] = [f"PMO-{i + 1}" for i in range(len(out))]
        out["Indicador"] = out["Indicador"].astype(str).str.strip()
        out["Linea"] = out["Linea"].apply(lambda v: str(v).strip() if pd.notna(v) else "")
        out["estado"] = out["estado"].apply(lambda v: str(v).strip() if pd.notna(v) else "")

        # cumplimiento_pct: Resultados Consolidados (Ejecución/Meta del
        # cierre oficial) > "Ind. cumplimiento PWA" del PMO > "% completado"
        # crudo — ver docstring del módulo.
        pwa_pct = (
            out["cumplimiento_pct"].apply(_parse_pct)
            if "cumplimiento_pct" in out.columns
            else pd.Series([None] * len(out), index=out.index)
        )
        pct_completado = (
            out["_pct_completado"].apply(_parse_pct)
            if "_pct_completado" in out.columns
            else pd.Series([None] * len(out), index=out.index)
        )
        cumplimiento_consolidado = self._cumplimiento_consolidado_por_nombre()
        consolidado_pct = out["Indicador"].apply(
            lambda nombre: cumplimiento_consolidado.get(_norm_nombre(nombre))
        )
        out["cumplimiento_pct"] = consolidado_pct.combine_first(pwa_pct).combine_first(
            pct_completado
        )

        fecha_inicio = out["_fecha_inicio"].apply(_parse_fecha)
        fecha_fin = out["_fecha_fin"].apply(_parse_fecha)
        anio_inicio: list[int | None] = []
        anio_fin: list[int | None] = []
        for fi, ff in zip(fecha_inicio, fecha_fin, strict=True):
            ai = int(fi.year) if fi is not None else None
            af = int(ff.year) if ff is not None else ai
            ai = ai if ai is not None else af
            if ai is not None and af is not None and af < ai:
                ai, af = af, ai
            anio_inicio.append(ai)
            anio_fin.append(af)
        out["anio_inicio"] = anio_inicio
        out["anio_fin"] = anio_fin
        out = out[out["anio_inicio"].notna() & out["anio_fin"].notna()].copy()
        out["anio_inicio"] = out["anio_inicio"].astype(int)
        out["anio_fin"] = out["anio_fin"].astype(int)

        # Confirmado con negocio 2026-09-27: el Informe Ejecutivo solo debe
        # contar proyectos del Centro de Proyectos que INICIARON dentro del
        # horizonte 2021-2025 (excluye proyectos formulados antes del ciclo
        # PDI actual o que arrancan ya en el siguiente ciclo, 2026+).
        out = out[out["anio_inicio"].between(2021, 2025)]

        return out[_OUT_COLS].reset_index(drop=True)

    def load_cualitativo(self) -> pd.DataFrame:
        """Columnas narrativas del Centro de Proyectos (Entregables, Impactos
        Generados, Riesgos, Objetivo del proyecto) para la triangulación
        cualitativa del Informe Estratégico — separado de load() para no
        tocar el shape que build_proyectos_pmo_gantt ya usa en producción."""
        cols = {
            "Nombre del proyecto": "nombre",
            "0. Estado del proyecto": "estado",
            "% completado": "pct_completado",
            "4. Líneas estratégicas": "linea",
            "Objetivo del proyecto": "objetivo_proyecto",
            "Entregables": "entregables",
            "Impactos Generados": "impactos",
            "Riesgos": "riesgos",
        }
        empty = pd.DataFrame(columns=list(cols.values()))
        if not self._exists():
            return empty
        try:
            df = self._excel.read_excel(PMO_PATH, sheet_name=PMO_SHEET)
        except Exception:
            return empty
        df.columns = [str(c).strip() for c in df.columns]
        available = {src: dst for src, dst in cols.items() if src in df.columns}
        if "Nombre del proyecto" not in available:
            return empty
        out = df[list(available.keys())].rename(columns=available)
        out = out[out["nombre"].notna() & (out["nombre"].astype(str).str.strip() != "")].copy()
        out["pct_completado"] = out["pct_completado"].apply(_parse_pct)
        for c in out.columns:
            if c == "pct_completado":
                continue
            out[c] = out[c].apply(lambda v: str(v).strip() if pd.notna(v) else "")
        return out.reset_index(drop=True)
