# 03 - MODELO DE DATOS

**Documento:** 03_Modelo_Datos.md  
**Versión:** 1.0  
**Fecha:** 22 de abril de 2026  
**Status:** ✅ Consolidado MDV

---

## 1. Modelo Conceptual

```
┌──────────────────────────────────────────────────────────┐
│                    INDICADOR                             │
│  ┌─ ID (PK)                                             │
│  ├─ Nombre                                              │
│  ├─ Descripción                                         │
│  ├─ Sentido (Ascendente/Descendente)                   │
│  ├─ Clasificación                                       │
│  ├─ Periodicidad (Mensual/Trimestral/Semestral/Anual) │
│  ├─ Unidad                                              │
│  ├─ Fórmula                                             │
│  └─ Estado (Activo/Inactivo)                           │
└──────────────────────────────────────────────────────────┘
              ↓ MUCHOS A MUCHOS ↓
┌──────────────────────────────────────────────────────────┐
│              INDICADOR_RESULTADO                         │
│  ┌─ ID_Indicador (FK)                                  │
│  ├─ Fecha                                              │
│  ├─ Año                                                │
│  ├─ Período (Mes/Semestre/Trimestre)                 │
│  ├─ Meta                                               │
│  ├─ Ejecución                                          │
│  ├─ Cumplimiento (calculado)                            │
│  └─ Fuente                                              │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Fuentes de Datos

### 2.1 Fuentes Oficiales de Negocio

| Fuente | Ruta | Tipo | Consumida por |
|--------|------|------|--------------|
| Resultados Consolidados | `data/output/Resultados Consolidados.xlsx` | Excel | services/data_loader.py, streamlit_app |
| API Kawak consolidada | `data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx` | Excel | scripts/actualizar_consolidado.py |
| Catálogo Kawak | `data/raw/Fuentes Consolidadas/Indicadores Kawak.xlsx` | Excel | scripts/actualizar_consolidado.py |
| Indicadores por CMI | `data/raw/Indicadores por CMI.xlsx` | Excel | services/data_loader.py, páginas CMI |
| Ficha Técnica | `data/raw/Ficha_Tecnica.xlsx` | Excel | services/data_loader.py |
| Acciones de mejora | `data/raw/acciones_mejora.xlsx` | Excel | services/data_loader.py |
| OM fuente histórica | `data/raw/OM.xlsx` / `OM.xls` | Excel | services/data_loader.py |
| Plan de acción | `data/raw/Plan de accion/PA_*.xlsx` | Excel | streamlit_app/pages/gestion_om.py |
| Jerarquía procesos | `data/raw/Subproceso-Proceso-Area.xlsx` | Excel | services/data_loader.py |

### 2.2 Fuentes de Persistencia

| Fuente | Ruta/Tabla | Tipo | Uso |
|--------|------------|------|-----|
| Registro OM local | `data/db/registros_om.db` | SQLite | Persistencia local OM |
| Registro OM remoto | `public.registros_om` (Supabase) | PostgreSQL | Persistencia remota |

### 2.3 Fuentes de Configuración

| Fuente | Ruta | Propósito |
|--------|------|-----------|
| Settings globales | `config/settings.toml` | Parámetros ETL/app |
| Contratos de datos | `config/data_contracts.yaml` | Reglas validación |
| Mapeo de procesos | `config/mapeos_procesos.yaml` | Jerarquía proceso/subproceso |

---

## 3. Hojas del Consolidado

| Hoja | Propósito | Uso |
|------|-----------|-----|
| **Consolidado Semestral** | Fuente principal general | Todas las páginas excepto Gestión OM |
| **Consolidado Historico** | Histórico para Gestión OM | Exclusivo gestion_om.py |
| **Consolidado Cierres** | Cierres semestrales | resumen_general.py, cmi_estrategico.py |
| **Catalogo Indicadores** | Catálogo de indicadores | Mantenimiento |

**Regla:** `Dataset_Unificado.xlsx` es referencia histórica, NO fuente primaria.

---

## 4. Data Contracts

### Convenciones de Tipos

```
string       → Texto (0-200 caracteres)
integer      → Número entero
float        → Número decimal
boolean      → true / false
datetime     → ISO 8601 (YYYY-MM-DD HH:MM:SS)
categorical  → Valores enumerados
```

### Atributos de Campo

```yaml
tipo: string
requerida: true/false
longitud_min: mínimo caracteres
longitud_max: máximo caracteres
min: valor mínimo (numeric)
max: valor máximo (numeric)
patron: regex pattern
valores_permitidos: lista de opciones
formato: formato específico
descripcion: explicación en lenguaje natural
```

### Responsabilidades

| Rol | Responsabilidad |
|-----|-----------------|
| Data Engineer | Mantener data contracts actualizado |
| QA | Validar contracts en tests |
| Analytics | Reportar infracciones |

---

## 5. Diccionario de Campos Principales

### Consolidado Semestral

| Campo | Tipo | Descripción |
|-------|------|-------------|
| Id | string | Identificador único del indicador |
| Nombre | string | Nombre del indicador |
| Fecha | date | Fecha del registro |
| Año | integer | Año |
| Mes | integer | Mes |
| Meta | float | Meta establecida |
| Ejecución | float | Ejecución real |
| Cumplimiento | float | Porcentaje de cumplimiento |
| Sentido | categorical | Ascendente/Descendente |
| Línea | string | Línea estratégica |
| Objetivo | string | Objetivo estratégico |
| tiene_om | boolean | Tiene oportunidad de mejora |

### Consolidado Cierres (Proyectos)

El consolidado de cierres se utiliza también para proyectos institucionales. Los proyectos se identifican mediante el flag `Proyecto == 1` en el archivo `Indicadores por CMI.xlsx`.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| Id | string | Identificador del proyecto |
| Indicador | string | Nombre del proyecto |
| Línea | string | Línea estratégica del proyecto |
| Objetivo | string | Objetivo estratégico |
| Anio | integer | Año del registro |
| Mes | integer | Mes del registro |
| Meta | float | Meta del proyecto |
| Ejecución | float | Ejecución real |
| cumplimiento_pct | float | Porcentaje de cumplimiento |

### Plan de Retos

Los retos se cargan desde el archivo `data/raw/Retos/Plan de retos.xlsx` con las siguientes hojas:

| Hoja | Descripción |
|------|-------------|
| Linea | Retos por línea estratégica |
| Objetivos | Detalle de objetivos por reto |

---

## 6. Trazabilidad de Cambios

Para mantener consistencia cuando cambie una fuente:

1. Actualizar primero `config/data_contracts.yaml`
2. Actualizar documentación
3. Ajustar loaders y páginas consumidoras
4. Validar visualmente en Streamlit
5. Ejecutar pruebas relevantes

---

## 7. Referencias

- **Data Contracts YAML:** [`config/data_contracts.yaml`](../../config/data_contracts.yaml)
- **Data Loader:** [`services/data_loader.py`](../../services/data_loader.py)
- **Fuentes completas:** [FUENTES_DATOS_PROYECTO.md](./FUENTES_DATOS_PROYECTO.md)
