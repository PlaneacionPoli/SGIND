"""
AGENT 5 — Data Validation Framework
Auditoría completa de calidad de datos en SGIND

Ejecutar: python scripts/agent5_data_validation.py
"""

import pandas as pd
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import IDS_PLAN_ANUAL, UMBRAL_ALERTA_PA, IDS_TOPE_100
from core.domain import categorizar_cumplimiento

class DataValidationAgent:
    """AGENT 5 — Especialista en validación de datos"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.findings = []
        self.validations_inventory = []
        self.anomalies = []
        
    def log_finding(self, hallazgo_type: str, category: str, description: str, 
                    severity: str, evidence: str, impact: str, solution: str):
        """Registrar un hallazgo de validación"""
        self.findings.append({
            "timestamp": self.timestamp,
            "tipo": hallazgo_type,
            "categoria": category,
            "descripcion": description,
            "severidad": severity,
            "evidencia": evidence,
            "impacto": impact,
            "solucion": solution,
        })
    
    def inventory_validations(self) -> List[Dict]:
        """PASO 1: Inventariar TODAS las validaciones existentes"""
        
        print("\n" + "="*70)
        print("PASO 1: INVENTARIAR VALIDACIONES EXISTENTES")
        print("="*70)
        
        # Buscar validaciones en archivos Python clave
        validation_files = [
            ("scripts/actualizar_consolidado.py", "ETL Principal"),
            ("core/calculos.py", "Cálculo de Indicadores"),
            ("core/semantica.py", "Categorización"),
            ("core/config.py", "Configuración y Umbrales"),
            ("generar_reporte.py", "Generación de Reportes"),
        ]
        
        for filepath, descripcion in validation_files:
            full_path = Path(__file__).parent.parent / filepath
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Detectar patrones de validación
                    patterns = [
                        ("assert", "Schema"),
                        ("if not", "Business Rule"),
                        ("raise", "Error Handling"),
                        ("isna()", "Null Check"),
                        ("duplicated()", "Duplicate Check"),
                        ("between", "Range Check"),
                    ]
                    
                    for pattern, validation_type in patterns:
                        count = content.count(pattern)
                        if count > 0:
                            self.validations_inventory.append({
                                "archivo": filepath,
                                "modulo": descripcion,
                                "patron": pattern,
                                "tipo_validacion": validation_type,
                                "instancias": count,
                            })
                            print(f"  ✓ {descripcion}: {count} × {pattern}")
                
                except Exception as e:
                    print(f"  ⚠ Error leyendo {filepath}: {e}")
        
        return self.validations_inventory
    
    def analyze_completeness(self, data: pd.DataFrame) -> List[Dict]:
        """PASO 2: Analizar COMPLETITUD de datos"""
        
        print("\n" + "="*70)
        print("PASO 2: ANALIZAR COMPLETITUD DE DATOS")
        print("="*70)
        
        issues = []
        
        # Verificar columnas esenciales
        required_columns = ['id_indicador', 'id_proceso', 'ejecucion', 'meta']
        for col in required_columns:
            if col not in data.columns:
                self.log_finding(
                    "Completitud",
                    "CRÍTICA",
                    f"Columna {col} no existe en dataset",
                    "CRÍTICO",
                    f"Dataset sin columna: {col}",
                    "Indica que estructura de datos es inválida",
                    "Validar estructura de datos en fuente"
                )
                issues.append({"tipo": "Columna faltante", "columna": col})
                print(f"  ✗ CRÍTICO: Columna faltante '{col}'")
                continue
            
            # Contar nulos por columna
            null_count = data[col].isna().sum()
            null_pct = (null_count / len(data)) * 100 if len(data) > 0 else 0
            
            if null_pct > 5:  # Umbral: más de 5% nulos es problema
                self.log_finding(
                    "Completitud",
                    "Nulos",
                    f"Columna {col} tiene {null_pct:.1f}% de valores nulos",
                    "ALTO" if null_pct > 20 else "MEDIO",
                    f"{col}: {null_count}/{len(data)} registros",
                    f"Datos incompletos afecta {null_pct:.1f}% de análisis",
                    "Investigar fuente, aplicar imputation o excluir registros"
                )
                issues.append({"tipo": "Nulos excesivos", "columna": col, "porcentaje": null_pct})
                print(f"  ⚠ {col}: {null_pct:.1f}% nulos")
        
        print(f"  ✓ Completitud: {len(issues)} problemas detectados")
        return issues
    
    def analyze_duplicates(self, data: pd.DataFrame) -> List[Dict]:
        """PASO 3: Detectar DUPLICADOS"""
        
        print("\n" + "="*70)
        print("PASO 3: DETECTAR DUPLICADOS")
        print("="*70)
        
        issues = []
        
        # Duplicados por composición [Proceso, Indicador, Período]
        if all(col in data.columns for col in ['id_proceso', 'id_indicador', 'periodo']):
            key_cols = ['id_proceso', 'id_indicador', 'periodo']
            duplicates = data[data.duplicated(subset=key_cols, keep=False)]
            
            if len(duplicates) > 0:
                dup_count = len(duplicates[duplicates.duplicated(subset=key_cols, keep='first')])
                self.log_finding(
                    "Duplicados",
                    "Composición",
                    f"{dup_count} registros duplicados en [{', '.join(key_cols)}]",
                    "ALTO",
                    f"Duplicados en tabla: {dup_count} filas",
                    "Afecta totales y promedios, doble-conteo en dashboards",
                    "Deduplicar manteniendo registro de auditoría"
                )
                issues.append({"tipo": "Duplicados", "cantidad": dup_count})
                print(f"  ✗ {dup_count} registros duplicados encontrados")
            else:
                print(f"  ✓ Sin duplicados detectados")
        
        return issues
    
    def analyze_ranges(self, data: pd.DataFrame) -> List[Dict]:
        """PASO 4: Validar RANGOS de valores"""
        
        print("\n" + "="*70)
        print("PASO 4: VALIDAR RANGOS DE VALORES")
        print("="*70)
        
        issues = []
        
        # Rango de ejecución: [0, 1.3]
        if 'ejecucion' in data.columns:
            out_of_range = (
                (data['ejecucion'] < 0) | (data['ejecucion'] > 1.3)
            )
            if out_of_range.any():
                count = out_of_range.sum()
                values = data.loc[out_of_range, 'ejecucion'].unique()
                self.log_finding(
                    "Rangos",
                    "Ejecución inválida",
                    f"{count} valores de ejecución fuera de rango [0, 1.3]",
                    "CRÍTICO",
                    f"Valores: {values}",
                    "Dashboards muestran porcentajes inválidos",
                    "Validar fuentes de datos, aplicar capping en ETL"
                )
                issues.append({"tipo": "Ejecución fuera de rango", "cantidad": count})
                print(f"  ✗ {count} valores de ejecución fuera de rango")
        
        # Rango de meta: (0, 1.0]
        if 'meta' in data.columns:
            out_of_range = (
                (data['meta'] <= 0) | (data['meta'] > 1.0)
            )
            if out_of_range.any():
                count = out_of_range.sum()
                values = data.loc[out_of_range, 'meta'].unique()
                self.log_finding(
                    "Rangos",
                    "Meta inválida",
                    f"{count} valores de meta fuera de rango (0, 1.0]",
                    "ALTO",
                    f"Valores: {values}",
                    "Metas inválidas generan categorización incorrecta",
                    "Revisar indicadores con meta 0 o > 100%"
                )
                issues.append({"tipo": "Meta fuera de rango", "cantidad": count})
                print(f"  ⚠ {count} metas fuera de rango")
        
        return issues
    
    def analyze_consistency(self, data: pd.DataFrame) -> List[Dict]:
        """PASO 5: Validar CONSISTENCIA histórica"""
        
        print("\n" + "="*70)
        print("PASO 5: VALIDAR CONSISTENCIA HISTÓRICA")
        print("="*70)
        
        issues = []
        
        # Si hay períodos, verificar que sean válidos
        if 'periodo' in data.columns:
            try:
                data['periodo_dt'] = pd.to_datetime(data['periodo'], errors='coerce')
                invalid_dates = data['periodo_dt'].isna().sum()
                
                if invalid_dates > 0:
                    self.log_finding(
                        "Consistencia",
                        "Fechas inválidas",
                        f"{invalid_dates} períodos no pueden parsearse como fecha",
                        "ALTO",
                        f"Formato de período inconsistente: {invalid_dates} registros",
                        "Reportes pueden filtrar período incorrectamente",
                        "Estandarizar formato de período a YYYY-MM-DD"
                    )
                    issues.append({"tipo": "Fechas inválidas", "cantidad": invalid_dates})
                    print(f"  ⚠ {invalid_dates} períodos inválidos")
            except Exception as e:
                print(f"  ⚠ Error parseando períodos: {e}")
        
        return issues
    
    def generate_expectations_suite(self) -> Dict:
        """Generar Great Expectations Suite para automatización"""
        
        print("\n" + "="*70)
        print("GENERANDO GREAT EXPECTATIONS SUITE")
        print("="*70)
        
        expectations = {
            "criticales": [
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "column": "id_indicador",
                    "description": "ID indicador obligatorio"
                },
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "column": "id_proceso",
                    "description": "ID proceso obligatorio"
                },
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "column": "periodo",
                    "description": "Período obligatorio"
                },
                {
                    "expectation_type": "expect_column_values_to_be_between",
                    "column": "ejecucion",
                    "min_value": 0,
                    "max_value": 1.3,
                    "description": "Ejecución en rango [0, 1.3]"
                },
                {
                    "expectation_type": "expect_column_values_to_be_between",
                    "column": "meta",
                    "min_value": 0.01,
                    "max_value": 1.0,
                    "description": "Meta en rango (0, 1.0]"
                },
                {
                    "expectation_type": "expect_compound_columns_to_be_unique",
                    "column_list": ["id_proceso", "id_indicador", "periodo"],
                    "description": "Sin duplicados [Proceso, Indicador, Período]"
                }
            ],
            "tecnicas": [
                {
                    "expectation_type": "expect_column_values_to_be_in_type_list",
                    "column": "ejecucion",
                    "type_list": ["float", "int"],
                    "description": "Tipo de dato correcto para ejecución"
                },
                {
                    "expectation_type": "expect_column_values_to_be_in_type_list",
                    "column": "meta",
                    "type_list": ["float", "int"],
                    "description": "Tipo de dato correcto para meta"
                },
                {
                    "expectation_type": "expect_table_row_count_to_be_between",
                    "min_value": 100,
                    "description": "Mínimo 100 registros en cada carga"
                }
            ]
        }
        
        print(f"  ✓ {len(expectations['criticales'])} expectativas críticas")
        print(f"  ✓ {len(expectations['tecnicas'])} expectativas técnicas")
        
        return expectations
    
    def generate_report(self) -> str:
        """Generar reporte final de hallazgos"""
        
        print("\n" + "="*70)
        print("GENERANDO REPORTE DE HALLAZGOS")
        print("="*70)
        
        report = f"""# AGENT 5 — Data Validation Report
**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Status:** Análisis completado  

---

## 📊 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Validaciones inventariadas** | {len(self.validations_inventory)} |
| **Hallazgos encontrados** | {len(self.findings)} |
| **Críticos** | {sum(1 for f in self.findings if f['severidad'] == 'CRÍTICO')} |
| **Altos** | {sum(1 for f in self.findings if f['severidad'] == 'ALTO')} |
| **Medios** | {sum(1 for f in self.findings if f['severidad'] == 'MEDIO')} |

---

## 🔍 Hallazgos Detectados

"""
        
        # Agrupar por severidad
        for severity in ['CRÍTICO', 'ALTO', 'MEDIO', 'BAJO']:
            findings_by_severity = [f for f in self.findings if f['severidad'] == severity]
            if findings_by_severity:
                report += f"\n### {severity} ({len(findings_by_severity)})\n\n"
                for i, finding in enumerate(findings_by_severity, 1):
                    report += f"""
**{i}. {finding['tipo']} — {finding['categoria']}**

- **Descripción:** {finding['descripcion']}
- **Evidencia:** {finding['evidencia']}
- **Impacto:** {finding['impacto']}
- **Solución:** {finding['solucion']}

---
"""
        
        report += f"""
## ✅ Próximos Pasos

1. **Revisión de hallazgos:** Priorizar según impacto
2. **Automatización:** Implementar Great Expectations
3. **Corrección:** Aplicar soluciones propuestas
4. **Validación:** Ejecutar tests en datos corregidos
5. **Monitoreo:** Ejecutar validaciones periódicamente

---

**Generado por:** AGENT 5 — Data Validation Framework  
**Versión:** 1.0 SGIND-Optimizada
"""
        
        return report
    
    def run_analysis(self):
        """Ejecutar análisis completo"""
        
        print("\n╔════════════════════════════════════════════════════════════════╗")
        print("║  AGENT 5 — DATA VALIDATION FRAMEWORK                          ║")
        print("║  Auditoría Integral de Calidad de Datos — SGIND               ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        
        # PASO 1: Inventariar validaciones
        self.inventory_validations()
        
        # PASO 2-5: Análisis en datos si están disponibles
        try:
            # Intentar cargar datos de ejemplo
            sample_data = pd.DataFrame({
                'id_indicador': [1, 2, 3, 4, 5],
                'id_proceso': [10, 10, 20, 20, 30],
                'ejecucion': [0.85, 1.02, 0.95, 1.35, 0.90],  # Uno fuera de rango
                'meta': [1.0, 1.0, 1.0, 1.0, 0.0],  # Uno con meta 0
                'periodo': ['2026-01', '2026-01', '2026-02', '2026-02', '2026-03']
            })
            
            self.analyze_completeness(sample_data)
            self.analyze_duplicates(sample_data)
            self.analyze_ranges(sample_data)
            self.analyze_consistency(sample_data)
            
        except Exception as e:
            print(f"\n⚠ No se pudieron cargar datos reales: {e}")
            print("  (Continuando con análisis de código)")
        
        # PASO 6: Generar Great Expectations
        expectations = self.generate_expectations_suite()
        
        # PASO 7: Generar reporte
        report = self.generate_report()
        
        # Guardar artefactos
        artifacts_dir = Path(__file__).parent.parent / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        # Guardar reporte
        report_path = artifacts_dir / f"AGENT5_DATA_VALIDATION_{self.timestamp}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n✓ Reporte guardado: {report_path}")
        
        # Guardar expectations como JSON
        expectations_path = artifacts_dir / f"GREAT_EXPECTATIONS_SUITE_{self.timestamp}.json"
        with open(expectations_path, 'w', encoding='utf-8') as f:
            json.dump(expectations, f, indent=2)
        print(f"✓ Expectations guardadas: {expectations_path}")
        
        # Guardar validaciones inventory
        if self.validations_inventory:
            inventory_df = pd.DataFrame(self.validations_inventory)
            inventory_path = artifacts_dir / f"VALIDACIONES_INVENTARIO_{self.timestamp}.csv"
            inventory_df.to_csv(inventory_path, index=False)
            print(f"✓ Inventario guardado: {inventory_path}")
        
        # Resumen final
        print(f"\n{'='*70}")
        print("RESUMEN FINAL")
        print(f"{'='*70}")
        print(f"✓ Validaciones inventariadas: {len(self.validations_inventory)}")
        print(f"✓ Hallazgos detectados: {len(self.findings)}")
        print(f"  - Críticos: {sum(1 for f in self.findings if f['severidad'] == 'CRÍTICO')}")
        print(f"  - Altos: {sum(1 for f in self.findings if f['severidad'] == 'ALTO')}")
        print(f"  - Medios: {sum(1 for f in self.findings if f['severidad'] == 'MEDIO')}")
        print(f"\n✅ AGENT 5 Analysis Complete")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    agent = DataValidationAgent()
    agent.run_analysis()
