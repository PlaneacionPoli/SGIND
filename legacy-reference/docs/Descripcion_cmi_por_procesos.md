🔹 Resumen (Resumen ejecutivo)

Objetivo de la pestaña
Propósito: ofrecer visión ejecutiva consolidada del estado del CMI por procesos en el corte seleccionado.
Decisiones: reportes de alta dirección, priorización de líneas de acción, validación rápida del estado institucional (por ejemplo, activar planes de contingencia para procesos en riesgo).
Estructura y navegación
Componentes: KPI cards (Indicadores activos, Cumplimiento promedio, Alertas, Riesgos), filtros globales (Año, Mes, Fuente), leyenda/footnote de filtrado.
Lógica: agregado a nivel institucional (todos los procesos) con opción de filtrar por año/mes; no hay drill directo a indicador desde todos los KPIs (algunos links faltan).
Usabilidad: buena claridad visual inicial; interacción limitada para profundizar (falta botón "Ver detalles" por KPI).
Visualizaciones
KPI cards: métricas principales (conteo de indicadores, % cumplimiento medio, # alertas/# riesgos). Dimensiones: corte temporal; agregación: snapshot mensual/semestral. Pertinencia: adecuada para resumen; falta indicador de dispersión (desviación) y tendencia.
Tabla resumen breve (footnote): lista de filtros aplicados.
Fuentes de datos
Origen: Resultados Consolidados.xlsx y tracking via DataService(); lectura Excel con openpyxl. Campos clave: Id, Indicador, Cumplimiento_pct, Anio, Mes. Frecuencia: semestral/mensual según origen. Observaciones: ausencia de metadatos "última actualización" por widget.
Regla CMI por Procesos: se seleccionan solo indicadores con `Subprocesos == 1`; el flag `Ind act` está deprecado para esta vista y los activos deben validarse por año con un cruce de `Id` contra Kawak.
Tablas
Aplican mínimamente (resumen textual). Columnas: no hay tabla detallada en esta pestaña. Funcionalidades: filtros globales afectan KPIs. Relación: KPIs derivan de agregaciones de la tabla base.
Indicadores y cálculos
Indicadores: conteo, promedio de cumplimiento, cuentas de alertas/riesgos. Fórmulas implícitas: promedio simple de Cumplimiento_pct. Metas no mostradas aquí. Semaforización: visual (colores) pero umbrales no mostrados; lógica distribuida (CSS/variables).
Análisis y narrativa
Insights: headline estático (ej. corte Diciembre 2025) y footnote con regla de filtro. Tipo: descriptivo. Calidad: útil para snapshot, insuficiente para diagnóstico (no muestra causas ni tendencia).
Formato y diseño
Colores: paleta institucional y variables CSS para semáforos. Jerarquía visual: KPI cards priorizadas. Legibilidad: buena tipografía; contraste aceptable en KPI pero tablas podrían mejorar contraste.
Evaluación crítica
Vacíos: falta de tendencia temporal y medida de dispersión; no hay link directo a detalle por KPI.
Redundancias: ninguno crítico en resumen.
Inconsistencias: ausencia de leyenda de semáforo y de metadatos de actualización.
Recomendaciones
Añadir sparklines/mini-series en cada KPI para tendencia (últimos 6 meses).
Mostrar "Última actualización" y origen exacto (fila/archivo).
Incluir legend de umbrales y link "ver indicadores asociados" en cada KPI.
Añadir desviación estándar o IQR para medir dispersion institucional.
🔹 Procesos y Unidades

Objetivo de la pestaña
Propósito: ofrecer desglose por tipo de proceso, ranking de procesos y variación vs año base.
Decisiones: reasignación de recursos, priorización de procesos con peor desempeño, detectar impactos por tipo de proceso.
Estructura y navegación
Componentes: tablas con conteos y cumplimiento por tipo de proceso; badge de "Monitoreo por tipo de proceso", lista de "Procesos con mejor cumplimiento", sección "Variación vs 2024". Filtros: Unidad, Proceso, Subproceso, Frecuencia, Año, Mes.
Lógica: agrupación principal por Proceso_padre/Tipo de proceso; comparativa año a año.
Usabilidad: tablas densas pero legibles; falta interacción de ordenamiento dinámico y drill desde cada fila.
Visualizaciones
Tablas (principal): tipo = tabla; muestra Proceso, indicadores, cumplimiento. Dimensiones: proceso; agregación: promedio por proceso (anual/corte). Pertinencia: tabla adecuada para ranking; sería más eficiente un bar chart horizontal para comparar cumplimientos.
Variación vs 2024: tabla delta (cumplimiento 2025 vs 2024). Pertinencia: alta para diagnóstico cambio relativo.
Fuentes de datos
Origen: tracking_df (DataService) + mapeo Subproceso-Proceso-Area.xlsx. Campos clave: Proceso_padre, Tipo de proceso, Cumplimiento/Cumplimiento_pct, Anio. Frecuencia: anual/mensual según corte. Observaciones: falta validación de tipos de proceso nulos y registro de procesos sin nombre (filas con proceso vacío detectadas).
Tablas
Columnas: Tipo de proceso, indicadores, cumplimiento, Proceso, Cumplimiento 2025, Cumplimiento 2024, Delta. Tipos: texto, entero, porcentaje. Funcionalidades: filtros aplicados desde la UI; falta búsqueda libre en tabla y export. Relación: alimentan KPI y treemap en otras vistas.
Indicadores y cálculos
Indicadores: conteo indicadores por proceso, cumplimiento medio por proceso, delta interanual. Fórmulas: cumplimiento_mean = mean(Cumplimiento_pct), Delta = Cumplimiento_2025 - Cumplimiento_2024. Metas no expuestas en la tabla. Semaforización: no aplicada en la tabla (solo en KPIs).
Análisis y narrativa
Insights: listados de top procesos y delta; tipo de análisis descriptivo/diagnóstico básico. Calidad: útil, pero carece de explicación sobre causas (por ejemplo, por qué hay subprocesos sin datos).
Formato y diseño
Uso de badges y tablas, tipografía consistente. Falta visual de comparación (barras horizontales/heatmap) para detectar outliers rápidamente.
Evaluación crítica
Vacíos: sin alertas dinámicas por proceso ni métricas de volumen (peso relativo por indicador).
Redundancias: tablas de top procesos se repiten entre pestañas (posible duplicidad de contenido).
Inconsistencias: filas con proceso vacío/NaN aparecen; no hay validación para ocultarlas o señalarlas.
Recomendaciones
Añadir gráfico de barras horizontales ordenadas por cumplimiento y una opción para normalizar por número de indicadores.
Implementar ordenamiento y búsqueda en tablas; permitir export CSV.
Marcar filas con datos incompletos y exponer contadores de "sin mapeo".
Añadir un heatmap mensual por proceso para ver estacionalidad y dispersion.
🔹 Indicadores

Objetivo de la pestaña
Propósito: ofrecer listado granular de indicadores con Meta, Ejecución y %Cumplimiento.
Decisiones: decisiones operativas, verificación de soportes y validación de responsables.
Estructura y navegación
Componentes: tabla detallada (muestra muestra de 25 indicadores en HTML; en Streamlit la tabla es dinámica), filtros de búsqueda por nombre, línea, objetivo, clasificaciones y tipo. Lógica: vista por indicador con posibilidad de filtrar por proceso/unidad. Usabilidad: buena búsqueda por texto, pero falta columna de trazabilidad (link a origen).
Visualizaciones
Tabla principal: tipo = tabla detallada (DataFrame). Métrica principal: Meta, Ejecucion, Cumplimiento_pct. Dimensiones: Indicador, Proceso, Unidad. Agregación: snapshot por mes. Pertinencia: tabla necesaria, pero sería mejor incorporar mini-gráficos (sparklines) y semáforo visual en columna.
Fuentes de datos
Origen: Indicadores por CMI.xlsx (catalogo) + Resultados Consolidados.xlsx para ejecución. Campos clave: Id, Indicador, Meta, Ejecucion, Cumplimiento_pct, Unidad. Frecuencia: corte mensual/semestral. Observaciones: múltiples valores — y 0.0% que requieren limpieza; tipo de dato inconsistente (ej. Meta en int/float/texto).
Tablas
Columnas mostradas: Indicador, Proceso, Subproceso, Unidad, Meta, Ejecucion, Cumplimiento_pct. Tipos: texto, int/float, porcentaje. Funcionalidades: filtrado por UI; orden y búsqueda básica; sin pivot ni agrupado inline. Relación: cada fila alimenta alertas/riesgo y puede mapearse a PDI.
Indicadores y cálculos
Indicadores presente: Cumplimiento individual (Ejecucion/Meta), tasas (accidentalidad), índices (severidad). Fórmulas: implícitas, no centralizadas. Metas: mostradas por registro pero no validadas ni tipificadas (p.ej. meta 0 vs no aplica). Semaforización: visual en otras pestañas pero no columna semáforo en tabla.
Análisis y narrativa
Insights: escasos dentro de la tabla (solo datos). Tipo: descriptivo. Calidad: adecuada para consulta; no incorpora análisis automático (ej. causas, soportes, outlier detection).
Formato y diseño
Legibilidad correcta; densidad alta en tablas; falta densidad visual (badges semáforo, mini charts). Consistencia: columnas consistentes entre vistas, aunque nombres de columnas varían (p. ej. Cumplimiento vs Cumplimiento_pct).
Evaluación crítica
Vacíos: no existe enlace a fila original, falta campo source_row/data_origin.
Redundancias: columnas duplicadas entre vistas (mismos datos presentados sin agregaciones distintas).
Inconsistencias: tipos inconsistentes y símbolos no normalizados (—).
Recomendaciones
Añadir columna de trazabilidad (archivo+sheet+row o link al registro).
Añadir sparkline por indicador y columna semáforo calculada por función central.
Validar y normalizar tipos al ingest; añadir flags QC (missing_meta, missing_exec).
Permitir export filtrado y filtro avanzado (p. ej. indicadores sin soporte documental).
🔹 Alertas

Objetivo de la pestaña
Propósito: concentrar indicadores en riesgo/alerta para priorización y respuesta inmediata.
Decisiones: activar planes de mitigación, reasignar recursos, pedir evidencias.
Estructura y navegación
Componentes: listado de alertas (cards en HTML; tabla en Streamlit), clasificación por riesgo (Riesgo/Alerta), botón "Ver ficha". Filtros: proceso/linea/objetivo. Lógica: filtrado por Cumplimiento_pct y reglas heurísticas (caídas, sin reporte). Usabilidad: buena visual; botones de ficha son útiles pero ficha modal debe contener origen y historial.
Visualizaciones
Cards list y tabla: tipo = lista de tarjetas + tabla. Métrica: Cumplimiento_pct, ejecución y brecha. Dimensiones: indicador, línea, objetivo. Agregación: snapshot y comparación periodo a periodo. Pertinencia: alto impacto visual; complementarlo con scoring numérico y gráfico de tendencia individual.
Fuentes de datos
Origen: tracking + catalogo CMI. Campos clave: Cumplimiento_pct, Ejecucion, Meta, Anio, Mes. Frecuencia: corte actual; Observaciones: indicadores con 0.0% muy frecuentes (posible ingest fallida o periodicidad no coincidente).
Tablas
Columnas: Indicador, Proceso, Unidad, Cumplimiento_pct. Tipos: texto, porcentaje. Funcionalidades: botón ver ficha, orden por severidad. Relación: enlace directo a ficha del indicador y posible export de alertas.
Indicadores y cálculos
Indicadores: severidad (porcentaje bajo), velocidad de caída (delta interperiodo), sin-reportes (no data). Fórmulas: no centralizadas; no existe scoring compuesto por severidad×velocidad×exposición. Semaforización: derivada visualmente (rojo/naranja) pero no estandarizada.
Análisis y narrativa
Insights: lista de indicadores en riesgo; poco diagnóstico automatizado sobre causas. Tipo: descriptivo/diagnóstico básico. Calidad: operativo pero insuficiente para priorizar sin scoring.
Formato y diseño
Excelente uso de color y tarjetas; botón modal para ficha es buen patrón. Legibilidad buena; contrastes de color adecuados para semáforos.
Evaluación crítica
Vacíos: falta scoring numérico y consolidado por proceso/linea; falta evidencia (soportes) y trazabilidad en ficha.
Redundancias: algunas alertas replicadas en otras pestañas sin señal clara de prioridad.
Inconsistencias: indicadores con 0.0% necesitan triage (no es siempre "en riesgo").
Recomendaciones
Implementar scoring de riesgo (Severidad × Velocidad × Exposición) y orden de prioridad.
Añadir validación automática para diferenciar "sin dato" de "0% real" y mostrar causa (p.ej. periodicidad diferente).
Incluir enlace a evidencias y posibilidad de asignar acción/owner desde la ficha.
Añadir gráficos de tendencia (últimos 6-12 periodos) dentro de la ficha modal.
🔹 Propuesta (Propuesta de mejora)

Objetivo de la pestaña
Propósito: proponer medidas de mejora priorizadas y recomendaciones estratégicas (p. ej. PDI 2026-2030).
Decisiones: planificación de acciones de mejora, asignación de esfuerzos en PDI/SGA.
Estructura y navegación
Componentes: tarjetas de plan de mejoramiento, texto descriptivo, lista de retos. Filtros: contextual (unidad/proceso). Lógica: recomendaciones manuales+automatizadas. Usabilidad: buena para comunicación ejecutiva; falta trazabilidad de propuestas a indicadores específicos.
Visualizaciones
KPI cards con texto; no hay gráficas analíticas. Pertinencia: ok para resumen, insuficiente para seguimiento de avance de acciones.
Fuentes de datos
Origen: derivadas del análisis y posiblemente de sistema de acciones (no integrado). Campos: no definidos de forma explícita. Observaciones: contenido mayormente editorial/manual.
Tablas
No aplica (no hay tabla de acciones vinculadas). Falta columna de estado/owner/fechas.
Indicadores y cálculos
No hay cálculos formales; se requieren KPIs de seguimiento de plan (avance %, tiempo de cierre de OM). Semaforización: no aplicada.
Análisis y narrativa
Insights: recomendaciones textuales (ej. priorizar cierres en determinadas métricas). Tipo: prescriptivo a nivel manual. Calidad: buena como punto de partida, requiere conexión a datos para seguimiento.
Formato y diseño
Limpio, tarjetas legibles; falta acción directa (crear acción, asignar responsable). Consistencia con resto del dashboard aceptable.
Evaluación crítica
Vacíos: no hay integración con registro de acciones/OM ni seguimiento automatizado.
Redundancias: recomendaciones generales pueden duplicar lo que pone "Alertas".
Inconsistencias: falta indicadores de impacto estimado de las propuestas.
Recomendaciones
Conectar propuestas a un registro de acciones (tabla con owner, fecha fin, % avance).
Añadir estimación de impacto (p. ej. si se mejora cumplimiento X pp, impacto institucional Y).
Permitir crear/abrir OM directamente desde la tarjeta de propuesta y enlazar a indicador(s).
🔹 Análisis Avanzado

Objetivo de la pestaña
Propósito: aportar análisis más profundo (ranking, riesgos top, comparativas) y herramientas para diagnóstico avanzado.
Decisiones: establecer planes estratégicos con evidencia (simulaciones, identificación de drivers).
Estructura y navegación
Componentes: top procesos, top riesgos, tablas comparativas, sección de análisis estadístico (parcial). Filtros: avanzados (proceso, subproceso, periodo). Lógica: enfoque táctico/diagnóstico. Usabilidad: potente pero fragmentada; falta integración de workflow analítico (export, guardar exploraciones).
Visualizaciones
Tablas de ranking; treemaps (en scripts); posibles heatmaps y bar charts en prototipo. Métricas: cumplimiento, counts, riesgos. Dimensiones: proceso/linea/objetivo. Agregación: mensual/anual. Pertinencia: buena base; falta visuales de incertidumbre y distribución (boxplots).
Fuentes de datos
Origen: tracking completo (full_work_df) + mapeo PDI. Campos: series históricas (Anio, Mes, Cumplimiento). Frecuencia: histórica (multi-año). Observaciones: no hay pruebas automatizadas para garantizar serie temporal completa por indicador.
Tablas
Columnas: Proceso, indicadores, cumplimiento, Indicador, Cumplimiento_pct. Funcionalidades: comparativas año-año; falta pivot dinámico y export de análisis. Relación: tablas sirven como input para simulaciones manuales.
Indicadores y cálculos
Indicadores: top/bottom by cumplimiento, delta interanual, conteos de riesgo. Fórmulas: promedios y diferencias; faltan proyecciones y modelos de sensibilidad. Semaforización: visual en tablas, pero no unificada.
Análisis y narrativa
Insights: lista de top procesos y riesgos; tipo: descriptivo/diagnóstico. Calidad: útil para análisis táctico; falta predictivo y causal (qué está impulsando el cambio).
Formato y diseño
Adecuado para análisis técnico; sin embargo UI dispersa y sin facilidades para reproducir análisis (no hay "guardar vista" ni notebook integrado).
Evaluación crítica
Vacíos: no hay forecast automático ni simulador integrable; falta métricas de calidad y confianza.
Redundancias: algunos listados replican lo mostrado en pestañas anteriores.
Inconsistencias: ausencia de indicadores de cobertura histórica por indicador (missing periods).
Recomendaciones
Añadir módulos de forecasting sencillo (extrapolación lineal, promedio móvil) y visualización con bandas de confianza.
Incluir heatmap mensual por proceso y boxplot para ver dispersión por proceso.
Implementar control de calidad temporal: mostrar % de periodos con datos por indicador y alertar series incompletas.
Permitir export del dataset filtrado y un "modo exploratorio" que genere un notebook o JSON con query reproducible.
Resumen ejecutivo del diagnóstico (1 línea)

Arquitectura funcional sólida con buenas piezas (filtrado, mapeo PDI), pero necesita centralizar fórmulas/umbrales, robustecer trazabilidad y limpieza de datos, estandarizar semaforización y añadir elementos analíticos (tendencias, scoring, forecast) y mejoras de UX (export, drill, sparklines, trazabilidad).