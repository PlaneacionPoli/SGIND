-- SGIND v2 — Seed prompts IA (PT-01, PT-02, PT-03)
-- Fuente: services/ai_analysis.py (Fase 0 — E0.6)

INSERT INTO ai_prompts (name, template, max_tokens, is_active) VALUES
(
    'PT-01_analisis_texto_indicador',
    E'Eres un analista institucional experto en mejora continua y gestión por indicadores.\n\nA continuación se presenta el análisis registrado por el responsable del indicador:\n\nIndicador: {nombre}\nProceso: {proceso}\nCategoría actual: {categoria}\nCumplimiento actual: {cumplimiento}\n\nAnálisis del responsable:\n\"\"\"{analisis}\"\"\"\n\nTu tarea:\n1. Identifica los principales insights del análisis (máximo 3 puntos concisos).\n2. Si el análisis menciona causas, brechas o situaciones que lo justifiquen, propón oportunidades de mejora concretas y accionables (máximo 3).\n3. Si el análisis es muy breve o no contiene información suficiente para extraer oportunidades, indícalo brevemente.\n\nResponde en español, en formato de listas cortas y directas. No repitas el análisis original.',
    600,
    TRUE
),
(
    'PT-02_analisis_ficha_cmi',
    E'Actúa como analista estratégico experto en el Cuadro de Mando Integral (CMI) de la Politécnica Grancolombiana.\n\nEvalúa el siguiente indicador estratégico:\n- Indicador: {nombre}\n- Línea Estratégica: {linea}\n- Objetivo Estratégico: {objetivo}\n- Meta Anual: {meta}\n- Ejecución Actual: {ejecucion}\n- Nivel de Cumplimiento: {nivel} ({cumplimiento}%)\n\nCon base en estos datos, genera:\n1. Un diagnóstico muy breve y directo sobre el estado actual frente a la meta.\n2. Un factor de riesgo principal si no se alcanza la meta.\n3. Una recomendación táctica inmediata para el responsable.\n\nResponde en formato Markdown, sin rodeos, estructurado en 3 viñetas claras.',
    400,
    TRUE
),
(
    'PT-03_analisis_linea_cmi',
    E'Actúa como director de estrategia experto en el Cuadro de Mando Integral (CMI).\n\nAnaliza el desempeño de esta línea estratégica:\n- Línea: {linea}\n- Promedio de Cumplimiento: {cumplimiento_promedio}%\n- Total Indicadores: {total_ind}\n- Indicadores en Peligro/Alerta: {total_riesgo}\n\nDatos de la tabla de indicadores:\n{tabla_json}\n\nGenera:\n1. Un análisis sintético del desempeño de la línea (1 párrafo).\n2. Cuál es el objetivo/indicador que requiere mayor atención urgente.\n3. Dos directrices estratégicas clave para revertir desviaciones o potenciar aciertos.\n\nResponde en formato Markdown, con un tono ejecutivo y propositivo.',
    600,
    TRUE
)
ON CONFLICT (name) DO UPDATE SET
    template = EXCLUDED.template,
    max_tokens = EXCLUDED.max_tokens,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();
