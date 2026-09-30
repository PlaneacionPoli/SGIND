"""Diagnóstico ejecutivo por proceso generado con IA (Gemini) para la pestaña
"Análisis IA" del Informe por Procesos — con flujo de auditoría y publicación.

A diferencia de narrativa_ia_service.py (narrativa de UNA ficha de indicador,
generada y mostrada de inmediato sin revisión), esta narrativa es a nivel de
PROCESO agregado y nunca se muestra a los lectores sin que alguien con rol
"auditor_ia" (o "administrador") la publique explícitamente:

  1. Cada vez que se abre el Informe por Procesos, se compara un "snapshot" de
     los resultados agregados del proceso/corte contra el último snapshot
     almacenado. Si cambiaron, se genera un nuevo BORRADOR con Gemini (o el
     heurístico existente como fallback — mismo patrón de degradación que
     narrativa_ia_service.py / ADR-007).
  2. El borrador NUNCA se expone en el endpoint de lectura pública; solo lo ve
     quien tiene rol de auditor a través de un endpoint dedicado.
  3. Publicar mueve el borrador a "publicado" (queda visible para todos los
     lectores) y archiva la versión publicada anterior en "historial", con
     quién y cuándo lo aprobó — la auditoría queda trazada en el mismo JSON.

Persistencia: JSON versionado bajo <SGIND_DATA_PATH>/derived/, igual que
narrativa_estrategica_service.py — sin tabla nueva en base de datos.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_MODEL = "gemini-2.5-flash"

_PROMPT_TEMPLATE = """Actúa como consultor estratégico institucional experto en indicadores de gestión.

Analiza los resultados agregados del proceso "{proceso}" en el corte {mes}/{anio} de un Cuadro de Mando Integral institucional:
- Cumplimiento promedio: {avg}% (score de salud: {score}/100)
- Total de indicadores evaluados: {total}
- Distribución de niveles: {cumple} cumplen, {alerta} en alerta, {peligro} en peligro
- Indicadores más críticos: {criticos_txt}
- Mayor mejora vs {base_anio}: {mejora_txt}
- Mayor riesgo vs {base_anio}: {riesgo_txt}

Con base ÚNICAMENTE en estos datos (no inventes cifras ni hechos adicionales), genera
un diagnóstico ejecutivo breve y accionable para la alta dirección. Responde en
español, en exactamente este formato, sin texto adicional ni encabezados:

DIAGNOSTICO: <2-3 frases, tono ejecutivo, no repitas literalmente todas las cifras>
FOCO: <1 frase señalando la prioridad más urgente>
DIRECTRIZ1: <1 acción concreta recomendada>
DIRECTRIZ2: <1 acción concreta recomendada>"""


def _output_path() -> Path:
    data_root = Path(get_settings().sgind_data_path).resolve()
    return data_root / "derived" / "narrativas_ia_procesos.json"


def _load_store() -> dict[str, Any]:
    path = _output_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("No se pudo leer narrativas_ia_procesos.json; se reinicia vacío.")
        return {}


def _save_store(store: dict[str, Any]) -> None:
    path = _output_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def _key(proceso: str, anio: int, mes: int) -> str:
    return f"{proceso.strip().upper()}|{anio}|{mes}"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _estado_color(avg: float | None) -> str:
    cump = avg or 0.0
    if cump >= 100:
        return "#16A34A"
    if cump >= 95:
        return "#2563EB"
    return "#DC2626"


def _build_snapshot(
    *,
    resumen: dict[str, Any],
    criticos: list[dict[str, Any]],
    mejora: dict[str, Any] | None,
    riesgo: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "score": resumen.get("score"),
        "avg": resumen.get("avg"),
        "total": resumen.get("total_indicadores"),
        "cumple": resumen.get("cumple"),
        "alerta": resumen.get("alerta"),
        "peligro": resumen.get("peligro"),
        "criticos": [
            {"indicador": c.get("indicador"), "cumplimiento": c.get("cumplimiento_pct")}
            for c in criticos[:3]
        ],
        "mejora": mejora,
        "riesgo": riesgo,
    }


def _get_client() -> Any | None:
    key = get_settings().gemini_api_key
    if not key:
        return None
    try:
        from google import genai
    except ImportError:
        logger.warning("Paquete google-genai no instalado; usando narrativa heurística.")
        return None
    try:
        return genai.Client(api_key=key)
    except Exception:
        logger.exception("No se pudo inicializar el cliente de Gemini.")
        return None


def _parse_respuesta(texto: str) -> dict[str, str] | None:
    campos = {"diagnostico": "", "foco": "", "directriz1": "", "directriz2": ""}
    for linea in texto.splitlines():
        limpio = linea.strip().lstrip("-•* ").strip()
        bajo = limpio.lower()
        if bajo.startswith("diagnóstico") or bajo.startswith("diagnostico"):
            campos["diagnostico"] = limpio.split(":", 1)[-1].strip()
        elif bajo.startswith("foco"):
            campos["foco"] = limpio.split(":", 1)[-1].strip()
        elif bajo.startswith("directriz1"):
            campos["directriz1"] = limpio.split(":", 1)[-1].strip()
        elif bajo.startswith("directriz2"):
            campos["directriz2"] = limpio.split(":", 1)[-1].strip()
    if not campos["diagnostico"]:
        return None
    return campos


def _fmt_change(item: dict[str, Any] | None) -> str:
    if not item:
        return "Sin datos comparativos."
    name = item.get("name", "—")
    change = item.get("change")
    if change is None:
        return f"{name} (sin variación calculada)"
    return f"{name} ({change:+.1f} pp)"


def _fallback_heuristico(
    *,
    proceso: str,
    resumen: dict[str, Any],
    criticos: list[dict[str, Any]],
) -> dict[str, Any]:
    """Contenido heurístico de respaldo, construido directamente a partir de los
    agregados ya calculados (resumen/criticos) — sin depender de un DataFrame."""
    avg = resumen.get("avg") or 0.0
    total = resumen.get("total_indicadores") or 0
    en_riesgo = (resumen.get("alerta") or 0) + (resumen.get("peligro") or 0)
    top_critico = criticos[0] if criticos else None

    if avg >= 100:
        estado = f"El proceso <strong>{proceso}</strong> supera la meta institucional en el corte actual."
    elif avg >= 95:
        estado = f"El proceso <strong>{proceso}</strong> mantiene desempeño estable con brechas acotadas."
    else:
        estado = f"El proceso <strong>{proceso}</strong> presenta desviación relevante y requiere priorización."

    foco = (
        f"Priorizar el indicador crítico '{top_critico.get('indicador')}' "
        f"({top_critico.get('cumplimiento_pct')}%)."
        if top_critico
        else "Sin indicadores críticos identificados en el corte actual."
    )
    dir_1 = "Enfocar seguimiento semanal en los indicadores en riesgo del proceso."
    dir_2 = (
        "Activar comité táctico con responsables por subproceso."
        if total and en_riesgo / total > 0.25
        else "Replicar buenas prácticas de subprocesos con mejor desempeño."
    )
    texto_html = (
        f"{estado} Hay <strong>{en_riesgo}</strong> indicadores en alerta/peligro "
        f"sobre <strong>{total}</strong>."
    )
    return {
        "titulo": "Diagnóstico heurístico del proceso",
        "estado_color": _estado_color(avg),
        "foco_urgente": foco,
        "directrices": [dir_1, dir_2],
        "texto_html": texto_html,
        "modelo": "heuristica",
    }


def _generar_contenido(
    *,
    proceso: str,
    anio: int,
    mes: int,
    resumen: dict[str, Any],
    criticos: list[dict[str, Any]],
    mejora: dict[str, Any] | None,
    riesgo: dict[str, Any] | None,
    base_anio: int,
) -> dict[str, Any]:
    """Genera el contenido de un borrador (vía Gemini si hay API key; si no, o si
    falla, con un heurístico de respaldo). Nunca lanza — siempre devuelve algo."""
    avg = resumen.get("avg") or 0.0
    fallback = _fallback_heuristico(proceso=proceso, resumen=resumen, criticos=criticos)

    client = _get_client()
    if client is None:
        return fallback

    criticos_txt = (
        ", ".join(f"{c.get('indicador')} ({c.get('cumplimiento_pct')}%)" for c in criticos[:3])
        or "Ninguno crítico en el corte"
    )
    prompt = _PROMPT_TEMPLATE.format(
        proceso=proceso,
        anio=anio,
        mes=mes,
        avg=avg,
        score=resumen.get("score"),
        total=resumen.get("total_indicadores"),
        cumple=resumen.get("cumple"),
        alerta=resumen.get("alerta"),
        peligro=resumen.get("peligro"),
        criticos_txt=criticos_txt,
        base_anio=base_anio,
        mejora_txt=_fmt_change(mejora),
        riesgo_txt=_fmt_change(riesgo),
    )
    try:
        response = client.models.generate_content(model=_MODEL, contents=prompt)
        texto = (response.text or "").strip()
        if not texto:
            raise ValueError("Respuesta vacía de Gemini")
    except Exception:
        logger.exception("Fallo al llamar a la API de Gemini; usando narrativa heurística.")
        return fallback

    parsed = _parse_respuesta(texto)
    if parsed is None:
        return fallback

    diagnostico = parsed["diagnostico"] or fallback["texto_html"]
    foco = parsed["foco"] or fallback["foco_urgente"]
    directrices = [d for d in (parsed["directriz1"], parsed["directriz2"]) if d] or fallback[
        "directrices"
    ]
    texto_html = f"<strong>Diagnóstico:</strong> {diagnostico}"
    return {
        "titulo": "Diagnóstico generado por IA",
        "estado_color": _estado_color(avg),
        "foco_urgente": foco,
        "directrices": directrices,
        "texto_html": texto_html,
        "modelo": _MODEL,
    }


def get_or_refresh_narrativa_ia_proceso(
    *,
    proceso: str,
    anio: int,
    mes: int,
    resumen: dict[str, Any],
    criticos: list[dict[str, Any]],
    mejora: dict[str, Any] | None,
    riesgo: dict[str, Any] | None,
    base_anio: int,
) -> dict[str, Any]:
    """Devuelve la entrada completa {publicado, borrador, historial} para
    (proceso, anio, mes). Si los resultados agregados cambiaron desde la última
    generación, crea un nuevo borrador — nunca publica automáticamente."""
    if not resumen or not resumen.get("total_indicadores"):
        return {"publicado": None, "borrador": None, "historial": []}

    snapshot = _build_snapshot(resumen=resumen, criticos=criticos, mejora=mejora, riesgo=riesgo)
    store = _load_store()
    key = _key(proceso, anio, mes)
    entry = store.get(key) or {"publicado": None, "borrador": None, "historial": []}

    publicado = entry.get("publicado")
    borrador = entry.get("borrador")
    if publicado and publicado.get("datos_snapshot") == snapshot:
        return entry
    if borrador and borrador.get("datos_snapshot") == snapshot:
        return entry

    try:
        contenido = _generar_contenido(
            proceso=proceso,
            anio=anio,
            mes=mes,
            resumen=resumen,
            criticos=criticos,
            mejora=mejora,
            riesgo=riesgo,
            base_anio=base_anio,
        )
    except Exception:
        logger.exception("No se pudo generar el borrador de narrativa IA de proceso.")
        return entry

    entry["borrador"] = {
        **contenido,
        "proceso": proceso,
        "anio": anio,
        "mes": mes,
        "datos_snapshot": snapshot,
        "generado_en": _now_iso(),
    }
    store[key] = entry
    try:
        _save_store(store)
    except Exception:
        logger.exception("No se pudo guardar narrativas_ia_procesos.json.")
    return entry


def leer_narrativa_ia_proceso(proceso: str, anio: int, mes: int) -> dict[str, Any]:
    store = _load_store()
    return store.get(_key(proceso, anio, mes)) or {
        "publicado": None,
        "borrador": None,
        "historial": [],
    }


def publicar_narrativa_ia_proceso(
    *, proceso: str, anio: int, mes: int, revisor_email: str
) -> dict[str, Any]:
    store = _load_store()
    key = _key(proceso, anio, mes)
    entry = store.get(key)
    if not entry or not entry.get("borrador"):
        raise ValueError("No hay un borrador pendiente para este proceso y corte.")

    historial = entry.get("historial") or []
    if entry.get("publicado"):
        historial.append(entry["publicado"])

    nuevo_publicado = {
        **entry["borrador"],
        "revisado_por": revisor_email,
        "revisado_en": _now_iso(),
    }
    entry["publicado"] = nuevo_publicado
    entry["borrador"] = None
    entry["historial"] = historial
    store[key] = entry
    _save_store(store)
    return entry
