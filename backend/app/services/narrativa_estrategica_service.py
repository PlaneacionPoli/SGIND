"""Informe Estratégico de Desempeño PDI — análisis cualitativo por línea
(triangulación objetivo oficial + entregables/impactos de proyectos +
resultado cuantitativo) y balance consolidado, con prospectiva PDI 2026-2030.

La narrativa es "estática" y de autoría humana (Consultor/Claude leyendo los
datos reales del Centro de Proyectos y el CMI) — no se genera con un LLM en
cada request ni se resume automáticamente por plantilla: eso producía texto
operativo (listas de entregables) impropio para Alta Dirección (feedback
2026-09-27). El texto se redacta una vez en
scripts/generar_narrativa_estrategica.py y se guarda aquí:
data/derived/narrativa_estrategica_2022_2025.json — el PDF y el dashboard
solo la leen (leer_narrativa_estrategica())."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.domain.resumen_builders import STRATEGIC_LINE_DEFS, norm_key

logger = logging.getLogger(__name__)

# Dentro del paquete app/ (services -> app, 2 niveles): estable tanto en
# local (backend/app/services/..) como en el contenedor (/app/app/services/..).
_PDI_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "pdi_2022_2026.json"


def _output_path() -> Path:
    """data/derived/narrativa_estrategica_2022_2025.json, relativo a
    SGIND_DATA_PATH (igual que ExcelReaderService.data_root) — NO contar
    niveles de carpetas desde __file__: local es backend/app/services/.. (4
    parents -> repo root) pero el contenedor copia backend/app -> /app/app
    (3 parents -> /app), así que ese conteo apuntaba a /data en vez de
    /app/data y la narrativa nunca se encontraba en producción
    (hallazgo 2026-09-27)."""
    data_root = Path(get_settings().sgind_data_path).resolve()
    # sgind_data_path apunta a <root>/data (ver ExcelReaderService); el JSON
    # derivado vive junto a raw/ dentro de esa misma carpeta.
    return data_root / "derived" / "narrativa_estrategica_2022_2025.json"

# Tarjetas del Consolidado (Balance / Logros en cifras / Retos priorizados):
# mismos hechos de TEXTOS_CONSOLIDADO re-presentados como datos estructurados.
# Viven aquí (no solo en el JSON generado) para que el dashboard las muestre
# sin depender de volver a correr scripts/generar_narrativa_estrategica.py.
TARJETAS_CONSOLIDADO = {
    "balance": {
        "logros_destacados": [
            {"label": "Acreditación CNA", "valor": "Otorgada 6 Años"},
            {"label": "Expansión Matrícula", "valor": "+13,1% vs. 2022"},
            {"label": "Sostenibilidad ISO", "valor": "Norma 14001:2015"},
        ],
        "auditoria": "Auditoría Interna OK",
    },
    "cifras": [
        {
            "titulo": "Estudiantes POLI",
            "valor": "56.807",
            "detalle": "+13,1% vs. 2022",
        },
        {
            "titulo": "Satisfacción NPS",
            "valor": "+25,4 pts",
            "detalle": "Mejora sostenida",
        },
        {
            "titulo": "Nuevos Programas",
            "valor": "26",
            "detalle": "Presenciales y virtuales",
        },
        {
            "titulo": "Clima Laboral",
            "valor": "GPTW",
            "detalle": "Certificado",
        },
    ],
    "retos_priorizados": [
        {
            "codigo": "P1",
            "titulo": "Centro de Excelencia Analítica",
            "detalle": (
                "Gobierno de TI, arquitectura de microservicios y modelos de IA "
                "como palanca de decisiones basadas en datos"
            ),
        },
        {
            "codigo": "P2",
            "titulo": "Sostener el ritmo de expansión",
            "detalle": (
                "Escalar los mecanismos de diferenciación comercial y "
                "diversificación de mercado validados en Pricing y Proyecto Silver"
            ),
        },
        {
            "codigo": "P3",
            "titulo": "Definir el camino de Eduvida",
            "detalle": "Fase I ya ejecutada; a la espera de las definiciones necesarias para continuar",
        },
    ],
}

_LINEA_LABELS = {
    "expansion": "Expansión",
    "transformacion organizacional": "Transformación Organizacional",
    "calidad": "Calidad",
    "experiencia": "Experiencia",
    "sostenibilidad": "Sostenibilidad",
    "educacion para toda la vida": "Educación para toda la vida",
}


def _load_pdi_oficial() -> dict[str, Any]:
    return json.loads(_PDI_JSON_PATH.read_text(encoding="utf-8"))["lineas"]


def leer_narrativa_estrategica() -> dict[str, Any] | None:
    """Lee el JSON estático ya generado — None si aún no se ha corrido el
    script de generación (el PDF/dashboard deben degradar con gracia)."""
    path = _output_path()
    if not path.exists():
        logger.warning("narrativa_estrategica_2022_2025.json no encontrado en %s", path)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.exception("No se pudo leer narrativa_estrategica_2022_2025.json")
        return None


def _pendientes_indicadores(worksheet_flags, key: str) -> list[str]:
    """Indicadores "Prov-" (catalogados, sin cierre/medición aún) por línea —
    FlagPlanEstrategico=NaN, 0 registros en Cierres (hallazgo 2026-09-27)."""
    if worksheet_flags.empty or "Id" not in worksheet_flags.columns:
        return []
    prov = worksheet_flags[worksheet_flags["Id"].astype(str).str.startswith("Prov")]
    if "Linea" not in prov.columns:
        return []
    prov = prov[prov["Linea"].apply(lambda v: norm_key(str(v)) == key)]
    return [str(v).strip() for v in prov["Indicador"].dropna().tolist()]


def _proyectos_de_linea_pendientes(proy_cualitativo, key: str) -> list[str]:
    if proy_cualitativo.empty:
        return []
    from app.domain.resumen_builders import _PMO_LINEA_ALIASES  # type: ignore[attr-defined]

    out = []
    for _, row in proy_cualitativo.iterrows():
        linea_raw = str(row.get("linea") or "").strip()
        linea_norm = norm_key(_PMO_LINEA_ALIASES.get(norm_key(linea_raw), linea_raw))
        if linea_norm != key:
            continue
        if str(row.get("estado") or "").strip() in ("Planeación", "Stand by"):
            out.append(row.get("nombre", ""))
    return out


def ensamblar_narrativa(
    resumen_service: Any,
    textos_lineas: dict[str, dict[str, str]],
    textos_consolidado: dict[str, str],
    tarjetas_consolidado: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Combina el texto de autoría humana (`textos_lineas`/`textos_consolidado`,
    ver scripts/generar_narrativa_estrategica.py) con los datos estructurados
    reales (cumplimiento, tagline/objetivos oficiales del PDI, proyectos
    pendientes, indicadores en alerta/peligro y catálogo "Prov-" sin medir)
    en el JSON final que consume el Informe Ejecutivo."""
    pdi_oficial = _load_pdi_oficial()
    informe = resumen_service.get_informe_ejecutivo()
    proy_cualitativo = resumen_service._proyectos_pmo.load_cualitativo()
    worksheet_flags = resumen_service._strategic._loaders.load_worksheet_flags()

    lineas_out: dict[str, Any] = {}
    for line_def in STRATEGIC_LINE_DEFS:
        key = line_def["key"]
        nombre_linea = _LINEA_LABELS.get(key, line_def["label"])
        oficial = pdi_oficial.get(key, {})
        li = next((x for x in informe["lineas"] if norm_key(x["linea"]) == key), None)
        if li is None or key not in textos_lineas:
            continue

        indicadores_criticos = [
            ind["indicador"]
            for obj in li["objetivos"]
            for ind in obj["indicadores"]
            if ind["nivel"] in ("Alerta", "Peligro")
        ]

        lineas_out[key] = {
            "nombre": nombre_linea,
            "tagline": oficial.get("tagline", ""),
            "objetivos_oficiales": oficial.get("objetivos", []),
            "parrafo_logros": textos_lineas[key]["logros"],
            "parrafo_pendientes": textos_lineas[key]["pendientes"],
            "proyectos_pendientes": _proyectos_de_linea_pendientes(proy_cualitativo, key),
            "indicadores_pendientes": _pendientes_indicadores(worksheet_flags, key),
            "indicadores_criticos": indicadores_criticos,
        }

    return {
        "fuente": "claude",
        "cumplimiento_global": informe["cumplimiento_global"],
        "consolidado": textos_consolidado,
        "tarjetas_consolidado": tarjetas_consolidado,
        "lineas": lineas_out,
    }


def guardar(data: dict[str, Any]) -> Path:
    path = _output_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
