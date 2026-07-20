# ADR-005: Gráficos — Recharts + Plotly.js

**Estado:** Aceptado | **Fecha:** 2026-06-13

## Decisión
- Gráficos simples (barras, líneas, KPIs): **Recharts**
- Gráficos complejos (sunburst, treemap, gauge): **Plotly.js** (`react-plotly.js`)

## Consecuencias
- Migrar templates de `heatmap_chart.py` a componentes React wrapper
- Bundle size mayor con Plotly — lazy load por página
