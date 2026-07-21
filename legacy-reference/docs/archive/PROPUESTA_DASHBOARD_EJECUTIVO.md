# PROPUESTA DE ARQUITECTURA DE DASHBOARD EJECUTIVO

## Sistema de Indicadores Institucionales — SGIND

**Versión documentoo:** 1.0  
**Fecha:** 22 de abril de 2026  
**Clasificación:** Propuesta de Arquitectura — Nivel Consultoría Enterprise  
**Proyecto de referencia:** Sistema de Indicadores Institucionales (SGIND) — Politécnico Grancolombiano  
**Alcance:** Diseño de arquitectura de dashboard de alto nivel para gestión institucional

---

# RESUMEN EJECUTIVO

Este documento propone una arquitectura integral de dashboard ejecutivo para el Sistema de Indicadores Institucionales (SGIND) del Politécnico Grancolombiano. La propuesta se fundamenta en el análisis técnico exhaustivo del proyecto existente, que comprende más de 1.000 indicadores consolidados desde múltiples fuentes (API Kawak, Excel histórico, catálogos institucionales, LMI Reporte) con un pipeline ETL de tres pasos que procesa 60.000+ registros mensuales y una suite de visualizaciones en Streamlit completamente funcionales.

La arquitectura propuesta se organiza en tres niveles jerárquicos de decisión (Estratégico, Táctico, Operativo), conectadas mediante navegación natural y un sistema de filtros inteligentes con dependencias contextuales. Se incorporan módulos de inteligencia artificial para análisis predictivo, detección de anomalías y copiloto conversacional que complementan las capacidades actuales del sistema. El modelo de gobernanza define roles de consumo, alimentación, validación y auditoría con trazabilidad completa.

La propuesta reutiliza el 85% de la lógica de negocio existente (cálculos de cumplimiento, categorización semántica, tendencias, нормализация), preserva la inversión actual en infraestructura de datos y añade valor ejecutivo mediante visuales Decisiongrade, storytelling estructurado y capacidades predictivas que el sistema actual no soporta nativamente.

**Supuestos de diseño adoptados:**

- Datos consolidados disponibles mensualmente con periodicidad de cierre: diciembre para anuales, junio para semestrales
- Indicadores categorizados en 6 líneas estratégicas: Expansión, Transformación Organizacional, Calidad, Experiencia, Sostenibilidad, Educación para Toda la Vida
- Sistema de categorización vigente: Peligro (<80%), Alerta (80-99%), Cumplimiento (100-104%), Sobrecumplimiento (≥105%)
- Indicadores Plan Anual con régimen especial: umbral 95%, tope máximo 100%
- Sistema de Oportunidades de Mejora (OM) activo con seguimiento de avance
- Datos de calidad disponibles desde Monitoreo_Informacion_Procesos
- Información de auditoría estructurada desde auditoria_resultados.xlsx

---

# 1. ARQUITECTURA GENERAL DEL DASHBOARD

## 1.1 Modelo de Niveles Jerárquicos

La arquitectura propuesta implementa un modelo de tres niveles interconectados que responde a las necesidades específicas de cada audiencia, desde la visión macro institucional hasta el análisis micro de indicadores individuales.

### Nivel 1 — Vista Estratégica (Macro)

**Usuario principal:** Alta dirección, rectoría, presidencia, consejo directivo, vicerrectores

Este nivel proporciona una visión institucional de 360 grados que permite a los tomadores de decisiones comprender rápidamente el estado general de la institución sin profundizar en detalles operativos. La información se presenta de manera agregada, visual y narrativamente estructurada para facilitar la comprensión en contextos de reunión ejecutiva.

Las preguntas que responde este nivel son: ¿Cómo we're performing globally versus our strategic targets?, ¿Cuáles líneas estratégicas están impulsando o frenando nuestro desempeño?, ¿Qué riesgos críticos requieren atención inmediata?, ¿Cuál es la proyección de cierre anual basada en tendencias actuales?, ¿Cómo comparamos versus el período anterior y versus la meta institucional?

Este nivel utiliza representaciones visuales de alto nivel como sunburst jerárquico, indicadores gauge de cumplimiento global, trendlines sparkline por línea estratégica, mapa de calor de riesgos y tablas de ranking ejecutivo. La frecuencia de actualización recomendada es mensual, con embargo de alertas en tiempo real para eventos críticos.

### Nivel 2 — Vista Táctica (Seguimiento)

**Usuario principal:** Directores, decanos, líderes de proceso, coordinadores de área, equipo de calidad

Este nivel permite el seguimiento detallado del desempeño por áreas de responsabilidad,facultades, procesos y proyectos estratégicos. Los usuarios pueden drill-down desde la vista estratégica para identificar patrones, tendencias y áreas de mejora específica.

Las preguntas que responde este nivel son: ¿Por qué línea u objetivo específico we're underperforming?, ¿Qué procesos o subprocesos están contribuyendo al bajo cumplimiento?, ¿Cuáles indicadores específicos requieren plan de mejora?, ¿Cuál es el avance de las acciones correctivas registradas?, ¿Cómo se compara el desempeño entre sedes o programas?

Este nivel implementa visualizaciones comparativas como barras apiladas por proceso/subproceso, heatmaps de evolución temporal, waterfall de contribución por categoría, tablas de detalle con drill-down y cohortes de seguimiento. La frecuencia de actualización es quincenal con alerts semanales para indicadores en deterioro.

### Nivel 3 — Vista Operativa (Micro)

**Usuario principal:** Analistas, equipos técnicos, responsables del dato, personal de calidad, operadores de sistema

Este nivel proporciona acceso granular a cada indicador individual, incluyendo metadatos completos, histórico de reportes, trazabilidad de fuentes, validationes de calidad y gestión de oportunidades de mejora.

Las preguntas que responde este nivel son: ¿Cuál es el valor exacto de meta, ejecución y cumplimiento para un indicador específico?, ¿Qué datos soporta este resultado y cuándo fueron reportados?, ¿Qué análisis cualitativo se ha registrado?, ¿La fuente está validada y cumple con estándares de calidad?, ¿Existe OM activa y cuál es su avance?

Este nivel utiliza tablas de datos enriquecidos con tooltips contextuales, timeline de evolución histórica, integration con sistema OM, panel dequality QC y trazabilidad completa. La frecuencia de actualización es diaria para datos crudos, semanal para consolidados.

## 1.2 Navegación Entre Niveles

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BARRA DE NAVEGACIÓN PRINCIPAL                    │
├─────────────────────────────────────────────────────────────────────┤
│  [🏠] SGIND     [Estrategia ▼] [Táctico ▼] [Operativo ▼]   [🔔]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  VISTA ACTUAL: ESTRATÉGICA (Macro)                                  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    DASHBOARD ESTRATÉGICO                       │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────��             │ │
│  │  │  TOTAL  │ │% CUMPL  │ │ALERTA   │ │PRONÓSTICO│ 🔽 Drill  │ │
│  │  │ KPIs    │ │Global   │ │Riesgos  │ │Cierre   │   Down    │ │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘             │ │
│  │                                                             │ │
│  │  [Ir a Línea →] [Ir a Objetivo →] [Ir a Indicador →]        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

La navegación implementa patrones de drill-down consistentes:

- Click en cualquier tarjeta de línea estratégica → Navega a vista táctica filtrada por esa línea
- Click en objetivo → Navega a detalle de indicadores de ese objetivo
- Click en indicador individual → Navega a ficha completa en vista operativa
- Breadcrumbs persistentes en toutes las vistas mostrando ruta de navegación
- Botón "Volver arriba" flotante para regresarn al nivel superior

---

# 2. PROPUESTA DE PESTAÑAS (TABS)

## 2.1 Estructura de Pestañas por Nivel

Based on el analysis del proyecto existente y las necesidades de decision de cada nivel, se propone la siguiente estructura de pestañas organizada jerárquicamente:

### Pestañas Nivel 1 — Estratégico

| # | Pestaña | Objetivo Principal | Usuario Clave | Criticidad | Decisiones Soportadas |
|---|--------|------------------|--------------|-----------|---------------------|
| 1 | **Resumen Ejecutivo** | Vista consolidada del estado institucional con métricas clave y narrativa automática | Rector, Consejo Directivo | 🔴 CRÍTICA | Revisión mensual de desempeño institucional, ajustes de política |
| 2 | **Cumplimiento Estratégico** | Seguimiento de KPIs PDI por líneas y objetivos estratégicos | Vicerrectores, Directores | 🔴 CRÍTICA | Priorización de recursos, rebalanceo estratégico |
| 3 | **Alertas y Riesgos** | Identificación proactiva de riesgos críticos con scoring | Alta Dirección | 🔴 CRÍTICA | Intervención temprana, activación de planes de contingencia |
| 4 | **Pronóstico y Simulación** | Proyección de cierre anual con escenarios what-if | Alta Dirección, Planeación | 🟡 ALTA | Ajustes de meta, planificación de recursos |

### Pestañas Nivel 2 — Táctico

| # | Pestaña | Objetito Principal | Usuario Clave | Criticidad | Decisiones Soportadas |
|---|--------|------------------|--------------|-----------|---------------------|
| 5 | **Seguimiento por Área/Proceso** | Desempeño detallado por proceso y subproceso | Directores, Líderes | 🟡 ALTA | Asignación de acciones de mejora, seguimiento de planes |
| 6 | **Gestión de OM** | Panel de oportunidades de mejora con avance | Equipo Calidad, Directores | 🟡 ALTA | Priorización de recursos de mejora, cierre de ciclos |
| 7 | **Proyectos Estratégicos** | Seguimiento de proyectos PDI y su contribución a indicadores | Coordinadores PDI | 🟢 MEDIA | Ajuste decronogramas, recursos |
| 8 | **Comparativas** | Análisis comparativo período a período, sede a sede | Directores, Planeación | 🟢 MEDIA | Identificación mejores prácticas |

### Pestañas Nivel 3 — Operativo

| # | Pestaña | Objetivo Principal | Usuario Clave | Criticidad | Decisiones Soportadas |
|---|--------|------------------|--------------|-----------|---------------------|
| 9 | **Explorador de Indicadores** | Consulta granular de cualquier indicador | Analistas, Responsable Dato | 🟢 MEDIA | Diagnóstico específico, validación |
| 10 | **Trazabilidad y QC** | Auditoría de fuentes, validationes, lineage | Data Engineer, QA | 🟢 MEDIA | Validation de calidad, investigación |
| 11 | **Calidad de Datos** | Métricas de calidad desde Monitoreo_Informacion_Procesos | Equipo Calidad | 🟢 MEDIA | Planes de mejora de calidad |
| 12 | **Auditorías** | Hallazgos de auditoría interna y externa | Equipo Calidad, Directores | 🟢 MEDIA | Planes de accióncorrectiva |

### Pestaña Transversal (Todos los Niveles)

| # | Pestaña | Objetivo Principal | Usuario Clave | Criticidad | Decisiones Soportadas |
|---|--------|------------------|--------------|-----------|---------------------|
| 13 | **IA Insights Center** | Centro de inteligencia artificial integrados | Todos los usuarios | 🟡 ALTA | Análisis automatizado, recomendaciones |

## 2.2 Descripción Detallada por Pestaña

### Pestaña 1: Resumen Ejecutivo

**Objetivo:** Proporcionar una vista instantánea del estado institucional que permita a la alta dirección comprender la situación en menos de 60 segundos y tener una narrativa lista para pérdelay.

Esta pestaña responde a la necesidad crítica de tener información consolidada y narrativamente estructurada para sesiones de consejo directivo y reuniones ejecutivo-as). Implementa un sistema de storytelling automático que proporciona: headline de estado (ej. "Institución-en linea de cumplir metas anualmente, con 3 líneas en riesgo"), key highlights (logros del período), lowlights (areas de atención inmediata), ynext steps sugeridos.

Los KPIs principales incluyen: Total indicadores activos, Porcentaje de cumplimiento global, Cantidad en Peligro, Cantidad en Alerta, Proyección de cierre, Variación vs período anterior, Tendencia (mejora/stable/empeora).

**Usuario principal:** Rector, presidente, consejo directivo, vicerrectores.

**Decisiones que soporta:** Revisión mensual de desempeño institucional, presentaciones executivas, ajustes de política estratégica de alto nivel.

**Nivel de criticidad:** 🔴 CRÍTICA — Es la pestaña de entrada principal para la alta dirección y debe reflejar el estado real en tiempo real.

### Pestaña 2: Cumplimiento Estratégico

**Objetivo:** Visualizar el avance de los indicadores PDI alineados a las 6 líneas estratégicas (Expansión, Transformación Organizacional, Calidad, Experiencia, Sostenibilidad, Educación para Toda la Vida) con drill-down hasta nivel de indicador individual.

El proyecto existente ya реалиiza visualización CMI Strategist a través las funciones `preparar_pdi_con_cierre()` y `load_pdi_catalog()` desde `services/strategic_indicators.py`. Esta pestaña reutiliza la infraestructura existente y añade: Comparativa año contra año por línea, Ranking de objetivos por cumplimiento, breakdown detallado por indicador, y asociación automática a OM cuando corresponde.

Esta pestaña implementa las visualizaciones siguientes:

- **Sunburst jerárquico** (línea → objetivo → indicador): Muestra la estructura jerárquica con colores por nivel de cumplimiento. Este visual ya existe parcialmente en `resumen_general.py:_build_sunburst()` y debe adaptarse.

- **Barras horizontales por línea**: Comparativa de cumplimiento promedio por línea estratégica con benchmark de meta (100%). Colores según category.

- **Sparklines históricas**: Evolución del cumplimiento por línea en los últimos 6 períodos para identificar tendencias.

- **Tabla de ranking ejecutivo**: Listado priorizado de indicadores en Peligro/Alerta con filtro por línea y objetivo.

### Pestaña 3: Alertas y Riesgos

**Objetivo:** Consolidar todas las señales de riesgo en una vista unificada con scoring de criticidad que permita priorización automática de atención.

Esta pestaña identifica y categoriza riesgos en múltiples dimensiones: Indicadores en Peligro (>10pp bajo meta o <70%), Indicadores que han caído más de 15pp vs período anterior, Indicadores sin reporte en ventana de periodicidad, Tendencias descendentes detectadas (3+ períodos consecutivos de caída), y OM vencidas sin cierre.

Implementa una matriz de riesgo combinada que pondera: Severidad (nivel de cumplimiento), Velocity (velocidad de deterioro), Exposure (% de indicadores afectados), y Complexity (dependencias con otros indicadores). Genera scoring automático de riesgo por línea/objetivo.

### Pestaña 4: Pronóstico y Simulación

**Objetivo:** Proyectar el cierre institucional con modelospredictivos simples y permitir simulación what-if de escenarios.

Utiliza técnicas de extrapolación lineal y promedio móvil para proyectar cierre anual basado en tendencias históricas. Permite configurar escenarios optimistas (asumir mejora del 5% mensual), base (mantener tendencia actual), y pesimistas (asumir deterioro del 3% mensual).

Implementa visualización de conos de incertidumbre que muestran rango probable de cierre, y sensitivity analyze mostrando qué líneas/objetivos tienen mayor impacto en el resultado final.

### Pestaña 5: Seguimiento por Área/Proceso

**Objetivo:** Proporcionar vista detallada del desempeño por proceso y subproceso según la jerarquía oficial (Proceso → Subproceso → Área).

Esta pestaña reutiliza la estructura existente en `resumen_por_proceso.py`, que ya carga datos desde Monitoreo_Informacion_Procesos y soporta filtrado por proceso/subproceso. Añade mejoras: Comparativa de subprocesos, Identificación de subprocesos críticos (mayor concentración de Peligro), Evolución temporal de calidad de datos, Drills hacia indicadores individuales.

### Pestaña 6: Gestión de OM

**Objetivo:** Panel integral de seguimiento de Oportunidades de Mejora vinculadas a indicadores en riesgo.

El proyecto existente implementa esta funcionalidad completamente a través de `gestion_om.py` con registro en BD (SQLite/PostgreSQL), tracking de avance desde archivos PA_*.xlsx, asociación automática a indicadores en Peligro/Alerta, y estados (Abierta, En Ejecución, Cerrada, Retrasada).

La propuesta mejora esta pestaña con: Dashboard de métricas OM (cobertura, avance promedio, OM vencidas), Kanban visual por estado, Filtros avanzados por tipo (OM Kawak, Reto Plan Anual, Proyecto Institucional), Panel de actions detalle con responsible y fechas.

### Pestaña 7: Proyectos Estratégicos

**Objetivo:** Seguimiento de la contribución de proyectos estratégicos (PDI, PA, proyectos institucionales) a los indicadores de desempeño.

Mapea indicadores a proyectos asociados, muestra avance de proyecto vs avance de indicadores relacionados, e identifica gaps de contribución.

### Pestaña 8: Comparativas

**Objetivo:** Análisis comparativo multidimensional para identificar patrones y mejores prácticas.

Compara: Período actual vs anterior (mismo mes), Sede vs sede, Programa vs programa, Línea estratégica vs estratégica, Proceso vs proceso. Soporta filtering y exportación de insights.

### Pestaña 9: Explorador de Indicadores

**Objetivo:** Consulta granular de cualquier indicador con todos sus metadatos, valores históricos y análisis disponibles.

Proporciona: Búsqueda por ID o nombre, Ficha técnica completa del indicador, Histórico de valores por período, Análisis cualitativo reportado, Trazabilidad de fuente(s), y Comparativa con similar.

### Pestaña 10: Trazabilidad y QC

**Objetivo:** Panel de auditoría técnica del pipeline ETL y calidad de datos.

Muestra artefactos de ingesta (desde `data/output/artifacts/ingesta_*.json`), métricas QC (tasas de éxito, errores por tipo), lineage de datos por indicador, Log de ejecuciones ETL, y Validaciones aplicadas.

### Pestaña 11: Calidad de Datos

**Objetivo:** Visualizar métricas de calidad de datos desde la fuente Monitoreo_Informacion_Procesos.

Recupera los datos procesados por `_load_calidad_data()` desde el archivo Excel existente y muestra: Scores por criterio (Oportunidad, Completitud, Consistencia, Precisión, Protocolo), Heatmap de calidad por proceso/subproceso, Comparativa histórica, y Acciones de mejora recomendadas.

### Pestaña 12: Auditorías

**Objetivo:** Consolidar hallazgos de auditoría interna y externa en contexto de indicadores.

Integra datos desde `auditoria_resultado.xlsx` procesado por `_load_auditoria_excel()`, y muestra: Fortalezas identificadas, Oportunidades de mejora, Hallazgos, No conformidades, Recomendaciones de desempeño. Asocia cada hallazgo a indicadores relacionados cuando aplica.

### Pestaña 13: IA Insights Center

**Objetivo:** Centro de inteligencia artificial integrado que proporciona análisis automatizado, recomendaciones y copiloto conversacional.

Esta pestaña se detalla en la Section 6 de este documento.

---

# 3. DISEÑO DE VISUALES POR PESTAÑA

## 3.1 Sistema de Tarjetas KPI (Cards)

El sistema implementa un catálogo estandarizado de tarjetas KPI reutilizables en todas las pestañas:

### Tarjeta: KPI Principal

| Campo | Descripción | Ejemplo |
|-------|-------------|--------|
| Título | Nombre del metric | "Cumplimiento Global" |
| Valor | Valor actual formateado | "87.3%" |
| Variación | Cambio vs periodo anterior | "+2.1%" |
| Tendencia | Sparkline 6 períodos | 📈 |
| Estado | Semáforo de color | 🟢/🟡/🔴 |
| Meta | Target vs actual | Meta: 100% |
| Proyección | Forecast de cierre | "Proyectado: 94%" |

### Tarjeta: Indicador Crítico

| Campo | Descripción |
|-------|-------------|
| 아이콘 | Categoría semafórica |
| ID | Identificador del indicador |
| Nombre | Nombre corto |
| Cumplimiento | Porcentaje actual |
| Kritik | Nivel de criticidad (Alta/Media/Baja) |
| OM Vinculada | ID de action asociada |

### Tarjeta: Meta de Cierre

| Campo | Descripción |
|-------|-------------|
| Valor Actual | Cumplimiento a la fecha |
| Proyección | Forecast de cierre anual |
| Brecha | Distancia a meta 100% |
| Requerimiento | Mensual necesario para cumplir |

### Tarjeta: Alerta de Riesgo

| Campo | Descripción |
|-------|-------------|
| Nivel | Severidad (Critico/Alto/Medio) |
| Línea/Objetivo | Área afectada |
| Variación | Cambio vs anterior |
| Tendencia | Dirección (-2pp/mes) |
| Acción Sugerida | Recomendación automática |

### Tarjeta: Forecast IA

| Campo | Descripción |
|-------|-------------|
| Escenario | Optimista/Base/Pesimista |
| Proyección | Valor proyectado |
| Confianza | Intervalo de confianza |
| Factores Clave | Inputs del modelo |

## 3.2 Catálogo de Visualizaciones

Cada gráfico se selecciona específicamente para responder preguntas de decisión concretas:

### Gráficos de Estado (¿Qué pasó?)

| Gráfico | Uso | Pestañas | Justificación |
|--------|-----|---------|-------------|
| **Gauge** | Cumplimiento global vs meta | Resumen Ejecutivo | Provide visión instantánea de desviación de target, standard en dashboard executivos |
| **Donut** | Distribución por categoría | Resumen Operativo | Muestra proporción dePeligro/Alerta/Cumplimiento de forma efectiva |
| **Barras apiladas** | Composición por proceso | Seguimiento por Área | Permite comparar contribución de cada proceso al total |
| **KPI card con delta** | Métrica con variación | Todas | Indica dirección y magnitud del cambio de forma prominent |

### Gráficos de Análisis (¿Por qué pasó?)

| Gráfico | Uso | Pestañas | Justificación |
|--------|-----|---------|-------------|
| **Waterfall** | Contribución por categoría | Cumplimiento Estratégico | Descompone variación total en partes explicativas |
| **Barras agrupadas** | Comparativa periodo/area | Comparativas | Facilita identificación de outliers |
| **Heatmap** | Matriz Línea×Trimestre | Cumplimiento Estratégico | Identifica patrones temporales complejos |
| **Pareto** | Indicadores críticos | Alertas y Riesgos | Prioriza esfuerzo en pocos indicadores que explican mayoría |

### Gráficos de Tendencia (¿Qué pasará?)

| Gráfico | Uso | Pestañas | Justificación |
|--------|-----|---------|-------------|
| **Línea temporal** | Evolución histórica | CMI Estratégico, Pronóstico | Estándar para series temporales, permite extrapolación visual |
| **Área interpolada** | Evolución con incertidumbre | Pronóstico y Simulación | Muestra rango de proyecciones |
| **Sparkline** | Mini-trend en tarjeta | Resumen Ejecutivo | Maximiza información por pixel |
| **Boxplot** | Distribución por periodo | Comparativas | Muestra dispersión, no solo promedio |

### Gráficos de Estructura (¿Cómo se relaciona?)

| Gráfico | Uso | Pestañas | Justificación |
|--------|-----|---------|-------------|
| **Sunburst** | Jerarquía Línea→Objetivo | CMI Estratégico | Visualiza estructura jerárquica del PDI de forma interactive |
| **Treemap** | Proporciones por proceso | Seguimiento por Área | Compara áreas por tamaño y cumplimiento simultáneamente |
| **Sankey** | Flujo de contribuciones | Pronóstico | Muestra cómo líneas contribuyen al total |
| **Radar** | Perfil multidimensional | Comparativas | Compara áreas por múltiples métricas |

### Gráficos de Detalle Operativo

| Gráfico | Uso | Pestañas | Justificación |
|--------|-----|---------|-------------|
| **Tabla con drill-down** | Explorador detallado | Explorador de Indicadores | Permite navegación jerárquica |
| **Cohort** | Evolución por grupo | Comparativas | Tracking de patrones por cohort |
| **Scatter** | Correlación Meta/Ejec | Explorador | Identifica indicadores atypicals |
| **Funnel** | Proceso de mejora | Gestión de OM | Visualiza embudo de acciones |

## 3.3 Especificación de Visuales por Pestaña

### Resumen Ejecutivo

- Tarjetas KPI: Total indicadores, Cumplimiento Global, En Peligro, En Alerta, Proyección Cierre, Variación Historico
- Gráficos: Donut distribución, Gauge global, Barras top/bottom líneas, Sparklines históricas, Histórico tendencia 12 meses
- Tabla: Top 5 mejoras, Top 5 retrocesos vs periodo anterior

### CMI Estratégico

- Sunburst jerárquico (Línea→Objetivo→Indicador) con drill-down
- Barras horizontales por línea estratégica
- Tabla de indicadores críticos filtrables
- Evolución temporal sparklines por línea

### Alertas y Riesgos

- Matriz de riesgo (Severity×Probability) con scoring automático
- Lista priorizada de alertas con drill-down a indicador
- Waterfall de contribución al riesgo global por línea
- Timeline de alertas detectadas

### Pronóstico y Simulación

- Líneas de proyección (Optimista/Base/Pesimista) con conos de incertidumbre
- Tabla de sensibilidad (qué líneas impactan más el resultado)
- Comparativa de escenarios

### Seguimiento por Área/Proceso

- Heatmap de calidad por subproceso (cuando aplica datos de Monitoreo)
- Barras apiladas por proceso/subproceso
- Tabla comparativa con variationvs previous period
- Breakdown drill-down a indicadores

### Gestión de OM

- Kanban visual por estado (Abierta/En Ejecución/Cerrada/Retrasada)
- Tabla de OM con avance y responsible
- Gráfico de embudo (creadas→en ejecución→cerradas)
- Timeline de vencimiento

### IA Insights Center

- Panel de insights generados automáticamente
- Tabla de recomendaciones priorizadas
- Visual de anomalías detectadas
- Chat/copiloto conversacional

---

# 4. SISTEMA DE FILTROS INTELIGENTES

## 4.1 Clasificación de Filtros

### Filtros Globales (Aplican a Todas las Pestañas)

| Filtro | Tipo | Origen de Datos | Dependencias |
|--------|------|----------------|--------------|
| **Año** | Selector único | Datos consolidados (Años disponibles: 2022-2026) | Ninguna |
| **Periodo** | Selector múltiple/ Rango | Meses/Semestres/Trimestres disponibles | Año seleccionado |
| **Sede** | Selector múltiple | Catálogo de sedes (si aplica) | Ninguna |

Estos filtros se posicionan en la barra lateral izquierda y persisten a través de toutes las pestañas, permitiendo context switching sin pérdida de filtro.

### Filtros Contextuales por Nivel

**Nivel 1 — Estratégico:**

- Línea estratégica (6 opciones: Expansión, Transformación Organizacional, Calidad, Experiencia, Sostenibilidad, Educación para Toda la Vida)
- Objetivo estratégico (filtrable por línea)
- Tipo de indicador (CMI/OPEX/FINANCIERO/etc.)

**Nivel 2 — Táctico:**

- Proceso (desde jerarquía oficial)
- Subproceso (dependiente de Proceso)
- Área (dependiente de Subproceso)
- Responsable (desdecatálogo)
- Estado OM (Abierta/Ejecución/Cerrada/Todas)

**Nivel 3 — Operativo:**

- ID Indicador (búsqueda exacta o contains)
- Periodicidad (Mensual/Trimestral/Semestral/Anual)
- Estado (Peligro/Alerta/Cumplimiento/Sobrecumplimiento/Pendiente)
- Indicador tiene OM asociada (Sí/No)
- Rango de cumplimiento (slider)

## 4.2 Comportamiento de Filtros Dependientes

```
┌─────────────────────────────────────────────────────────────────┐
│                    JERARQUÍA DE FILTROS                        │
├─────────────────────────────────────────────────────────────────┤
│  [Año] ──→ [Periodo] ──→ [Línea] ──→ [Objetivo]           │
│                │                                            │
│    ┌──────────┴──────────┐                                 │
│    ▼                     ▼                                │
│ [Proceso] ──→ [Subproceso] ──→ [Área]                      │
│                           │                                 │
│                           ▼                                 │
│                    [Indicador] ──→ [Período Histórico]      │
└─────────────────────────────────────────────────────────────────┘
```

Cuando el usuario selecciona un valor en un filtro padre, los filtros hijos se actualizan automáticamente para mostrar solo opciones válidas basadas en la selección padre.

**Ejemplo de flujo:**

1. Usuario selecciona "2025" en Año
2. Periodo se actualiza a meses disponibles de 2025 (siempre incluye cierre Dic)
3. Si usuario selecciona "Expansión" en Línea, Objetivos filtra solo objetivos de esa línea
4. Si usuario selecciona "Proceso" luego, Subprocesos filtra solo subprocesos de ese proceso actual
5. Click en indicador filtra Histórico solo a ese indicador

## 4.3 Filtros Inteligentes con IA (Future State)

El sistema debe implementar en Fase 3 filtros predictivos que aprenden de patrones de uso:

- "Mis indicadores frecuentes" (basado en historial de navegación del usuario)
- "Similares a X" (basado en correlación histórica)
- "Suggestfilters" (basado en anomalías detectadas)
- "Alertas persistentes" (basado en indicadores que el usuario revisa frecuentemente cuando están en riesgo)

---

# 5. STORYTELLING EJECUTIVO

## 5.1 Estructura Narrativa del Dashboard

El dashboard implementa una narrativa de datos estructurada que guía al usuario a través de una historia coherente: ¿Qué pasó? → ¿Por qué pasó? → ¿Qué pasará? → ¿Qué debemos hacer?

### Secuencia de Lectura Natural

**Paso 1: Headline (10 segundos)**

El usuario llega al dashboard y ve imediatamente un headline ejecutivo que sintetiza el estado. Formato sugerido:

> "Institución termina {periodo} con {cumplimiento}% de cumplimiento global — {tendencia} de {variacion}% vs periodo anterior. {n} indicadores en Peligro requieren atención inmediata."

Esto se implementa en el area de "Resumen Ejecutivo" como prominently displayed KPI card.

**Paso 2: Contexto Visual (20 segundos)**

El usuario escanea visuales de alto nivel para comprender estructura. Sunburst muestra qué líneas contribuye más, Donut muestra distribución de estado, Trendlines muestran evolución.

**Paso 3: Detalle Selectivo (variable)**

El usuario drilla-down áreas específicas según su area de responsabilidad o interés. Filters y drill-down proporcionan acceso directo.

**Paso 4: Accion (próximo paso)**

Usuario identifica acciones necesarias y accede a funcionalidad de gestión (registrar OM, crear plan, agendar seguimiento).

## 5.2 Orden Narrativo por Pestaña

### Resumen Ejecutivo

1. **Headline**: Métricas key con variación vs anterior
2. **Sunburst**: Estructura de cumplimiento por línea
3. **Top movers**: Mejores y peores indicadores del periodo
4. **Pronóstico**: Proyección de cierre vs meta
5. **Acciones**: Botones de acción rápida (drill down, exportar, nueva OM)

### CMI Estratégico

1. **Por línea**: Cards de las 6 líneas con cumplimiento y tendencia
2. **Jerarquía**: Click en cualquier línea para detallado
3. **Heatmap**: Evolución trimestral por línea
4. **Detalle**: Objetivos que requieren atención

### Alertas y Riesgos

1. **Matriz de riesgo**: Vista general de criticidad por área
2. **Lista priorizada**: Alertasy riesgos ordenados por scoring
3. **Drill-down**: Detalle de cada alerta
4. **Acciones sugeridas**: Recomendaciones de remediation

---

# 6. MÓDULO DE IA INTEGRADO

## 6.1 Arquitectura del Centro de IA

El IA Insights Center se propone como pestaña transversal que centraliza capacidades de inteligencia artificial. La arquitectura se компоненты следующим образом:

```
┌───────────────────────────────────────────────────────────────────┐
│                  IA INSIGHTS CENTER                    │
├───────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐              │
│  │  Resumen IA     │  │ Insights       │              │
│  │  Automático    │  │ Detectados    │              │
│  └────────────────┘  └────────────────┘              │
│  ┌────────────────┐  ┌────────────────┐              │
│  │  Riesgos       │  │ Recomendaciones│   [💬 Chat]   │
│  │  Predichos     │  │  Generadas      │              │
│  └────────────────┘  └────────────────┘              │
└───────────────────────────────────────────────────────────┘
```

## 6.2 Funcionalidades de IA

### Resumen Ejecutivo Automático

**Input:** Datos del periodo actual + historico  
**Output:** Texto narrativo de 3-5 oraciones sintetizando estado

El sistema genera resúmenes usando templates predefinidos con datos dinámicos. Ejemplo:

> "La institución cierra {periodo} con cumplimiento del {x}%, {situación} respecto al {y}% del periodo anterior. {Línea} impulsa el desempeño con {cumplimiento}% promedio, mientras {Línea2} requiere atención con {cumplimiento}%. Se proyect{a} cerrar el año en {proyección}%."

### Hallazgos Clave

**Input:** Datos consolidados del periodo  
**Output:** Lista de 3-7 insights significativos

El sistema identifica:

- Cambio significative (>10pp) vs anterior
- Indicador outperformer (mayor mejora relative)
- Indicador underperformer (mayor deterioro)
- Tendencias anomalas (3+ periodos de deterioro)
- Breakouts de categoría (Peligro→Cumplimiento)
- Breakdown de categoría (Cumplimiento→Peligro)

### Desviaciones Relevantes

**Input:** Comparativa actual vs historico vs meta  
**Output:** Lista de desviaciones actionable

Detecta: Indicadores deviate >15pp de su promedio histórico, líneas onde performance está significativamente below tendencia, y procesos con concentración atypica de riesgo.

### Anomalías Detectadas

**Input:** Serie histórica de cada indicador  
**Output:** Lista de anomalías estadísticas

Utiliza técnicas simples (z-score >2.5, cambio >2 desviaciones estándar, patrones fuera de rango) para identificar datos que requieren investigación.

### Riesgos Potenciales

**Input:** Tendencias actuales + historico  
**Output:** Scoring de riesgo por línea/objetivo

Predice: Líneas con tendencia descendente sostenida (riesgo alto), objetivos cuyos indicadores están deteriorando consistentemente (riesgo medio), y areas con alta concentración de Peligro (riesgo crítico).

### Recomendaciones Automáticas

**Input:** Estado actual + patterns históricos + inventory de actions  
**Output:** Lista priorizada de recomendaciones

Sugiere automáticamente: "Crear OM para indicador [X] lleva 3+ periodos en Peligro", "Revisar proceso [Y] tiene concentración atypica de riesgo", "Considerar ajuste de meta para indicador [Z] given tendencia".

### Explicación de Causas

**Input:** Indicador en estado anomalous  
**Output:** Análisis de factores correlacionados

Identifica y presenta: Variables que más correlacionan con el valor del indicador, otros indicadores que muestran patrón similar, y factores externos identificados en análisis cualitativo.

### Predicción de Cierre

**Input:** Datos YTD + tendencias  
**Output:** Proyección de cierre por línea/objetivo/institución

Implementa modelos simples: Promedio móvil de cierre, Regresión lineal basada en tendencia, yescenarios configurable (optimista/pesimista).

### Simulación de Escenarios

**Input:** Parámetros configurables por usuario  
**Output:** Impacto proyectado en cierre

Permite al usuario configurar "what-if": "¿Qué pasa si todos los indicadores en Alerta mejoran 10pp?", "¿Qué pasa si OM vinculadas cierran con avance promedio histórico?"

### Preguntas Sugeridas

**Input:** Contexto actual + patrones  
**Output:** Lista de preguntas relevantes

Sugiere preguntas like: "¿Cuál es el indicador más crítico actualmente?", "¿Qué línea ha mejorado más en los últimos 3 periodos?", "¿Cuántas OM necesitamos cerrar para cumplir meta?"

### Copiloto Conversacional

**Input:** Consulta en lenguaje natural  
**Output:** Respuesta con visuales y datos relevantes

El usuario puede preguntar: "¿Cómo cerró Expansión este año?" → Sistema responde con métricas y visuales relevantes. "¿Qué indica que calidad bajará?" → Muestra indicadores relevantes, tendencia, y contexto.

## 6.3 Integración Técnica

### Opción A: API Externa (recomendada para fase 1)

Conectar a servicio de LLM (OpenAI, Anthropic, Google Vertex) mediante API para generación de resúmenes, insights, y chat. La implementación:

```python
# services/ai_insights.py (futuro)
def generar_resumen(data: pd.DataFrame, period: str) -> str:
    prompt = f"Genera resumen ejecutivo de 3 oraciones para datos..."
    response = llm.chat.completions.create(prompt, model="gpt-4")
    return response.choices[0].message.content

def analizar_preguntas(pregunta: str, data: pd.DataFrame) -> dict:
    # Retrieve contexto relevante
    # Generate respuesta
    # Suggest follow-ups
    return {"respuesta": "...", "visuales": [...], "siguientes": [...]}
```

### Opción B: Reglas Locales (fallback)

Para entornos sin acceso a APIs externas, implementar analisis basado en reglas. Menos sophisticated pero sin dependencias externas:

```python
# services/rule_based_insights.py (implementación local)
def detectar_cambios_significativos(df: pd.DataFrame) -> List[dict]:
    # Regla: Cambio >10pp vs anterior
    # Return: Lista de cambios significativos
    pass

def predecir_cierre(df: pd.DataFrame, linea: str) -> dict:
    # Promedio móvil simple
    # Return: Proyección optimista/pesimista
    pass
```

---

# 7. MEJORA UX/UI

## 7.1 Principios de Diseño

### Layout General

El dashboard sigue una estructura de three-column layout adaptada a Streamlit:

```
┌──────────────────────────────────────────────────────────────┐
│  BARRA SUPERIOR: Logo + Título + Usuario + Notificaciones     │
├─────────────┬────────────────────────────────────────────────┬────┤
│             │                                                │    │
│  SIDEBAR   │              MAIN CONTENT                     │ IA │
│  FILTROS  │              (Visuales y Datos)               │    │
│             │                                                │    │
│  [200px]   │           [flexible]                       │[250]│
│             │                                                │    │
├─────────────┴────────────────────────────────────────────────┴────┤
│  BARRA INFERIOR: Metadatos + Version + Help                    │
└──────────────────────────────────────────────────────┘
```

### Espaciado y Jerarquía Visual

- **Unidad base de spacing:** 8px (tomada de estándar Tailwind)
- **Padding de secciones:** 24px (3 unidades)
- **Gap entre cards:** 16px (2 unidades)
- **Margen de contenido:** 32px (4 unidades)
- **Border-radius:** 12px para cards, 8px para buttons

### Sistema de Colores

Los colores se mantienen fieles a lo existente y se norman:

```
COLORES INSTITUCIONALES:
├── Primario:     #0D2746 (Azul Poli profundo)
├── Secundario:  #1D4E89 (Azul Poli medio)
├── Acento:      #FBAF17 (Dorado)
└── Fondo:       #F5F7FA (Gris claro)

COLORES DE CATEGORÍA:
├── Peligro:     #D32F2F (Rojo)
├── Alerta:      #FBAF17 (Naranja/Dorado)
├── Cumplimiento:#43A047 (Verde)
└── Sobrecumpl:#6699FF (Azul)

COLORES DE LÍNEA (PDI):
├── Expansión:                    #FBAF17
├── Transformación Organizacional: #42F2F2
├── Calidad:                   #EC0677
├── Experiencia:              #1FB2DE
├── Sostenibilidad:            #A6CE38
└── Educación para Toda la Vida: #0F385A
```

### Iconografía

- Usar emoji set consistente para categorías y acciones
- Evitar iconos mixtos (algunos emoji, algunos font)
-Mantener iconografía unicode/emoji de forma consistente através

### Navegación

- Sidebar de navegación por nivel (Strategic/Tactical/Operational)
- Pestañas dentro de cada nivel
- Breadcrumbs para orientacion always visible
- Drills-down claramente indicated con arrows y tooltips

### Microinteracciones

- **Hover states:** Ligero cambio de opacidad (0.9->1.0)
- **Transitions:** 200ms ease-out para cambios de estado
- **Loading:** Skeleton screens durante carga de datos
- **Tooltips:** 150ms delay, position adaptativo

### Tooltips Enriquecidos

Cada elemento de dato muestra información adicional on hover:

- **Tarjeta KPI:** Meta, anterior, promedio histórico
- **Indicador tabla:** sparkline tendencias, último valor, variación
- **Gráfico:** Valores exacto al hover, contexto
- **Celda de tabla:** Metadatos, fuente, fecha de actualización

### Accesibilidad

- Contraste mínimo WCAG AA (4.5:1 texto, 3:1 UI elements)
- Alternativos textuales para gráficos complejos (disclaimer + tab-separated)
- Navegación por teclado completa
- Labels ARIA para controles
- Soporte para lectores de pantalla

### Responsive Design

Breakpoints adoptados:

- **Desktop:** >1200px — Layout completo de 3 columnas
- **Tablet:** 768-1200px — Sidebar collapsible, 2 columnas
- **Mobile:** <768px — Sidebar como drawer, 1 columna, scroll horizontal si es necesario

---

# 8. MODELO DE GOBERNANZA DEL DASHBOARD

## 8.1 Matriz de Responsabilidades

| Rol | Consumption | Input | Validation | Approval | Admin |
|-----|-------------|-------|------------|----------|-------|
| **Rector/Director** | Read-only | — | — | Aprobación estratégica | — |
| **Equipo Directivo** | Read-only | — | Comment | — | — |
| **Líder de Proceso** | Read + Filtros | Propuestas OM | Valida datos área | Aprueba OM su área | — |
| **Equipo Calidad** | Read + Filtros | Registra OM, Planes | Valida calidad, findings | Aprueba planes | — |
| **Analista BI** | Read + Filtros + Export | Reporta issues | Investiga issues | — | Mantiene templates |
| **Data Engineer** | Full | Pipeline, Sources | Valida QC | — | Mantiene ETL, sources |

## 8.2 Flujo de Datos y Validación

```
                    ┌──────────────────────────────────────┐
                    │     ETL PIPELINE (EXISTING)          │
                    │  consolidar → actualizar → reporte │
                    └──────────────┬───────────────────┘
                                 │
                    ┌────────────▼───────────────────┐
                    │   CONSOLIDATED DATA STORE    │
                    │  (ExcelResultados)        │
                    └──────────────┬───────────────────┘
                                 │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
┌───────▼───────┐      ┌───────▼───────┐      ┌───────▼───────┐
│  DASHBOARD    │      │  EXCEL       │      │  API        │
│  (streamlit)  │      │  EXPORT     │      │  (futuro)   │
└───────┬───────┘      └───────┬───────┘      └───────┬───────┘
        │                   │                   │
        │    ┌────────────┴────────────┐    │
        │    │   USER VALIDATION    │    │
        │    │  1. View data   │    │
        │    │  2. Filter    │    │
        │    │  3. Export   │    │
        │    │  4. Comment │    │
        │    └────────────────────┘   │
        │                         │
        │    ┌────────────────────┐
        │    │  OM WORKFLOW   │
        │    │  1. Create  │
        │    │  2. Assign │
        │    │  3. Update │
        │    │  4. Close │
        │    └────────────────────┘
```

## 8.3 Trazabilidad

Cada dato mostrado en el dashboard debe mantener trazabilidad completa:

- **Origen:** Fuente de datos (API Kawak, Excel, catálogo)
- **Timestamp:** Fecha de última actualización
- **Versión:** Identificador único del consolidado
- **Proceso:** Transformaciones aplicadas desde origen

**Implementation:**

- Incluir metadata en cada DataFrame de carga (`_cargar_consolidado_cierres` returns datos con metadatos)
- Display en footer: "Datos actualizados: {fecha} | Origen: {fuente} | Versión: {hash}"
- Log de acceso y exportación para auditoría

## 8.4 Control de Cambios

### Pipeline de Cambios

1. **Cambios menores** (filtros, formatting):
   - Approve: Analista BI
   - Implement: Direct en main branch

2. **Cambios mayores** (nuevas pestañas, calculado):
   - Approve: Equipo Calidad + Arquitectura
   - Review: PR con tests
   - Implement: Feature branch → Merge

3. **Cambios críticos** (fuentes, ETL):
   - Approve: Data Engineer lead
   - Review: Full test suite + QA sign-off
   - Implement: Release note + Rollback plan

### Versionado

- **Dashboard:** Major.Minor.Patch (ej. 1.0.0)
- **Data:** Fecha de consolidación (AAAAMMDD)
- **Changelog:** Git release notes

---

# 9. ROADMAP DE IMPLEMENTACIÓN

## 9.1 Fases Propuestas

### Fase 1 — Quick Wins (Semanas 1-3)

**Objetivo:** Entregar valor inmediato mejorando el sistema actual sin desarrollo significativo.

| # | Entregable | Esfuerzo | Impacto | Dependencias |
|---|-----------|----------|---------|--------------|
| 1 | Reorganizar existing pages en estructura de 3 niveles | Bajo | Alto | Ninguna |
| 2 | Agregar navegación con breadcrumbs y drill-down | Medio | Alto | Existentes páginas |
| 3 | Crear Pestaña 1: Resumen Ejecutivo mejorada | Medio | Alto | Datos existentes |
| 4 | Agregar filtros globales (Año, Periodo) a sidebar | Bajo | Alto | Ninguna |
| 5 | Mejorar tooltips con información context | Bajo | Medio | Ninguna |

**Criterio de éxito:** Users puede navegar de estratégico → indicador individual en menos de 3 clicks.

**Entregables técnicos:**

- Nuevo `app.py` con routing por nivel
- Templates de página por nivel
- Filtros globales persistentes en session_state

### Fase 2 — Optimización (Semanas 4-8)

**Objetivo:** Completar funcionalidades core del dashboard propuesto.

| # | Entregable | Esfuerzo | Impacto | Dependencias |
|---|-----------|----------|---------|--------------|
| 1 | Completar pestañas de Nivel 1 (Estatégico) | Medio | Alto | Fase 1 |
| 2 | Completar pestañas de Nivel 2 (Táctico) | Medio | Alto | Datos existentes |
| 3 | Implementar sistema de filtros dependientes | Medio | Alto | Ninguna |
| 4 | Agregarpronóstico básico (avg móvil) | Medio | Medio | Datos históricos |
| 5 | Implementar alertas y scoring de riesgo | Alto | Alto | Ninguna |
| 6 | Mejorar visuals (gauge, waterfall, heatmap) | Medio | Medio | Plotly existant |

**Criterio de éxito:** Dashboard proporciona todas las funcionalidades identificadas en sección 2 sin regression de features actuales.

**Entregables técnicos:**

- Módulos de visualización especializados (`components/charts_v2.py`)
- Motor de scoring de riesgo (`core/risk_score.py`)
- Pronóstico básico (`services/forecasting.py`)

### Fase 3 — IA Avanzada (Semanas 9-14)

**Objetivo:** Integrar capacidades de inteligencia artificial progresiva.

| # | Entregable | Esfuerzo | Impacto | Dependencias |
|---|-----------|----------|---------|--------------|
| 1 | Insights automático (reglas locales) | Medio | Medio | Fase 2 |
| 2 | Detección de anomalías(z-score) | Medio | Medio | Datos históricos |
| 3 | Pronóstico con escenarios | Alto | Alto | Fase 2 |
| 4 | Recomendaciones automáticas | Alto | Medio | Rules engine |
| 5 | Copiloto conversacional básico | Alto | Alto | API LLM externa |
| 6 | IA Insights Center completo | Alto | Alto | Todo anterior |

**Criterio de éxito:** IA proporciona insights accionables en al menos 80% de las consultas típicas de usuario.

**Entregables técnicos:**

- Módulo de insights (`services/ai_insights.py`)
- Motor de anomalías (`core/anomaly_detection.py`)
- Copiloto (`services/chatbot.py`)
- Integración API (configurable)

### Fase 4 — Gobernanza Predictiva (Semanas 15-20)

**Objetivo:** Completar modelo de gobernanza y preparar para producción enterprise.

| # | Entregable | Esfuerzo | Impacto | Dependencias |
|---|-----------|----------|---------|--------------|
| 1 | Implementar modelo de roles completo | Medio | Alto | Ninguna |
| 2 | Workflow de aprobación OM integrado | Alto | Alto | Datos existants |
| 3 | Sistema de auditoría y logging | Medio | Alto | Ninguna |
| 4 | Notificaciones automáticas | Medio | Medio | Email config |
| 5 | API REST pública | Alto | Alto | Ninguna |
| 6 | Mobile responsive | Alto | Medio | Ninguna |

**Criterio de éxito:** Sistema soporta operación enterprise con audit trail, approvals, y notificaciones.

## 9.2 Priorización Realista

Basado en análisis del proyecto existente, la siguiente priorización maximiza ROI dentro de recursos existentes:

### Prioridad Crítica (primero)

1. Reorganización en estructura de 3 niveles — Permite navegación clara
2. Resumen Ejecutivo mejorado — Vista de entrada para alta dirección
3. Filtros globales persistentes — Context switching sin fricción
4. Pronóstico básico — Necesidad no cubierta actualmente
5. Alertas y scoring de riesgo — Proaktiv gestión de riesgo

### Prioridad Alta

6. Gestión OM integrada en vista táctica — Visibilidad centralizada
7. Drills-down consistentes — Navegación fluida
8. Comparativas período a período — Análisis de tendencia
9. Heatmap de calidad por proceso — Cuando aplica datos Monitoreo

### Prioridad Media

10. IA InsightsCenter básico — Sin dependexternal APIs
11. Explorador de indicadores — Consulta granular
12. Trazabilidad y QC — Auditoría técnica
13. Exportaciones configurables — Consumo de usuarios

### Prioridad Futuro

14. Copiloto conversacional — Requiere API LLM
15. API REST — Requiere arquitectura adicional
16. Mobile — Requiere diseño adicional
17. Notificaciones automáticas — Requiere configuración email

---

# 10. ANÁLISIS DE BRECHAS Y OPORTUNIDADES

## 10.1 Estado Actual vs Propuesta

| Componente | Estado Actual | Estado Propuesto | Gap |
|-----------|------------|--------------|-----|
| Niveles de vista | No existen (1 página) | 3 niveles jerárquicos | ALTO |
| Navegación | Links básicos | Drill-down con breadcrumb | MEDIO |
| Filtros | Por página independiente | Globales + dependientes | ALTO |
| Pronóstico | No existe | Proyección con escenarios | ALTO |
| IA Insights | No existe | Centro completo | ALTO |
| Scoring de riesgo | Manual | Automático scoring | ALTO |
| Storytelling | No estructurado | Narrativa estructurada | MEDIO |
| Gobernanza | Parcial (documentado) | Completa | MEDIO |

## 10.2 Reutilización de Componentes Existentes

El sistema existente proporciona foundation sólida que la propuesta reutiliza:

### Componentes a Reutilizar (85%)

- `core/semantica.py`: Lógica de categorización, normalización
- `core/calculos.py`: Funciones de cálculo compartidas
- `services/strategic_indicators.py`: Carga PDI, préparation CMI
- `services/data_loader.py`: Carga de datos consolidados
- `gestion_om.py`: Workflow de OM (refinar, no reescribir)
- `resumen_por_proceso.py`: Calidad/processos (refinar)
- Pipeline ETL: Foundation de datos
- Test suite: Coverage de regresión

### Componentes a Crear/Mejorar

- `app.py`: Routing y navegación por niveles
- `components/dashboard/charts_v2.py`: Visualizaciones nuevas
- `components/dashboard/tabs/`: Nuevas pestañas
- `components/ia_insights/`: Centro de IA
- `core/filters.py`: Sistema de filtros inteligentes
- `core/forecasting.py`: Pronósticos
- `core/risk_scoring.py`: Scoring de riesgo

---

# 11. RECOMENDACIONES Y PRÓXIMOS PASOS

## 11.1 Recommendations Clave

1. **Priorizar navigation reorganizada:** La falta de estructura de niveles es el gaps más impactante para adoption executivo.

2. **Reutilizar 85% de código existente:** Avoid rewrites; focus en mejorar experiencia de usuario.

3. **Implementar pronóstico básico en Fase 2:** La predicción de cierre es necesidad urgently no covered.

4. **Adoptar IA progresivamente:** Start con reglas simples; evolucionar a LLM cuando haya validated data.

5. **Documentar gobernanza formally:** El proyecto ya tiene gobierno partial pero necesita formalización.

## 11.2 Criterios de Éxito Medibles

| Métrica | Baseline Actual | Target (Fase 2) | Target (Fase 4) |
|---------|--------------|------------------|------------------|
| Tiempo para drill-down estratégico→indicador | N/A (no existe) | <3 clicks | <2 clicks |
| Tasa de uso Resumen Ejecutivo | Unknown | +50% | +100% |
| Satisfacción usuario (encuesta) | Unknown | >4/5 | >4.5/5 |
| Cobertura de OM con scoring | 0% (manual) | 100% | 100% |
| Pronóstico disponible | No | Sí | Sí (con escenarios) |
| Insights IA automatizados | 0 | — | >20 |

## 11.3 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|-------|------------|---------|--------------|
| Complejidad de implementación | Alta | Alto | Phases incrementales con validación |
| Dependencia API externa para IA | Media | Medio | Fallback a reglas locales |
| Adoption de usuarios | Media | Alto | Change management, capacitación |
| Performance con grandes datasets | Media | Alto | Optimización de caché, lazy loading |
| Data quality issues | Alta | Alto | QC previo, validación en fuente |

---

# ANEXO A: MAPA DE COMPONENTES TÉCNICOS

## A.1 Estructura de Archivos Propuesta

```
streamlit_app/
├── app.py                          ← Entry point con routing por niveles
├── main.py                        ← [EXISTE]
├── pages/
│   ├── nivel1_estrategico/
│   │   ├── resumen_ejecutivo.py    ← NUEVO (mejorado)
│   │   ├── cumplimiento_pdi.py   ← MEJORADO (de cmi_estrategico.py)
│   │   ├── alertas_riesgos.py    ← NUEVO
│   │   └── pronostico.py        ← NUEVO
│   ├── nivel2_tactico/
│   │   ├── seguimiento_area.py   ← MEJORADO (de resumen_por_proceso.py)
│   │   ├── gestion_om.py       ← MEJORADO (existente)
│   │   ├── proyectos.py        ← NUEVO
│   │   └── comparativas.py    ← NUEVO
│   ├── nivel3_operativo/
│   │   ├── explorador.py       ← NUEVO
│   │   ├── trazabilidad.py  ← MEJORADO (de tablero_operativo.py)
│   │   ├── calidad_datos.py  ← MEJORADO
│   │   └── auditorias.py     ← MEJORADO
│   └── shared/
│       ├── ia_insights.py       ← NUEVO
│       └── api_resumen.py     ← NUEVO
├── components/
│   ├── charts/
│   │   ├── charts.py         ← [EXISTE]
│   │   └── charts_v2.py    ← NUEVO (gauge, waterfall, heatmap)
│   ├── filters/
│   │   └── filters.py     ← NUEVO (filtros inteligentes)
│   ├── cards/
│   │   └── kpi_cards.py  ← NUEVO (sistema de tarjetas)
│   └── navigation/
│       └── breadcrumbs.py  ← NUEVO
├── services/
│   ├── data_loader.py    ← [EXISTE]
│   ├── forecasting.py  ← NUEVO
│   ├── risk_scoring.py← NUEVO
│   ├── insights.py   ← NUEVO
│   └── chatbot.py    ← NUEVO
├── core/
│   ├── semantica.py ← [EXISTE]
│   ├── calculos.py ← [EXISTE]
│   ├── config.py  ← [EXISTE]
│   └── filters.py ← NUEVO (lógica de filtros)
```

## A.2 Dependencias de Datos por Pestaña

| Pestaña | Fuente Principal | Hoja Backup | Frecuencia |
|--------|---------------|-------------|-----------|
| Resumen Ejecutivo | Consolidado Cierres | — | Mensual |
| CMI Estratégico | Consolidado Cierres | Indicadores por CMI | Mensual |
| Alertas y Riesgos | Consolidado Historico | — | Mensual |
| Pronóstico | Consolidado Cierres | Histórico | Mensual |
| Seguimiento Área | Consolidado Semestral | Monitoreo | Mensual |
| Gestión OM | Consolidado Historico | Plan de acción, BD OM | Mensual |
| Proyectos | Indicadores por CMI | — | Mensual |
| Comparativas | Consolidado Cierres | — | Mensual |
| Explorador | Consolidado Historico | — | Mensual |
| Trazabilidad | artifacts/ingesta_*.json | — | Diaria |
| Calidad | Monitoreo | LISTA CHEQUEO | Mensual |
| Auditorías | auditoria_resultado.xlsx | — | Por auditoría |

---

*Documento generado como parte del proyecto SGIND*  
*Fecha de elaboración: 22 de abril de 2026*  
*Versión: 1.0*