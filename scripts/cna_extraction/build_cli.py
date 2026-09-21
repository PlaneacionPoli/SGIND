"""
scripts/cna_extraction/build_cli.py

Entrypoint de la Fase 2: recorre el catálogo + detector de estructura,
normaliza al esquema de Metricas y escribe en
data/output/Resultados_Consolidados_CNA.xlsx (nunca en data/raw/).

Deliberadamente separado de cli.py (Fase 1, solo diagnóstico) para que el
límite de "Fase 1 no escribe nada" siga siendo válido sin tocar ese módulo.

Uso:
    python -m scripts.cna_extraction.build_cli --write     # incremental, agrega solo lo nuevo
    python -m scripts.cna_extraction.build_cli --rebuild   # reconstruye el consolidado desde cero
    python -m scripts.cna_extraction.build_cli --backfill-fuente  # solo completa la columna Fuente
    python -m scripts.cna_extraction.build_cli --refresh-ids T3   # reprocesa solo esas tablas/gráficos
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import openpyxl

from core.config import DATA_RAW
from scripts.cna_extraction.catalog import build_factor_caracteristica_rows, load_catalog
from scripts.cna_extraction.normalize import build_metricas_rows, make_id
from scripts.cna_extraction.sheet_resolver import resolve_sheets
from scripts.cna_extraction.structure_detector import detect_structure
from scripts.cna_extraction.writer import OUTPUT_FILE, backfill_fuente, replace_ids, write_full, write_incremental
from scripts.etl.audit import AuditTrail

DEFAULT_SOURCE = DATA_RAW / "Plan de mejoramiento" / "Anexo Estadístico Dcto. Autoevaluacion.xlsx"


def build_records(
    xlsx_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, str]], list[str], list[str]]:
    """Devuelve (records, stats, factor_caracteristica_rows, hojas_sin_catalogo,
    catalogo_sin_hoja).

    El número de tablas/gráficos del Anexo Estadístico NO es estático — cambia
    de un año a otro (tablas nuevas, renumeradas o retiradas). `resolve_sheets`
    ya detecta ambos tipos de desajuste sin asumir una cantidad fija, pero
    hasta ahora esta función los descartaba en silencio (`continue` sin
    registrar nada) — el reporte de diagnóstico de Fase 1 sí los mostraba,
    pero Fase 2 (la que realmente alimenta el consolidado de producción) no
    dejaba ningún rastro si alguien la corría directamente. Ahora ambos casos
    se devuelven explícitamente para que `main()` los reporte y queden en el
    audit trail — un desajuste silencioso aquí significa indicadores faltantes
    en el dashboard sin ninguna alerta.
    """
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    try:
        catalog = load_catalog(xlsx_path)
        resolved, hojas_sin_catalogo = resolve_sheets(catalog, wb)
        stats = {
            "valores_cualitativos_no_convertidos": 0,
            "totales_calculados_por_suma": 0,
            "filas_sin_etiqueta_categoria": 0,
            "totales_sin_etiqueta_reclasificados": 0,
            "filas_sin_etiqueta_omitidas": 0,
            "valores_separador_de_miles_corregidos": 0,
            "filas_resumen_omitidas": 0,
        }
        all_records: list[dict[str, Any]] = []
        catalogo_sin_hoja: list[str] = []

        for item in resolved:
            if item.catalog_record is None:
                continue  # ya contabilizado en hojas_sin_catalogo
            if item.sheet_name is None:
                catalogo_sin_hoja.append(item.catalog_record.id_hint or item.catalog_record.nombre)
                continue
            ws = wb[item.sheet_name]
            raw_rows = [list(row) for row in ws.iter_rows(values_only=True)]
            structure = detect_structure(raw_rows, item.catalog_record.numero)
            all_records.extend(build_metricas_rows(structure, item.catalog_record, stats))

        factor_caracteristica_rows = build_factor_caracteristica_rows(catalog)
        return all_records, stats, factor_caracteristica_rows, hojas_sin_catalogo, catalogo_sin_hoja
    finally:
        wb.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fase 2 — construye/actualiza el consolidado CNA en data/output/ (incremental)."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--write",
        action="store_true",
        help="Escritura incremental: agrega solo registros nuevos (por Llave), preserva los existentes.",
    )
    mode.add_argument(
        "--rebuild",
        action="store_true",
        help="Reescribe el consolidado desde cero a partir del Anexo (descarta filas existentes). "
        "Usar tras un fix de extracción, no como corrida periódica.",
    )
    mode.add_argument(
        "--backfill-fuente",
        action="store_true",
        help="Completa la columna Fuente del consolidado existente desde 'Índice Tablas' (por Id), "
        "sin agregar ni quitar filas.",
    )
    mode.add_argument(
        "--refresh-ids",
        nargs="+",
        metavar="ID",
        help="Reprocesa solo los Ids indicados (T3, G2, I5…) desde el Anexo y reemplaza sus filas en el "
        "consolidado, sin tocar el resto. Usar cuando cambió el layout de esas tablas.",
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Ruta al Anexo Estadístico.")
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE, help="Archivo de salida (data/output/).")
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"No se encontró el archivo fuente: {args.source}")

    if args.backfill_fuente:
        fuente_by_id = {
            make_id(rec): rec.fuente.strip()
            for rec in load_catalog(args.source)
            if rec.numero is not None and rec.fuente.strip()
        }
        result = backfill_fuente(fuente_by_id, args.output)
        print(f"Archivo de salida: {args.output}")
        print(f"Filas: {result['filas']} | con Fuente: {result['filas_con_fuente']} | Ids sin Fuente en el catálogo: {result['ids_sin_fuente']}")
        return

    records, stats, factor_caracteristica_rows, hojas_sin_catalogo, catalogo_sin_hoja = build_records(
        args.source
    )
    if args.refresh_ids:
        ids = {i.strip().upper() for i in args.refresh_ids}
        records = [r for r in records if str(r["Id"]).upper() in ids]
        if not records:
            raise SystemExit(f"El Anexo no produjo filas para {sorted(ids)}; no se modificó el consolidado.")
        result = replace_ids(records, ids, args.output, factor_caracteristica_rows=factor_caracteristica_rows)
        print(f"Archivo de salida: {args.output}")
        print(f"Ids reprocesados: {', '.join(sorted(ids))}")
        print(f"Filas reemplazadas: {result['filas_reemplazadas']} -> nuevas: {result['filas_nuevas']}")
        print(f"Registros totales tras la corrida: {result['registros_totales']}")
        return
    writer_fn = write_full if args.rebuild else write_incremental
    result = writer_fn(records, args.output, factor_caracteristica_rows=factor_caracteristica_rows)

    try:
        AuditTrail().registrar_ejecucion(
            evento="rebuild_consolidado_cna" if args.rebuild else "build_consolidado_cna",
            detalles={
                **result,
                **stats,
                "archivo_salida": str(args.output),
                "hojas_sin_catalogo": hojas_sin_catalogo,
                "catalogo_sin_hoja": catalogo_sin_hoja,
            },
            exitoso=True,
        )
    except Exception:
        pass

    print(f"Archivo de salida: {args.output}")
    print(f"Registros existentes antes de esta corrida: {result['registros_existentes']}")
    print(f"Registros nuevos insertados: {result['registros_nuevos_insertados']}")
    print(f"Registros totales tras la corrida: {result['registros_totales']}")
    print(f"Valores cualitativos no convertidos: {stats['valores_cualitativos_no_convertidos']}")
    print(f"Totales calculados por suma de subdivisiones: {stats['totales_calculados_por_suma']}")
    print(f"Filas sin etiqueta de categoría (desambiguadas, revisar manualmente): {stats['filas_sin_etiqueta_categoria']}")
    print(f"Filas sin etiqueta que eran el Total (reclasificadas/omitidas): {stats['totales_sin_etiqueta_reclasificados']}")
    print(f"Filas sin etiqueta que no eran el Total (omitidas): {stats['filas_sin_etiqueta_omitidas']}")
    print(f"Filas de resumen (%Part/Ingreso, Subtotal) omitidas en tablas de inversión: {stats['filas_resumen_omitidas']}")
    print(f"Valores con separador de miles leído como decimal (corregidos, validados con el Total): {stats['valores_separador_de_miles_corregidos']}")

    # El número de tablas/indicadores del Anexo Estadístico cambia con el
    # tiempo — esto NO se puede asumir estático de un año a otro. Estos dos
    # avisos son la señal de que el catálogo ("Índice Tablas") y el workbook
    # real se desalinearon y algún indicador puede estar faltando en el
    # consolidado. No se detiene la corrida (el resto de indicadores sigue
    # siendo válido), pero debe revisarse manualmente antes de confiar en el
    # resultado como completo.
    if hojas_sin_catalogo:
        print(
            f"\n[AVISO] {len(hojas_sin_catalogo)} hoja(s) del workbook SIN registro en el catálogo "
            f"'Índice Tablas' (no se extrajeron sus datos): {', '.join(hojas_sin_catalogo)}"
        )
    if catalogo_sin_hoja:
        print(
            f"[AVISO] {len(catalogo_sin_hoja)} indicador(es) del catálogo SIN hoja correspondiente en el "
            f"workbook (no se extrajeron sus datos): {', '.join(catalogo_sin_hoja)}"
        )


if __name__ == "__main__":
    main()
