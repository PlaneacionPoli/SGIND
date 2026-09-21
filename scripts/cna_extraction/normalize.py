"""
scripts/cna_extraction/normalize.py

Fase 2 — normaliza las filas ya detectadas por structure_detector.py al
esquema objetivo de la hoja "Metricas" (Resultados_Consolidados_CNA_actualizado.xlsx):

    Id, Indicador, Subindicador, Factor, Caracteristica, Fecha, Año, Mes,
    Periodo, Ejecución, Ejecución s, Decimales, DecimalesEje, Proyecto, Llave

Reglas de negocio aplicadas aquí (todas confirmadas con el usuario o
derivadas directamente de la hoja "Metricas" existente):

- Cuando una tabla tiene subdivisiones, el valor del indicador principal
  (Subindicador=None) debe ser el TOTAL. Si la hoja ya trae una fila/columna
  Total explícita, se usa tal cual; si no la trae, se calcula como la suma
  de las subdivisiones por periodo.
- "Ejecución" (numérico) y "Ejecución s" (código de unidad ENT/DEC/%/$) son
  columnas DISTINTAS en el archivo de referencia — confirmado inspeccionando
  sus valores reales (solo 4 códigos posibles). El Anexo no etiqueta la
  unidad por celda, así que se infiere con una heurística simple y se deja
  constancia en el reporte de validación cuando la inferencia es incierta.
- Valores no numéricos (cualitativos) en indicadores que se esperaban
  cuantitativos NO se fuerzan a número (regla del usuario, sección 10): se
  cuentan y reportan, pero no se escriben en Metricas en esta iteración.
- `Llave` extiende el patrón legacy (`{Id}-{Fecha}`) a
  `{Id}|{Subindicador}|{Periodo}` porque un mismo Id ahora puede tener
  varias filas de Subindicador para el mismo periodo.
- `Id` lleva el prefijo del tipo de hoja de origen (T/G/I = Tabla/Gráfico/
  Ilustración) en vez del número pelado del Anexo. Las tres series de
  numeración del Anexo son independientes y reinician en 1, así que sin el
  prefijo "Gráfico 21" e "Ilustración 21" comparten Id=21 y sus filas se
  mezclan bajo el mismo indicador (caso real detectado: "Evolución
  Bilingüismo..." contaminado con "Medios destacados para el Poli").
"""

from __future__ import annotations

from datetime import date
from math import isclose
from typing import Any

from scripts.cna_extraction.models import CatalogRecord, SheetStructure
from scripts.cna_extraction.structure_detector import is_total_label

_MES_POR_SEMESTRE = {1: "Junio", 2: "Diciembre"}


def period_to_fecha_anio_mes(periodo: Any) -> tuple[date | None, int | None, str | None, str | None]:
    """Normaliza un periodo detectado ('YYYY', 'YYYY-1', 'YYYY-2') a
    (fecha, año, mes, periodo_normalizado). Los años sin semestre se tratan
    como cierre anual (semestre 2 / Diciembre), igual que el resto de la
    hoja Metricas existente. Periodos no reconocibles devuelven todo None
    salvo el periodo original (se conserva para trazabilidad/reporte)."""
    if periodo is None:
        return None, None, None, None

    text = str(periodo).strip()
    if "-" in text:
        anio_str, sem_str = text.split("-", 1)
        try:
            anio = int(anio_str)
            semestre = int(sem_str)
        except ValueError:
            return None, None, None, text
        if semestre not in (1, 2):
            return None, None, None, text
        mes = _MES_POR_SEMESTRE[semestre]
        dia = 30 if semestre == 1 else 31
        fecha = date(anio, 6 if semestre == 1 else 12, dia)
        return fecha, anio, mes, text

    try:
        anio = int(text)
    except ValueError:
        return None, None, None, text

    periodo_norm = f"{anio}-2"
    return date(anio, 12, 31), anio, "Diciembre", periodo_norm


_TIPO_PREFIX = {"tabla": "T", "grafico": "G", "ilustracion": "I"}


def make_id(catalog_record: CatalogRecord) -> str:
    """Id con prefijo de tipo de hoja (T/G/I) — ver nota de módulo sobre por
    qué el número pelado del Anexo no es único entre Tabla/Gráfico/
    Ilustración."""
    prefix = _TIPO_PREFIX.get(catalog_record.tipo, "")
    return f"{prefix}{catalog_record.numero}"


def make_llave(id_: str, subindicador: str | None, periodo: str | None) -> str:
    return f"{id_}|{subindicador or ''}|{periodo or ''}"


def infer_ejecucion(value: Any) -> tuple[float | None, str | None, bool]:
    """Separa el valor crudo en (Ejecución numérica, Ejecución s = código de
    unidad inferido, es_cualitativo). Solo infiere entre ENT/DEC/% — no hay
    forma de distinguir '$' sin contexto adicional de la hoja, así que se
    deja ENT/DEC como heurística conservadora (ver reporte de validación
    para los casos límite: proporciones 0-1 se marcan '%')."""
    if value is None:
        return None, None, False
    if isinstance(value, bool):
        return None, None, True
    if isinstance(value, (int, float)):
        if isinstance(value, int) or float(value).is_integer():
            return float(value), "ENT", False
        if 0 < value <= 1:
            return float(value), "%", False
        return float(value), "DEC", False

    text = str(value).strip()
    cleaned = text.replace("$", "").replace("%", "").replace(",", "").strip()
    try:
        parsed = float(cleaned)
    except ValueError:
        return None, None, True

    if "%" in text:
        return parsed, "%", False
    if "$" in text:
        return parsed, "$", False
    if parsed.is_integer():
        return parsed, "ENT", False
    return parsed, "DEC", False


def infer_decimales(ejecucion: float | None, unidad: str | None) -> tuple[int, int]:
    if ejecucion is None:
        return 0, 0
    if unidad == "%":
        return 2, 0
    if unidad == "DEC":
        return 2, 2
    return 0, 0


def _reclasifica_totales_sin_etiqueta(
    detector_rows: list[dict[str, Any]], stats: dict[str, int]
) -> list[dict[str, Any]]:
    """Una fila de datos sin etiqueta propia (`category_ambiguous`) puede ser el
    TOTAL de la hoja con la celda de etiqueta vacía (Gráfico 1/2, Tabla 133).
    Dejarla como categoría "(sin etiqueta #1)" duplicaba el dato: aparecía como
    una categoría más y además se sintetizaba un total que la volvía a sumar.

    Se valida contra los datos: si en todos los periodos comparables su valor
    es igual a la suma de las filas de detalle etiquetadas, es el total y se
    reclasifica como `total_explicito` (Subindicador vacío); si la hoja ya trae
    un Total explícito para ese periodo se omite por redundante. Si NO coincide
    con la suma (Gráfico 19, Tabla 133) tampoco es una categoría utilizable:
    no tiene nombre y repite datos, así que se OMITE (decisión de negocio
    2026-09-21) y solo cuenta el Total. Antes se conservaba como
    "(sin etiqueta #n)" y sumaba de más en el consolidado."""
    suma_detalle: dict[str, float] = {}
    periodos_con_total: set[str] = set()
    for row in detector_rows:
        ejecucion, _, cualitativo = infer_ejecucion(row["value"])
        if ejecucion is None or cualitativo or not row["period"]:
            continue
        if row["row_kind"] == "total_explicito":
            periodos_con_total.add(row["period"])
        elif not row.get("category_ambiguous"):
            suma_detalle[row["period"]] = suma_detalle.get(row["period"], 0.0) + ejecucion

    puntos: dict[tuple[str, ...], list[tuple[str, float]]] = {}
    for row in detector_rows:
        if not row.get("category_ambiguous") or not row["period"]:
            continue
        ejecucion, _, cualitativo = infer_ejecucion(row["value"])
        if ejecucion is not None and not cualitativo:
            puntos.setdefault(tuple(map(str, row["category_path"])), []).append((row["period"], ejecucion))

    es_total = {
        clave
        for clave, pts in puntos.items()
        if all(p in suma_detalle and isclose(v, suma_detalle[p], rel_tol=1e-9, abs_tol=1e-9) for p, v in pts)
    }
    resultado: list[dict[str, Any]] = []
    for row in detector_rows:
        if row.get("category_ambiguous"):
            if tuple(map(str, row["category_path"])) not in es_total:
                stats["filas_sin_etiqueta_omitidas"] = stats.get("filas_sin_etiqueta_omitidas", 0) + 1
                continue
            stats["totales_sin_etiqueta_reclasificados"] = stats.get("totales_sin_etiqueta_reclasificados", 0) + 1
            if row["period"] in periodos_con_total:
                continue  # la hoja ya trae el Total explícito de ese periodo
            row = {**row, "row_kind": "total_explicito", "category_ambiguous": False}
        resultado.append(row)
    return resultado


def _build_from_generic_rows(
    detector_rows: list[dict[str, Any]],
    catalog_record: CatalogRecord,
    stats: dict[str, int],
) -> list[dict[str, Any]]:
    id_ = make_id(catalog_record)
    indicador = catalog_record.nombre
    detector_rows = _reclasifica_totales_sin_etiqueta(detector_rows, stats)

    detalle_by_period: dict[str, list[tuple[list[Any], float]]] = {}
    total_periods_present: set[str] = set()
    records: list[dict[str, Any]] = []

    for row in detector_rows:
        category_path = row["category_path"]
        periodo_raw = row["period"]
        ejecucion, unidad, es_cualitativo = infer_ejecucion(row["value"])

        if row.get("category_ambiguous"):
            stats["filas_sin_etiqueta_categoria"] = stats.get("filas_sin_etiqueta_categoria", 0) + 1

        if es_cualitativo:
            stats["valores_cualitativos_no_convertidos"] += 1
            continue
        if ejecucion is None:
            continue  # celda vacía, no es un dato a reportar

        subindicador = None if row["row_kind"] == "total_explicito" else _join_category_path(category_path)
        fecha, anio, mes, periodo = period_to_fecha_anio_mes(periodo_raw)
        decimales, decimales_eje = infer_decimales(ejecucion, unidad)

        records.append(
            {
                "Id": id_,
                "Indicador": indicador,
                "Subindicador": subindicador,
                "Factor": catalog_record.factor_raw,
                "Caracteristica": catalog_record.caracteristica,
                "Proceso": None,
                "Periodicidad": None,
                "Sentido": None,
                "Fecha": fecha,
                "Año": anio,
                "Mes": mes,
                "Periodo": periodo,
                "Meta": None,
                "Ejecución": ejecucion,
                "Ejecución s": unidad,
                "Decimales": decimales,
                "DecimalesEje": decimales_eje,
                "Proyecto": None,
                "Llave": make_llave(id_, subindicador, periodo),
                "Fuente": catalog_record.fuente.strip() or None,
            }
        )

        if row["row_kind"] == "total_explicito" and periodo:
            total_periods_present.add(periodo)
        elif row["row_kind"] == "detalle" and periodo:
            detalle_by_period.setdefault(periodo, []).append((category_path, ejecucion))

    # Regla de negocio: si hay subdivisiones sin Total explícito para un
    # periodo dado, el indicador principal se calcula como suma de detalle.
    # Con una sola categoría el "total" sería una copia exacta de esa fila (el
    # dashboard lo sumaba dos veces), así que no se sintetiza.
    categorias = {tuple(map(str, path)) for entries in detalle_by_period.values() for path, _ in entries}
    for periodo, entries in detalle_by_period.items():
        if periodo in total_periods_present or len(categorias) < 2:
            continue
        total_value = sum(v for _, v in entries)
        fecha, anio, mes, periodo_norm = period_to_fecha_anio_mes(periodo)
        decimales, decimales_eje = infer_decimales(total_value, "DEC" if not float(total_value).is_integer() else "ENT")
        records.append(
            {
                "Id": id_,
                "Indicador": indicador,
                "Subindicador": None,
                "Factor": catalog_record.factor_raw,
                "Caracteristica": catalog_record.caracteristica,
                "Proceso": None,
                "Periodicidad": None,
                "Sentido": None,
                "Fecha": fecha,
                "Año": anio,
                "Mes": mes,
                "Periodo": periodo_norm,
                "Meta": None,
                "Ejecución": total_value,
                "Ejecución s": "ENT" if float(total_value).is_integer() else "DEC",
                "Decimales": decimales,
                "DecimalesEje": decimales_eje,
                "Proyecto": None,
                "Llave": make_llave(id_, None, periodo_norm),
                "Fuente": catalog_record.fuente.strip() or None,
            }
        )
        stats["totales_calculados_por_suma"] += 1

    return records


def _join_category_path(category_path: list[Any]) -> str | None:
    parts = [str(c) for c in category_path if c is not None and not is_total_label(c)]
    return " - ".join(parts) if parts else None


def build_metricas_rows(
    structure: SheetStructure,
    catalog_record: CatalogRecord,
    stats: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """Convierte SheetStructure.rows al esquema de la hoja Metricas.
    `stats` (opcional) acumula contadores para el reporte de validación de
    Fase 2 (valores cualitativos descartados, totales calculados por suma)."""
    if stats is None:
        stats = {
            "valores_cualitativos_no_convertidos": 0,
            "totales_calculados_por_suma": 0,
            "filas_sin_etiqueta_categoria": 0,
        }

    if structure.kind in ("unresolved", "event_log_atypical"):
        return []

    return _build_from_generic_rows(structure.rows, catalog_record, stats)
