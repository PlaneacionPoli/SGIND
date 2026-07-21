# 01 - ARQUITECTURA DEL SISTEMA

**Documento:** 01_Arquitectura.md  
**Versión:** 1.0  
**Fecha:** 22 de abril de 2026  
**Status:** ✅ Consolidado MDV

---

## 1. Visión General del Sistema

SGIND es un **sistema batch de reportería institucional** que consolida 1,000+ indicadores desde múltiples fuentes, aplica reglas de negocio, y entrega dashboards interactivos.

```
ENTRADA (Múltiples fuentes: API Kawak, Excel, PDF)
    ↓
CONSOLIDACIÓN ETL (3 pasos, 45-50 seg)
    ↓
CÁLCULOS (Cumplimiento, tendencias, categorización)
    ↓
VALIDACIÓN (Data contracts, integridad)
    ↓
SALIDA (Dashboard Streamlit + Reportes Excel)
```

### Paradigma: Post-Procesamiento

SGIND implementa **consolidación → reportería → reglas → monitoreo**, NO real-time. Es un batch diario/semanal que:
1. Consolida datos históricos
2. Aplica reglas de negocio
3. Genera reportería estática
4. Expone en dashboard interactivo

---

## 2. Arquitectura en Capas

### 2.1 Capa de Integración (Fuentes)

| Componente | Tipo | Ubicación | Entrada | Salida |
|-----------|------|-----------|---------|--------|
| API Kawak | Sistema web | Kawak.cloud | GET /api/indicators?year=2026 | JSON |
| Excel Histórico | Archivo | `data/raw/Kawak/Catalogo_2026.xlsx` | Hojas: Indicadores, Procesos | 1000+ registros |
| LMI Reporte | Archivo | `data/raw/lmi_reporte.xlsx` | Hoja: LMI | Tracking |
| API Interna | Base datos | PostgreSQL (prod) | Query OMs | 50-200 registros |

### 2.2 Capa de Consolidación (ETL)

**Orquestador:** `scripts/actualizar_consolidado.py`

| Módulo | Responsabilidad |
|--------|----------------|
| `config.py` | Configuración centralizada (año cierre, IDs especiales, rutas) |
| `fuentes.py` | Carga de fuentes externas (API, Kawak, catálogos) |
| `catalogo.py` | Construcción del catálogo de indicadores |
| `builders.py` | Constructores de registros para Histórico, Semestral, Cierres |
| `extraccion.py` | Lógica de extracción de valores (Meta, Ejecución) |
| `signos.py` | Obtención de signos (+/-) por indicador |
| `formulas_excel.py` | Reescritura de fórmulas Excel y materialización |
| `escritura.py` | Escritura de filas al workbook |
| `cumplimiento.py` | Cálculo de cumplimiento |

### 2.3 Capa de Negocio (Core)

| Módulo | Responsabilidad |
|--------|----------------|
| `core/semantica.py` | Categorización de cumplimiento, normalización |
| `core/config.py` | Umbrales y constantes globales |
| `core/calculos.py` | Funciones de cálculo compartidas |

### 2.4 Capa de Presentación (Streamlit)

| Página | Descripción |
|--------|-------------|
| `resumen_general.py` | Dashboard principal con KPIs |
| `cmi_estrategico.py` | Indicadores PDI por líneas/objetivos |
| `plan_mejoramiento.py` | Indicadores CNA por factores |
| `gestion_om.py` | Oportunidades de mejora |
| `resumen_por_proceso.py` | Vista por proceso/subproceso |

---

## 3. Principios de Diseño

- **Separación de capas:** Core (lógica) ≠ Services (datos) ≠ UI (presentación)
- **Testeabilidad:** Lógica en `core/` sin dependencias Streamlit
- **Configurabilidad:** Umbrales en `core/config.py` (no hardcodeados)
- **Persistencia dual:** SQLite (dev) + PostgreSQL (prod)

---

## 4. Decisiones Arquitectónicas Clave

### 4.1 Sin Redis Cloud
- **Decisión:** No implementar caché Redis Cloud
- **Razón:** Sin presupuesto de inversión
- **Alternativa:** Caché local en memoria con TTL configurable

### 4.2 Consolidado Semestral como Hoja Principal
- La hoja **Consolidado Semestral** es la fuente general para la mayoría de páginas
- **Consolidado Historico** es exclusivo para Gestión OM
- **Consolidado Cierres** para procesos de consolidación

### 4.3 Modelo de Datos Desnormalizado
- Datos desnormalizados en Excel para facilitar auditorías manuales
- Fórmulas Excel mantenidas para transparencia
- Validaciones en Python y en data contracts

---

## 5. Estructura de Archivos Clave

```
Sistema_Indicadores_Poli/
├── core/
│   ├── semantica.py      # Lógica categorización (ELIMINAR duplicates)
│   ├── config.py        # Umbrales, constantes
│   └── calculos.py      # Funciones compartidas
├── services/
│   ├── data_loader.py   # Pipeline ETL 5 fases
│   └── strategic_indicators.py  # Indicadores PDI/CNA
├── scripts/
│   ├── actualizar_consolidado.py  # Orquestador ETL
│   └── integrate_consolidado.py
├── streamlit_app/
│   └── pages/           # Páginas del dashboard
├── data/
│   ├── raw/             # Fuentes originales
│   ├── output/          # Resultados consolidados
│   └── db/              # SQLite local
└── docs/
    └── core/            # Documentación consolidada
```

---

## 6. Métricas del Sistema

| Métrica | Valor |
|---------|-------|
| Indicadores activos | 1,000+ |
| Períodos históricos | 60+ (2022-2026, monthly) |
| Registros en consolidado | 60,000+ |
| Frecuencia actualización | Diaria (06:00 UTC) |
| Tiempo procesamiento ETL | 45-50 segundos |
| Tests | 149/149 ✅ |
| Coverage | 41% |

---

## 7. CI/CD y Quality Gates

### Workflows Implementados

| Workflow | Trigger | Validaciones |
|----------|---------|-------------|
| **Tests** | push/PR a main/develop | pytest + coverage |
| **Lint** | push/PR a main/develop | ruff, mypy, bandit |
| **Deploy Staging** | push a develop | Health check en staging |

### Thresholds de Coverage
- 🟢 Verde: ≥ 80%
- 🟡 Naranja: 60-79%
- 🔴 Rojo: < 60%

---

## 8. Referencias

- **Data Contracts:** [DATA-CONTRACTS.md](../02-MODELO-DATOS/DATA-CONTRACTS.md)
- **Fuentes de Datos:** [FUENTES_DATOS_PROYECTO.md](./FUENTES_DATOS_PROYECTO.md)
- **Configuración:** [`config/settings.toml`](../config/settings.toml)
