# 04 - DASHBOARD Y VISUALIZACIÓN

**Documento:** 04_Dashboard.md  
**Versión:** 1.0  
**Fecha:** 22 de abril de 2026  
**Status:** ✅ Consolidado MDV

---

## 1. Páginas del Dashboard

| Página | Descripción | Fuente Principal | Status |
|--------|-------------|------------------|--------|
| **Resumen General** | Dashboard principal KPIs | Consolidado Cierres | ✅ Producción |
| **CMI Estratégico** | Indicadores PDI por líneas | Consolidado Cierres + Indicadores por CMI | ✅ Producción |
| **CMI Estratégico Tabulado** | Vista tabular del CMI | Consolidado Cierres | ✅ Producción |
| **CMI por Procesos** | Indicadores por proceso | Consolidado Semestral | ✅ Producción |
| **Plan de Mejoramiento** | Indicadores CNA | Consolidado Cierres + Indicadores por CMI | ✅ Producción |
| **Gestión OM** | Oportunidades de mejora | Consolidado Historico | ✅ Producción |
| **Resumen por Proceso** | Vista por proceso/subproceso | Consolidado Semestral | ✅ Producción |
| **Seguimiento Reportes** | Tracking de envío de reportes | Registros internos | 🟡 Beta |
| **Diagnóstico** | Validación de datos y sincronización | Data contracts | 🟡 Beta |
| **Informe por Procesos** | Reporte detallado por proceso | Consolidado Semestral | 🟡 Beta |
| **PDI Acreditación** | Indicadores para acreditación | Indicadores por CMI | 🟡 Beta |
| **Tablero Operativo** | Vista ejecutiva operacional | Consolidado Cierres | 🟡 Beta |

---

### 1.1 Descripciones Detalladas de Nuevas Páginas

#### CMI Estratégico Tabulado
- **Archivo:** `streamlit_app/pages/cmi_estrategico_tabulado.py`
- **Propósito:** Presentación tabular del CMI Estratégico (alternativa a vista jerárquica)
- **Datos:** Mismos indicadores que CMI Estratégico, diferentes visualización
- **Filtros:** Línea, Objetivo, Período
- **Status:** ✅ Producción

#### CMI por Procesos
- **Archivo:** `streamlit_app/pages/cmi_por_procesos_resumen.py`
- **Propósito:** Indicadores organizados por proceso y subproceso institucional
- **Datos:** Indicadores con jerarquía de procesos desde `Subproceso-Proceso-Area.xlsx`
- **Filtros:** Proceso, Subproceso, Período
- **Status:** ✅ Producción

#### Seguimiento Reportes (Beta)
- **Archivo:** `streamlit_app/pages/seguimiento_reportes.py`
- **Propósito:** Tracking de envío y entrega de reportes
- **Datos:** Registro interno (base datos local)
- **Filtros:** Período, Destinatario, Estado
- **Status:** 🟡 Experimental - puede cambiar

#### Diagnóstico (Beta)
- **Archivo:** `streamlit_app/pages/diagnostico.py`
- **Propósito:** Validación automática de datos y sincronización entre fuentes
- **Datos:** Análisis de data contracts vs datos reales
- **Alertas:** Infracciones de tipos, datos faltantes, inconsistencias
- **Status:** 🟡 Experimental

#### Informe por Procesos
- **Archivo:** `streamlit_app/pages/informe_por_procesos.py`
- **Propósito:** Reporte detallado de cumplimiento por proceso
- **Datos:** Consolidado Semestral + Jerarquía de procesos
- **Incluye:** Tablas, gráficos, resumen ejecutivo por proceso
- **Status:** ✅ Producción

#### PDI Acreditación
- **Archivo:** `streamlit_app/pages/pdi_acreditacion.py`
- **Propósito:** Indicadores específicos para proceso de acreditación institucional
- **Datos:** Indicadores con flag especial en `Indicadores por CMI.xlsx`
- **Filtros:** Año, Factor de acreditación
- **Status:** ✅ Producción

#### Tablero Operativo
- **Archivo:** `streamlit_app/pages/tablero_operativo.py`
- **Propósito:** Dashboard ejecutivo con vista consolidada de salud institucional
- **Datos:** Cierres semestrales + tendencias
- **KPIs:** Total, Peligro, Alerta, Cumplimiento, Sobrecumplimiento
- **Status:** 🟡 Producción

---

## 2. Catálogo de Gráficos

### 2.1 Gráficos Disponibles

| ID | Nombre | Tipo Chart | Uso |
|----|--------|------------|-----|
| `BAR_H` | Barra Horizontal | bar | Comparaciones por categoría |
| `BAR_V` | Barra Vertical | bar | Tendencias temporales |
| `LINE` | Línea | line | Evolución histórica |
| `PIE` | Pie | pie | Distribución proporcional |
| `SCATTER` | Dispersión | scatter | Correlaciones |
| `TABLE` | Tabla | table | Datos detallados |
| `GAUGE` | Medidor | gauge | Valores únicos vs umbral |
| `BOLINDER` | Bollinger | line | Bandas de volatilidad |
| `TREEMAP` | Treemap | treemap | Jerarquías |

### 2.2 Colores por Categoría

| Categoría | Color | Uso |
|-----------|-------|-----|
| Peligro | `#D32F2F` 🔴 | Cumplimiento < 80% (régimen Regular) |
| Alerta | `#FBAF17` 🟡 | Cumplimiento 80-99% (régimen Regular) |
| Cumplimiento | `#43A047` 🟢 | Cumplimiento 100%+ (régimen Regular) |
| Sobrecumplimiento | `#6699FF` 🔵 | Cumplimiento ≥ 105% (régimen Regular) |
| Sin Dato | `#9E9E9E` ⚪ | Sin información |

> Los mismos colores aplican a los otros dos regímenes de categorización
> (Plan Anual y Negativo-Porcentual), pero con cortes de porcentaje distintos
> — ver la tabla completa de los 3 regímenes en
> [`02_Logica_Indicadores.md`](02_Logica_Indicadores.md).

### 2.3 Personalización

```python
# Paleta personalizada
colores_personalizados = {
    "Peligro": "#D32F2F",
    "Alerta": "#FBAF17", 
    "Cumplimiento": "#43A047",
    "Sobrecumplimiento": "#6699FF"
}

# Aplicar a gráfico
fig = px.bar(df, x="mes", y="valor", color="categoria",
             color_discrete_map=colores_personalizados)
```

---

## 3. Indicadores Clave (KPIs)

### Dashboard Principal

| KPI | Descripción | Cálculo |
|-----|-------------|---------|
| Total Indicadores | Cantidad total | COUNT(*) |
| En Peligro | Indicadores < 80% | COUNT WHERE cumplimiento < 0.80 |
| En Alerta | Indicadores 80-99% | COUNT WHERE cumplimiento 0.80-0.99 |
| Cumpliendo | Indicadores ≥ 100% | COUNT WHERE cumplimiento ≥ 1.00 |
| % Cumplimiento Global | Promedio ponderado | SUM(ejecución) / SUM(meta) |

---

## 4. Filtros por Página

### Resumen General
- **Año:** Dropdown selección año
- **Período:** Semestre/Mes

### CMI Estratégico
- **Línea:** Dropdown líneas PDI
- **Objetivo:** Dropdown objetivos por línea
- **Indicador:** Búsqueda por ID/Nombre

### Plan de Mejoramiento
- **Factor:** Dropdown factores CNA
- **Característica:** Dropdown características
- **Estado OM:** Activa/Cerrada/Nueva

### Gestión OM
- **Estado OM:** Dropdown estados
- **Avance:** Slider rango %
- **Fecha creación:** Range date

---

## 5. Fuentes por Página

### Fuentes Detalladas

| Página | Función | Archivo | Entrada |
|--------|---------|---------|---------|
| resumen_general | `_load_consolidado_cierres()` | Resultados Consolidados.xlsx | Consolidado Cierres |
| cmi_estrategico | `load_cierres()` | Resultados Consolidados.xlsx | Consolidado Cierres |
| cmi_estrategico | `load_pdi_catalog()` | Indicadores por CMI.xlsx | Worksheet |
| cmi_estrategico | `get_cmi_estrategico_ids()` | cmi_filters.py | Worksheet (flags) |
| cmi_estrategico | `ai_analysis.generate_narrative()` | ai_analysis.py | DataFrame |
| cmi_estrategico_tabulado | `load_cierres()` | Resultados Consolidados.xlsx | Consolidado Cierres |
| cmi_por_procesos | `_load_calidad_data()` | Monitoreo_Informacion_Procesos.xlsx | Primera hoja |
| cmi_por_procesos | `load_procesos_map()` | Subproceso-Proceso-Area.xlsx | Worksheet |
| plan_mejoramiento | `load_cna_catalog()` | Indicadores por CMI.xlsx | Worksheet |
| plan_mejoramiento | `cargar_acciones_mejora()` | acciones_mejora.xlsx | Acciones |
| gestion_om | `cargar_dataset_historico()` | Resultados Consolidados.xlsx | Consolidado Historico |
| gestion_om | `_cargar_avance_om()` | Plan de accion/PA_*.xlsx | Primera hoja |
| resumen_por_proceso | `_load_calidad_data()` | Monitoreo_Informacion_Procesos.xlsx | Primera |
| resumen_por_proceso | `load_procesos_map()` | Subproceso-Proceso-Area.xlsx | Worksheet |
| seguimiento_reportes | `load_reporte_tracking()` | (Interno) | registros_om.db |
| diagnostico | `validate_data_contracts()` | data_contracts.yaml | Config |
| diagnostico | `_validate_consolidado()` | Resultados Consolidados.xlsx | Todas hojas |
| informe_por_procesos | `_load_calidad_data()` | Monitoreo_Informacion_Procesos.xlsx | Primera |
| informe_por_procesos | `load_procesos_map()` | Subproceso-Proceso-Area.xlsx | Worksheet |
| pdi_acreditacion | `load_cierres()` | Resultados Consolidados.xlsx | Consolidado Cierres |
| pdi_acreditacion | `filter_acreditacion_indicators()` | Indicadores por CMI.xlsx | Flag acreditación |
| tablero_operativo | `_load_base_data_by_type()` | (Múltiples) | Múltiples |
| tablero_operativo | `_generate_narrative()` | ai_analysis.py | DataFrame |

---

## 6. Resumen General - Modo Dinámico

### 6.1 Selector de Vista

La página **Resumen General** cuenta con un selector de modo que adapta la visualización según el tipo de datos:

| Modo | Descripción | Datos Mostrados |
|------|-------------|-----------------|
| **Indicadores** | Vista de indicadores PDI | Fichas, chips, Sunburst, narrativa de indicadores |
| **Proyectos** | Vista de proyectos institucionales | Chips de proyectos (cerrados/ejecución/planeación), Gantt 2022-2025 |
| **Plan de Retos** | Vista de retos | Chips de retos, tabla por línea estratégica |
| **Consolidado** | Vista combinada | Integración de indicadores + proyectos + retos |

### 6.2 Funciones de Carga Unificada

```python
# Función principal de carga de datos
_load_base_data_by_type(category: str, year: int)
```

**Parámetros:**
- `category`: "Indicadores" | "Proyectos" | "Plan de Retos" | "Consolidado"
- `year`: Año a consultar

**Retorna:** `(linea_summary, objetivo_df, pdi_base_df, historico_df, pdi_estrategico)`

**Nota importante - Carga de Proyectos:**
Los proyectos se cargan directamente desde `load_cierres()` (no desde `preparar_pdi_con_cierre`), filtrando por el flag `Proyecto == 1` en el archivo `Indicadores por CMI.xlsx`. Se obtiene el último registro por proyecto para el año seleccionado, y se agrega la Línea estratégica desde `worksheet_flags`.

### 6.3 Chips por Categoría

| Categoría | Chips Mostrados |
|-----------|-----------------|
| Indicadores | Total, Sobrecumplimiento, Cumplimiento, Alerta, Peligro |
| Proyectos | Total Proyectos, Cerrados (100%), En Ejecución, Planeación |
| Plan de Retos | Total Retos, % Meta Esperada, % Avance Real, Cumplimiento |
| Consolidado | Total, Indicadores, Proyectos, Retos |

### 6.4 Visualizaciones por Categoría

| Categoría | Visualización Principal |
|-----------|------------------------|
| Indicadores | Tablas: "Indicadores que mejoraron" / "Indicadores en riesgo" |
| Proyectos | Gráfico Gantt (barras horizontales) 2022-2025 con % cumplimiento |
| Plan de Retos | Tarjetas por línea con número de retos y cumplimiento |
| Consolidado | Vista combinada de las tres anteriores |

### 6.5 Narrativa Ejecutiva Dinámica

La función `_generate_narrative()` genera texto personalizado según la categoría:

- **Indicadores**: Habla de "indicadores PDI", salud institucional, alertas
- **Proyectos**: Menciona "proyectos cerrados", "en ejecución", "en planeación"
- **Retos**: Se enfoca en "retos completados" y avance vs metas
- **Consolidado**: Vista combinada general

---

## 7. Dashboard HTML Estáticos

### Archivos Disponibles

| Archivo | Descripción |
|---------|-------------|
| `dashboard_profesional.html` | Dashboard profesional completo |
| `dashboard_diplomatic.html` | Diseño diplomático |
| `dashboard_mini.html` | Versión mínima |
| `dashboard_prueba.html` | Pruebas |

### Características Comunes
- Renderizado con Jinja2
- Datos embebidos en HTML
- Sin servidor backend
- Portables y auditables

---

## 8. Referencias

- **Catálogo gráficos:** [`CATALOGO_GRAFICOS_v2.md`](../../10-GUIAS-ESTANDARES/CATALOGO_GRAFICOS_v2.md)
- **Guía colores:** [`GUIA_PERSONALIZACION_COLORES.md`](../../10-GUIAS-ESTANDARES/GUIA_PERSONALIZACION_COLORES.md)
- **Diagnósticos:** [`diagnostico_dashboard.md`](../../09-DIAGNOSTICOS/diagnostico_dashboard.md)
