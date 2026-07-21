# 📚 Documentación SGIND - Mínimo Documentación Viable (MDV)

> **Última actualización:** 22 de abril de 2026  
> **Status:** ✅ FASE 3 COMPLETA | Reducción MDV aplicada: 81 → 7 documentos (91% reducción)

---

## 🎯 Objetivo

Documentación **mínima pero suficiente** - 7 documentos que cubren todo lo necesario.

---

## 📂 Estructura

```
docs/
├── core/                          ← Documentación MDV activa (7 archivos)
│   ├── 01_Arquitectura.md         ← Arquitectura del sistema
│   ├── 02_Logica_Indicadores.md   ← Cálculo de cumplimiento
│   ├── 03_Modelo_Datos.md         ← Fuentes y esquemas
│   ├── 04_Dashboard.md           ← Visualización y gráficos
│   ├── 05_Operativo.md           ← ETL, deployment, configs
│   ├── 06_Testing_Calidad.md     ← Tests y validación
│   └── 07_Decisiones.md          ← Problemas resueltos
│
├── archive/                      ← Documentación histórica / referencia
├── sql/                          ← Scripts SQL
├── GOVERNANCE.md                 ← Políticas de documentación
└── README.md                     ← Este archivo
```

---

## 📖 Los 7 Documentos MDV

### [01_Arquitectura.md](core/01_Arquitectura.md)
Arquitectura en capas, decisiones técnicas, estructura de archivos, métricas.

### [02_Logica_Indicadores.md](core/02_Logica_Indicadores.md)  
Cálculo de cumplimiento, categorización (Regular/PA), umbrales, "No Aplica".

### [03_Modelo_Datos.md](core/03_Modelo_Datos.md)
Modelo conceptual, fuentes de datos, data contracts, diccionario de campos.

### [04_Dashboard.md](core/04_Dashboard.md)
Páginas, catálogo de gráficos, colores, KPIs, filtros.

### [05_Operativo.md](core/05_Operativo.md)
Pipeline ETL, deployment Streamlit Cloud, GitHub Actions, troubleshooting.

### [06_Testing_Calidad.md](core/06_Testing_Calidad.md)
Estado de tests (149/149), suites, coverage, CI/CD, data validation.

### [07_Decisiones.md](core/07_Decisiones.md)
Problemas resueltos (DRY, enums), decisiones arquitectónicas, lecciones.

---

## 🔗 Documentación de Referencia

| Documento | Descripción |
|-----------|-------------|
| [GOVERNANCE.md](GOVERNANCE.md) | Políticas de documentación (SSOT, KISS) |
| [archive/FUENTES_DATOS_PROYECTO.md](archive/FUENTES_DATOS_PROYECTO.md) | Catálogo completo de fuentes con rutas |
| [archive/FUENTES_POR_PAGINA.md](archive/FUENTES_POR_PAGINA.md) | Detalle de qué fuente/hoja usa cada página |
| [archive/05-FASE2/FASE_2_PLAN.md](archive/05-FASE2/FASE_2_PLAN.md) | Plan detallado Fase 2 |

---

## 📊 Estado del Proyecto

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Documentos docs/** | 7 (de 81) | ✅ 91% reducción |
| **Tests Totales** | 149 | ✅ |
| **Tests Pasando** | 149 | ✅ 100% |
| **Coverage** | 41% | 🟡 |
| **Fases Completadas** | FASE 3 | ✅ |

---

## 🚀 Inicio Rápido

### Para entender el sistema
1. [01_Arquitectura.md](core/01_Arquitectura.md) - Visión general
2. [02_Logica_Indicadores.md](core/02_Logica_Indicadores.md) - Cómo se calculan los indicadores

### Para desarrollo
1. [03_Modelo_Datos.md](core/03_Modelo_Datos.md) - Fuentes y esquemas
2. [05_Operativo.md](core/05_Operativo.md) - Configuración local

### Para testing
1. [06_Testing_Calidad.md](core/06_Testing_Calidad.md) - Tests y coverage
2. [07_Decisiones.md](core/07_Decisiones.md) - Problemas conocidos

---

## 🔧 Configuración del Sistema

- **[config.toml](../config.toml)** - Configuración Streamlit
- **[config/settings.toml](../config/settings.toml)** - Parámetros ETL
- **[requirements.txt](../requirements.txt)** - Dependencias Python

---

**Proyecto:** Sistema de Indicadores Policial (SGIND)  
**Status:** ✅ OPERACIONAL  
**Reducción:** 81 → 7 documentos (91%) ✅
