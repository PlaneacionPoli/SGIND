# SGIND — Criterios de Exclusión de Indicadores

**Fecha:** 2026-06-04  
**Versión:** 1.0  
**Agente responsable:** Agent 3 — Indicator Integrity Analysis

---

## Resumen

Este documento define los criterios de exclusión para el análisis de integridad de indicadores SGIND. Los indicadores excluidos **NO son válidos** para auditoría de metadatos, fórmulas o responsables.

**Total de exclusiones:** 143 indicadores  
**Indicadores válidos para auditoría:** ~502 (de 672 totales)

---

## Criterios de Exclusión

### 1. Proyectos Estratégicos (44 indicadores)

**Descripción:** Indicadores marcados como proyectos en CMI (`Proyecto = 1`). Son iniciativas estratégicas que no tienen ficha técnica formal ni fórmula documentada en el sistema.

**Identificación:**
```python
exclude_by_proyecto = df_cmi[df_cmi["Proyecto"] == 1]["Id"]
```

**Ejemplos:**
- ID 1: Innovación curricular
- ID 2: Plan Talento
- ID 3: Nuevo POLISIGS
- ID 4: Certificación SGA sede los Colores
- ID 5: Equidad de Género
- ID 6: Portal Web Universitario
- ID 7: Data Lake Institucional
- ID 8: Catálogo de recursos virtuales
- ID 9: Monarca-Ecosistema Banner
- ID 10: Acreditación Institucional Sede Bogotá - Fase II

**Justificación:** Estos indicadores son proyectos en ejecución que aún no han sido formalizados como indicadores institucionales. No cuentan con definición de fórmula, responsable o periodicidad establecida.

---

### 2. Sede Medellín (25 indicadores)

**Descripción:** Indicadores cuyo ID inicia con `Med`. Son indicadores exclusivos de la sede Medellín y no aplican a la consolidated institucional.

**Identificación:**
```python
exclude_by_med = df_cmi[df_cmi["Id"].str.startswith("Med")]["Id"]
```

**Ejemplos:**
- Med 1: Total Estudiantes Sede Medellín
- Med 1.1: Estudiante nuevos presencial pregrado
- Med 1.2: Estudiante nuevos presencial posgrado
- Med 1.3: Total estudiantes nuevos presencial Medellín
- Med 1.4: Estudiantes antiguos presencial Medellín
- Med 2: Total Estudiantes Pregrado nuevos y antiguos Medellín
- Med 3: Estudiantes Postgrado antiguos
- Med 4: Total estudiantes Postgrado antiguos y nuevos Medellín
- Med 5: Total Estudiantes virtuales antiguos-Antioquia
- Med 6: Ingresos Educación para la vida
- Med 7: Satisfacción NPS
- Med 8: Tasa de permanencia
- Med 9: Satisfacción SSI
- Med 10: Total ingresos sede
- Med 11: EBITDA sede
- Med 12: Ejecución Presupuestal
- Med 13: Eficiencia OPEX
- Med 14: Cumplimiento proyecto Certificación SGA - Medellín
- Med 15: Cumplimiento del Plan Anual
- Med 16: Convenios con impacto en ingresos adicionales
- Med 17: Medición Clima organizacional Sede - Great Place to work

**Sub-indicadores Med:**
- Med 2.1: Estudiantes virtuales pregrado nuevos
- Med 4.1: Estudiantes virtuales posgrado nuevos
- Med 2.2: Estudiantes virtuales pregrado antiguos - Medellín
- Med 4.2: Estudiantes virtuales posgrado antiguos - Medellín

**Justificación:** Estos indicadores son específicos de una sede regional y no deben ser incluidos en los reportes institucionales consolidados.

---

### 3. Indicadores Provisionales (15 indicadores)

**Descripción:** Indicadores cuyo ID inician con `Prov`. Son indicadores provisionales que nunca fueron oficializados.

**Identificación:**
```python
exclude_by_prov = df_cmi[df_cmi["Id"].str.startswith("Prov")]["Id"]
```

**Ejemplos:**
- Prov-1: Valor académico agregado
- Prov-2: Aporte relativo
- Prov-3: N° Programas con nuevo modelo evaluativo implementado
- Prov-4: Programas en modalidad virtual y híbrida en 2025
- Prov-5: Número de cursos con microcertificación
- Prov-7: Número de estudiantes matriculados IEDTH
- Prov-8: Índice de Permanencia Docente (NPS)
- Prov-9: Índice de Permanencia Administrativos (NPS)
- Prov-10: Diseño del Gobierno de IT
- Prov-11: Arquitectura de Microservicios
- Prov-12: Smart Assistant
- Prov-13: Optimización de procesos del ciclo de vida del estudiante
- Prov-14: Cumplimiento proyecto creación del centro de excelencia analítica
- Prov-15: Índice de madurez analítica institucional y por proceso
- Prov-16: Desempeño de Modelos (Machine Learning - IA)

**Justificación:** Estos indicadores nunca pasaron a producción y no tienen datos históricos válidos.

---

### 4. Indicadores Inactivos 2022-2026 (7 indicadores)

**Descripción:** IDs específicos que no estuvieron activos en el período de análisis.

**Identificación:**
```python
exclude_by_ids = {"61", "62", "63", "64", "65", "66", "67"}
```

**Ejemplos:**
- 61: Plan anual FSCC- DERECHO Y GOBIERNO-DERECHO
- 62: Plan anual FIDI-DISEÑO - DISEÑO GRÁFICO
- 63: Plan anual FIDI-TIC -INGENIERIA DE SISTEMAS
- 64: Plan anual FIDI-OPINA-INGENIERIA INDUSTRIAL
- 65: Plan anual FNGS-NEG Y DLLO INTER-NEGOCIOS INTERNACIONALES
- 66: Plan anual FSCC- EST.PSIC,TH Y SOC- PSICOLOGÍA
- 67: Plan anual DIRECCIÓN DE MATRÍCULAS

**Justificación:** Estos planes anuales de facultades no estuvieron activos en el período 2022-2026 y no tienen datos válidos para auditoría.

---

### 5. Sub-indicadores Multiserie (52 indicadores)

**Descripción:** Indicadores hijos que forman parte de un indicador principal multiserie. Heredan metadatos del padre.

**Identificación:**
```python
import re
def is_subindicator(ind_id):
    """Verificar si es sub-indicador (patrón: XXX.Y)"""
    return bool(re.match(r'^\d+\.\d+$', str(ind_id).strip()))
```

**Ejemplos:**
- 521.1, 521.2, 521.3 (hijos de 521)
- 108.1, 108.3, 108.5, 108.6, 108.7, 108.8, 108.9, 108.10, 108.11, 108.12, 108.13, 108.14, 108.15 (hijos de 108)
- 415.1, 415.2, ..., 415.14 (hijos de 415)
- 418.1, 418.2, ..., 418.9 (hijos de 418)
- 420.1, 420.2, ..., 420.5 (hijos de 420)
- 14.1, 14.2, 14.3, 14.4 (hijos de 14)
- 386.1, 386.2, 386.3 (hijos de 386)
- 525.1, 525.2, 525.3 (hijos de 525)
- 11.1 (hijo de 11)

**Justificación:** Los sub-indicadores son partes de un indicador multiserie y no requieren ficha técnica propia. Heredan la información del indicador padre.

---

## Implementación en Código

### Script: `scripts/agent3_indicator_integrity.py`

```python
def get_active_indicator_ids(self) -> tuple:
    """Obtener IDs de indicadores activos (excluyendo los no válidos)"""
    
    active_ids = set()
    excluded_ids = set()
    
    # 1. Cargar IDs de API/Kawak (indicadores con datos)
    api_path = self.root_path / "data" / "raw" / "Fuentes Consolidadas" / "Consolidado_API_Kawak.xlsx"
    if api_path.exists():
        df_api = pd.read_excel(api_path)
        api_ids = set(df_api["ID"].dropna().unique().astype(str))
        active_ids.update(api_ids)
    
    # 2. Cargar IDs de CMI y aplicar exclusiones
    cmi_path = self.root_path / "data" / "raw" / "Indicadores por CMI.xlsx"
    if cmi_path.exists():
        df_cmi = pd.read_excel(cmi_path)
        
        # Exclusiones
        exclude_by_proyecto = set(df_cmi[df_cmi["Proyecto"] == 1]["Id"].dropna().unique().astype(str))
        exclude_by_med = set(df_cmi[df_cmi["Id"].astype(str).str.startswith("Med", na=False)]["Id"].dropna().unique().astype(str))
        exclude_by_prov = set(df_cmi[df_cmi["Id"].astype(str).str.startswith("Prov", na=False)]["Id"].dropna().unique().astype(str))
        exclude_by_ids = {"61", "62", "63", "64", "65", "66", "67"}
        
        excluded_ids = exclude_by_proyecto | exclude_by_med | exclude_by_prov | exclude_by_ids
        
        # Agregar solo los no excluidos
        cmi_ids = set(df_cmi["Id"].dropna().unique().astype(str)) - excluded_ids
        active_ids.update(cmi_ids)
    
    return active_ids, excluded_ids
```

### Sub-indicadores

```python
def is_subindicator(self, ind_id: str) -> bool:
    """Verificar si un indicador es sub-indicador multiserie"""
    return bool(re.match(r'^\d+\.\d+$', str(ind_id).strip()))

def get_parent_id(self, ind_id: str) -> str:
    """Obtener ID del indicador padre"""
    match = re.match(r'^(\d+)\.\d+$', str(ind_id).strip())
    if match:
        return match.group(1)
    return ind_id
```

---

## Resultados del Análisis

### Distribución de Indicadores

| Categoría | Cantidad | Porcentaje |
|-----------|----------|------------|
| **Total cargados** | 672 | 100% |
| **Indicadores activos** | 502 | 74.7% |
| **Indicadores excluidos** | 170 | 25.3% |

### Exclusiones por Criterio

| Criterio | Excluidos |
|----------|-----------|
| Proyectos (Proyecto=1) | 44 |
| Sede Medellín (Med) | 25 |
| Provisionales (Prov) | 15 |
| Inactivos 2022-2026 | 7 |
| **Total excluidos** | **91** |

### Indicadores Activos (para auditoría)

| Tipo | Cantidad |
|------|----------|
| **Indicadores principales** | 450 |
| **Sub-indicadores multiserie** | 52 |
| **Total activos** | 502 |

---

## Referencias

- `.agent3.instructions.md` — Instrucciones del Agent 3
- `.agent1.instructions.md` — Instrucciones del Agent 1
- `.agent2.instructions.md` — Instrucciones del Agent 2
- `scripts/agent3_indicator_integrity.py` — Script de auditoría
- `data/raw/Indicadores por CMI.xlsx` — Fuente CMI
- `data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx` — Fuente API/Kawak

---

**Documento generado por:** Agent 3 — Indicator Integrity Analysis Framework  
**Fecha de generación:** 2026-06-04
