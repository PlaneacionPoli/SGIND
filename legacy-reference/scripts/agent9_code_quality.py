"""
AGENT 9 — Code Quality & Refactoring Framework
Auditoría de código, refactorización y modularización

Ejecutar: python scripts/agent9_code_quality.py
"""

import os
import ast
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Set
import sys

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class CodeQualityAgent:
    """AGENT 9 — Especialista en calidad de código"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.findings = []
        self.functions = {}
        self.imports = defaultdict(set)
        self.duplicates = []
        
    def scan_python_files(self) -> List[Path]:
        """Encontrar todos los archivos Python"""
        patterns = ["core/**/*.py", "scripts/**/*.py", "services/**/*.py", "tests/**/*.py"]
        files = []
        for pattern in patterns:
            files.extend(self.root_path.glob(pattern))
        return sorted(set(files))
    
    def analyze_function_complexity(self, file_path: Path) -> List[Dict]:
        """Analizar complejidad ciclomática de funciones"""
        
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Contar condiciones
                    conditions = 0
                    for n in ast.walk(node):
                        if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                            conditions += 1
                    
                    # Contar líneas
                    line_count = node.end_lineno - node.lineno if node.lineno and node.end_lineno else 0
                    
                    # Registrar función
                    self.functions[node.name] = {
                        "file": str(file_path),
                        "lineno": node.lineno,
                        "conditions": conditions,
                        "lines": line_count,
                        "params": len(node.args.args),
                    }
                    
                    # Detectar problemas
                    if conditions > 10:
                        self.log_finding(
                            f"CAQ-CMP-{len(self.findings)+1}",
                            "ALTO",
                            "Complejidad Ciclomática",
                            str(file_path),
                            node.lineno,
                            node.name,
                            f"Complejidad: {conditions} (máximo recomendado: 10)",
                            "Función con excesivas ramificaciones",
                            "Refactorizar en funciones más pequeñas",
                            conditions / 10 * 3,  # horas estimadas
                        )
                    
                    if line_count > 100:
                        self.log_finding(
                            f"CAQ-LEN-{len(self.findings)+1}",
                            "MEDIO",
                            "Función Larga",
                            str(file_path),
                            node.lineno,
                            node.name,
                            f"Longitud: {line_count} líneas (máximo: 50)",
                            "Función demasiado larga, difícil de mantener",
                            "Dividir en funciones más pequeñas",
                            line_count / 50,
                        )
                    
                    if len(node.args.args) > 5:
                        self.log_finding(
                            f"CAQ-PAR-{len(self.findings)+1}",
                            "MEDIO",
                            "Muchos Parámetros",
                            str(file_path),
                            node.lineno,
                            node.name,
                            f"Parámetros: {len(node.args.args)} (máximo: 5)",
                            "Función con demasiados parámetros",
                            "Usar objetos o dataclasses para agrupar parámetros",
                            1,
                        )
        
        except Exception as e:
            print(f"⚠ Error analizando {file_path}: {e}")
        
        return issues
    
    def detect_duplicated_functions(self):
        """Detectar funciones con nombres similares (potencial duplicación)"""
        
        function_names = defaultdict(list)
        for fname, info in self.functions.items():
            # Buscar patrones similares
            base_name = fname.split('_')[0]
            function_names[base_name].append((fname, info))
        
        # Encontrar duplicados potenciales
        for base_name, functions in function_names.items():
            if len(functions) > 1:
                names = [f[0] for f in functions]
                if any(
                    n in ['categorizar_cumplimiento', 'calcular_cumplimiento', 
                          'compute_cumplimiento', '_categorizar'] 
                    for n in names
                ):
                    files = [f[1]['file'] for f in functions]
                    self.log_finding(
                        f"CAQ-DUP-{len(self.findings)+1}",
                        "CRÍTICO",
                        "Duplicación de Código",
                        ",".join(set(files)),
                        0,
                        f"Funciones: {', '.join(names)}",
                        f"Múltiples versiones de {base_name}*() en diferentes archivos",
                        "Inconsistencia en resultados, difícil de mantener",
                        "Centralizar en core/semantica.py, usar desde todos lados",
                        5,
                    )
    
    def analyze_imports(self):
        """Analizar estructura de imports para detectar acoplamiento"""
        
        try:
            for file_path in self.scan_python_files():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module:
                                self.imports[str(file_path)].add(node.module)
                
                except Exception as e:
                    pass  # Skip files that can't be parsed
        
        except Exception as e:
            print(f"⚠ Error analizando imports: {e}")
    
    def log_finding(self, finding_id: str, severity: str, finding_type: str,
                   location: str, lineno: int, symbol: str, description: str,
                   impact: str, solution: str, effort_hours: float):
        """Registrar un hallazgo"""
        self.findings.append({
            "id": finding_id,
            "severidad": severity,
            "tipo": finding_type,
            "ubicacion": location,
            "linea": lineno,
            "simbolo": symbol,
            "descripcion": description,
            "impacto": impact,
            "solucion": solution,
            "esfuerzo_horas": effort_hours,
            "timestamp": self.timestamp,
        })
    
    def generate_metrics_report(self) -> Dict:
        """Generar métricas de código"""
        
        total_files = len(self.scan_python_files())
        total_functions = len(self.functions)
        
        # Métricas por función
        avg_complexity = sum(f['conditions'] for f in self.functions.values()) / max(total_functions, 1)
        avg_length = sum(f['lines'] for f in self.functions.values()) / max(total_functions, 1)
        
        return {
            "total_files": total_files,
            "total_functions": total_functions,
            "avg_complexity": round(avg_complexity, 2),
            "avg_length": round(avg_length, 2),
            "functions_with_high_complexity": sum(1 for f in self.functions.values() if f['conditions'] > 10),
            "functions_too_long": sum(1 for f in self.functions.values() if f['lines'] > 100),
            "functions_too_many_params": sum(1 for f in self.functions.values() if f['params'] > 5),
        }
    
    def generate_report(self) -> str:
        """Generar reporte final"""
        
        report = f"""# AGENT 9 — Code Quality & Refactoring Report
**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Status:** Análisis completado  

---

## 📊 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Archivos Python** | {self.generate_metrics_report()['total_files']} |
| **Funciones encontradas** | {self.generate_metrics_report()['total_functions']} |
| **Hallazgos detectados** | {len(self.findings)} |
| **Críticos** | {sum(1 for f in self.findings if f['severidad'] == 'CRÍTICO')} |
| **Altos** | {sum(1 for f in self.findings if f['severidad'] == 'ALTO')} |
| **Medios** | {sum(1 for f in self.findings if f['severidad'] == 'MEDIO')} |

---

## 📈 Métricas de Código

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Complejidad promedio** | {self.generate_metrics_report()['avg_complexity']:.1f} | ⚠ |
| **Longitud promedio función** | {self.generate_metrics_report()['avg_length']:.0f} líneas | 🟡 |
| **Funciones complejas (>10)** | {self.generate_metrics_report()['functions_with_high_complexity']} | |
| **Funciones largas (>100)** | {self.generate_metrics_report()['functions_too_long']} | |
| **Funciones muchos parámetros** | {self.generate_metrics_report()['functions_too_many_params']} | |

---

## 🔍 Hallazgos Detectados

"""
        
        # Agrupar por severidad
        for severity in ['CRÍTICO', 'ALTO', 'MEDIO', 'BAJO']:
            findings_by_severity = [f for f in self.findings if f['severidad'] == severity]
            if findings_by_severity:
                report += f"\n### {severity} ({len(findings_by_severity)})\n\n"
                for finding in findings_by_severity:
                    report += f"""**{finding['id']} — {finding['tipo']}**

- **Ubicación:** {finding['ubicacion']}:{finding['linea']}
- **Símbolo:** `{finding['simbolo']}`
- **Descripción:** {finding['descripcion']}
- **Impacto:** {finding['impacto']}
- **Solución:** {finding['solucion']}
- **Esfuerzo:** {finding['esfuerzo_horas']:.1f} horas

---
"""
        
        report += """
## ✅ Próximos Pasos

1. **Revisar hallazgos CRÍTICOS:** Duplicación (centralizar)
2. **Refactorizar funciones complejas:** Dividir en funciones menores
3. **Centralizar configuración:** Mover umbrales a core/config.py
4. **Mejorar tests:** Aumentar cobertura de funciones auditadas
5. **Modularizar:** Separar responsabilidades entre módulos

---

**Generado por:** AGENT 9 — Code Quality & Refactoring Framework  
**Versión:** 1.0 SGIND-Optimizada
"""
        
        return report
    
    def run_analysis(self):
        """Ejecutar análisis completo"""
        
        print("\n╔════════════════════════════════════════════════════════════════╗")
        print("║  AGENT 9 — CODE QUALITY & REFACTORING FRAMEWORK               ║")
        print("║  Auditoría Integral de Calidad de Código — SGIND              ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        
        # PASO 1: Inventariar archivos
        print("\n" + "="*70)
        print("PASO 1: INVENTARIAR ARCHIVOS PYTHON")
        print("="*70)
        
        files = self.scan_python_files()
        print(f"  ✓ {len(files)} archivos Python encontrados")
        
        # PASO 2: Analizar complejidad
        print("\n" + "="*70)
        print("PASO 2: ANALIZAR COMPLEJIDAD Y LONGITUD")
        print("="*70)
        
        for file_path in files:
            self.analyze_function_complexity(file_path)
        
        print(f"  ✓ {len(self.functions)} funciones analizadas")
        
        # PASO 3: Detectar duplicación
        print("\n" + "="*70)
        print("PASO 3: DETECTAR DUPLICACIÓN")
        print("="*70)
        
        self.detect_duplicated_functions()
        print(f"  ✓ Análisis de duplicación completado")
        
        # PASO 4: Analizar imports
        print("\n" + "="*70)
        print("PASO 4: ANALIZAR IMPORTS Y ACOPLAMIENTO")
        print("="*70)
        
        self.analyze_imports()
        print(f"  ✓ {len(self.imports)} archivos con imports analizados")
        
        # PASO 5: Generar reporte
        print("\n" + "="*70)
        print("GENERANDO REPORTES")
        print("="*70)
        
        report = self.generate_report()
        metrics = self.generate_metrics_report()
        
        # Guardar artefactos
        artifacts_dir = self.root_path / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        # Guardar reporte
        report_path = artifacts_dir / f"AGENT9_CODE_QUALITY_{self.timestamp}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✓ Reporte guardado: {report_path}")
        
        # Guardar métricas
        metrics_path = artifacts_dir / f"CODE_METRICS_{self.timestamp}.json"
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metrics": metrics,
                "functions": self.functions,
                "findings": self.findings,
            }, f, indent=2, default=str)
        print(f"✓ Métricas guardadas: {metrics_path}")
        
        # Resumen final
        print(f"\n{'='*70}")
        print("RESUMEN FINAL")
        print(f"{'='*70}")
        print(f"✓ Archivos analizados: {metrics['total_files']}")
        print(f"✓ Funciones encontradas: {metrics['total_functions']}")
        print(f"✓ Hallazgos detectados: {len(self.findings)}")
        print(f"  - Críticos: {sum(1 for f in self.findings if f['severidad'] == 'CRÍTICO')}")
        print(f"  - Altos: {sum(1 for f in self.findings if f['severidad'] == 'ALTO')}")
        print(f"  - Medios: {sum(1 for f in self.findings if f['severidad'] == 'MEDIO')}")
        print(f"\n✅ AGENT 9 Analysis Complete")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    agent = CodeQualityAgent()
    agent.run_analysis()
