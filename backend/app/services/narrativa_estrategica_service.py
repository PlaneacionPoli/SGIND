"""Informe Estratégico de Desempeño PDI — análisis cualitativo por línea
(triangulación objetivo oficial + entregables/impactos de proyectos +
resultado cuantitativo) y balance consolidado, con prospectiva PDI 2026-2030.

Esta narrativa es "estática": se genera UNA VEZ con generar_y_guardar() (ver
scripts/generar_narrativa_estrategica.py) y se guarda en
data/derived/narrativa_estrategica_2022_2025.json — el PDF y el dashboard la
leen de ahí (leer_narrativa_estrategica()), no la regeneran en cada request.
Mismo patrón de degradación de narrativa_ia_service.py / ADR-007: usa Gemini
si hay GEMINI_API_KEY, si no cae a un heurístico basado en plantillas."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.domain.resumen_builders import STRATEGIC_LINE_DEFS, norm_key

logger = logging.getLogger(__name__)

_MODEL = "gemini-2.5-flash"
_PDI_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "pdi_2022_2026.json"
_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "data"
    / "derived"
    / "narrativa_estrategica_2022_2025.json"
)

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
    if not _OUTPUT_PATH.exists():
        return None
    try:
        return json.loads(_OUTPUT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.exception("No se pudo leer narrativa_estrategica_2022_2025.json")
        return None


def _get_gemini_client() -> Any | None:
    key = get_settings().gemini_api_key
    if not key:
        return None
    try:
        from google import genai
    except ImportError:
        logger.warning("Paquete google-genai no instalado.")
        return None
    try:
        return genai.Client(api_key=key)
    except Exception:
        logger.exception("No se pudo inicializar el cliente de Gemini.")
        return None


def _call_gemini(client: Any, prompt: str) -> str | None:
    try:
        response = client.models.generate_content(model=_MODEL, contents=prompt)
        texto = (response.text or "").strip()
        return texto or None
    except Exception:
        logger.exception("Fallo al llamar a Gemini para narrativa estratégica.")
        return None


# ── Insumos por línea (cuantitativo + entregables/impactos del PMO) ────────


def _proyectos_de_linea(proy_cualitativo, key: str) -> list[dict[str, str]]:
    if proy_cualitativo.empty:
        return []
    from app.domain.resumen_builders import _PMO_LINEA_ALIASES  # type: ignore[attr-defined]

    rows = []
    for _, row in proy_cualitativo.iterrows():
        linea_raw = str(row.get("linea") or "").strip()
        linea_norm = norm_key(_PMO_LINEA_ALIASES.get(norm_key(linea_raw), linea_raw))
        if linea_norm != key:
            continue
        rows.append(
            {
                "nombre": row.get("nombre", ""),
                "estado": row.get("estado", ""),
                "pct": row.get("pct_completado"),
                "objetivo_proyecto": row.get("objetivo_proyecto", ""),
                "entregables": row.get("entregables", ""),
                "impactos": row.get("impactos", ""),
                "riesgos": row.get("riesgos", ""),
            }
        )
    return rows


def _pendientes_indicadores(worksheet_flags, key: str) -> list[str]:
    """Indicadores "Prov-" (catalogados, sin cierre/medición aún) por línea —
    ver hallazgo 2026-09-27: FlagPlanEstrategico=NaN, 0 registros en Cierres."""
    if worksheet_flags.empty or "Id" not in worksheet_flags.columns:
        return []
    prov = worksheet_flags[worksheet_flags["Id"].astype(str).str.startswith("Prov")]
    if "Linea" not in prov.columns:
        return []
    prov = prov[prov["Linea"].apply(lambda v: norm_key(str(v)) == key)]
    return [str(v).strip() for v in prov["Indicador"].dropna().tolist()]


def _limpiar_entregable(texto: str) -> str:
    """Las celdas de Entregables/Impactos del Centro de Proyectos traen
    varias líneas con viñetas "•" — se toma solo la primera línea (el
    entregable principal) para que quepa en un párrafo narrativo sin verse
    como una lista pegada."""
    primera = texto.replace("\r", "\n").split("\n")[0]
    return primera.lstrip("•-* ").strip()


def _fmt_lista(items: list[str], limite: int = 6) -> str:
    items = [i for i in items if i]
    if not items:
        return "ninguno registrado"
    shown = items[:limite]
    extra = len(items) - len(shown)
    texto = "; ".join(shown)
    if extra > 0:
        texto += f" (+{extra} más)"
    return texto


# ── Heurísticos (fallback sin Gemini, ADR-007) ──────────────────────────────


def _heuristico_logros(
    *, nombre_linea: str, objetivo_titulo: str, cumplimiento: float, n_proyectos_cerrados: int,
) -> str:
    """Texto para Alta Dirección: síntesis gerencial, sin enumerar
    entregables/tareas operativas de proyectos (ver feedback 2026-09-27) —
    esa granularidad es insumo del prompt a Gemini, no del texto final."""
    estado = (
        "sobresaliente" if cumplimiento >= 100
        else "satisfactorio" if cumplimiento >= 95
        else "en consolidación"
    )
    cierre_txt = (
        f"el cierre de {n_proyectos_cerrados} proyectos estratégicos"
        if n_proyectos_cerrados > 0
        else "la ejecución de su portafolio de proyectos"
    )
    return (
        f"La línea {nombre_linea} registra un desempeño {estado} ({cumplimiento:.1f}% de "
        f"cumplimiento acumulado) frente a su objetivo estratégico de {objetivo_titulo.lower()}. "
        f"{cierre_txt.capitalize()} en el ciclo consolida avances de madurez institucional y "
        f"valor agregado más allá de la ejecución operativa, en línea con lo trazado en el "
        f"PDI 2022-2026 para esta línea."
    )


def _heuristico_pendientes(
    *, nombre_linea: str, proyectos_pendientes: list[str], indicadores_pendientes: list[str],
    indicadores_criticos: list[str],
) -> str:
    partes = []
    if proyectos_pendientes:
        partes.append(
            f"quedan {len(proyectos_pendientes)} proyecto(s) en planeación o en pausa "
            f"({_fmt_lista(proyectos_pendientes, 4)})"
        )
    if indicadores_criticos:
        partes.append(
            f"{len(indicadores_criticos)} indicador(es) en zona de alerta o peligro "
            f"({_fmt_lista(indicadores_criticos, 4)})"
        )
    if indicadores_pendientes:
        partes.append(
            f"{len(indicadores_pendientes)} indicador(es) catalogados sin medición aún "
            f"({_fmt_lista(indicadores_pendientes, 4)})"
        )
    if not partes:
        return (
            f"La línea {nombre_linea} cierra el ciclo sin pendientes críticos identificados; "
            f"la prioridad para el PDI 2026-2030 es sostener el ritmo alcanzado y explorar "
            f"metas más ambiciosas sobre la misma base construida."
        )
    return (
        f"Hacia el cierre del ciclo, {'; '.join(partes)}. Estos elementos son el insumo "
        f"directo para la formulación del PDI 2026-2030 en {nombre_linea}: requieren "
        f"decisión explícita sobre continuidad, redefinición de alcance o cierre, y "
        f"asignación de recursos antes del inicio del siguiente ciclo."
    )


def _heuristico_consolidado(cumplimiento_global: float, lineas_resumen: list[dict]) -> dict[str, str]:
    mejor = max(lineas_resumen, key=lambda x: x["cumplimiento"])
    peor = min(lineas_resumen, key=lambda x: x["cumplimiento"])
    resumen = (
        f"El PDI 2022-2026 cierra su corte 2022-2025 con un cumplimiento institucional "
        f"acumulado del {cumplimiento_global:.1f}%, reflejo de una ejecución sostenida en "
        f"las 6 líneas estratégicas. {mejor['nombre']} lidera el desempeño "
        f"({mejor['cumplimiento']:.1f}%), mientras {peor['nombre']} concentra las mayores "
        f"oportunidades de cierre de brecha ({peor['cumplimiento']:.1f}%) de cara al "
        f"siguiente ciclo de planeación."
    )
    logros = (
        "Los mayores logros transformacionales del ciclo se concentran en la consolidación "
        "de arquitectura tecnológica institucional, el fortalecimiento de la oferta académica "
        "y el avance sostenido en cumplimiento financiero y de indicadores misionales."
    )
    retos = (
        "Los retos priorizados para el PDI 2026-2030 giran en torno a los proyectos aún en "
        "planeación o en pausa, los indicadores sin medición consolidada y el cierre de las "
        "brechas identificadas en las líneas con menor cumplimiento relativo."
    )
    return {"resumen_ejecutivo": resumen, "logros": logros, "retos_priorizados": retos}


# ── Orquestación ─────────────────────────────────────────────────────────


def generar_narrativa_estrategica(resumen_service: Any) -> dict[str, Any]:
    """Arma la narrativa cualitativa completa (por línea + consolidado) a
    partir de: PDI oficial (pdi_2022_2026.json), Centro de Proyectos
    (entregables/impactos/riesgos) e indicadores CMI (cumplimiento +
    catálogo "Prov-" de pendientes). Usa Gemini si hay API key; si no,
    heurístico. `resumen_service` es una instancia de ResumenService."""
    pdi_oficial = _load_pdi_oficial()
    informe = resumen_service.get_informe_ejecutivo()
    proy_cualitativo = resumen_service._proyectos_pmo.load_cualitativo()
    worksheet_flags = resumen_service._strategic._loaders.load_worksheet_flags()
    client = _get_gemini_client()
    fuente = "gemini" if client is not None else "heuristico"

    lineas_out: dict[str, Any] = {}
    lineas_resumen_cuanti: list[dict] = []

    for line_def in STRATEGIC_LINE_DEFS:
        key = line_def["key"]
        nombre_linea = _LINEA_LABELS.get(key, line_def["label"])
        oficial = pdi_oficial.get(key, {})
        li = next((x for x in informe["lineas"] if norm_key(x["linea"]) == key), None)
        if li is None:
            continue

        cumplimiento = li["retos"]["cumplimiento"]
        lineas_resumen_cuanti.append({"nombre": nombre_linea, "cumplimiento": cumplimiento})

        proyectos_linea = _proyectos_de_linea(proy_cualitativo, key)
        cerrados = [
            p["nombre"] for p in proyectos_linea if p["estado"] in ("Cierre", "Finalizado")
        ]
        pendientes_proy = [
            p["nombre"] for p in proyectos_linea if p["estado"] in ("Planeación", "Stand by")
        ]
        entregables = [p["entregables"] for p in proyectos_linea if p["entregables"]][:4]
        indicadores_pendientes = _pendientes_indicadores(worksheet_flags, key)
        indicadores_criticos = [
            ind["indicador"]
            for obj in li["objetivos"]
            for ind in obj["indicadores"]
            if ind["nivel"] in ("Alerta", "Peligro")
        ]

        objetivo_principal = oficial.get("objetivos", [{}])[0]
        objetivo_titulo = objetivo_principal.get("titulo", nombre_linea)

        parrafo_logros = None
        parrafo_pendientes = None

        if client is not None:
            objetivos_txt = "\n".join(
                f"- Objetivo {o['numero']}. {o['titulo']}: {o['descripcion']}"
                for o in oficial.get("objetivos", [])
            )
            prompt_logros = (
                "Actúa como Consultor Senior en Planeación Estratégica de Educación Superior. "
                f"Redacta UN ÚNICO PÁRRAFO cualitativo, denso, de tono gerencial (para Rectoría y "
                f"Consejo Superior), sobre los LOGROS de la línea estratégica '{nombre_linea}' del "
                "Plan de Desarrollo Institucional 2022-2026 del Politécnico Grancolombiano. "
                "Triangula obligatoriamente: (1) el objetivo estratégico oficial, (2) los "
                "entregables/impactos clave de los proyectos cerrados, (3) el resultado "
                "cuantitativo acumulado de los indicadores. Evita enumerar tareas operativas; "
                "enfócate en valor agregado institucional, madurez de procesos y transformación "
                "lograda. No uses viñetas ni encabezados, solo el párrafo.\n\n"
                f"Objetivo(s) estratégico(s) oficiales:\n{objetivos_txt}\n\n"
                f"Cumplimiento cuantitativo acumulado: {cumplimiento:.1f}%.\n"
                f"Proyectos cerrados: {_fmt_lista(cerrados)}.\n"
                f"Entregables/impactos clave reportados: {_fmt_lista(entregables)}."
            )
            parrafo_logros = _call_gemini(client, prompt_logros)

            prompt_pendientes = (
                "Actúa como Consultor Senior en Planeación Estratégica de Educación Superior. "
                f"Redacta UN ÚNICO PÁRRAFO cualitativo sobre los PENDIENTES y la PROSPECTIVA "
                f"hacia el PDI 2026-2030 de la línea '{nombre_linea}'. Identifica causas raíz "
                "estratégicas (no operativas) y conviértelas en prioridades para el siguiente "
                "ciclo de planeación. No uses viñetas, solo el párrafo, tono directo y "
                "sintetizado.\n\n"
                f"Proyectos no iniciados/en pausa: {_fmt_lista(pendientes_proy)}.\n"
                f"Indicadores en zona de alerta o peligro: {_fmt_lista(indicadores_criticos)}.\n"
                f"Indicadores catalogados sin medición consolidada aún: "
                f"{_fmt_lista(indicadores_pendientes)}."
            )
            parrafo_pendientes = _call_gemini(client, prompt_pendientes)

        if not parrafo_logros:
            parrafo_logros = _heuristico_logros(
                nombre_linea=nombre_linea,
                objetivo_titulo=objetivo_titulo,
                cumplimiento=cumplimiento,
                proyectos_cerrados=cerrados,
                entregables=entregables,
            )
        if not parrafo_pendientes:
            parrafo_pendientes = _heuristico_pendientes(
                nombre_linea=nombre_linea,
                proyectos_pendientes=pendientes_proy,
                indicadores_pendientes=indicadores_pendientes,
                indicadores_criticos=indicadores_criticos,
            )

        lineas_out[key] = {
            "nombre": nombre_linea,
            "tagline": oficial.get("tagline", ""),
            "objetivos_oficiales": oficial.get("objetivos", []),
            "parrafo_logros": parrafo_logros,
            "parrafo_pendientes": parrafo_pendientes,
            "proyectos_pendientes": pendientes_proy,
            "indicadores_pendientes": indicadores_pendientes,
            "indicadores_criticos": indicadores_criticos,
        }

    cumplimiento_global = informe["cumplimiento_global"]
    consolidado = None
    if client is not None:
        resumen_lineas_txt = "\n".join(
            f"- {x['nombre']}: {x['cumplimiento']:.1f}%" for x in lineas_resumen_cuanti
        )
        prompt_consolidado = (
            "Actúa como Consultor Senior en Planeación Estratégica de Educación Superior. "
            "Redacta, para Rectoría y Consejo Superior, un RESUMEN EJECUTIVO CUALITATIVO "
            "CONSOLIDADO (un párrafo) del cierre del PDI 2022-2026 (corte 2022-2025) del "
            "Politécnico Grancolombiano, y un BALANCE ESTRATÉGICO en dos párrafos separados: "
            "uno de LOGROS transformacionales y otro de RETOS PRIORIZADOS para el PDI "
            "2026-2030. Responde en español, exactamente en este formato, sin viñetas:\n"
            "RESUMEN: <párrafo>\nLOGROS: <párrafo>\nRETOS: <párrafo>\n\n"
            f"Cumplimiento global acumulado: {cumplimiento_global:.1f}%.\n"
            f"Cumplimiento por línea:\n{resumen_lineas_txt}"
        )
        texto = _call_gemini(client, prompt_consolidado)
        if texto:
            partes = {"resumen_ejecutivo": "", "logros": "", "retos_priorizados": ""}
            for linea in texto.splitlines():
                limpio = linea.strip()
                if limpio.upper().startswith("RESUMEN:"):
                    partes["resumen_ejecutivo"] = limpio.split(":", 1)[-1].strip()
                elif limpio.upper().startswith("LOGROS:"):
                    partes["logros"] = limpio.split(":", 1)[-1].strip()
                elif limpio.upper().startswith("RETOS:"):
                    partes["retos_priorizados"] = limpio.split(":", 1)[-1].strip()
            if all(partes.values()):
                consolidado = partes

    if consolidado is None:
        consolidado = _heuristico_consolidado(cumplimiento_global, lineas_resumen_cuanti)

    return {
        "fuente": fuente,
        "cumplimiento_global": cumplimiento_global,
        "consolidado": consolidado,
        "lineas": lineas_out,
    }


def generar_y_guardar(resumen_service: Any) -> Path:
    """Genera la narrativa completa y la guarda en
    data/derived/narrativa_estrategica_2022_2025.json (crea la carpeta si
    no existe). Devuelve la ruta escrita."""
    data = generar_narrativa_estrategica(resumen_service)
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return _OUTPUT_PATH
