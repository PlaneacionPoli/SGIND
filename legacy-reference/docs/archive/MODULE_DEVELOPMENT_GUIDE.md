# Module Development Guide

## Step-by-Step Tutorial: Creating a New Refactored Module

This guide walks you through creating a new page using the proven 6-module pattern. We'll use an example: `quality_dashboard.py` (hypothetical new page).

---

## Phase 1: Planning (15 minutes)

### 1.1 Define the Page Purpose
- **Name:** Quality Dashboard
- **Purpose:** Display quality metrics by process and time period
- **Main Views:**
  - Overview: Total metrics
  - By Process: Process-specific quality scores
  - Trends: Historical quality trends
  - Details: Detailed quality checklist results

### 1.2 Identify Data Sources
```python
data_sources = {
    "quality_checklist": "Data/calidad_checklist.xlsx",
    "process_map": "DataService.get_process_map()",
    "consolidado": "DataService.get_consolidado()",
}
```

### 1.3 Sketch Data Flow
```
Load quality_checklist.xlsx
    ↓
Load process map
    ↓
Merge on process ID
    ↓
Calculate quality scores (transform)
    ↓
Group by process, time period
    ↓
Visualize (charts)
    ↓
Render (Streamlit UI)
```

---

## Phase 2: Create Config Module (10 minutes)

### File: `quality_dashboard_config.py`

```python
"""Configuration for quality dashboard page."""

from pathlib import Path

# ===== File Paths =====
_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_CALIDAD_XLSX = _DATA_DIR / "calidad_checklist.xlsx"

# ===== Constants =====
MESES_OPCIONES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

MES_MAP = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
    "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12,
}

# ===== Quality Score Thresholds =====
QUALITY_EXCELLENT = 90      # 90%+
QUALITY_GOOD = 75           # 75-89%
QUALITY_ACCEPTABLE = 60     # 60-74%
QUALITY_POOR = 0            # <60%

# ===== Colors (Hex) =====
QUALITY_COLORS = {
    "Excelente": "#2E7D32",      # Green
    "Buena": "#FBC02D",          # Amber
    "Aceptable": "#F57C00",      # Orange
    "Deficiente": "#C62828",     # Red
    "Sin dato": "#9E9E9E",       # Gray
}

# ===== Status Mapping =====
QUALITY_DIMENSIONS = [
    "Documentación",
    "Cumplimiento de SLA",
    "Satisfacción del usuario",
    "Disponibilidad del sistema",
]

# ===== Display Constants =====
ITEMS_PER_PAGE = 15
CHART_HEIGHT = 400
```

### Key Points:
- ✅ All constants in one place
- ✅ File paths use Path objects
- ✅ Colors match other modules for consistency
- ✅ No code logic, only configuration

---

## Phase 3: Create Transforms Module (20 minutes)

### File: `quality_dashboard_utils_transforms.py`

```python
"""Data transformation utilities for quality dashboard."""

import unicodedata
import pandas as pd
import numpy as np
from typing import Tuple

from streamlit_app.pages.quality_dashboard_config import (
    QUALITY_EXCELLENT, QUALITY_GOOD, QUALITY_ACCEPTABLE, QUALITY_POOR,
    QUALITY_COLORS
)

# ===== Text Normalization =====

def _norm_key(value: str) -> str:
    """Normalize string key (uppercase, NFKD, remove diacritics).
    
    Args:
        value: String to normalize
        
    Returns:
        Normalized string (uppercase, no diacritics)
    """
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _to_float(value) -> float | None:
    """Convert value to float, handling percentage strings.
    
    Args:
        value: Value to convert (int, float, str, or None)
        
    Returns:
        Float or None if conversion fails
    """
    if pd.isna(value):
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    text = str(value).strip().replace("%", "").strip()
    try:
        return float(text)
    except (ValueError, AttributeError):
        return None


# ===== Quality Score Categorization =====

def _categoria_calidad(score: float) -> str:
    """Categorize quality score (0-100).
    
    Args:
        score: Quality score (0-100)
        
    Returns:
        Category: "Excelente", "Buena", "Aceptable", "Deficiente", "Sin dato"
    """
    if pd.isna(score):
        return "Sin dato"
    
    try:
        score = float(score)
    except (ValueError, TypeError):
        return "Sin dato"
    
    if score >= QUALITY_EXCELLENT:
        return "Excelente"
    elif score >= QUALITY_GOOD:
        return "Buena"
    elif score >= QUALITY_ACCEPTABLE:
        return "Aceptable"
    else:
        return "Deficiente"


def _color_para_score(score: float) -> str:
    """Get color for quality score.
    
    Args:
        score: Quality score (0-100)
        
    Returns:
        Hex color code
    """
    categoria = _categoria_calidad(score)
    return QUALITY_COLORS.get(categoria, QUALITY_COLORS["Sin dato"])


# ===== Score Calculation =====

def _calcular_score_proceso(df: pd.DataFrame) -> dict:
    """Calculate overall quality score per process.
    
    Args:
        df: DataFrame with quality results
        
    Returns:
        Dict: {process_name: quality_score}
    """
    if df.empty or "Proceso" not in df.columns:
        return {}
    
    scores = {}
    for proceso in df["Proceso"].dropna().unique():
        proceso_df = df[df["Proceso"] == proceso]
        
        # Calculate average of all metrics
        metricas = [col for col in ["Puntualidad", "Documentacion", "Conformidad"]
                   if col in proceso_df.columns]
        
        if metricas:
            avg_scores = []
            for metrica in metricas:
                values = pd.to_numeric(proceso_df[metrica], errors='coerce')
                if not values.empty:
                    avg_scores.append(values.mean())
            
            if avg_scores:
                scores[proceso] = np.mean(avg_scores)
    
    return scores


def _dedup_calidad_df(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate quality records, keeping most recent.
    
    Args:
        df: DataFrame with potential duplicates
        
    Returns:
        DataFrame with duplicates removed (latest record per item)
    """
    if df.empty or "Id" not in df.columns:
        return df
    
    df = df.copy()
    
    # Sort by date (latest first) then remove duplicates on key
    if "Fecha" in df.columns:
        df = df.sort_values("Fecha", ascending=False)
    elif "fecha" in df.columns:
        df = df.sort_values("fecha", ascending=False)
    
    return df.drop_duplicates(subset=["Id"], keep="first")


def _ensure_calidad_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure DataFrame has required quality columns.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        DataFrame with added columns (if missing)
    """
    df = df.copy()
    
    required = ["Id", "Proceso", "Fecha", "Puntualidad", "Documentacion", "Conformidad"]
    for col in required:
        if col not in df.columns:
            df[col] = None
    
    return df


def _build_score_ranking(df: pd.DataFrame, limit: int = 10) -> list[dict]:
    """Build ranked list of processes by quality score.
    
    Args:
        df: DataFrame with quality data
        limit: Top N processes to return
        
    Returns:
        List of dicts: [{"proceso": str, "score": float, "categoria": str}, ...]
    """
    scores = _calcular_score_proceso(df)
    
    ranking = [
        {
            "proceso": proceso,
            "score": score,
            "categoria": _categoria_calidad(score),
            "color": _color_para_score(score)
        }
        for proceso, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return ranking[:limit]


# ===== Time Series Aggregation =====

def _aggregate_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate quality scores by month.
    
    Args:
        df: DataFrame with quality data (must have Fecha column)
        
    Returns:
        DataFrame grouped by month with average scores
    """
    if df.empty or "Fecha" not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce')
    df["Año-Mes"] = df["Fecha"].dt.to_period("M")
    
    agg_dict = {
        "Puntualidad": "mean",
        "Documentacion": "mean",
        "Conformidad": "mean",
    }
    
    return df.groupby("Año-Mes").agg(agg_dict).reset_index()
```

### Key Points:
- ✅ All functions are pure (no side effects)
- ✅ Comprehensive docstrings with Args/Returns
- ✅ Type hints on all functions
- ✅ Handles edge cases (NaN, None, conversion errors)
- ✅ Highly testable
- ✅ Reusable across pages

---

## Phase 4: Create Data Module (15 minutes)

### File: `quality_dashboard_utils_data.py`

```python
"""Data loading and caching for quality dashboard."""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Tuple

from streamlit_app.pages.quality_dashboard_config import _CALIDAD_XLSX
from streamlit_app.pages.quality_dashboard_utils_transforms import (
    _ensure_calidad_columns, _dedup_calidad_df
)
from streamlit_app.services.data_service import DataService


# ===== Data Loaders (Cached) =====

@st.cache_data(ttl=3600)
def _load_calidad_raw() -> Tuple[pd.DataFrame, str | None]:
    """Load raw quality checklist data from Excel.
    
    Returns:
        Tuple: (DataFrame, error_message or None)
    """
    try:
        if not _CALIDAD_XLSX.exists():
            return pd.DataFrame(), f"File not found: {_CALIDAD_XLSX}"
        
        df = pd.read_excel(_CALIDAD_XLSX, sheet_name="Resultados")
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)


@st.cache_data(ttl=1800)
def _load_process_map() -> pd.DataFrame:
    """Load process hierarchy mapping.
    
    Returns:
        DataFrame with columns: Proceso_padre, Proceso, Subproceso
    """
    try:
        ds = DataService()
        return ds.get_process_map()
    except Exception:
        return pd.DataFrame()


# ===== Data Preparation =====

def _prepare_calidad_data(year: int, mes: int) -> pd.DataFrame:
    """Prepare quality data for dashboard.
    
    Orchestration function that:
    1. Loads raw data
    2. Validates columns
    3. Deduplicates
    4. Filters by year/month
    5. Merges with process map
    
    Args:
        year: Filter by year (e.g., 2026)
        mes: Filter by month (1-12)
        
    Returns:
        Processed DataFrame ready for visualization
    """
    # Load data
    df_calidad, error = _load_calidad_raw()
    if error:
        st.warning(f"⚠️ Error loading quality data: {error}")
        return pd.DataFrame()
    
    if df_calidad.empty:
        return pd.DataFrame()
    
    # Ensure required columns
    df_calidad = _ensure_calidad_columns(df_calidad)
    
    # Deduplicate
    df_calidad = _dedup_calidad_df(df_calidad)
    
    # Filter by date
    df_calidad["Fecha"] = pd.to_datetime(df_calidad["Fecha"], errors='coerce')
    df_calidad = df_calidad[
        (df_calidad["Fecha"].dt.year == year) &
        (df_calidad["Fecha"].dt.month == mes)
    ]
    
    # Merge with process map
    df_map = _load_process_map()
    if not df_map.empty:
        df_calidad = df_calidad.merge(
            df_map,
            left_on="Proceso",
            right_on="Proceso",
            how="left"
        )
    
    return df_calidad


# ===== Metrics Aggregation =====

@st.cache_data
def _get_calidad_summary(year: int, mes: int) -> dict:
    """Get summary metrics for quality dashboard.
    
    Args:
        year: Year filter
        mes: Month filter
        
    Returns:
        Dict with aggregated metrics
    """
    df = _prepare_calidad_data(year, mes)
    
    if df.empty:
        return {
            "total_procesos": 0,
            "promedio_score": 0.0,
            "procesos_excelentes": 0,
            "procesos_deficientes": 0,
        }
    
    from streamlit_app.pages.quality_dashboard_utils_transforms import (
        _calcular_score_proceso, _categoria_calidad
    )
    
    scores = _calcular_score_proceso(df)
    categorias = [_categoria_calidad(s) for s in scores.values()]
    
    return {
        "total_procesos": len(scores),
        "promedio_score": sum(scores.values()) / len(scores) if scores else 0.0,
        "procesos_excelentes": categorias.count("Excelente"),
        "procesos_deficientes": categorias.count("Deficiente"),
    }
```

### Key Points:
- ✅ `@st.cache_data` decorators for performance
- ✅ `_prepare_*` function as orchestration
- ✅ Error handling with user-friendly messages
- ✅ Clear separation of loading vs. aggregation
- ✅ Type hints with Tuple returns

---

## Phase 5: Create Visuals Module (15 minutes)

### File: `quality_dashboard_visuals.py`

```python
"""Visualization functions for quality dashboard."""

import plotly.graph_objects as go
import pandas as pd

from streamlit_app.pages.quality_dashboard_config import QUALITY_COLORS
from streamlit_app.pages.quality_dashboard_utils_transforms import (
    _build_score_ranking, _aggregate_by_month
)


def _build_quality_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Create pie chart of quality score distribution.
    
    Args:
        df: DataFrame with quality data
        
    Returns:
        plotly.graph_objects.Figure
    """
    from streamlit_app.pages.quality_dashboard_utils_transforms import _categoria_calidad
    
    df = df.copy()
    df["Categoria"] = df.get("Score", 0).apply(_categoria_calidad)
    
    counts = df["Categoria"].value_counts()
    colors = [QUALITY_COLORS.get(cat, "#999") for cat in counts.index]
    
    fig = go.Figure(data=[go.Pie(
        labels=counts.index,
        values=counts.values,
        marker=dict(colors=colors),
    )])
    
    fig.update_layout(
        title="Distribución de Calidad por Categoría",
        height=400
    )
    
    return fig


def _build_process_ranking_chart(df: pd.DataFrame, limit: int = 10) -> go.Figure:
    """Create bar chart of processes ranked by quality score.
    
    Args:
        df: DataFrame with quality data
        limit: Number of top processes to show
        
    Returns:
        plotly.graph_objects.Figure
    """
    ranking = _build_score_ranking(df, limit=limit)
    
    if not ranking:
        # Empty chart
        return go.Figure().add_annotation(text="No data available")
    
    procesos = [r["proceso"] for r in ranking]
    scores = [r["score"] for r in ranking]
    colors = [r["color"] for r in ranking]
    
    fig = go.Figure(data=[go.Bar(
        x=procesos,
        y=scores,
        marker=dict(color=colors),
        text=[f"{s:.1f}%" for s in scores],
        textposition="auto",
    )])
    
    fig.update_layout(
        title=f"Top {limit} Procesos por Puntuación de Calidad",
        xaxis_title="Proceso",
        yaxis_title="Puntuación (%)",
        height=400,
        showlegend=False,
    )
    
    return fig


def _build_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Create line chart of quality trends over time.
    
    Args:
        df: DataFrame with quality data
        
    Returns:
        plotly.graph_objects.Figure
    """
    monthly = _aggregate_by_month(df)
    
    if monthly.empty:
        return go.Figure().add_annotation(text="No trend data")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly["Año-Mes"].astype(str),
        y=monthly["Puntualidad"],
        name="Puntualidad",
        mode='lines+markers',
    ))
    
    fig.add_trace(go.Scatter(
        x=monthly["Año-Mes"].astype(str),
        y=monthly["Documentacion"],
        name="Documentación",
        mode='lines+markers',
    ))
    
    fig.update_layout(
        title="Tendencia de Calidad por Mes",
        xaxis_title="Período",
        yaxis_title="Puntuación (%)",
        height=400,
    )
    
    return fig
```

### Key Points:
- ✅ Pure functions returning go.Figure
- ✅ No st.* calls (testable without Streamlit)
- ✅ Color configuration imported from config
- ✅ Error handling (empty data)

---

## Phase 6: Create Renderers Module (20 minutes)

### File: `quality_dashboard_renderers.py`

```python
"""Streamlit rendering components for quality dashboard."""

import streamlit as st
import pandas as pd

from streamlit_app.pages.quality_dashboard_config import QUALITY_COLORS
from streamlit_app.pages.quality_dashboard_utils_transforms import (
    _categoria_calidad, _color_para_score, _build_score_ranking
)


def _render_quality_header() -> None:
    """Render page header with title and description."""
    st.markdown("""
    # 🎯 Tablero de Calidad
    
    Monitoreo de métricas de calidad por proceso y período.
    """)


def _render_kpi_cards(summary: dict) -> None:
    """Render KPI cards with quality metrics.
    
    Args:
        summary: Dict with keys: total_procesos, promedio_score, etc.
    """
    cols = st.columns(4)
    
    with cols[0]:
        st.metric(
            "📊 Total Procesos",
            summary.get("total_procesos", 0)
        )
    
    with cols[1]:
        st.metric(
            "⭐ Promedio",
            f"{summary.get('promedio_score', 0):.1f}%"
        )
    
    with cols[2]:
        st.metric(
            "🟢 Excelentes",
            summary.get("procesos_excelentes", 0)
        )
    
    with cols[3]:
        st.metric(
            "🔴 Deficientes",
            summary.get("procesos_deficientes", 0)
        )


def _render_ranking_table(df: pd.DataFrame, limit: int = 15) -> None:
    """Render quality ranking table.
    
    Args:
        df: DataFrame with quality data
        limit: Number of rows to display
    """
    ranking = _build_score_ranking(df, limit=limit)
    
    if not ranking:
        st.info("No hay datos de calidad disponibles")
        return
    
    # Build table data
    rows = []
    for i, item in enumerate(ranking, 1):
        rows.append({
            "Rank": i,
            "Proceso": item["proceso"],
            "Puntuación": f"{item['score']:.1f}%",
            "Categoría": item["categoria"],
        })
    
    df_display = pd.DataFrame(rows)
    st.dataframe(df_display, use_container_width=True, hide_index=True)


def _render_quality_summary_cards(df: pd.DataFrame) -> None:
    """Render individual quality cards per process.
    
    Args:
        df: DataFrame with quality data
    """
    ranking = _build_score_ranking(df, limit=5)
    
    for item in ranking:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"### {item['proceso']}")
            
            with col2:
                st.markdown(f"**Puntuación**")
                st.markdown(f"## {item['score']:.1f}%")
            
            with col3:
                st.markdown(f"**Estado**")
                st.markdown(f"### {item['categoria']}")


def _render_section_title(title: str, icon: str = "📌") -> None:
    """Render styled section title.
    
    Args:
        title: Section title
        icon: Emoji icon prefix
    """
    st.markdown(f"## {icon} {title}")
    st.divider()
```

### Key Points:
- ✅ All st.* calls concentrated here
- ✅ No data transformation logic
- ✅ Uses config colors
- ✅ Reusable component functions

---

## Phase 7: Create Main Orchestration Module (20 minutes)

### File: `quality_dashboard.py`

```python
"""Quality Dashboard page - Main orchestration module."""

import streamlit as st
import pandas as pd
from datetime import datetime

from streamlit_app.services.data_service import DataService
from streamlit_app.pages.quality_dashboard_config import MESES_OPCIONES
from streamlit_app.pages.quality_dashboard_utils_transforms import (
    _dedup_calidad_df, _ensure_calidad_columns
)
from streamlit_app.pages.quality_dashboard_utils_data import (
    _prepare_calidad_data, _get_calidad_summary
)
from streamlit_app.pages.quality_dashboard_visuals import (
    _build_quality_distribution_chart, _build_process_ranking_chart,
    _build_trend_chart
)
from streamlit_app.pages.quality_dashboard_renderers import (
    _render_quality_header, _render_kpi_cards, _render_ranking_table,
    _render_quality_summary_cards, _render_section_title
)


def render() -> None:
    """Main render function for quality dashboard."""
    
    # Header
    _render_quality_header()
    
    # Filter panel
    current_year = datetime.now().year
    anos = list(range(current_year - 2, current_year + 1))
    
    col1, col2 = st.columns(2)
    with col1:
        year_sel = st.selectbox("Año", anos, index=len(anos)-1)
    with col2:
        mes_sel = st.selectbox("Mes", MESES_OPCIONES, index=11)  # December
    
    mes_num = MESES_OPCIONES.index(mes_sel) + 1
    
    # Load data
    df = _prepare_calidad_data(year_sel, mes_num)
    
    if df.empty:
        st.warning("No hay datos de calidad disponibles para este período")
        return
    
    # Get summary
    summary = _get_calidad_summary(year_sel, mes_num)
    
    # Render KPIs
    _render_section_title("Resumen General", "📊")
    _render_kpi_cards(summary)
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Distribución",
        "🏆 Ranking",
        "📉 Tendencias",
        "📋 Detalle"
    ])
    
    with tab1:
        _render_section_title("Distribución de Calidad")
        fig = _build_quality_distribution_chart(df)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        _render_section_title("Procesos Mejor Evaluados")
        col_chart, col_table = st.columns([1, 1])
        
        with col_chart:
            fig = _build_process_ranking_chart(df)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_table:
            _render_quality_summary_cards(df)
    
    with tab3:
        _render_section_title("Tendencias Históricas")
        fig = _build_trend_chart(df)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        _render_section_title("Tabla Detallada")
        _render_ranking_table(df, limit=20)


# Re-exports for backward compatibility
_prepare_calidad_data_export = _prepare_calidad_data
_dedup_calidad_df_export = _dedup_calidad_df
_ensure_calidad_columns_export = _ensure_calidad_columns
```

### Key Points:
- ✅ Single `render()` function as entry point
- ✅ Clean orchestration: load → filter → transform → visualize → render
- ✅ Minimal logic (delegates to other layers)
- ✅ Re-exports for test compatibility
- ✅ Clear tab structure

---

## Phase 8: Create Tests (20 minutes)

### File: `tests/test_quality_dashboard_transforms.py`

```python
"""Tests for quality dashboard transformations."""

import pytest
import pandas as pd
from streamlit_app.pages.quality_dashboard_utils_transforms import (
    _categoria_calidad, _color_para_score, _to_float, _norm_key,
    _dedup_calidad_df, _ensure_calidad_columns, _calcular_score_proceso
)


class TestCategorizacion:
    """Test quality score categorization."""
    
    def test_categoria_excelente(self):
        assert _categoria_calidad(95.0) == "Excelente"
    
    def test_categoria_buena(self):
        assert _categoria_calidad(82.5) == "Buena"
    
    def test_categoria_aceptable(self):
        assert _categoria_calidad(65.0) == "Aceptable"
    
    def test_categoria_deficiente(self):
        assert _categoria_calidad(45.0) == "Deficiente"
    
    def test_categoria_nan_retorna_sin_dato(self):
        assert _categoria_calidad(None) == "Sin dato"


class TestConversion:
    """Test value conversions."""
    
    def test_to_float_from_int(self):
        assert _to_float(85) == 85.0
    
    def test_to_float_from_string_percentage(self):
        assert _to_float("85.5%") == 85.5
    
    def test_to_float_nan_returns_none(self):
        assert _to_float(None) is None
    
    def test_norm_key_uppercase(self):
        assert _norm_key("proceso") == "PROCESO"


class TestDeduplicacion:
    """Test deduplication logic."""
    
    def test_dedup_keeps_latest(self):
        df = pd.DataFrame({
            "Id": [1, 1, 2],
            "Fecha": ["2026-01-01", "2026-01-05", "2026-01-03"],
            "Score": [80, 90, 85]
        })
        df["Fecha"] = pd.to_datetime(df["Fecha"])
        
        result = _dedup_calidad_df(df)
        
        assert len(result) == 2
        assert result[result["Id"] == 1]["Score"].iloc[0] == 90
    
    def test_dedup_empty_df(self):
        df = pd.DataFrame()
        result = _dedup_calidad_df(df)
        assert result.empty


@pytest.fixture
def sample_quality_df():
    """Sample quality data for testing."""
    return pd.DataFrame({
        "Id": [1, 2, 3],
        "Proceso": ["Compras", "RH", "IT"],
        "Puntualidad": [85, 92, 78],
        "Documentacion": [90, 88, 80],
        "Conformidad": [92, 90, 75],
    })


def test_calcular_score_proceso(sample_quality_df):
    """Test process score calculation."""
    scores = _calcular_score_proceso(sample_quality_df)
    
    assert len(scores) == 3
    assert "Compras" in scores
    assert scores["Compras"] > 0
```

### Key Points:
- ✅ Test pure functions only
- ✅ Use fixtures for sample data
- ✅ Test edge cases (NaN, empty, invalid)
- ✅ Clear test names

---

## Phase 9: File Structure Summary

```
streamlit_app/pages/
├── quality_dashboard_config.py             (115L)
├── quality_dashboard_utils_transforms.py   (250L)
├── quality_dashboard_utils_data.py         (200L)
├── quality_dashboard_visuals.py            (150L)
├── quality_dashboard_renderers.py          (200L)
└── quality_dashboard.py                    (300L)

tests/
└── test_quality_dashboard_transforms.py   (150L)
```

**Total: ~1,365 lines of focused, testable, maintainable code**

---

## Phase 10: Quick Checklist Before Committing

- [ ] All 6 modules created
- [ ] `render()` function works end-to-end
- [ ] All imports resolve without errors
- [ ] Tests pass: `pytest tests/test_quality_dashboard_*`
- [ ] No hardcoded values (all in config)
- [ ] Re-exports added for backward compatibility
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions
- [ ] Git commit with standard message

### Example Git Commit:
```bash
git add streamlit_app/pages/quality_dashboard*.py tests/test_quality_dashboard*.py
git commit -m "feat(quality): Add quality dashboard using 6-module pattern

MODULES CREATED:
1. quality_dashboard_config.py (115L)
2. quality_dashboard_utils_transforms.py (250L)
3. quality_dashboard_utils_data.py (200L)
4. quality_dashboard_visuals.py (150L)
5. quality_dashboard_renderers.py (200L)
6. quality_dashboard.py (300L)

✅ Total: 1,215L focused modules
✅ Tests: All passing
✅ Pattern: Standard 6-layer architecture"
```

---

## Troubleshooting

### Issue: Import Error
**Solution:** Check layer dependency rules (Config → Transforms → Data → Visuals/Renderers → Main)

### Issue: Tests Fail
**Solution:** Ensure transforms functions are pure (no I/O, no Streamlit calls)

### Issue: Slow Performance
**Solution:** Add `@st.cache_data` decorators to data loading functions in Layer 3

### Issue: Inconsistent Colors
**Solution:** Ensure all colors imported from config layer, not hardcoded

---

## Next Steps

After creating your module:

1. **Add to page navigation** (`streamlit_app/__init__.py` or sidebar config)
2. **Update documentation** (add to architecture diagram)
3. **Create endpoint** (if building API)
4. **Monitor performance** (use Streamlit profiler)
5. **Gather feedback** (from business users)

---

## See Also

- [PHASE3_ARCHITECTURE.md](./PHASE3_ARCHITECTURE.md) - Full architecture documentation
- [BEST_PRACTICES.md](./BEST_PRACTICES.md) - Code quality guidelines
- [Test Examples](../tests/) - More test patterns
