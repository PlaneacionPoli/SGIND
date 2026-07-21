"""
AGENT 3 — Indicator Integrity Analysis Framework (Versión Completa v4)
Auditoría integral de TODOS los indicadores SGIND
Maneja sub-indicadores multiserie desde CMI

Ejecutar: python scripts/agent3_indicator_integrity.py
"""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class IndicatorIntegrityAgent:
    """AGENT 3 — Especialista en auditoría de integridad de indicadores"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.indicators = {}
        self.findings = []
        
    def is_subindicator(self, ind_id: str) -> bool:
        """Verificar si un indicador es sub-indicador multiserie (ej: 521.1, 108.13)"""
        return bool(re.match(r'^\d+\.\d+$', str(ind_id).strip()))
    
    def get_parent_id(self, ind_id: str) -> str:
        """Obtener ID del indicador padre (ej: 521.1 -> 521)"""
        match = re.match(r'^(\d+)\.\d+$', str(ind_id).strip())
        if match:
            return match.group(1)
        return ind_id
    
    def load_all_indicators(self) -> pd.DataFrame:
        """Cargar TODOS los indicadores desde múltiples fuentes"""
        
        all_indicators = []
        existing_ids = set()
        
        # 1. Cargar desde Ficha Técnica (fuente principal con más información)
        # Desde la fusión 2026-07-13, vive en 'Ficha Tecnica Detalle' del
        # directorio maestro (antes 'Ficha_Tecnica_Indicadores.xlsx').
        ficha_path = self.root_path / "data" / "raw" / "Catalogo de Indicadores.xlsx"
        if ficha_path.exists():
            df_ficha = pd.read_excel(ficha_path, sheet_name="Ficha Tecnica Detalle")
            logger.info(f"  Ficha Técnica: {len(df_ficha)} registros cargados")
            
            for _, row in df_ficha.iterrows():
                ind_id = str(row.get("Id Ind", row.get("ID Kawak", "")))
                
                ind = {
                    "id": ind_id,
                    "nombre": row.get("Nombre del indicador", ""),
                    "clasificacion": row.get("Clasificación", row.get("Clasificaci\u00f3n", "")),
                    "proceso": row.get("Proceso/Subproceso", ""),
                    "periodicidad": row.get("Frecuencia", ""),
                    "sentido": row.get("Sentido", ""),
                    "tipo": row.get("Tipo de Indicador", ""),
                    "formula": row.get("Formula", ""),
                    "responsable_calculo": row.get("Responsable del calculo", ""),
                    "responsable_analisis": row.get("Responsable del analisis", ""),
                    "unidad": row.get("Unidad", ""),
                    "descripcion": row.get("Descripción del indicador", row.get("Descripci\u00f3n del indicador", "")),
                    "linea_estrategica": row.get("Linea_Estrategica", ""),
                    "objetivo": row.get("Objetivo_Estrategico", ""),
                    "meta_general": row.get("Meta General", ""),
                    "es_subindicador": False,  # Ficha Técnica solo tiene principales
                    "indicador_padre": None,
                    "fuente": "Ficha Técnica"
                }
                all_indicators.append(ind)
                existing_ids.add(ind_id)
        
        # 2. Cargar desde Catalogo Indicadores (incluye sub-indicadores)
        # Desde la fusión 2026-07-13 (antes 'Indicadores por CMI.xlsx').
        cmi_path = self.root_path / "data" / "raw" / "Catalogo de Indicadores.xlsx"
        temp_cmi_path = self.root_path / "temp_cmi.xlsx"

        # Use temp copy if original is locked
        if cmi_path.exists():
            try:
                df_cmi = pd.read_excel(cmi_path, sheet_name="Catalogo Indicadores")
            except PermissionError:
                logger.info("  Original locked, using temp copy...")
                if temp_cmi_path.exists():
                    df_cmi = pd.read_excel(temp_cmi_path, sheet_name="Catalogo Indicadores")
                else:
                    import shutil
                    shutil.copy2(cmi_path, temp_cmi_path)
                    df_cmi = pd.read_excel(temp_cmi_path, sheet_name="Catalogo Indicadores")
            logger.info(f"  CMI: {len(df_cmi)} registros cargados")
            
            subindicadores_count = 0
            principales_count = 0
            
            for _, row in df_cmi.iterrows():
                ind_id = str(row.get("Id", ""))
                
                # Solo agregar si no existe ya
                if ind_id not in existing_ids:
                    es_sub = self.is_subindicator(ind_id)
                    
                    ind = {
                        "id": ind_id,
                        "nombre": row.get("Indicador", ""),
                        "clasificacion": row.get("Clasificacion", ""),
                        "proceso": row.get("Subproceso", ""),
                        "periodicidad": row.get("Periodicidad", ""),
                        "sentido": row.get("Sentido", ""),
                        "tipo": row.get("Tipo de indicador", ""),
                        "formula": "",
                        "responsable_calculo": "",
                        "responsable_analisis": "",
                        "unidad": "",
                        "descripcion": "",
                        "linea_estrategica": row.get("Linea_Estrategica", ""),
                        "objetivo": row.get("Objetivo_Estrategico", ""),
                        "meta_general": row.get("Meta_Estrategica", ""),
                        "es_subindicador": es_sub,
                        "indicador_padre": self.get_parent_id(ind_id) if es_sub else None,
                        "fuente": "Catalogo Indicadores"
                    }
                    all_indicators.append(ind)
                    existing_ids.add(ind_id)
                    
                    if es_sub:
                        subindicadores_count += 1
                    else:
                        principales_count += 1
            
            logger.info(f"    - Principales nuevos: {principales_count}")
            logger.info(f"    - Sub-indicadores: {subindicadores_count}")
        
        # Crear DataFrame
        df_all = pd.DataFrame(all_indicators)
        
        # Estadísticas
        total = len(df_all)
        subindicadores = df_all[df_all["es_subindicador"] == True].shape[0]
        principales = total - subindicadores
        
        logger.info(f"  Total registros: {total}")
        logger.info(f"  Indicadores principales: {principales}")
        logger.info(f"  Sub-indicadores multiserie: {subindicadores}")
        
        return df_all
    
    def get_active_indicator_ids(self) -> set:
        """Obtener IDs de indicadores que están activos en CMI o tienen datos en Kawak/API"""
        
        active_ids = set()
        excluded_ids = set()
        
        # 1. Cargar IDs de Consolidado_API_Kawak (indicadores con datos)
        api_path = self.root_path / "data" / "raw" / "Fuentes Consolidadas" / "Consolidado_API_Kawak.xlsx"
        if api_path.exists():
            df_api = pd.read_excel(api_path)
            api_ids = set(df_api["ID"].dropna().unique().astype(str))
            active_ids.update(api_ids)
            logger.info(f"  API/Kawak: {len(api_ids)} indicadores únicos con datos")
        
        # 2. Cargar IDs de Catalogo Indicadores y aplicar filtros de exclusión
        # Desde la fusión 2026-07-13 (antes 'Indicadores por CMI.xlsx').
        cmi_path = self.root_path / "data" / "raw" / "Catalogo de Indicadores.xlsx"
        temp_cmi_path = self.root_path / "temp_cmi.xlsx"

        if cmi_path.exists():
            try:
                df_cmi = pd.read_excel(cmi_path, sheet_name="Catalogo Indicadores")
            except PermissionError:
                if temp_cmi_path.exists():
                    df_cmi = pd.read_excel(temp_cmi_path, sheet_name="Catalogo Indicadores")
                else:
                    import shutil
                    shutil.copy2(cmi_path, temp_cmi_path)
                    df_cmi = pd.read_excel(temp_cmi_path, sheet_name="Catalogo Indicadores")
            
            # IDs a excluir por various razones
            exclude_by_proyecto = set(df_cmi[df_cmi["Proyecto"] == 1]["Id"].dropna().unique().astype(str))
            
            # Med: IDs que inician con "Med" (Sede Medellín)
            exclude_by_med = set(df_cmi[df_cmi["Id"].astype(str).str.startswith("Med", na=False)]["Id"].dropna().unique().astype(str))
            
            # Prov: IDs que inician con "Prov" (Proyectos no oficializados)
            exclude_by_prov = set(df_cmi[df_cmi["Id"].astype(str).str.startswith("Prov", na=False)]["Id"].dropna().unique().astype(str))
            
            # IDs 61-67 (inactivos 2022-2026)
            exclude_by_ids = {"61", "62", "63", "64", "65", "66", "67"}
            
            excluded_ids = exclude_by_proyecto | exclude_by_med | exclude_by_prov | exclude_by_ids
            
            logger.info(f"  CMI exclusiones:")
            logger.info(f"    - Proyectos (Proyecto=1): {len(exclude_by_proyecto)}")
            logger.info(f"    - Med (Sede Medellín): {len(exclude_by_med)}")
            logger.info(f"    - Prov (no oficializados): {len(exclude_by_prov)}")
            logger.info(f"    - IDs 61-67 (inactivos 2022-2026): {len(exclude_by_ids)}")
            logger.info(f"    - Total excluidos: {len(excluded_ids)}")
            
            # Agregar solo los no excluidos
            cmi_ids = set(df_cmi["Id"].dropna().unique().astype(str)) - excluded_ids
            active_ids.update(cmi_ids)
            logger.info(f"  CMI válidos: {len(cmi_ids)}")
        
        logger.info(f"  Total indicadores activos (CMI ∪ API - excluidos): {len(active_ids)}")
        return active_ids, excluded_ids
    
    def audit_formula_uniqueness(self, df_indicators: pd.DataFrame) -> List[Dict]:
        """Auditar unicidad de fórmulas"""
        
        findings = []
        
        # Verificar que exista una única definición en docs
        docs_path = self.root_path / "docs" / "core" / "02_Logica_Indicadores.md"
        if docs_path.exists():
            with open(docs_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            formula_patterns = [
                r"cumplimiento\s*=\s*ejecución\s*/\s*meta",
                r"cumplimiento\s*=\s*meta\s*/\s*ejecución",
                r"min\(cumplimiento,\s*1\.3\)"
            ]
            
            for pattern in formula_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if len(matches) > 1:
                    findings.append({
                        "tipo": "Fórmula_Duplicada_Docs",
                        "severidad": "MEDIA",
                        "descripcion": f"Múltiples definiciones de fórmula encontradas en docs: {len(matches)}",
                        "ubicacion": str(docs_path),
                        "recomendación": "Consolidar en una única definición"
                    })
        
        # Verificar implementación en código
        calc_path = self.root_path / "core" / "calculos.py"
        if calc_path.exists():
            with open(calc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if "def categorizar_cumplimiento" in content:
                if "_categorizar_cumplimiento_oficial" in content:
                    findings.append({
                        "tipo": "Delegación_Correcta",
                        "severidad": "OK",
                        "descripcion": "calculos.py delega a domain.categorization (fuente única)",
                        "ubicacion": "core/calculos.py:77-87",
                        "recomendación": "Mantener"
                    })
        
        return findings
    
    def audit_metadata_completeness(self, df_indicators: pd.DataFrame) -> List[Dict]:
        """Auditar completitud de metadatos para indicadores principales"""
        
        findings = []
        
        for _, row in df_indicators.iterrows():
            ind_id = row.get("id", "")
            ind_name = row.get("nombre", "")
            es_subindicador = row.get("es_subindicador", False)
            
            # Los sub-indicadores no requieren ficha técnica propia
            if es_subindicador:
                continue
            
            # Verificar nombre
            if not ind_name or pd.isna(ind_name) or str(ind_name).strip() == "":
                findings.append({
                    "tipo": "Sin_Nombre",
                    "severidad": "MEDIA",
                    "indicador": ind_id,
                    "descripcion": f"Indicador {ind_id} sin nombre",
                    "recomendación": "Asignar nombre descriptivo"
                })
            
            # Verificar clasificación
            clasificacion = row.get("clasificacion", "")
            if not clasificacion or pd.isna(clasificacion) or str(clasificacion).strip() == "":
                findings.append({
                    "tipo": "Sin_Clasificación",
                    "severidad": "BAJA",
                    "indicador": ind_id,
                    "descripcion": f"Indicador {ind_id} ({ind_name}) sin clasificación",
                    "recomendación": "Asignar clasificación (CMI, Proceso, etc.)"
                })
            
            # Verificar proceso
            proceso = row.get("proceso", "")
            if not proceso or pd.isna(proceso) or str(proceso).strip() == "":
                findings.append({
                    "tipo": "Sin_Proceso",
                    "severidad": "MEDIA",
                    "indicador": ind_id,
                    "descripcion": f"Indicador {ind_id} ({ind_name}) sin proceso asignado",
                    "recomendación": "Asignar proceso al que pertenece"
                })
            
            # Verificar periodicidad
            periodicidad = row.get("periodicidad", "")
            if not periodicidad or pd.isna(periodicidad) or str(periodicidad).strip() == "":
                findings.append({
                    "tipo": "Sin_Periodicidad",
                    "severidad": "MEDIA",
                    "indicador": ind_id,
                    "descripcion": f"Indicador {ind_id} ({ind_name}) sin periodicidad definida",
                    "recomendación": "Definir periodicidad (Mensual, Trimestral, etc.)"
                })
            
            # Verificar sentido
            sentido = row.get("sentido", "")
            if not sentido or pd.isna(sentido) or str(sentido).strip() == "":
                findings.append({
                    "tipo": "Sin_Sentido",
                    "severidad": "BAJA",
                    "indicador": ind_id,
                    "descripcion": f"Indicador {ind_id} ({ind_name}) sin sentido definido",
                    "recomendación": "Definir sentido (Positivo/Negativo)"
                })
            
            # Verificar fórmula
            formula = row.get("formula", "")
            if not formula or pd.isna(formula) or str(formula).strip() == "":
                findings.append({
                    "tipo": "Sin_Fórmula",
                    "severidad": "ALTA",
                    "indicador": ind_id,
                    "descripcion": f"Indicador {ind_id} ({ind_name}) sin fórmula documentada",
                    "recomendación": "Documentar fórmula de cálculo"
                })
            
            # Verificar responsable de cálculo
            resp_calc = row.get("responsable_calculo", "")
            if not resp_calc or pd.isna(resp_calc) or str(resp_calc).strip() == "":
                findings.append({
                    "tipo": "Sin_Responsable_Cálculo",
                    "severidad": "BAJA",
                    "indicador": ind_id,
                    "descripcion": f"Indicador {ind_id} ({ind_name}) sin responsable de cálculo",
                    "recomendación": "Asignar responsable de cálculo"
                })
            
            # Verificar responsable de análisis
            resp_analisis = row.get("responsable_analisis", "")
            if not resp_analisis or pd.isna(resp_analisis) or str(resp_analisis).strip() == "":
                findings.append({
                    "tipo": "Sin_Responsable_Análisis",
                    "severidad": "BAJA",
                    "indicador": ind_id,
                    "descripcion": f"Indicador {ind_id} ({ind_name}) sin responsable de análisis",
                    "recomendación": "Asignar responsable de análisis"
                })
        
        return findings
    
    def audit_indicator_consistency(self, df_indicators: pd.DataFrame) -> List[Dict]:
        """Auditar consistencia entre indicadores"""
        
        findings = []
        
        # Verificar que sub-indicadores tengan indicador padre válido
        subindicadores = df_indicators[df_indicators["es_subindicador"] == True]
        principales_ids = set(df_indicators[df_indicators["es_subindicador"] == False]["id"].tolist())
        
        for _, row in subindicadores.iterrows():
            ind_id = row.get("id", "")
            padre_id = row.get("indicador_padre", "")
            
            if padre_id and padre_id not in principales_ids:
                findings.append({
                    "tipo": "Sub_Indicador_Sin_Padre",
                    "severidad": "MEDIA",
                    "indicador": ind_id,
                    "descripcion": f"Sub-indicador {ind_id} tiene padre {padre_id} que no existe como indicador principal",
                    "recomendación": "Verificar relación padre-hijo"
                })
        
        return findings
    
    def audit_hardcoding(self) -> List[Dict]:
        """Auditar valores hardcodeados"""
        
        findings = []
        
        calc_path = self.root_path / "core" / "calculos.py"
        if calc_path.exists():
            with open(calc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            magic_numbers = re.findall(r'(?<![a-zA-Z_])(?:0\.\d{2,}|1\.\d{1,2})\b', content)
            
            if magic_numbers:
                findings.append({
                    "tipo": "Magic_Numbers",
                    "severidad": "MEDIA",
                    "descripcion": f"Valores numéricos hardcodeados encontrados: {set(magic_numbers)}",
                    "ubicacion": "core/calculos.py",
                    "recomendación": "Mover a config/settings.toml o core/config.py"
                })
        
        return findings
    
    def generate_audit_matrix(self, df_indicators: pd.DataFrame) -> pd.DataFrame:
        """Generar matriz de auditoría para TODOS los indicadores"""
        
        matrix_data = []
        
        for _, row in df_indicators.iterrows():
            ind_id = row.get("id", "")
            ind_name = row.get("nombre", "")
            es_subindicador = row.get("es_subindicador", False)
            
            if es_subindicador:
                # Sub-indicadores solo muestran que son parte de un padre
                matrix_data.append({
                    "ID": ind_id,
                    "Nombre": str(ind_name)[:50] if ind_name and not pd.isna(ind_name) else "Sub-indicador",
                    "Tipo": "Sub-indicador",
                    "Padre": row.get("indicador_padre", ""),
                    "Clasificación": "-",
                    "Proceso": "-",
                    "Periodicidad": "-",
                    "Sentido": "-",
                    "Fórmula": "-",
                    "Responsable": "-",
                    "Fuente": row.get("fuente", "Desconocida")
                })
            else:
                # Indicadores principales
                has_clasificacion = row.get("clasificacion") and not pd.isna(row.get("clasificacion")) and str(row.get("clasificacion")).strip() != ""
                has_proceso = row.get("proceso") and not pd.isna(row.get("proceso")) and str(row.get("proceso")).strip() != ""
                has_periodicidad = row.get("periodicidad") and not pd.isna(row.get("periodicidad")) and str(row.get("periodicidad")).strip() != ""
                has_sentido = row.get("sentido") and not pd.isna(row.get("sentido")) and str(row.get("sentido")).strip() != ""
                has_formula = row.get("formula") and not pd.isna(row.get("formula")) and str(row.get("formula")).strip() != ""
                has_responsable = row.get("responsable_calculo") and not pd.isna(row.get("responsable_calculo")) and str(row.get("responsable_calculo")).strip() != ""
                
                matrix_data.append({
                    "ID": ind_id,
                    "Nombre": str(ind_name)[:50] if ind_name and not pd.isna(ind_name) else "Sin nombre",
                    "Tipo": "Principal",
                    "Padre": "",
                    "Clasificación": "✅" if has_clasificacion else "❌",
                    "Proceso": "✅" if has_proceso else "❌",
                    "Periodicidad": "✅" if has_periodicidad else "❌",
                    "Sentido": "✅" if has_sentido else "❌",
                    "Fórmula": "✅" if has_formula else "❌",
                    "Responsable": "✅" if has_responsable else "❌",
                    "Fuente": row.get("fuente", "Desconocida")
                })
        
        return pd.DataFrame(matrix_data)
    
    def generate_report(self, df_indicators: pd.DataFrame, total_all: int, total_active: int, total_inactive: int) -> str:
        """Generar reporte completo de auditoría"""
        
        # Ejecutar auditorías
        formula_findings = self.audit_formula_uniqueness(df_indicators)
        metadata_findings = self.audit_metadata_completeness(df_indicators)
        consistency_findings = self.audit_indicator_consistency(df_indicators)
        hardcoding_findings = self.audit_hardcoding()
        
        all_findings = formula_findings + metadata_findings + consistency_findings + hardcoding_findings
        
        # Estadísticas (solo indicadores principales)
        df_principales = df_indicators[df_indicators["es_subindicador"] == False]
        df_subindicadores = df_indicators[df_indicators["es_subindicador"] == True]
        
        total_indicators = len(df_indicators)
        total_principales = len(df_principales)
        total_subindicadores = len(df_subindicadores)
        
        # Contar campos completados (solo principales)
        def count_valid(col_name, df):
            if col_name in df.columns:
                return len(df[df[col_name].notna() & (df[col_name].astype(str).str.strip() != "")])
            return 0
        
        with_name = count_valid("nombre", df_principales)
        with_clasificacion = count_valid("clasificacion", df_principales)
        with_proceso = count_valid("proceso", df_principales)
        with_periodicidad = count_valid("periodicidad", df_principales)
        with_sentido = count_valid("sentido", df_principales)
        with_formula = count_valid("formula", df_principales)
        with_responsable = count_valid("responsable_calculo", df_principales)
        
        # Generar reporte
        report = f"""# AGENT 3 — Indicator Integrity Audit Report (Completo v5)
**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Status:** Auditoría completada  

---

## 📊 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Total registros cargados (todas las fuentes)** | {total_all} |
| **Indicadores activos (CMI ∪ API)** | {total_active} |
| **Indicadores inactivos (excluidos)** | {total_inactive} |
| **Indicadores principales analizados** | {total_principales} |
| **Sub-indicadores multiserie** | {total_subindicadores} |

### Completitud (Solo Indicadores Principales)

| Campo | Completados | Faltantes | Porcentaje |
|-------|-------------|-----------|------------|
| Nombre | {with_name} | {total_principales - with_name} | {(with_name/total_principales*100):.1f}% |
| Clasificación | {with_clasificacion} | {total_principales - with_clasificacion} | {(with_clasificacion/total_principales*100):.1f}% |
| Proceso | {with_proceso} | {total_principales - with_proceso} | {(with_proceso/total_principales*100):.1f}% |
| Periodicidad | {with_periodicidad} | {total_principales - with_periodicidad} | {(with_periodicidad/total_principales*100):.1f}% |
| Sentido | {with_sentido} | {total_principales - with_sentido} | {(with_sentido/total_principales*100):.1f}% |
| Fórmula | {with_formula} | {total_principales - with_formula} | {(with_formula/total_principales*100):.1f}% |
| Responsable | {with_responsable} | {total_principales - with_responsable} | {(with_responsable/total_principales*100):.1f}% |

### Hallazgos

| Severidad | Cantidad |
|-----------|----------|
| **Críticos** | {len([f for f in all_findings if f['severidad'] == 'CRÍTICA'])} |
| **Altos** | {len([f for f in all_findings if f['severidad'] == 'ALTA'])} |
| **Medios** | {len([f for f in all_findings if f['severidad'] == 'MEDIA'])} |
| **Bajos** | {len([f for f in all_findings if f['severidad'] == 'BAJA'])} |
| **OK** | {len([f for f in all_findings if f['severidad'] == 'OK'])} |

---

## 🔍 Distribución por Fuente

"""
        
        if "fuente" in df_indicators.columns:
            source_counts = df_indicators["fuente"].value_counts()
            for source, count in source_counts.items():
                report += f"- **{source}:** {count} registros\n"
        
        report += f"""

---

## 📋 Sub-indicadores Multiserie Detectados

| Indicador Principal | Sub-indicadores |
|---------------------|-----------------|
"""
        
        # Agrupar sub-indicadores por padre
        if total_subindicadores > 0:
            sub_by_parent = df_subindicadores.groupby("indicador_padre").size().sort_values(ascending=False)
            for padre, count in sub_by_parent.head(15).items():
                report += f"| {padre} | {count} sub-indicadores |\n"
        
        report += f"""

**Nota:** Los sub-indicadores (ej: 521.1, 108.13) son parte de indicadores multiserie y NO se cuentan como faltantes.

---

## 🎯 Hallazgos por Tipo (Solo Indicadores Principales)

### Metadatos Faltantes
"""
        
        metadata_by_type = defaultdict(int)
        for f in metadata_findings:
            metadata_by_type[f["tipo"]] += 1
        
        for tipo, count in sorted(metadata_by_type.items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"- **{tipo}:** {count} indicadores\n"
        
        report += f"""

---

## 📁 Recomendaciones

### Inmediatas (0-2 horas)
1. Completar fórmulas para los {total_principales - with_formula} indicadores principales faltantes
2. Asignar proceso a los {total_principales - with_proceso} indicadores sin proceso
3. Definir periodicidad para los {total_principales - with_periodicidad} indicadores sin periodicidad

### Corto Plazo (2-8 horas)
1. Asignar responsable a los {total_principales - with_responsable} indicadores sin responsable
2. Definir sentido a los {total_principales - with_sentido} indicadores sin sentido
3. Crear tests unitarios para fórmulas críticas

### Largo Plazo (> 8 horas)
1. Crear dashboard de integridad de indicadores
2. Implementar alertas automáticas de inconsistencias
3. Automatizar validación docs vs código

---

**Generado por:** AGENT 3 — Indicator Integrity Analysis Framework  
**Versión:** 1.0 SGIND-Optimizada (Versión Completa v4 - con sub-indicadores desde CMI)
"""
        
        return report
    
    def run_analysis(self):
        """Ejecutar auditoría completa"""
        
        print("\n╔════════════════════════════════════════════════════════════════╗")
        print("║  AGENT 3 — INDICATOR INTEGRITY ANALYSIS FRAMEWORK            ║")
        print("║  Auditoría Integral de Indicadores Activos SGIND             ║")
        print("║  (Solo indicadores activos en CMI o con datos en Kawak/API)  ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        
        # PASO 1: Cargar TODOS los indicadores
        print("\n" + "="*70)
        print("PASO 1: CARGAR TODOS LOS INDICADORES")
        print("="*70)
        
        df_all_indicators = self.load_all_indicators()
        
        # PASO 2: Obtener indicadores activos
        print("\n" + "="*70)
        print("PASO 2: FILTRAR INDICADORES ACTIVOS (CMI ∪ API - EXCLUSIONES)")
        print("="*70)
        
        active_ids, excluded_ids = self.get_active_indicator_ids()
        
        # Filtrar solo indicadores activos
        df_indicators = df_all_indicators[df_all_indicators["id"].isin(active_ids)].copy()
        
        total_all = len(df_all_indicators)
        total_active = len(df_indicators)
        total_inactive = total_all - total_active
        
        print(f"  Total indicadores cargados: {total_all}")
        print(f"  Indicadores activos: {total_active}")
        print(f"  Indicadores excluidos: {total_inactive}")
        print(f"    - Proyectos: {len([i for i in excluded_ids if i in ['1','2','3','4','5','6','7','8','9','10']])}+")
        print(f"    - Med (Medellín): {len([i for i in excluded_ids if i.startswith('Med')])}")
        print(f"    - IDs 61-67: {len([i for i in excluded_ids if i in ['61','62','63','64','65','66','67']])}")
        
        # PASO 3: Auditar fórmulas
        print("\n" + "="*70)
        print("PASO 3: AUDITAR FÓRMULAS (SOLO ACTIVOS)")
        print("="*70)
        
        formula_findings = self.audit_formula_uniqueness(df_indicators)
        print(f"  ✓ {len(formula_findings)} hallazgos de fórmulas")
        
        # PASO 4: Auditar metadatos
        print("\n" + "="*70)
        print("PASO 4: AUDITAR METADATOS (SOLO INDICADORES ACTIVOS)")
        print("="*70)
        
        metadata_findings = self.audit_metadata_completeness(df_indicators)
        print(f"  ✓ {len(metadata_findings)} hallazgos de metadatos")
        
        # PASO 5: Auditar consistencia
        print("\n" + "="*70)
        print("PASO 5: AUDITAR CONSISTENCIA")
        print("="*70)
        
        consistency_findings = self.audit_indicator_consistency(df_indicators)
        print(f"  ✓ {len(consistency_findings)} hallazgos de consistencia")
        
        # PASO 6: Auditar hardcoding
        print("\n" + "="*70)
        print("PASO 6: AUDITAR HARDCODING")
        print("="*70)
        
        hardcoding_findings = self.audit_hardcoding()
        print(f"  ✓ {len(hardcoding_findings)} hallazgos de hardcoding")
        
        # PASO 7: Generar reportes
        print("\n" + "="*70)
        print("GENERANDO REPORTES")
        print("="*70)
        
        report = self.generate_report(df_indicators, total_all, total_active, total_inactive)
        
        # Guardar artefactos
        artifacts_dir = self.root_path / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        report_path = artifacts_dir / f"AGENT3_INDICATOR_INTEGRITY_{self.timestamp}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✓ Reporte guardado: {report_path}")
        
        # Guardar matriz CSV
        matrix = self.generate_audit_matrix(df_indicators)
        matrix_path = artifacts_dir / f"AGENT3_AUDIT_MATRIX_{self.timestamp}.csv"
        matrix.to_csv(matrix_path, index=False)
        print(f"✓ Matriz guardada: {matrix_path}")
        
        # Guardar hallazgos JSON
        all_findings = formula_findings + metadata_findings + consistency_findings + hardcoding_findings
        findings_path = artifacts_dir / f"AGENT3_FINDINGS_{self.timestamp}.json"
        with open(findings_path, 'w', encoding='utf-8') as f:
            json.dump(all_findings, f, indent=2, ensure_ascii=False)
        print(f"✓ Hallazgos guardados: {findings_path}")
        
        # Guardar indicadores JSON
        indicators_path = artifacts_dir / f"AGENT3_ALL_INDICATORS_{self.timestamp}.json"
        df_indicators.to_json(indicators_path, orient="records", force_ascii=False, indent=2)
        print(f"✓ Indicadores guardados: {indicators_path}")
        
        print(f"\n{'='*70}")
        print("RESUMEN FINAL")
        print(f"{'='*70}")
        
        df_principales = df_indicators[df_indicators["es_subindicador"] == False]
        df_subindicadores = df_indicators[df_indicators["es_subindicador"] == True]
        
        print(f"✓ Total registros: {len(df_indicators)}")
        print(f"  - Indicadores principales: {len(df_principales)}")
        print(f"  - Sub-indicadores multiserie: {len(df_subindicadores)}")
        print(f"✓ Hallazgos totales: {len(all_findings)}")
        print(f"✓ Críticos: {len([f for f in all_findings if f['severidad'] == 'CRÍTICA'])}")
        print(f"✓ OK: {len([f for f in all_findings if f['severidad'] == 'OK'])}")
        print(f"\n✅ AGENT 3 Analysis Complete")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    agent = IndicatorIntegrityAgent()
    agent.run_analysis()
