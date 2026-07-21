# Mapeo de Campos - SGIND ETL

## Flujo de Datos

```
API Kawak (JSON)
    ↓
consolidar_api.py
    ↓
Consolidado_API_Kawak.xlsx
    ↓
actualizar_consolidado.py
    ↓
Resultados Consolidados.xlsx
    ↓
Dashboard Streamlit
```

---

## 1. Fuente: API Kawak

### Campos de Entrada (JSON → Excel)

| Campo Original | Tipo | Descripción | Transformación |
|----------------|------|-------------|----------------|
| `ID` | int/str | Identificador del indicador | Normalizado a string (474.0 → "474") |
| `fecha` | date | Mes reportado | Convertido a datetime |
| `resultado` | float | Valor del indicador (0-1.3) | Validación de rango |
| `analisis` | str | Texto descriptivo | Limpieza de HTML |
| `variables` | str | Componentes desglosados | Conservado tal cual |
| `revisado` | bool | Si fue validado | Convertido a boolean |

### Campos Adicionales (detectados en auditoría)

| Campo | Filas con Datos | Uso |
|-------|-----------------|-----|
| `descripcion` | 12,703 | Descripción del indicador |
| `frecuencia` | 12,703 | Frecuencia de medición |
| `campos_adicionales` | 12,703 | Metadatos extra |
| `Tipo` | 12,703 | Tipo de indicador |
| `año_archivo` | 12,703 | Año del archivo fuente |
| `fecha_corte` | 12,703 | Fecha de corte de datos |
| `responsable` | 12,703 | Persona responsable |
| `proceso` | 12,703 | Proceso asociado |
| `clasificacion` | 12,703 | Clasificación del indicador |
| `estado` | 12,703 | Estado actual |
| `nombre` | 12,703 | Nombre del indicador |
| `sentido` | 12,703 | Sentido del indicador |
| `series` | 738 | Series temporales |
| `exceso` | 1,134 | Valores en exceso |
| `peligro` | 2,349 | Indicadores en peligro |
| `cumplimiento` | 2,350 | Valor de cumplimiento |
| `alerta` | 2,349 | Alertas activas |
| `meta` | 2,362 | Meta definida |

---

## 2. Transformación: consolidar_api.py

### Salida: Indicadores Kawak.xlsx

| Campo Salida | Tipo | Origen | Transformación |
|--------------|------|--------|----------------|
| `Año` | int | `año_archivo` | Año del archivo |
| `Id` | str | `ID` | Normalizado (474.0 → "474") |
| `Indicador` | str | `nombre` | Limpieza HTML |
| `Clasificacion` | str | `clasificacion` | Strip whitespace |
| `Proceso` | str | `proceso` | Strip whitespace |
| `Tipo` | str | `Tipo` | Strip whitespace |
| `Tipo de variable` | str | `Tipo de variable` | Strip whitespace |
| `Periodicidad` | str | `frecuencia` | Strip whitespace |
| `Sentido` | str | `sentido` | Strip whitespace |

### Salida: Consolidado_API_Kawak.xlsx

| Campo Salida | Tipo | Origen | Transformación |
|--------------|------|--------|----------------|
| `ID` | str | `ID` | Normalizado |
| `fecha` | datetime | `fecha` | Convertido a datetime |
| `resultado` | float | `resultado` | Validación de rango |
| `analisis` | str | `analisis` | Limpieza HTML |
| `variables` | str | `variables` | Conservado |
| `revisado` | bool | `revisado` | Convertido a boolean |
| `año_archivo` | int | - | Añadido durante procesamiento |
| *Todos los campos originales* | - | - | Conservados |

---

## 3. Transformación: actualizar_consolidado.py

### Entrada: Consolidado_API_Kawak.xlsx

### Salida: Resultados Consolidados.xlsx

#### Hoja: Consolidado Historico

| Campo Salida | Tipo | Origen | Transformación |
|--------------|------|--------|----------------|
| `Id` | str | `ID` | Normalizado |
| `Fecha` | datetime | `fecha` | Formato Excel |
| `Indicador` | str | lookup | Desde catálogo Kawak |
| `Meta` | float | `meta` | Valor de meta |
| `Ejecucion` | float | `resultado` | Valor ejecutado |
| `Cumplimiento` | float | calculado | Ejecucion/Meta |
| `Categoria` | str | calculado | Semaforización |
| `Anio` | int | `fecha` | Año extraído |
| `Mes` | int | `fecha` | Mes extraído |
| `Tipo_Registro` | str | - | "Historico" |

#### Hoja: Consolidado Semestral

| Campo Salida | Tipo | Origen | Transformación |
|--------------|------|--------|----------------|
| `Id` | str | `ID` | Normalizado |
| `Fecha` | datetime | `fecha` | Formato Excel |
| `Indicador` | str | lookup | Desde catálogo Kawak |
| `Meta` | float | `meta` | Valor de meta |
| `Ejecucion` | float | `resultado` | Agregación semestral |
| `Cumplimiento` | float | calculado | Ejecucion/Meta |
| `Categoria` | str | calculado | Semaforización |
| `Anio` | int | `fecha` | Año extraído |
| `Mes` | int | `fecha` | Mes extraído |
| `Tipo_Registro` | str | - | "Semestral" |

#### Hoja: Consolidado Cierres

| Campo Salida | Tipo | Origen | Transformación |
|--------------|------|--------|----------------|
| `Id` | str | `ID` | Normalizado |
| `Fecha` | datetime | `fecha` | Formato Excel |
| `Indicador` | str | lookup | Desde catálogo Kawak |
| `Meta` | float | `meta` | Valor de meta |
| `Ejecucion` | float | `resultado` | Agregación cierre |
| `Cumplimiento` | float | calculado | Ejecucion/Meta |
| `Categoria` | str | calculado | Semaforización |
| `Anio` | int | `fecha` | Año extraído |
| `Mes` | int | `fecha` | Mes extraído |
| `Tipo_Registro` | str | - | "Cierres" |

---

## 4. Reglas de Negocio

### Rangos Válidos

| Campo | Mínimo | Máximo | Descripción |
|-------|--------|--------|-------------|
| `resultado` | 0 | 1.3 | 0% a 130% |
| `Meta` | 0 | 1.3 | 0% a 130% |
| `Ejecucion` | 0 | 1.3 | 0% a 130% |
| `Cumplimiento` | 0 | 1 | 0% a 100% |

### Semaforización

| Categoría | Rango | Color |
|-----------|-------|-------|
| Verde | Cumplimiento ≥ 0.9 | 🟢 |
| Amarillo | 0.7 ≤ Cumplimiento < 0.9 | 🟡 |
| Rojo | Cumplimiento < 0.7 | 🔴 |

### IDs Especiales

| Campo | IDs | Descripción |
|-------|-----|-------------|
| `IDS_PLAN_ANUAL` | 373, 390, 414-418, 420, 469-471 | Indicadores del plan anual |
| `IDS_TOPE_100` | 208, 218 | Indicadores con tope de 100% |

---

## 5. Validaciones por Capa

### Layer 1: Entrada (consolidar_api.py)

- ✅ Columnas requeridas: ID, fecha, resultado
- ✅ No nulos en ID y fecha
- ✅ Fechas en rango válido
- ✅ Resultados numéricos

### Layer 1.5: Post-consolidación

- ✅ Tamaño mínimo: 1,000 registros
- ✅ IDs únicos: > 50
- ✅ Rango de fechas: > 1 año
- ✅ Sin valores negativos
- ✅ Resultados ≤ 1.3

### Layer 2: Post-construcción

- ✅ Llaves únicas
- ✅ Campos requeridos presentes
- ✅ Rangos de valores válidos
- ✅ Sin filas vacías

### Layer 3: Pre-escritura

- ✅ Columnas esperadas
- ✅ IDs no nulos
- ✅ Fechas válidas
- ✅ Sin duplicados exactos
- ✅ Tamaño razonable (10-50,000)

---

## 6. Campos Huérfanos (Requieren Revisión)

Los siguientes campos tienen datos pero no se usan actualmente en el cálculo de indicadores:

| Campo | Filas | Recomendación |
|-------|-------|---------------|
| `descripcion` | 12,703 | Revisar utilidad para reportes |
| `frecuencia` | 12,703 | Usar para validación temporal |
| `campos_adicionales` | 12,703 | Evaluar contenido |
| `series` | 738 | Implementar desglose por series |
| `exceso` | 1,134 | Usar para indicadores de alerta |
| `peligro` | 2,349 | Integrar en semaforización |
| `alerta` | 2,349 | Mostrar en dashboard |

---

**Última actualización:** 2026-06-03  
**Maintainer:** Equipo SGIND
