"""Narrativa con IA generativa (Claude) para fichas de indicador — C-02.

Portado desde services/ai_analysis.py (legacy Streamlit). Reutiliza el
fallback heurístico de app.domain.procesos_builders cuando no hay
ANTHROPIC_API_KEY configurada o la llamada a la API falla, siguiendo el
mismo patrón obligatorio de degradación del legacy y de ADR-007.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.domain.procesos_builders import generate_ficha_narrativa_heuristica

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"

_PROMPT_TEMPLATE = """Actúa como analista estratégico experto en indicadores de gestión institucional.

Evalúa el siguiente indicador:
- Indicador: {nombre}
- Proceso: {proceso}
- Meta: {meta}
- Ejecución actual: {ejecucion}
- Nivel de cumplimiento: {nivel} ({cumplimiento})

Con base en estos datos, genera:
1. Un diagnóstico muy breve y directo sobre el estado actual frente a la meta.
2. Un factor de riesgo principal si no se alcanza la meta.
3. Una recomendación táctica inmediata para el responsable.

Responde en español, en exactamente 3 líneas, cada una iniciando con
"Diagnóstico:", "Riesgo:" y "Recomendación:" respectivamente. No agregues
texto adicional ni encabezados."""


def _get_client() -> Any | None:
    key = get_settings().anthropic_api_key
    if not key:
        return None
    try:
        import anthropic
    except ImportError:
        logger.warning("Paquete anthropic no instalado; usando narrativa heurística.")
        return None
    try:
        return anthropic.Anthropic(api_key=key)
    except Exception:
        logger.exception("No se pudo inicializar el cliente de Anthropic.")
        return None


def _parse_respuesta(texto: str) -> dict[str, str] | None:
    campos = {"diagnostico": "", "riesgo": "", "recomendacion": ""}
    for linea in texto.splitlines():
        limpio = linea.strip().lstrip("-•* ").strip()
        bajo = limpio.lower()
        if bajo.startswith("diagnóstico") or bajo.startswith("diagnostico"):
            campos["diagnostico"] = limpio.split(":", 1)[-1].strip()
        elif bajo.startswith("riesgo"):
            campos["riesgo"] = limpio.split(":", 1)[-1].strip()
        elif bajo.startswith("recomendación") or bajo.startswith("recomendacion"):
            campos["recomendacion"] = limpio.split(":", 1)[-1].strip()
    if not any(campos.values()):
        return None
    return campos


def generar_narrativa_ficha(
    *,
    nombre: str,
    meta: Any,
    ejecucion: Any,
    nivel: str,
    cumplimiento: float | None,
    proceso: str | None = None,
) -> dict[str, str]:
    """Narrativa de ficha vía Claude si hay API key configurada; si no, o si falla, usa el heurístico."""
    fallback = generate_ficha_narrativa_heuristica(
        nombre=nombre,
        meta=meta,
        ejecucion=ejecucion,
        nivel=nivel,
        cumplimiento=cumplimiento,
        proceso=proceso,
    )

    client = _get_client()
    if client is None:
        return fallback

    prompt = _PROMPT_TEMPLATE.format(
        nombre=nombre,
        proceso=proceso or "N/A",
        meta=meta,
        ejecucion=ejecucion,
        nivel=nivel,
        cumplimiento=f"{cumplimiento}%" if cumplimiento is not None else "N/D",
    )
    try:
        message = client.messages.create(
            model=_MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = message.content[0].text.strip()
    except Exception:
        logger.exception("Fallo al llamar a la API de Claude; usando narrativa heurística.")
        return fallback

    parsed = _parse_respuesta(texto)
    if parsed is None:
        return fallback

    proc_ctx = f" en el proceso <strong>{proceso}</strong>" if proceso else ""
    diagnostico = parsed["diagnostico"] or fallback["diagnostico"]
    riesgo = parsed["riesgo"] or fallback["riesgo"]
    recomendacion = parsed["recomendacion"] or fallback["recomendacion"]
    texto_html = (
        f"<strong>Diagnóstico:</strong> {diagnostico}{proc_ctx}<br/>"
        f"<strong>Riesgo principal:</strong> {riesgo}<br/>"
        f"<strong>Recomendación táctica:</strong> {recomendacion}<br/>"
        f"<strong>Meta / Ejecución:</strong> {meta} / {ejecucion} — Nivel: {nivel}"
    )
    return {
        "diagnostico": diagnostico,
        "riesgo": riesgo,
        "recomendacion": recomendacion,
        "texto_html": texto_html,
        "fuente": "claude",
    }
