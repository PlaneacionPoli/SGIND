"""Narrativa con IA generativa (Gemini) para fichas de indicador — C-02.

Portado desde services/ai_analysis.py (legacy Streamlit), originalmente sobre
Claude. Se migró a Gemini (Google AI Studio) porque su free tier no requiere
tarjeta de crédito ni presupuesto asignado — decisión de producto de la Fase 4
del plan de remediación ("buscar otra IA gratuita que pueda implementarse").
Reutiliza el fallback heurístico de app.domain.procesos_builders cuando no hay
GEMINI_API_KEY configurada o la llamada a la API falla, siguiendo el mismo
patrón obligatorio de degradación del legacy y de ADR-007.

Obtener una API key gratuita: https://aistudio.google.com/app/apikey
(no requiere tarjeta de crédito). Límites del free tier para gemini-2.5-flash
al momento de escribir esto: 15 solicitudes/min, 1500 solicitudes/día,
1M tokens/min — de sobra para narrativas generadas bajo demanda al abrir
una ficha de indicador.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.domain.procesos_builders import generate_ficha_narrativa_heuristica

logger = logging.getLogger(__name__)

_MODEL = "gemini-2.5-flash"

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
    """Narrativa de ficha vía Gemini si hay API key configurada; si no, o si falla, usa el heurístico."""
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
        "fuente": "gemini",
    }
