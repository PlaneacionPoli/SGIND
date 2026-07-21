# Best Practices Guide

## Code Quality, Performance & Maintainability

---

## Part 1: Code Organization

### ✅ DO: Keep Modules Focused

**Good:**
```python
# streamlit_app/pages/resumen_por_proceso_utils_transforms.py
# 233 lines - Single responsibility: Data normalization & calculations

def _cumplimiento_pct(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate compliance percentage."""
    ...

def _categoria_por_pct(pct: float) -> str:
    """Categorize compliance level."""
    ...

def _build_variation_tables(df: pd.DataFrame) -> list:
    """Calculate month-over-month variations."""
    ...
```

**Avoid:**
```python
# All-in-one file (BAD)
def _load_data(): ...
def _transform_data(): ...
def _render_ui(): ...
def _save_to_db(): ...
def _send_email(): ...
# Too many responsibilities → hard to test, reuse, maintain
```

### ✅ DO: Use Clear Naming Conventions

**Good:**
```python
def _load_indicadores_por_cmi():         # Data loading
def _ensure_nivel_cumplimiento(df):      # Data validation
def _render_resumen_overview_cards():    # UI rendering
def _build_variation_tables(df):         # Calculations
def _categoria_por_pct(pct):            # Categorization
```

**Avoid:**
```python
def _process(x):                 # Too generic
def _helper_func():              # Not descriptive
def _temp_function():            # Suggests temporary
def process_data_1():            # Numbered functions
```

### ✅ DO: Group Related Functions

**Good - By Layer:**
```python
# config.py
MESES_OPCIONES = [...]           # Constants
MES_MAP = {...}                  # Mappings
NIVELES_COLORS = {...}           # Configuration

# utils_transforms.py
def _norm_key(): ...             # Normalization
def _ensure_nivel(): ...         # Validation
def _cumplimiento_pct(): ...     # Calculation

# utils_data.py
def _load_*(): ...               # Loading
def _prepare_*(): ...            # Orchestration
```

**Avoid:**
```python
# Random function order
def _cumplimiento_pct(): ...
def _render_card(): ...
def _load_data(): ...
def _norm_key(): ...
# Functions scattered across file → hard to find
```

---

## Part 2: Data Handling

### ✅ DO: Use Type Hints

**Good:**
```python
def _cumplimiento_pct(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate compliance percentage.
    
    Args:
        df: DataFrame with potential compliance columns
        
    Returns:
        DataFrame with 'cumplimiento_pct' column
    """
    pass

def _categoria_por_pct(pct: float | None) -> str:
    """Categorize compliance level.
    
    Args:
        pct: Compliance percentage (0-100) or None
        
    Returns:
        Category string: "Sobrecumplimiento", "Cumplimiento", etc.
    """
    pass
```

**Avoid:**
```python
def _cumplimiento_pct(df):
    """Calculate compliance percentage."""
    pass

def _categoria_por_pct(pct):
    """Categorize."""
    pass
```

### ✅ DO: Handle None/NaN Gracefully

**Good:**
```python
def _to_float(value) -> float | None:
    """Convert to float, return None on error."""
    if pd.isna(value):
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    try:
        return float(str(value).replace("%", ""))
    except (ValueError, AttributeError, TypeError):
        return None
    # Handles: None, NaN, "85.5%", "invalid", etc.
```

**Avoid:**
```python
def _to_float(value):
    return float(value)  # Crashes on None or invalid input
```

### ✅ DO: Copy DataFrames Before Mutation

**Good:**
```python
def _ensure_nivel_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    """Add compliance level column."""
    df = df.copy()  # Avoid modifying input
    df["Nivel"] = df["cumplimiento_pct"].apply(_categoria_por_pct)
    return df
```

**Avoid:**
```python
def _ensure_nivel_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    df["Nivel"] = df["cumplimiento_pct"].apply(_categoria_por_pct)  # Mutates input!
    return df
```

### ✅ DO: Validate Data Early

**Good:**
```python
def _process_tracking_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process tracking data with validation."""
    
    # 1. Check empty
    if df.empty:
        return pd.DataFrame()
    
    # 2. Ensure required columns
    required = ["Id", "Indicador", "Cumplimiento"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    
    # 3. Process
    df = df.copy()
    df["cumplimiento_pct"] = _cumplimiento_pct(df)
    
    return df
```

**Avoid:**
```python
def _process_tracking_data(df: pd.DataFrame) -> pd.DataFrame:
    # Assume data is valid → crashes later on missing columns
    df["cumplimiento_pct"] = _cumplimiento_pct(df)
    return df
```

---

## Part 3: Caching & Performance

### ✅ DO: Cache Data Loading

**Good:**
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def _load_indicadores_por_cmi():
    """Load indicator metadata (slow, stable data)."""
    return pd.read_excel(_INDICADORES_XLSX)


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def _prepare_tracking(df, map_df, month_num):
    """Prepare tracking data (fast operation, stable results)."""
    # Merge, transform, aggregate
    return result_df
```

**Avoid:**
```python
def _load_indicadores_por_cmi():
    """Loads Excel every render → SLOW"""
    return pd.read_excel(_INDICADORES_XLSX)
```

### ✅ DO: Use Appropriate TTL

**TTL Guidelines:**
- **Stable data (config, metadata):** 3600-7200 seconds (1-2 hours)
- **Daily data (tracking):** 1800 seconds (30 minutes)
- **Real-time data (current metrics):** 300 seconds (5 minutes) or @st.cache_data(ttl=0)
- **User-specific data:** Don't cache (different per session)

**Good:**
```python
@st.cache_data(ttl=7200)
def _load_proceso_master():
    """Master data - changes rarely."""
    return pd.read_excel(_PROCESO_MASTER_XLSX)

@st.cache_data(ttl=300)
def _get_real_time_metrics():
    """Real-time data - changes frequently."""
    return DataService().get_current_metrics()
```

### ✅ DO: Profile Before Optimizing

**Good:**
```python
import streamlit as st
import time

@st.cache_data
def _expensive_operation(df):
    start = time.time()
    result = df.groupby("Proceso").agg(...)
    elapsed = time.time() - start
    print(f"Operation took {elapsed:.2f}s")  # Profile result
    return result
```

**Avoid:**
```python
# Guessing what's slow → wastes time on micro-optimizations
```

### ✅ DO: Use Lazy Loading for Large Datasets

**Good:**
```python
# Load summary (lightweight)
@st.cache_data
def _load_summary():
    return pd.read_csv(_SUMMARY_CSV)  # 50KB

# Load detailed (on-demand)
def _load_details(year: int, mes: int):
    # Only load requested month
    return pd.read_excel(
        _DETAILS_XLSX,
        sheet_name=f"{year}-{mes:02d}"
    )
```

**Avoid:**
```python
# Load all years → memory bloat
@st.cache_data
def _load_all_details():
    return pd.read_excel(_HUGE_FILE)  # 500MB+
```

---

## Part 4: Error Handling

### ✅ DO: Handle Missing Files Gracefully

**Good:**
```python
@st.cache_data
def _load_calidad_data():
    """Load quality checklist data."""
    try:
        if not _CALIDAD_XLSX.exists():
            st.warning(f"⚠️ Archivo no encontrado: {_CALIDAD_XLSX}")
            return pd.DataFrame(), "File not found"
        
        df = pd.read_excel(_CALIDAD_XLSX)
        return df, None
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame(), str(e)
```

**Avoid:**
```python
def _load_calidad_data():
    """Crashes if file missing."""
    return pd.read_excel(_CALIDAD_XLSX)  # FileNotFoundError!
```

### ✅ DO: Provide Helpful Error Messages

**Good:**
```python
def _prepare_tracking(df, map_df, month_num):
    """Prepare tracking data."""
    
    if df.empty:
        st.warning("⚠️ No tracking data available")
        return pd.DataFrame()
    
    missing_cols = [col for col in ["Indicador", "Meta"] if col not in df.columns]
    if missing_cols:
        st.error(f"❌ Missing columns: {', '.join(missing_cols)}")
        return pd.DataFrame()
    
    # Process
    return df
```

**Avoid:**
```python
def _prepare_tracking(df, map_df, month_num):
    result = df.merge(map_df)  # KeyError if merge keys don't exist
    return result[["Indicador", "Meta", "Missing"]].fillna(0)  # KeyError!
```

### ✅ DO: Log Errors Without Crashing

**Good:**
```python
def _render_tab_alertas():
    """Render alerts tab (skip if error)."""
    try:
        df_alerts = _get_alert_data()
        _render_alert_cards(df_alerts)
    except Exception as e:
        st.info(f"⚠️ No se pudieron cargar las alertas: {e}")
        # Page continues to work
```

**Avoid:**
```python
def _render_tab_alertas():
    df_alerts = _get_alert_data()  # Crashes entire page if error
    _render_alert_cards(df_alerts)
```

---

## Part 5: Testing

### ✅ DO: Test Pure Functions

**Good:**
```python
# tests/test_transforms.py

def test_cumplimiento_pct_from_percentage_string():
    df = pd.DataFrame({"Cumplimiento": ["85.5%"]})
    result = _cumplimiento_pct(df)
    assert result["cumplimiento_pct"].iloc[0] == 85.5

def test_categoria_sobrecumplimiento():
    assert _categoria_por_pct(105.0) == "Sobrecumplimiento"

def test_categoria_nan_returns_sin_dato():
    assert _categoria_por_pct(None) == "Sin dato"
```

**Avoid:**
```python
# Testing Streamlit-dependent code
def test_render_cards():
    # Requires active Streamlit session → flaky, slow
    _render_resumen_overview_cards({})
```

### ✅ DO: Use Fixtures for Sample Data

**Good:**
```python
@pytest.fixture
def sample_tracking_df():
    """Sample tracking data for testing."""
    return pd.DataFrame({
        "Id": [1, 2, 3],
        "Indicador": ["A", "B", "C"],
        "Cumplimiento": [85.5, 92.0, 78.3],
    })

def test_ensure_nivel_adds_column(sample_tracking_df):
    result = _ensure_nivel_cumplimiento(sample_tracking_df)
    assert "Nivel de cumplimiento" in result.columns
    assert len(result) == 3
```

**Avoid:**
```python
def test_ensure_nivel():
    df = pd.DataFrame({"Cumplimiento": [85.5]})
    # Repeated test data across many tests → hard to maintain
    result = _ensure_nivel_cumplimiento(df)
    assert "Nivel de cumplimiento" in result.columns
```

### ✅ DO: Test Edge Cases

**Good:**
```python
def test_cumplimiento_pct_handles_all_input_types():
    """Test with various input types."""
    assert _to_float(85) == 85.0          # int
    assert _to_float(85.5) == 85.5        # float
    assert _to_float("85.5") == 85.5      # string
    assert _to_float("85.5%") == 85.5     # percentage
    assert _to_float(None) is None        # None
    assert _to_float("invalid") is None   # invalid string
    assert _to_float(np.nan) is None      # NaN
```

**Avoid:**
```python
def test_cumplimiento_pct():
    assert _to_float(85) == 85.0  # Only test happy path
```

---

## Part 6: Documentation

### ✅ DO: Write Clear Docstrings

**Good - Google Style:**
```python
def _build_variation_tables(df: pd.DataFrame, exec_col: str = "Ejecucion") -> list[dict]:
    """Calculate month-over-month variations per indicator.
    
    Identifies top improvements and declines based on execution metrics.
    
    Args:
        df: DataFrame with execution data (must contain 'Indicador', 'Ejecucion' columns)
        exec_col: Column name for execution values (default: "Ejecucion")
        
    Returns:
        List of dicts with keys:
        - 'Indicador': Indicator name
        - 'Anterior': Previous month value
        - 'Actual': Current month value
        - 'Delta': Change (absolute)
        - 'Variacion': Change percentage
        
    Raises:
        ValueError: If required columns missing
        
    Example:
        >>> df = pd.DataFrame({
        ...     'Indicador': ['MetaA', 'MetaB'],
        ...     'Ejecucion': [85, 92]
        ... })
        >>> result = _build_variation_tables(df)
        >>> len(result) >= 0
    """
    pass
```

**Avoid:**
```python
def _build_variation_tables(df, exec_col):
    """Build tables."""  # Too vague
    pass
```

### ✅ DO: Document Configuration Constants

**Good:**
```python
# streamlit_app/pages/resumen_por_proceso_config.py

# ===== Compliance Thresholds (%) =====
# Used to categorize indicator performance:
#   >= 105% → Sobrecumplimiento (exceeded target)
#   >= 100% → Cumplimiento (met target)
#   >= 80%  → Alerta (below target but acceptable)
#   < 80%   → Peligro (critical, needs attention)
THRESHOLD_SOBRECUMPLIMIENTO = 1.05
THRESHOLD_CUMPLIMIENTO = 1.00
THRESHOLD_ALERTA = 0.80

# ===== Color Scheme (Hex) =====
# Matches corporate branding and accessibility standards
NIVELES_COLORS = {
    "Sobrecumplimiento": "#6699FF",  # Blue (positive)
    "Cumplimiento": "#2E7D32",       # Green (success)
    "Alerta": "#F9A825",             # Amber (warning)
    "Peligro": "#C62828",            # Red (danger)
    "Sin dato": "#6E7781",           # Gray (unknown)
}
```

**Avoid:**
```python
THRESHOLD_SOBRECUMPLIMIENTO = 1.05  # What does 1.05 mean?
NIVELES_COLORS = {"Sobrecumplimiento": "#6699FF"}  # Why this color?
```

---

## Part 7: Code Style

### ✅ DO: Follow Python Conventions

**Good:**
```python
# PEP 8 compliant
def _calculate_metric(data: pd.DataFrame) -> dict:
    """Calculate metric from data."""
    result = {}
    
    for col in data.columns:
        result[col] = data[col].mean()
    
    return result


class IndicatorProcessor:
    """Process indicator data."""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
    
    def process(self) -> pd.DataFrame:
        """Process the data."""
        return self.data.copy()
```

**Avoid:**
```python
# Not PEP 8
def Calculate_Metric(data):
    result={}
    for col in data.columns:result[col]=data[col].mean()
    return result
```

### ✅ DO: Use f-Strings for Formatting

**Good:**
```python
periodo = "Enero 2026"
mensaje = f"Datos de {periodo}"

indicador = "Indicador A"
valor = 85.5
texto = f"{indicador}: {valor:.1f}%"
```

**Avoid:**
```python
mensaje = "Datos de " + periodo  # String concatenation
texto = "%s: %.1f%%" % (indicador, valor)  # Old formatting
```

### ✅ DO: Use Pathlib for File Paths

**Good:**
```python
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_ARCHIVO_XLSX = _DATA_DIR / "indicadores.xlsx"

if _ARCHIVO_XLSX.exists():
    df = pd.read_excel(_ARCHIVO_XLSX)
```

**Avoid:**
```python
import os

_ARCHIVO = "C:\\Users\\user\\..\\data\\indicadores.xlsx"  # Hardcoded path
_ARCHIVO = os.path.join("..", "data", "indicadores.xlsx")  # OS-specific
```

---

## Part 8: Version Control

### ✅ DO: Commit Frequently with Clear Messages

**Good:**
```bash
# Focused commits
git commit -m "refactor(transforms): Extract _cumplimiento_pct to pure function

- Moves calculation logic from data layer to transform layer
- Improves testability (no I/O dependencies)
- Handles multiple input formats (%, decimal, None)
- Adds type hints and docstring"

git commit -m "fix(renderers): Fix KPI card layout on mobile"

git commit -m "test(utils): Add tests for compliance categorization"
```

**Avoid:**
```bash
# Large, vague commits
git commit -m "WIP: lots of changes"
git commit -m "updates"
git commit -m "Fix bug"  # Which bug?
```

### ✅ DO: Use Feature Branches

**Good:**
```bash
git checkout -b feature/quality-dashboard
# Make changes
git commit -m "feat(quality): Add quality dashboard"
git push origin feature/quality-dashboard
# Create PR for review
```

**Avoid:**
```bash
# Direct commits to main
git checkout main
git commit -m "Quick fix"
git push origin main
```

---

## Part 9: Performance Optimization Checklist

- [ ] Profile slow functions with `time.time()` or `@profile` decorator
- [ ] Use `@st.cache_data` on data loading (check TTL is appropriate)
- [ ] Use `@st.cache_resource` for expensive one-time computations
- [ ] Use `pd.query()` instead of boolean indexing for large DataFrames
- [ ] Use `pd.eval()` for complex calculations
- [ ] Avoid `.apply()` on large Series → use vectorized operations
- [ ] Filter data as early as possible (before joins, aggregations)
- [ ] Lazy load large datasets (load on-demand, not upfront)
- [ ] Use appropriate data types (int32 instead of int64 if possible)
- [ ] Monitor memory usage: `df.memory_usage(deep=True).sum()`

---

## Part 10: Code Review Checklist

Before committing, ask yourself:

### Structure
- [ ] Does this follow the 6-module pattern?
- [ ] Is each module single-responsibility?
- [ ] Are imports organized (stdlib → project → own)?
- [ ] Are there circular dependencies?

### Data Handling
- [ ] Do functions have type hints?
- [ ] Do functions have docstrings?
- [ ] Is None/NaN handled gracefully?
- [ ] Are DataFrames copied before mutation?

### Performance
- [ ] Are data loaders cached?
- [ ] Is the cache TTL appropriate?
- [ ] Are there obvious inefficiencies?
- [ ] Is the code readable over fast?

### Testing
- [ ] Are transform functions tested?
- [ ] Are edge cases covered?
- [ ] Do tests pass locally?
- [ ] Is coverage acceptable (70%+)?

### Documentation
- [ ] Are public functions documented?
- [ ] Are configuration constants explained?
- [ ] Are assumptions documented?
- [ ] Is the architecture clear?

---

## Quick Reference: Common Mistakes

| Mistake | Fix | Impact |
|---------|-----|--------|
| Hardcoded paths | Use `Path(__file__).parent / ...` | Breaks on different machines |
| No type hints | Add `: Type → ReturnType` | Hard to debug, IDE can't help |
| Mutating input DataFrames | Use `df.copy()` first | Side effects, unexpected behavior |
| Catching all exceptions | Catch specific exceptions | Hides bugs, hard to debug |
| No caching on data loads | Add `@st.cache_data` | Slow page loads |
| Mixing concerns (UI + logic) | Separate into layers | Hard to test, reuse |
| String concatenation for paths | Use `Path` objects | Breaks cross-platform |
| No validation on inputs | Check `df.empty`, required columns | Crashes on bad data |
| Testing Streamlit code | Test pure functions only | Flaky tests, slow CI |
| Large commits | Small, focused commits | Hard to review, debug |

---

## Resources

- [PEP 8 Style Guide](https://pep8.org)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Pandas Best Practices](https://pandas.pydata.org/docs/user_guide/index.html)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Pytest Documentation](https://docs.pytest.org)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

---

## Questions?

Refer to:
- [PHASE3_ARCHITECTURE.md](./PHASE3_ARCHITECTURE.md) for architectural patterns
- [MODULE_DEVELOPMENT_GUIDE.md](./MODULE_DEVELOPMENT_GUIDE.md) for creating new modules
- Code examples in `streamlit_app/pages/` for reference implementations
