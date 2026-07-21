"""
scripts/generar_auditoria_csv.py
================================
Extrae texto de los PDFs de auditoría (interna y externa),
envía el contenido a Google Gemini (gratuito) para que identifique
por proceso: fortalezas, oportunidades de mejora, hallazgos,
no conformidades y recomendaciones de desempeño.
Guarda el resultado en data/raw/Auditoria/auditoria_resultado.csv

Uso:
    python scripts/generar_auditoria_csv.py

Requiere:
    - GOOGLE_API_KEY en variable de entorno o .env
      Obtén una gratis en: https://aistudio.google.com/app/apikey
    - pypdf  (pip install pypdf)
    - google-generativeai (pip install google-generativeai)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# ── Rutas ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
PDF_INTERNA = ROOT / "data/raw/Auditoria/INFORME AUDITORIA INTERNA FINAL  9001-14001-45001-21001.pdf"
PDF_EXTERNA = ROOT / "data/raw/Auditoria/Informe Auditoria Externa Icontec 2025.pdf"
OUTPUT_XLSX = ROOT / "data/raw/Auditoria/auditoria_resultado.xlsx"

# ── Carga .env si existe ──────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


# ── Extracción de texto PDF ──────────────────────────────────────────────────
def extraer_texto_pdf(path: Path) -> str:
    """Extrae todo el texto de un PDF usando pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        print("Instalando pypdf…")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
        from pypdf import PdfReader

    reader = PdfReader(str(path))
    paginas = []
    for i, page in enumerate(reader.pages):
        texto = page.extract_text() or ""
        paginas.append(f"--- Página {i + 1} ---\n{texto}")
    return "\n".join(paginas)


# ── Prompt del sistema ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Eres un experto en sistemas de gestión de calidad ISO 9001, 14001, 45001 y 21001.
Tu tarea es analizar informes de auditoría (interna y/o externa) de una institución de educación superior llamada Politécnico Grancolombiano.
Para cada proceso identificado en el informe, extrae la siguiente información y devuelve ÚNICAMENTE un JSON válido (sin texto adicional, sin markdown) con esta estructura:

[
  {
    "proceso": "Nombre del proceso tal como aparece en el informe",
    "tipo_auditoria": "Interna" | "Externa",
    "fortalezas": "Texto con las fortalezas identificadas. Vacío si no hay.",
    "oportunidades_mejora": "Texto con las oportunidades de mejora. Vacío si no hay.",
    "hallazgos": "Texto con los hallazgos. Vacío si no hay.",
    "no_conformidades": "Texto con las no conformidades. Vacío si no hay.",
    "recomendacion_desempeno": "Recomendación específica relacionada con indicadores, medición o desempeño del proceso. Vacío si no hay."
  },
  ...
]

Reglas:
- Incluye TODOS los procesos mencionados en el informe.
- Si un proceso tiene múltiples hallazgos, concaténalos en un solo campo separados por ' | '.
- Sé conciso pero completo.
- Si un campo no tiene información relevante, déjalo como cadena vacía "".
- No inventes información que no esté en el texto.
"""


# ── Llamada al LLM ────────────────────────────────────────────────────────────
def analizar_con_llm(texto: str, tipo: str) -> list[dict]:
    """Envía el texto del PDF a Google Gemini (SDK nuevo google-genai) y retorna lista de dicts."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY no configurada.")
        print("  Obtén tu key gratuita en: https://aistudio.google.com/app/apikey")
        sys.exit(1)

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Instalando google-genai…")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-genai"])
        from google import genai
        from google.genai import types

    client = genai.Client(api_key=api_key)

    # Configuración por modelo: max_output_tokens (los Gemini 2.5 soportan hasta 65536)
    MODELOS_CONFIG = {
        "gemini-2.5-flash":      65536,
        "gemini-2.5-flash-lite": 65536,
        "gemma-3-27b-it":        8192,
        "gemma-3-12b-it":        8192,
    }
    modelos = list(MODELOS_CONFIG.keys())

    # Limitar texto según modelo (~800k para Gemini, ~30k para Gemma)
    # Se aplica por modelo en el loop

    user_msg_base = f"Informe de Auditoría {tipo}:\n\n{texto}"

    last_error = None

    for modelo in modelos:
        max_output = MODELOS_CONFIG[modelo]
        # Gemma tiene límite de entrada de ~15k tokens ≈ 30k chars
        max_input_chars = 30_000 if "gemma" in modelo else 800_000
        if len(texto) > max_input_chars:
            print(f"  ⚠ Texto truncado a {max_input_chars} chars para {modelo}.")
            user_msg = f"Informe de Auditoría {tipo}:\n\n{texto[:max_input_chars]}"
        else:
            user_msg = user_msg_base

        try:
            print(f"  Consultando {modelo} para Auditoría {tipo}…")
            response = client.models.generate_content(
                model=modelo,
                contents=user_msg,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                    max_output_tokens=max_output,
                ),
            )
            raw = response.text.strip()
            # Limpiar posibles bloques de código markdown
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.rstrip("`").strip()
            # Intentar reparar JSON truncado: cortar en el último objeto completo
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                # Reparar: truncar al último "}" seguido de posible "," y cerrar el array
                last_close = raw.rfind("}")
                if last_close > 0:
                    repaired = raw[:last_close + 1] + "\n]"
                    return json.loads(repaired)
                raise
        except json.JSONDecodeError as e:
            print(f"  ⚠ {modelo} devolvió JSON inválido: {e}")
            last_error = e
            continue
        except Exception as e:
            print(f"  ⚠ {modelo} falló: {e}")
            last_error = e
            continue

    print(f"  ERROR: Todos los modelos fallaron. Último error: {last_error}")
    return []


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    import pandas as pd

    resultados: list[dict] = []

    # ── Auditoría Interna ─────────────────────────────────────────────────────
    if PDF_INTERNA.exists():
        print(f"Extrayendo texto: {PDF_INTERNA.name}")
        texto_interna = extraer_texto_pdf(PDF_INTERNA)
        print(f"  Caracteres extraídos: {len(texto_interna):,}")
        hallazgos_interna = analizar_con_llm(texto_interna, "Interna")
        resultados.extend(hallazgos_interna)
        print(f"  Procesos identificados (Interna): {len(hallazgos_interna)}")
    else:
        print(f"⚠ No encontrado: {PDF_INTERNA}")

    # ── Auditoría Externa ─────────────────────────────────────────────────────
    if PDF_EXTERNA.exists():
        print(f"\nExtrayendo texto: {PDF_EXTERNA.name}")
        texto_externa = extraer_texto_pdf(PDF_EXTERNA)
        print(f"  Caracteres extraídos: {len(texto_externa):,}")
        hallazgos_externa = analizar_con_llm(texto_externa, "Externa")
        resultados.extend(hallazgos_externa)
        print(f"  Procesos identificados (Externa): {len(hallazgos_externa)}")
    else:
        print(f"⚠ No encontrado: {PDF_EXTERNA}")

    if not resultados:
        print("No se encontraron resultados. Verifica los PDFs y la API key.")
        sys.exit(1)

    # ── Construir DataFrame final ─────────────────────────────────────────────
    df = pd.DataFrame(resultados)

    # Columnas esperadas
    columnas = [
        "proceso",
        "tipo_auditoria",
        "fortalezas",
        "oportunidades_mejora",
        "hallazgos",
        "no_conformidades",
        "recomendacion_desempeno",
    ]
    for col in columnas:
        if col not in df.columns:
            df[col] = ""

    df = df[columnas]
    df = df.fillna("")

    # ── Pivotear para tener una fila por proceso con columnas Interna/Externa ──
    df_pivot = _pivotear_por_tipo(df)

    # Guardar como Excel (evita problemas de separador ; en Latinoamérica)
    OUTPUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        df_pivot.to_excel(writer, index=False, sheet_name="Auditoria")
        # Ajustar ancho de columnas automáticamente
        ws = writer.sheets["Auditoria"]
        for col in ws.columns:
            max_len = max((len(str(cell.value)) if cell.value else 0) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 80)
    print(f"\n✅ Excel guardado: {OUTPUT_XLSX}")
    print(f"   Filas: {len(df_pivot)} | Columnas: {list(df_pivot.columns)}")
    print(df_pivot.head())


def _pivotear_por_tipo(df: "pd.DataFrame") -> "pd.DataFrame":
    """
    Transforma el DataFrame de (proceso, tipo_auditoria, campos…)
    a una fila por proceso con columnas separadas para Interna y Externa.
    """
    import pandas as pd

    CAMPOS = ["fortalezas", "oportunidades_mejora", "hallazgos", "no_conformidades", "recomendacion_desempeno"]

    # Normalizar nombre de proceso
    df["proceso"] = df["proceso"].str.strip().str.upper()

    # Separar por tipo
    df_i = df[df["tipo_auditoria"].str.lower().str.contains("interna", na=False)].copy()
    df_e = df[df["tipo_auditoria"].str.lower().str.contains("externa", na=False)].copy()

    def agregar(sub_df: "pd.DataFrame", sufijo: str) -> "pd.DataFrame":
        sub_df = sub_df.groupby("proceso")[CAMPOS].agg(lambda x: " | ".join(filter(None, x))).reset_index()
        sub_df.columns = ["proceso"] + [f"{c}_{sufijo}" for c in CAMPOS]
        return sub_df

    df_i_agg = agregar(df_i, "interna") if not df_i.empty else pd.DataFrame(columns=["proceso"] + [f"{c}_interna" for c in CAMPOS])
    df_e_agg = agregar(df_e, "externa") if not df_e.empty else pd.DataFrame(columns=["proceso"] + [f"{c}_externa" for c in CAMPOS])

    # Merge full outer join para incluir procesos que solo están en uno
    merged = pd.merge(df_i_agg, df_e_agg, on="proceso", how="outer")
    merged = merged.fillna("")
    merged = merged.sort_values("proceso").reset_index(drop=True)
    return merged


if __name__ == "__main__":
    main()
