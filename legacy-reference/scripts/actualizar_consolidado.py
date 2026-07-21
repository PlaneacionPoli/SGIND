"""
scripts/actualizar_consolidado.py
Versión 8 — Orquestador principal del ETL.
Toda la lógica de negocio vive en scripts/etl/.
Este archivo contiene SOLO el flujo main() y las importaciones.

REQUISITO: ejecutar primero  python scripts/consolidar_api.py
  → genera data/raw/Fuentes Consolidadas/Indicadores Kawak.xlsx
  → genera data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx

═══════════════════════════════════════════════════════════════════════
QUÉ ES "No Aplica":
  Un indicador marca "No Aplica" cuando NO corresponde medirlo en ese
  período específico (por diseño, estacionalidad, fase del proyecto, etc.)
  No es un dato faltante ni un error: es una decisión explícita.

CÓMO SE DETECTA en la fuente API:
  1. El campo 'analisis' contiene el texto "no aplica" → es_na = True
  2. resultado=NaN  Y  sin datos en variables/series → es_na = True

CÓMO SE ESCRIBE en el consolidado:
  - Col K  (Ejecucion)        → None  (celda vacía)
  - Col O  (Ejecucion_Signo)  → "No Aplica"
  - Col L  (Cumplimiento)     → ""  via fórmula
  - Col J  (Meta)             → se conserva si existe, None si no
═══════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
import shutil
import sys
import tempfile
import warnings
from datetime import datetime
from pathlib import Path
from typing import Tuple

import openpyxl
import pandas as pd

warnings.filterwarnings("ignore")

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import consolidar_api  # noqa: E402  — regenera Consolidado_API_Kawak.xlsx / Indicadores Kawak.xlsx

# ── ETL modules ───────────────────────────────────────────────────
from etl.config import (  # noqa: E402
    AÑO_CIERRE_ACTUAL, OUTPUT_FILE, OUTPUT_DIR,
    SERIES_SUBINDICADORES_MAP, CRONOGRAMA_SERIES_FLAT,
)
from etl.normalizacion import _id_str  # noqa: E402
from etl.validation_gate import validar_consolidado_api_entrada  # noqa: E402
from etl.agent5_corrections import AGENT5Corrections  # noqa: E402
from etl.fuentes import (                          # noqa: E402
    cargar_fuente_consolidada,
    cargar_kawak_validos,
    cargar_metadatos_kawak,
    cargar_metadatos_cmi,
    cargar_mapa_procesos,
    cargar_lmi_reporte,
    cargar_consolidado_api_kawak_lookup,
    cargar_periodicidad_kawak_por_año,
)
from etl.catalogo import (                         # noqa: E402
    cargar_catalogo_completo,
    cargar_config_patrones,     # noqa: F401  re-export usado por orchestrator
    construir_catalogo,
)
from etl.signos import obtener_signos                          # noqa: E402
from etl.formulas_excel import (                               # noqa: E402
    _reescribir_formulas,
    _materializar_formula_año,
    _materializar_cumplimiento,
    _ensure_tipo_registro_header,
)
from etl.escritura import (                        # noqa: E402
    llaves_de_df, deduplicar_sheet, escribir_filas, escribir_hoja_nueva,
    worksheet_a_dataframe,
)
from etl.purga import (                            # noqa: E402
    purgar_filas_invalidas,
    limpiar_cierres_existentes,
    _dedup_cierres_por_año,
    reparar_meta_vacia,
    reparar_multiserie,
    reparar_semestral_agregados,
    reparar_desglose_variables,
    reparar_metas_fijas,
)
from etl.builders import (                         # noqa: E402
    construir_registros_historico,
    construir_registros_semestral,
    construir_registros_cierres,
    expandir_series_como_subindicadores,
    extraer_cronograma_proyectos,
    construir_registros_poblacion,
)
from etl.workbook_io import workbook_local_copy   # noqa: E402
from etl.versioning import VersionManager         # noqa: E402
from etl.audit import AuditTrail                  # noqa: E402
from etl.retry_handler import retry_pipeline      # noqa: E402
from etl.notifications import EmailNotifier         # noqa: E402
from etl.intermediate_validation import (          # noqa: E402
    validate_after_build_records,
    validate_before_write,
    log_validation_result,
)
from etl.pipeline_metrics import MetricsCollector   # noqa: E402

# ── Logging ───────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


def apply_agent5_corrections_to_registros(
    regs_hist: list, regs_sem: list, regs_cierres: list, trail, logger
) -> Tuple[list, list, list, dict]:
    """
    Aplicar correcciones AGENT 5 a los registros antes de escribir.

    HALLAZGOS CRÍTICOS:
    1. Ejecución > 1.3 → Capping automático
    2. Meta = 0 → Flagging para revisión

    Args:
        regs_hist: Lista de dicts (registro histórico)
        regs_sem: Lista de dicts (registro semestral)
        regs_cierres: Lista de dicts (registro cierres)
        trail: AuditTrail para registrar cambios
        logger: Logger para mensajes

    Returns:
        Tuple (regs_hist_corregido, regs_sem_corregido, regs_cierres_corregido, reporte_correcciones)
    """
    logger.info("🔧 Aplicando correcciones AGENT 5 (hallazgos críticos)…")

    reporte_total = {
        "historico": {"ejecucion_capping": 0, "meta_validaciones": 0},
        "semestral": {"ejecucion_capping": 0, "meta_validaciones": 0},
        "cierres": {"ejecucion_capping": 0, "meta_validaciones": 0},
    }

    # Procesar cada conjunto de registros
    for nombre_hoja, regs in [
        ("Historico", regs_hist),
        ("Semestral", regs_sem),
        ("Cierres", regs_cierres),
    ]:
        if not regs:
            logger.info(f"   {nombre_hoja}: sin registros, omitiendo")
            continue

        # Convertir lista de dicts a DataFrame
        df_temp = pd.DataFrame(regs)

        # Aplicar correcciones
        df_corregido, reporte_correcciones = AGENT5Corrections.apply_all_corrections(df_temp)

        # Registrar hallazgos en audit trail
        if reporte_correcciones.get("ejecucion_capping", 0) > 0:
            trail.registrar_cambio_datos(
                tipo_cambio="corrección_crítica",
                tabla=f"Consolidado {nombre_hoja}",
                registros_afectados=reporte_correcciones["ejecucion_capping"],
                descripcion=f"Capping ejecución > 1.3 a máximo 1.3",
                usuario="etl_agent5",
            )
            logger.warning(
                f"   ⚠️  {nombre_hoja}: {reporte_correcciones['ejecucion_capping']} "
                "registros con ejecución capeada"
            )

        if reporte_correcciones.get("meta_zero_count", 0) > 0:
            trail.registrar_cambio_datos(
                tipo_cambio="validación_crítica",
                tabla=f"Consolidado {nombre_hoja}",
                registros_afectados=reporte_correcciones["meta_zero_count"],
                descripcion=f"Detectados {reporte_correcciones['meta_zero_count']} registros con meta=0 (requiere revisión)",
                usuario="etl_agent5",
            )
            logger.error(
                f"   🔴 {nombre_hoja}: {reporte_correcciones['meta_zero_count']} "
                "registros con META=0 detectados (revisar manualmente)"
            )

        # Convertir DataFrame corregido de vuelta a lista de dicts
        regs_corregidos = df_corregido.to_dict(orient="records")

        # Actualizar referencia (aunque sea local, se retorna)
        if nombre_hoja == "Historico":
            regs_hist = regs_corregidos
            reporte_total["historico"] = reporte_correcciones
        elif nombre_hoja == "Semestral":
            regs_sem = regs_corregidos
            reporte_total["semestral"] = reporte_correcciones
        elif nombre_hoja == "Cierres":
            regs_cierres = regs_corregidos
            reporte_total["cierres"] = reporte_correcciones

    logger.info("✅ Correcciones AGENT 5 aplicadas")
    return regs_hist, regs_sem, regs_cierres, reporte_total


logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────

@retry_pipeline(max_attempts=3, initial_wait=2.0, max_wait=60.0)
def main() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%H:%M:%S",
        )

    logger.info("=" * 65)
    logger.info("  ACTUALIZAR CONSOLIDADO  —  Año cierre: %s", AÑO_CIERRE_ACTUAL)
    logger.info("=" * 65)
    
    # ── 0. INICIAR MÉTRICAS ────────────────────────────────────────
    metrics_collector = MetricsCollector(OUTPUT_DIR.parent / "artifacts")
    metrics_collector.start_pipeline()

    # ── 0.5 Regenerar consolidados intermedios desde fuentes crudas ──
    # Reconstruye Indicadores Kawak.xlsx y Consolidado_API_Kawak.xlsx desde
    # data/raw/Kawak/*.xlsx y data/raw/API/*.xlsx en CADA corrida, para que
    # una base recién cargada en API/Kawak siempre se refleje sin depender
    # de que alguien ejecute consolidar_api.py manualmente antes.
    logger.info("0.5 Regenerando consolidados intermedios (Kawak/API)…")
    try:
        consolidar_api.consolidar_kawak()
        consolidar_api.consolidar_api()
    except Exception as e:
        logger.error(f"❌ Error regenerando consolidados intermedios: {e}")
        raise

    # ── 1. Cargar fuente principal ────────────────────────────────
    logger.info("1. Cargando fuente consolidada API/Kawak…")
    step1 = metrics_collector.start_step("cargar_fuente")
    df_api = cargar_fuente_consolidada()
    logger.info("   %d registros fuente", len(df_api))
    metrics_collector.finish_step(
        status="ok",
        input_rows=len(df_api),
        output_rows=len(df_api)
    )

    # ── 1.5 VALIDAR CONTRATO DE ENTRADA ───────────────────────────
    logger.info("1.5 Validando contrato de datos (LAYER 1)…")
    validacion = validar_consolidado_api_entrada(df_api, verbose=True)
    if validacion.status == "error":
        logger.error("❌ VALIDACIÓN FALLIDA — Pipeline bloqueado")
        sys.exit(1)
    # noqa: E501
    logger.info("✅ Gate 1 OK: datos listos para procesar")

    # ── 2. Catálogo (un solo I/O) ─────────────────────────────────
    logger.info("2. Cargando catálogo…")
    cat_data = cargar_catalogo_completo()
    extraccion_map       = cat_data["extraccion_map"]
    tipo_calculo_map     = cat_data["tipo_calculo_map"]
    tipo_indicador_map   = cat_data["tipo_indicador_map"]
    variables_campo_map  = cat_data["variables_campo_map"]

    # ── 3. Metadatos y catálogos auxiliares ───────────────────────
    logger.info("3. Cargando metadatos y catálogos auxiliares…")
    kawak_validos   = cargar_kawak_validos()
    metadatos_kawak = cargar_metadatos_kawak()
    metadatos_cmi   = cargar_metadatos_cmi()
    mapa_procesos   = cargar_mapa_procesos()
    ids_metrica     = cargar_lmi_reporte()
    kawak_por_año   = cargar_periodicidad_kawak_por_año()
    logger.info("   kawak_por_año: %d entradas (Id, Año)", len(kawak_por_año))

    api_kawak_lookup = cargar_consolidado_api_kawak_lookup(extraccion_map)
    logger.info("   api_kawak_lookup: %d entradas", len(api_kawak_lookup))

    # ── 4. Config patrones ────────────────────────────────────────
    logger.info("4. Cargando config_patrones…")
    config_patrones = cargar_config_patrones()
    logger.info("   %d patrones configurados", len(config_patrones))
    # ── 4.5 Inicializar versionado y auditoría ──────────────────
    logger.info("4.5 Inicializando versionado y auditoría…")
    vm = VersionManager(OUTPUT_FILE, max_versions=5)
    trail = AuditTrail()
    notifier = EmailNotifier()  # Inicializar notificador
    
    if not notifier.enabled:
        logger.info("   💬 Email notifications deshabilitado")
    else:
        logger.info(f"   💬 Email notifications habilitado para: {notifier.recipient_emails}")
    
    # Registrar inicio de consolidación
    trail.registrar_ejecucion(
        evento="consolidacion_iniciada",
        detalles={
            "año_cierre": AÑO_CIERRE_ACTUAL,
            "timestamp_inicio": datetime.now().isoformat(),
            "registros_api": len(df_api),
        },
        usuario="etl_script",
        exitoso=True,
    )
    # ── 5. Abrir workbook ─────────────────────────────────────────
    logger.info("5. Abriendo workbook %s…", OUTPUT_FILE.name)
    with workbook_local_copy(OUTPUT_FILE) as (local_output_file, source_workbook):
        if source_workbook != OUTPUT_FILE:
            logger.warning(
                "   Usando %s como fuente de lectura por acceso inestable a %s",
                source_workbook.name,
                OUTPUT_FILE.name,
            )
        wb = openpyxl.load_workbook(local_output_file)

        # ── 5.5 Crear versión (backup) antes de modificar ──────────
        logger.info("5.5 Creando versión de seguridad…")
        try:
            version_path = vm.crear_version(tag="pre_consolidacion")
            trail.registrar_cambio_datos(
                tipo_cambio="backup",
                tabla="Resultados Consolidados",
                registros_afectados=0,
                descripcion=f"Versión de seguridad previa a consolidación",
                usuario="etl_script",
            )
        except Exception as e:
            logger.warning(f"   No se pudo crear versión de seguridad: {e}")
            trail.registrar_error("versionado", str(e), usuario="etl_script")

        ws_hist     = wb["Consolidado Historico"]
        ws_sem      = wb["Consolidado Semestral"]
        ws_cierres  = wb["Consolidado Cierres"]

        # ── 6. Leer históricos existentes para signos ─────────────────
        logger.info("6. Leyendo hojas existentes…")
        with pd.ExcelFile(local_output_file) as xls:
            df_hist_ex = pd.read_excel(xls, sheet_name="Consolidado Historico")
            df_sem_ex = pd.read_excel(xls, sheet_name="Consolidado Semestral")
            df_cierres_ex = pd.read_excel(xls, sheet_name="Consolidado Cierres")
    signos = obtener_signos(df_hist_ex, df_sem_ex, df_cierres_ex)
    logger.info("   %d indicadores con signo", len(signos))

    # ── 7. Purgar filas inválidas ──────────────────────────────────
    logger.info("7. Purgando filas inválidas…")
    for ws, nom in [(ws_hist, "Historico"), (ws_sem, "Semestral"), (ws_cierres, "Cierres")]:
        _ensure_tipo_registro_header(ws)
        purgar_filas_invalidas(ws, nom, kawak_validos)

    limpiar_cierres_existentes(ws_cierres)

    # ── 7.5 Releer estado post-purge ────────────────────────────────
    # CRÍTICO: df_hist_ex/df_sem_ex/df_cierres_ex (paso 6) se leyeron ANTES
    # del purge de arriba. Si se usan tal cual para calcular llaves_hist/
    # sem/cierres (paso 9), los builders creen que una fila recién purgada
    # "ya existe" (su llave sigue en el set) y NUNCA la reconstruyen: el
    # dato se pierde en vez de regenerarse. Se recalculan aquí desde el
    # estado real y actual del workbook.
    df_hist_ex = worksheet_a_dataframe(ws_hist)
    df_sem_ex = worksheet_a_dataframe(ws_sem)
    df_cierres_ex = worksheet_a_dataframe(ws_cierres)

    # ── 8. Construir escalas históricas ───────────────────────────
    logger.info("8. Construyendo escalas históricas…")
    hist_escalas: dict = {}
    if not df_hist_ex.empty and "Id" in df_hist_ex.columns:
        df_hist_ids = (
            df_hist_ex.assign(_id=df_hist_ex["Id"].map(_id_str))
            .loc[lambda d: d["_id"].astype(str).str.len() > 0, ["_id", "Meta", "Ejecucion"]]
            .drop_duplicates(subset=["_id"], keep="first")
            .set_index("_id")
        )
        hist_escalas = df_hist_ids[["Meta", "Ejecucion"]].to_dict(orient="index")

    # ── 9. Preparar fuentes para builders ─────────────────────────
    logger.info("9. Preparando fuentes para builders…")
    # Llaves existentes (calculadas desde Id+Fecha reales)
    llaves_hist    = llaves_de_df(df_hist_ex)
    llaves_sem     = llaves_de_df(df_sem_ex)
    llaves_cierres = llaves_de_df(df_cierres_ex)

    # ── 9.5 Excluir llaves de sub-indicadores y proyectos para forzar
    #        regeneración con valores correctos (variables PAGE/PEGE, PARPR/PAEPR)
    _IDS_POBLACION = {"14", "14.1", "14.2", "14.3", "14.4"}
    _ids_regenerar = (
        set(SERIES_SUBINDICADORES_MAP.keys())
        | set(CRONOGRAMA_SERIES_FLAT.values())
        | _IDS_POBLACION
    )
    def _excluir_llaves(llaves: set, ids: set) -> set:
        return {lv for lv in llaves if not any(lv.startswith(id_ + "-") for id_ in ids)}
    llaves_hist    = _excluir_llaves(llaves_hist,    _ids_regenerar)
    llaves_sem     = _excluir_llaves(llaves_sem,     _ids_regenerar)
    llaves_cierres = _excluir_llaves(llaves_cierres, _ids_regenerar)
    logger.info(
        "9.5 Forzando regeneración de %d IDs (sub-indicadores + proyectos)",
        len(_ids_regenerar),
    )

    # Normalizar fecha en df_api
    df_api["fecha"] = pd.to_datetime(df_api["fecha"], errors="coerce")
    df_api = df_api.dropna(subset=["fecha"]).copy()
    id_series = df_api["Id"].map(_id_str)
    fecha_series = df_api["fecha"]
    df_api["LLAVE"] = (
        id_series
        + "-"
        + fecha_series.dt.year.astype(int).astype(str)
        + "-"
        + fecha_series.dt.month.astype(int).astype(str).str.zfill(2)
        + "-"
        + fecha_series.dt.day.astype(int).astype(str).str.zfill(2)
    )

    # ── 10. Construir nuevos registros ────────────────────────────
    logger.info("10. Construyendo nuevos registros…")

    regs_hist, skip_h, na_h = construir_registros_historico(
        df_api, llaves_hist, hist_escalas,
        config_patrones=config_patrones,
        mapa_procesos=mapa_procesos,
        kawak_validos=kawak_validos,
        extraccion_map=extraccion_map,
        api_kawak_lookup=api_kawak_lookup,
        variables_campo_map=variables_campo_map,
        tipo_indicador_map=tipo_indicador_map,
        metadatos_cmi=metadatos_cmi,
        kawak_por_año=kawak_por_año,
    )
    logger.info("   Histórico: %d nuevos, %d omitidos, %d NA", len(regs_hist), skip_h, na_h)

    regs_sem, skip_s, na_s = construir_registros_semestral(
        df_api, llaves_sem, hist_escalas,
        config_patrones=config_patrones,
        mapa_procesos=mapa_procesos,
        kawak_validos=kawak_validos,
        extraccion_map=extraccion_map,
        api_kawak_lookup=api_kawak_lookup,
        tipo_calculo_map=tipo_calculo_map,
        variables_campo_map=variables_campo_map,
        tipo_indicador_map=tipo_indicador_map,
        metadatos_cmi=metadatos_cmi,
        kawak_por_año=kawak_por_año,
    )
    logger.info("   Semestral: %d nuevos, %d omitidos, %d NA", len(regs_sem), skip_s, na_s)

    regs_cierres, skip_c, na_c = construir_registros_cierres(
        df_api, hist_escalas,
        config_patrones=config_patrones,
        mapa_procesos=mapa_procesos,
        kawak_validos=kawak_validos,
        extraccion_map=extraccion_map,
        api_kawak_lookup=api_kawak_lookup,
        tipo_calculo_map=tipo_calculo_map,
        variables_campo_map=variables_campo_map,
        tipo_indicador_map=tipo_indicador_map,
        metadatos_cmi=metadatos_cmi,
        kawak_por_año=kawak_por_año,
    )
    logger.info("   Cierres:   %d nuevos, %d omitidos, %d NA", len(regs_cierres), skip_c, na_c)

    # ── 10.5 APLICAR CORRECCIONES AGENT 5 solo a indicadores principales ──
    # Se aplica ANTES de añadir sub-indicadores y proyectos para que estos
    # mantengan su escala porcentual (0-100) sin ser capeados incorrectamente
    regs_hist, regs_sem, regs_cierres, _ = apply_agent5_corrections_to_registros(
        regs_hist, regs_sem, regs_cierres, trail, logger
    )

    # ── 10.4 Expandir series como sub-indicadores ─────────────────
    logger.info("10.4 Expandiendo series como sub-indicadores…")
    regs_sub_hist    = expandir_series_como_subindicadores(df_api, llaves_hist,   modo="historico", metadatos_cmi=metadatos_cmi, kawak_por_año=kawak_por_año)
    regs_sub_sem     = expandir_series_como_subindicadores(df_api, llaves_sem,    modo="semestral", metadatos_cmi=metadatos_cmi, kawak_por_año=kawak_por_año)
    regs_sub_cierres = expandir_series_como_subindicadores(df_api, llaves_cierres, modo="cierres", metadatos_cmi=metadatos_cmi, kawak_por_año=kawak_por_año)
    regs_hist    += regs_sub_hist
    regs_sem     += regs_sub_sem
    regs_cierres += regs_sub_cierres
    logger.info(
        "   Sub-indicadores: +%d histórico, +%d semestral, +%d cierres",
        len(regs_sub_hist), len(regs_sub_sem), len(regs_sub_cierres),
    )

    # ── 10.45 Extraer proyectos cronograma desde series de padres ────
    logger.info("10.45 Extrayendo proyectos cronograma (441/509/603)…")
    regs_proy_hist    = extraer_cronograma_proyectos(df_api, llaves_hist,    modo="historico", metadatos_cmi=metadatos_cmi, kawak_por_año=kawak_por_año)
    regs_proy_sem     = extraer_cronograma_proyectos(df_api, llaves_sem,     modo="semestral", metadatos_cmi=metadatos_cmi, kawak_por_año=kawak_por_año)
    regs_proy_cierres = extraer_cronograma_proyectos(df_api, llaves_cierres, modo="cierres", metadatos_cmi=metadatos_cmi, kawak_por_año=kawak_por_año)
    regs_hist    += regs_proy_hist
    regs_sem     += regs_proy_sem
    regs_cierres += regs_proy_cierres
    logger.info(
        "   Proyectos cronograma: +%d histórico, +%d semestral (jun), +%d cierres (dic/último)",
        len(regs_proy_hist), len(regs_proy_sem), len(regs_proy_cierres),
    )

    # ── 10.46 Construir Total Población (14, 14.1-14.4) ──────────────
    logger.info("10.46 Construyendo Total Población (14, 14.1-14.4)…")
    regs_pob_hist    = construir_registros_poblacion(df_api, llaves_hist,    modo="historico", metadatos_cmi=metadatos_cmi, kawak_por_año=kawak_por_año)
    regs_pob_sem     = construir_registros_poblacion(df_api, llaves_sem,     modo="semestral", metadatos_cmi=metadatos_cmi, kawak_por_año=kawak_por_año)
    regs_pob_cierres = construir_registros_poblacion(df_api, llaves_cierres, modo="cierres", metadatos_cmi=metadatos_cmi, kawak_por_año=kawak_por_año)
    regs_hist    += regs_pob_hist
    regs_sem     += regs_pob_sem
    regs_cierres += regs_pob_cierres
    logger.info(
        "   Total Población: +%d histórico, +%d semestral, +%d cierres",
        len(regs_pob_hist), len(regs_pob_sem), len(regs_pob_cierres),
    )

    # ── 10.6 VALIDACIÓN INTERMEDIA (post-construcción) ──────────────
    logger.info("10.6 Validación intermedia post-construcción…")
    for nombre_hoja, regs in [("Historico", regs_hist), ("Semestral", regs_sem), ("Cierres", regs_cierres)]:
        if regs:
            validation = validate_after_build_records(regs, nombre_hoja)
            log_validation_result(validation)
            
            if validation.status == "error":
                logger.error(f"❌ Validación post-construcción FALLIDA para {nombre_hoja}")
                # No bloquear pero registrar
                trail.registrar_error(
                    evento="validacion_intermedia",
                    error=f"Validación post-construcción fallida para {nombre_hoja}",
                    usuario="etl_script"
                )

    # ── 11. Escribir nuevas filas ─────────────────────────────────
    logger.info("11. Escribiendo nuevas filas…")
    if regs_hist:
        escribir_filas(ws_hist, regs_hist, signos, ids_metrica=ids_metrica)
    if regs_sem:
        escribir_filas(ws_sem, regs_sem, signos, ids_metrica=ids_metrica)
    if regs_cierres:
        escribir_filas(ws_cierres, regs_cierres, signos, ids_metrica=ids_metrica)

    # ── 12. Reparar valores vacíos y recalcular ───────────────────
    logger.info("12. Reparando valores y recalculando…")
    for ws, nom in [(ws_hist, "Historico"), (ws_sem, "Semestral"), (ws_cierres, "Cierres")]:
        reparar_meta_vacia(ws, api_kawak_lookup, nom)
        reparar_multiserie(
            ws, api_kawak_lookup, tipo_calculo_map, nom,
            extraccion_map, tipo_indicador_map,
        )

    if tipo_calculo_map:
        reparar_semestral_agregados(
            ws_sem, df_api, extraccion_map, tipo_calculo_map, "Semestral",
            variables_campo_map, tipo_indicador_map,
        )
        reparar_semestral_agregados(
            ws_cierres, df_api, extraccion_map, tipo_calculo_map, "Cierres",
            variables_campo_map, tipo_indicador_map,
        )

    # ── 12.5 Reparar Desglose Variables y metas fijas (última pasada) ──
    reparar_desglose_variables(
        ws_hist, df_api, extraccion_map, variables_campo_map, tipo_indicador_map, "Historico"
    )
    reparar_desglose_variables(
        ws_sem, df_api, extraccion_map, variables_campo_map, tipo_indicador_map, "Semestral",
        tipo_calculo_map=tipo_calculo_map,
    )
    reparar_desglose_variables(
        ws_cierres, df_api, extraccion_map, variables_campo_map, tipo_indicador_map, "Cierres",
        tipo_calculo_map=tipo_calculo_map,
    )
    for ws, nom in [(ws_hist, "Historico"), (ws_sem, "Semestral"), (ws_cierres, "Cierres")]:
        reparar_metas_fijas(ws, nom)

    # ── 13. Deduplicar y reescribir fórmulas ─────────────────────
    logger.info("13. Deduplicando y reescribiendo fórmulas…")
    from etl.escritura import limpiar_ordenar_hoja

    # Ordenar siempre por ID y Fecha en todos los consolidados
    limpiar_ordenar_hoja(ws_hist, "Historico", ordenar_por=["Id", "Fecha"])
    limpiar_ordenar_hoja(ws_sem, "Semestral", ordenar_por=["Id", "Fecha"])
    limpiar_ordenar_hoja(ws_cierres, "Cierres", ordenar_por=["Id", "Fecha"])

    # ── 14. Actualizar Catálogo Indicadores ───────────────────────
    logger.info("14. Actualizando Catálogo Indicadores…")
    df_catalogo = construir_catalogo(df_api, df_hist_ex, metadatos_kawak, metadatos_cmi)
    if not df_catalogo.empty:
        escribir_hoja_nueva(wb, "Catalogo Indicadores", df_catalogo)
        logger.info("   %d indicadores en catálogo", len(df_catalogo))

    # ── 15. Guardar ───────────────────────────────────────────────
    logger.info("15. Guardando %s…", OUTPUT_FILE.name)
    # Backup anterior (compatibilidad)
    backup = OUTPUT_FILE.with_suffix(".bak.xlsx")
    try:
        respaldo_origen = source_workbook if source_workbook.exists() else OUTPUT_FILE
        shutil.copy2(respaldo_origen, backup)
    except Exception as exc:
        logger.warning("   No se pudo crear backup clásico: %s", exc)

    try:
        with tempfile.TemporaryDirectory(prefix="sip_excel_save_", ignore_cleanup_errors=True) as temp_dir:
            temp_root = Path(temp_dir)
            local_output_saved = temp_root / OUTPUT_FILE.name
            wb.save(local_output_saved)
            if hasattr(wb, "close"):
                wb.close()
            shutil.copy2(local_output_saved, OUTPUT_FILE)

            # ── Generar copia solo valores ────────────────────────────
            valores_file = OUTPUT_FILE.with_name(OUTPUT_FILE.stem + " VALORES.xlsx")
            wb_val = openpyxl.load_workbook(local_output_saved)
            for ws in wb_val.worksheets:
                try:
                    _materializar_cumplimiento(ws)
                except Exception as e:
                    logger.warning(f"No se pudo materializar cumplimiento en hoja {ws.title}: {e}")
            local_valores_saved = temp_root / valores_file.name
            wb_val.save(local_valores_saved)
            if hasattr(wb_val, "close"):
                wb_val.close()
            shutil.copy2(local_valores_saved, valores_file)

        logger.info("   Guardado correctamente.")
        logger.info(f"   Copia solo valores guardada en: {valores_file}")
        
        # Registrar consolidación exitosa
        trail.registrar_ejecucion(
            evento="consolidacion_completada",
            detalles={
                "registros_historico": len(regs_hist),
                "registros_semestral": len(regs_sem),
                "registros_cierres": len(regs_cierres),
                "total_nuevos": len(regs_hist) + len(regs_sem) + len(regs_cierres),
            },
            usuario="etl_script",
            exitoso=True,
        )
        
    except Exception as consolidation_error:
        logger.error(f"❌ ERROR durante consolidación: {consolidation_error}")
        logger.info("🔄 Intentando rollback automático…")
        
        # Enviar alerta de fallo
        audit_summary = trail.resumen()
        notifier.send_pipeline_failure_alert(
            error=consolidation_error,
            operation="Consolidación ETL - Actualizar Consolidado",
            audit_summary=audit_summary,
        )
        
        # Registrar error en audit trail
        trail.registrar_error(
            evento="consolidacion",
            error=f"{type(consolidation_error).__name__}: {consolidation_error}",
            usuario="etl_script",
        )
        
        # Intentar rollback
        if vm.restaurar_ultima_version():
            logger.info("✅ Rollback completado — consolidado anterior restaurado")
            trail.registrar_ejecucion(
                evento="rollback_ejecutado",
                detalles={"razon": "error_consolidacion"},
                usuario="etl_script",
                exitoso=True,
            )
            # Enviar alerta de recuperación
            notifier.send_recovery_success_alert(
                operation="Consolidación ETL",
                recovery_method="Rollback automático a versión anterior",
                audit_summary=audit_summary,
            )
        else:
            logger.error("❌ NO se pudo restaurar versión anterior — REQUIERE INTERVENCIÓN MANUAL")
            trail.registrar_error(
                evento="rollback",
                error="Fallo restauración de versión anterior",
                usuario="etl_script",
            )
        
        # Re-lanzar excepción para que se note el error
        raise

    # ── Resumen final ─────────────────────────────────────────────
    total_nuevos = len(regs_hist) + len(regs_sem) + len(regs_cierres)
    logger.info("=" * 65)
    logger.info("  COMPLETADO — %d registros nuevos totales", total_nuevos)
    logger.info("=" * 65)
    
    # ── Resumen de auditoría ──────────────────────────────────────
    audit_summary = trail.resumen()
    logger.info("AUDITORÍA: %d eventos registrados | %d exitosos | %d errores",
                audit_summary["total_eventos"],
                audit_summary["eventos_exitosos"],
                audit_summary["eventos_error"])
    logger.info(f"Archivo de auditoría: {trail.audit_file}")
    
    # ── Finalizar métricas ────────────────────────────────────────
    metrics_collector.finish_pipeline(status="ok")
    logger.info("📊 Métricas de rendimiento guardadas")


if __name__ == "__main__":
    main()
