# 06 - TESTING Y CALIDAD

**Documento:** 06_Testing_Calidad.md  
**Versión:** 2.1  
**Fecha:** 17 de junio de 2026 (actualizado Sprint Pending — cobertura módulos 0%)  
**Status:** ✅ Consolidado MDV

---

## 1. Estado Actual

> Última medición: 17-jun-2026, pytest-cov sobre `core/`, `scripts/etl/`, `services/`.

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Tests Totales** | 903 | ✅ |
| **Tests Pasando** | 903 | ✅ 100% |
| **Coverage Global** | 50% | 🟡 |
| **Coverage core/domain/** | ~90% | ✅ |
| **Coverage scripts/etl/cumplimiento.py** | 89% | ✅ |
| **Coverage services/loaders/pipeline.py** | 82% | ✅ |
| **Coverage scripts/etl/extraccion.py** | ~60% | 🟡 |
| **Coverage scripts/etl/normalizacion.py** | ~95% | ✅ |
| **Coverage scripts/etl/builders.py** | 88% | ✅ Nuevo |
| **Coverage services/ficha_pdf/utils.py** | 100% | ✅ Nuevo |
| **Coverage scripts/etl/fuentes.py** | 32% | 🟡 Nuevo |
| **Coverage scripts/etl/purga.py** | 30% | 🟡 Nuevo |
| **Coverage scripts/etl/escritura.py** | 29% | 🟡 Nuevo |
| **Coverage services/data_loader.py** | 23% | 🔴 (DIP issue) |
| **Meta** | 70% en módulos core/etl | ⏳ En progreso |

**Nuevos tests agregados en FASE 4 (jun-2026):**
- `tests/test_etl_utils.py` — 75 tests: normalizacion, periodos, no_aplica, signos
- `tests/test_etl_extraccion.py` — 34 tests: extraccion de meta/ejec desde variables/series

**Nuevos tests agregados en Sprint Pending (jun-2026):**
- `tests/test_ficha_pdf_utils.py` — 14 tests: `nivel_color`, `safe` (100% cobertura del módulo)
- `tests/test_etl_fuentes.py` — 22 tests: `homologar_proceso`, loaders con archivo ausente/mock
- `tests/test_etl_builders.py` — 27 tests: `construir_registros_historico/semestral/cierres` con mocks
- `tests/test_etl_purga_escritura.py` — 32 tests: `_ejec_score`, `llaves_de_df`, `get_last_data_row`, `deduplicar_sheet`, `limpiar_cierres_existentes`, `purgar_filas_invalidas`

**Módulos con cobertura baja (próximos sprints):**
- `scripts/etl/escritura.py` (29%) — funciones openpyxl complejas: `limpiar_ordenar_hoja`, `escribir_filas`
- `scripts/etl/fuentes.py` (32%) — loaders de Kawak 2025 y lookup consolidado
- `scripts/etl/purga.py` (30%) — `_dedup_cierres_por_año`, `reparar_meta_vacia`
- `services/ficha_pdf/builder.py` (13%) — requiere reportlab con datos reales
- `services/data_loader.py` (23%) — DIP issue pendiente (ARQ-006)

---

## 2. Suites de Tests

### 2.1 test_e2e_pipeline.py (19 tests)

**Propósito:** Validar pipeline ETL end-to-end

**Área:** `services/data_loader.py`

**Tests:**
- `test_cargar_dataset_retorna_dataframe`
- `test_cargar_dataset_columnas_requeridas`
- `test_cargar_dataset_tiene_registros`
- `test_cargar_dataset_historico`
- `test_cargar_dataset_historico_columnas`
- `test_resumen_om_por_id`
- `test_calcular_cumplimiento`
- `test_normalizar_nombres`
- Y otros 11 tests adicionales

**Fixtures:**
- `plan_anual_id` - ID de indicador Plan Anual
- `regular_indicator_id` - ID de indicador regular

### 2.2 test_pages_resumen_por_proceso.py (19 tests)

**Propósito:** Validar página Resumen por Proceso

**Área:** `streamlit_app/pages/resumen_por_proceso.py`

**Tests:**
- `test_resumen_por_procesoPage`
- `test_procesar_dataframe_resumen`
- `test_filtrar_por_proceso`
- `test_calcular_totales`
- `test_tiene_porcentaje True/False`
- Y otros 14 tests adicionales

### 2.3 test_pages_gestion_om.py (21 tests)

**Propósito:** Validar página Gestión OM

**Área:** `streamlit_app/pages/gestion_om.py`

**Tests:**
- `test_gestionOMPage`
- `test_color_alerta`
- `test_color_peligro`
- `test_icono_alerta`
- `test_icono_peligro`
- `test_nombre_om_default`
- Y otros 15 tests adicionales

---

## 3. Ejecución de Tests

### 3.1 Comando Principal

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con coverage
pytest tests/ --cov=. --cov-report=html

# Solo una suite
pytest tests/test_e2e_pipeline.py -v
```

### 3.2 CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest --cov=. --cov-report=xml --cov-report=term
      - uses: codecov/codecov-action@v3
```

---

## 4. Validación de Robustez

### 4.1 Áreas Críticas Testeadas

| Área | Descripción | Prioridad |
|------|-------------|-----------|
| Enum comparisons | Comparaciones enum vs strings | 🔴 Alta |
| Normalización | Casos con/sin porcentaje | 🔴 Alta |
| Color/Icon functions | Funciones que esperaban enums | 🔴 Alta |
| Data loading | Carga de datasets | 🟡 Media |
| Edge cases | Indicadores sin datos | 🟡 Media |

### 4.2 Patterns de Test

```python
# CORRECTO: Comparar con .value
assert cat == CategoriaCumplimiento.PELIGRO.value

# CORRECTO: Parámetros explícitos
df = preparar_dataframe(tiene_porcentaje=True)

# CORRECTO: Funciones con strings
color = color_alerta("Alerta")  # No pasar enums
```

---

## 5. Plan de Mejora de Coverage (18% → 80%)

### 5.1 Módulos Priorizados para Testing

#### 🔴 FASE 1 CRÍTICA (Semana 1) — 0% → 40%
**Impacto:** Producción, indicadores, dashboards

| Módulo | Líneas | Coverage | Tests Necesarios | Tiempo |
|--------|--------|----------|------------------|--------|
| `services/cmi_filters.py` | 170 | 11% | 12-15 | 3h |
| `services/data_loader.py` | 336 | 38% | 15-20 | 4h |
| `services/data_validation.py` | 266 | 75% | 5-8 | 2h |
| **Subtotal** | **772** | **40%** | **32-43** | **9h** |

**Tests específicos para CMI Filters:**
```python
# test_cmi_filters_coverage.py
- get_cmi_estrategico_ids() → todas las variantes
- filter_by_line() → todos los casos edge
- normalize_indicator_ids() → caracteres especiales, nulos
- get_cmi_metadata() → ausencia de campos
```

**Tests específicos para Data Loader:**
```python
# test_data_loader_full_coverage.py
- _load_consolidado_cierres() → todas las hojas
- cargar_dataset() → errores de lectura, archivos faltantes
- _validate_columns() → validación estricta
- _enrich_with_metadata() → casos especiales
```

#### 🟠 FASE 2 ALTA (Semana 2-3) — 40% → 60%
**Impacto:** Integraciones, reporting

| Módulo | Líneas | Coverage | Tests Necesarios | Tiempo |
|--------|--------|----------|------------------|--------|
| `services/strategic_indicators.py` | 318 | 86% | 8-10 | 2h |
| `services/ai_analysis.py` | 104 | 50% | 12-15 | 3h |
| `scripts/etl/cumplimiento.py` | 55 | 89% | 2-3 | 1h |
| `scripts/etl/notifications.py` | 104 | 79% | 5-8 | 2h |
| **Subtotal** | **581** | **76%** | **27-36** | **8h** |

**Tests específicos:**
- `strategic_indicators.py`: Casos de error en carga de Excel
- `ai_analysis.py`: Generación de narrativas con datos vacíos
- `notifications.py`: Fallos de SMTP, webhooks

#### 🟡 FASE 3 MEDIA (Semana 4) — 60% → 80%
**Impacto:** Scripts auxiliares, CLI

| Módulo | Líneas | Coverage | Tests Necesarios | Tiempo |
|--------|--------|----------|------------------|--------|
| `scripts/etl/` (14 archivos) | 2,150+ | <5% | 40-50 | 12h |
| `scripts/consolidation/` (8 archivos) | 800+ | <10% | 20-25 | 8h |
| `scripts/` auxiliares (12 archivos) | 2,000+ | 0% | 30-40 | 10h |
| **Subtotal** | **4,950+** | **2%** | **90-115** | **30h** |

### 5.2 Estrategia de Testing por Módulo

#### Pattern: Test Doubles (Mocks)

```python
# services/data_loader.py - Usar mock de pandas.read_excel
@patch('pandas.read_excel')
def test_cargar_dataset_archivo_corrompido(self, mock_read):
    mock_read.side_effect = openpyxl.utils.exceptions.InvalidFileException()
    
    result = cargar_dataset('data/invalid.xlsx')
    
    assert result is None or result.empty
    assert logger.error.called  # Verificar que se loguea error
```

#### Pattern: Fixtures con Datos Reales

```python
# tests/fixtures/consolidado_fixtures.py
@pytest.fixture
def consolidado_sample():
    """DataFrame con estructura real del Consolidado"""
    return pd.read_excel('tests/data/consolidado_sample.xlsx')
```

#### Pattern: Parametrization para Edge Cases

```python
@pytest.mark.parametrize("input,expected", [
    (None, "Sin dato"),
    ("", "Sin dato"),
    (np.nan, "Sin dato"),
    ("95%", "Cumplimiento"),  # Plan Anual
])
def test_categorizar_edge_cases(self, input, expected):
    result = categorizar_cumplimiento(input)
    assert result == expected
```

### 5.3 Roadmap de Implementación

**Semana 1 (9-13 mayo):** FASE 1 CRÍTICA
```bash
# Crear archivo de tests
touch tests/test_services_coverage_phase1.py

# Ejecutar solo nuevos tests
pytest tests/test_services_coverage_phase1.py -v --cov

# Meta: 40%
```

**Semana 2-3 (14-24 mayo):** FASE 2 ALTA
```bash
# Agregar tests de integraciones
pytest tests/ -v --cov=services --cov=scripts/etl/

# Meta: 60%
```

**Semana 4+ (25 mayo+):** FASE 3 MEDIA
```bash
# Coverage completo
pytest tests/ --cov --cov-report=html

# Meta: 80% global
```

### 5.4 Validación y Métricas

| Milestone | Coverage | Tests | Timestamp |
|-----------|----------|-------|-----------|
| Baseline | 18% | 573 | 2026-05-09 |
| FASE 1 ✅ | 40% | 605-615 | 2026-05-13 |
| FASE 2 ✅ | 60% | 632-651 | 2026-05-24 |
| FASE 3 ✅ | 80%+ | 722-788 | 2026-06-06 |

### 5.5 Áreas de Exclusión (No testear)

Los siguientes módulos NO requieren cobertura alta:

| Módulo | Razón |
|--------|-------|
| `scripts/profile_pipeline.py` | Solo para debugging |
| `scripts/debug_cascada.py` | Análisis adhoc |
| `streamlit_app/` | Tested manualmente |
| `notebooks/` | Exploración, no código producción |

---

## 6. Coverage Goals

**Estado actual:** 41% → Necesita incremento

### 5.1 Plan de Mejora

1. **Corto plazo (S3-4):** Agregar tests para `core/semantica.py`
2. **Medio plazo (S5-6):** Coverage para `services/data_loader.py`
3. **Largo plazo (S7-8):** Tests de integración completos

---

## 6. Data Validation

### 6.1 Contratos de Datos

```yaml
# config/data_contracts.yaml
fuentes:
  resultados_consolidados:
    hoja: Consolidado Semestral
    columnas_requeridas:
      - Id
      - Fecha
      - Meta
      - Ejecución
      - Cumplimiento
    tipos:
      Id: string
      Meta: float
      Ejecución: float
      Cumplimiento: float
```

### 6.2 Validaciones Automáticas

- **Null checks:** Campos requeridos no nulos
- **Type checks:** Tipos de datos correctos
- **Range checks:** Valores dentro de rangos válidos
- **Uniqueness:** Llaves únicas

---

## 7. Referencias

- **Tests folder:** [`tests/`](../../tests/)
- **Fixtures:** [`tests/conftest.py`](../../tests/conftest.py)
- **Data contracts:** [`config/data_contracts.yaml`](../../config/data_contracts.yaml)
- **Validación robustness:** [`VALIDACION_TEST_ROBUSTNESS.md`](../../06-FASE3/VALIDACION_TEST_ROBUSTNESS.md)
