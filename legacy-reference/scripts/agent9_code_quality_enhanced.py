"""
AGENT 9 ENHANCED — Code Quality & Architecture Audit Framework
Auditoría integral: Higiene + Clean Architecture + DDD + SOLID

Ejecutar: python scripts/agent9_code_quality_enhanced.py
"""

import os
import ast
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Set, Tuple
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class CodeQualityEnhanced:
    """AGENT 9 ENHANCED — Auditoría integral de código"""

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.findings = []
        self.functions = {}
        self.imports = defaultdict(set)
        self.all_defined_symbols = set()
        self.all_used_symbols = set()
        self.files_scanned = []
        self.architecture_violations = []
        self.solid_violations = []

    def scan_python_files(self) -> List[Path]:
        """Encontrar todos los archivos Python excluidas temporales"""
        patterns = ["core/**/*.py", "scripts/**/*.py", "services/**/*.py", "tests/**/*.py", "*.py"]
        files = []
        for pattern in patterns:
            files.extend(self.root_path.glob(pattern))

        # Excluir temporales y tests de AGENT 9
        files = [
            f
            for f in files
            if not any(
                x in f.name
                for x in [
                    "__tmp_",
                    "_tmp_",
                    "tmp_",
                    "fix_",
                    "agent9_code_quality.py",
                ]
            )
        ]

        return sorted(set(files))

    def extract_all_symbols(self, files: List[Path]) -> None:
        """Extraer todos los símbolos definidos y usados"""
        logger.info("\n📋 Extrayendo símbolos definidos y usados...")

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    # Símbolos definidos
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        self.all_defined_symbols.add(node.name)

                    # Símbolos usados (Name nodes)
                    if isinstance(node, ast.Name):
                        self.all_used_symbols.add(node.id)
            except:
                pass

    def detect_dead_code(self, files: List[Path]) -> None:
        """Detectar archivos huérfanos, funciones no usadas, tests inactivos"""
        logger.info("\n📋 Detectando dead code...")

        # 1. Tests inactivos (skip markers)
        for file_path in [f for f in files if "test" in f.name]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        # Detectar decoradores de skip
                        for decorator in node.decorator_list:
                            dec_name = ""
                            if isinstance(decorator, ast.Name):
                                dec_name = decorator.id
                            elif isinstance(decorator, ast.Attribute):
                                dec_name = decorator.attr
                            elif isinstance(decorator, ast.Call):
                                if isinstance(decorator.func, ast.Name):
                                    dec_name = decorator.func.id
                                elif isinstance(decorator.func, ast.Attribute):
                                    dec_name = decorator.func.attr

                            if dec_name in ["skip", "skipif", "xfail"]:
                                self.log_finding(
                                    f"CAQ-DEAD-{len(self.findings)+1}",
                                    "MEDIO",
                                    "Test Inactivo",
                                    str(file_path),
                                    node.lineno,
                                    node.name,
                                    f"Test con decorador @{dec_name}",
                                    "Test no está siendo ejecutado",
                                    "Remover o activar test",
                                    1,
                                )
            except:
                pass

        # 2. Archivos temporales no documentados
        for file_path in files:
            if any(x in file_path.name for x in ["_tmp_", "tmp_", "__tmp_"]):
                self.log_finding(
                    f"CAQ-DEAD-{len(self.findings)+1}",
                    "BAJO",
                    "Archivo Temporal",
                    str(file_path),
                    0,
                    file_path.name,
                    f"Archivo con patrón temporal en nombre",
                    "Potencial código descartado",
                    "Eliminar o documentar propósito",
                    0.5,
                )

        # 3. Archivos con fix_ o fix patterns (reparaciones adhoc)
        for file_path in files:
            if any(x in file_path.name for x in ["fix_", "test_fix_", "debug_"]):
                self.log_finding(
                    f"CAQ-DEAD-{len(self.findings)+1}",
                    "MEDIO",
                    "Archivo Ad-Hoc",
                    str(file_path),
                    0,
                    file_path.name,
                    f"Archivo que parece reparación puntual",
                    "Código no integrado en pipeline",
                    "Integrar a codebase o eliminar",
                    2,
                )

    def validate_clean_architecture(self, files: List[Path]) -> None:
        """Validar separación Clean Architecture"""
        logger.info("\n📋 Validando Clean Architecture...")

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content)

                # Categorizar archivo
                if "streamlit_app" in str(file_path):
                    layer = "presentation"
                elif "scripts" in str(file_path) and "etl" in str(file_path):
                    layer = "application"
                elif "core" in str(file_path) and "domain" in str(file_path):
                    layer = "domain"
                elif "services" in str(file_path):
                    layer = "application"
                elif "core" in str(file_path):
                    layer = "infrastructure"
                else:
                    layer = "unknown"

                # Analizar imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        module = node.module or ""

                        # Validación: Presentación no debe importar de domain
                        if layer == "presentation" and "core" in module and "domain" in module:
                            self.architecture_violations.append(
                                {
                                    "file": str(file_path),
                                    "layer": layer,
                                    "violation": f"Presentation imports domain directly: {module}",
                                    "severity": "ALTO",
                                }
                            )
                            self.log_finding(
                                f"CAQ-ARCH-{len(self.findings)+1}",
                                "ALTO",
                                "Clean Architecture Violation",
                                str(file_path),
                                node.lineno,
                                module,
                                f"Capa Presentación importa directamente de Domain",
                                "Violación de Clean Architecture",
                                "Usar Application layer como intermediaria",
                                4,
                            )

                        # Validación: Domain no debe importar de externos pesados
                        if layer == "domain" and any(
                            x in module for x in ["pandas", "sqlalchemy", "requests", "streamlit"]
                        ):
                            self.architecture_violations.append(
                                {
                                    "file": str(file_path),
                                    "layer": layer,
                                    "violation": f"Domain imports external: {module}",
                                    "severity": "CRÍTICO",
                                }
                            )
                            self.log_finding(
                                f"CAQ-ARCH-{len(self.findings)+1}",
                                "CRÍTICO",
                                "Domain Contamination",
                                str(file_path),
                                node.lineno,
                                module,
                                f"Domain layer importa librería externa: {module}",
                                "Domain debe ser puro, sin dependencias",
                                "Mover lógica a Infrastructure layer",
                                3,
                            )
            except:
                pass

    def validate_ddd(self, files: List[Path]) -> None:
        """Validar Domain-Driven Design modeling"""
        logger.info("\n📋 Validando Domain-Driven Design...")

        # Buscar definiciones de clases clave
        entities = []
        value_objects = []
        aggregates = []

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        docstring = ast.get_docstring(node) or ""

                        # Detectar por convención de nombres o docstrings
                        if "Entity" in class_name or "entity" in docstring.lower():
                            entities.append(class_name)
                        elif "ValueObject" in class_name or "value object" in docstring.lower():
                            value_objects.append(class_name)
                        elif "Aggregate" in class_name or "aggregate" in docstring.lower():
                            aggregates.append(class_name)

                        # Validar Value Objects son immutables
                        if "ValueObject" in class_name or "value_object" in class_name.lower():
                            has_setattr = any(
                                isinstance(m, ast.FunctionDef) and m.name == "__setattr__"
                                for m in node.body
                            )
                            if not has_setattr:
                                # Revisar si hay __slots__
                                has_slots = any(
                                    isinstance(m, ast.Assign) and any(
                                        isinstance(t, ast.Name) and t.id == "__slots__" for t in m.targets
                                    )
                                    for m in node.body
                                )

                                if not has_slots:
                                    self.log_finding(
                                        f"CAQ-DDD-{len(self.findings)+1}",
                                        "MEDIO",
                                        "Value Object no Immutable",
                                        str(file_path),
                                        node.lineno,
                                        class_name,
                                        f"Value Object {class_name} no implementa inmutabilidad",
                                        "Value Objects deben ser immutables",
                                        "Implementar @frozen o __slots__ + __setattr__",
                                        2,
                                    )
            except:
                pass

        # Validaciones DDD
        if not aggregates:
            self.log_finding(
                f"CAQ-DDD-{len(self.findings)+1}",
                "MEDIO",
                "No Aggregate Roots Detected",
                "core/domain/",
                0,
                "models",
                "No se detectaron agregados raíz definidos",
                "DDD requiere agregados claros",
                "Definir Indicador, Proceso como agregados raíz",
                4,
            )

        if not value_objects:
            self.log_finding(
                f"CAQ-DDD-{len(self.findings)+1}",
                "MEDIO",
                "No Value Objects Detected",
                "core/domain/",
                0,
                "models",
                "No se detectaron value objects",
                "DDD recomienda value objects",
                "Modelar Fórmula, MetaCumplimiento como value objects",
                3,
            )

    def validate_solid(self, files: List[Path]) -> None:
        """Validar principios SOLID"""
        logger.info("\n📋 Validando SOLID principles...")

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        method_count = len([m for m in node.body if isinstance(m, ast.FunctionDef)])
                        lines = node.end_lineno - node.lineno if node.lineno and node.end_lineno else 0

                        # S — Single Responsibility: ¿Clase < 200 líneas y < 8 métodos?
                        if lines > 200:
                            self.log_finding(
                                f"CAQ-SOLID-{len(self.findings)+1}",
                                "ALTO",
                                "SRP Violation (Class Too Long)",
                                str(file_path),
                                node.lineno,
                                class_name,
                                f"Clase {lines} líneas (máximo: 200)",
                                "Probablemente multiple responsabilidades",
                                "Dividir en clases más pequeñas",
                                lines / 200 * 4,
                            )

                        if method_count > 8:
                            self.log_finding(
                                f"CAQ-SOLID-{len(self.findings)+1}",
                                "MEDIO",
                                "SRP Violation (Too Many Methods)",
                                str(file_path),
                                node.lineno,
                                class_name,
                                f"Clase con {method_count} métodos (máximo: 8)",
                                "Probablemente multiple responsabilidades",
                                "Dividir en clases especializadas",
                                method_count / 8 * 2,
                            )

                        # D — Dependency Inversion: ¿Directa instantiación de depencias?
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef) and method.name == "__init__":
                                for n in ast.walk(method):
                                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                                        # Detectar new obj() sin inyección
                                        if n.func.id in ["DatabaseManager", "APIClient", "FileLoader"]:
                                            self.log_finding(
                                                f"CAQ-SOLID-{len(self.findings)+1}",
                                                "ALTO",
                                                "DIP Violation (Direct Instantiation)",
                                                str(file_path),
                                                method.lineno,
                                                f"{class_name}.__init__",
                                                f"Instancia directa de {n.func.id}",
                                                "Violación de Dependency Inversion",
                                                "Inyectar como parámetro de constructor",
                                                2,
                                            )

            except:
                pass

    def analyze_function_complexity(self, file_path: Path) -> None:
        """Analizar complejidad ciclomática"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    conditions = sum(1 for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While)))
                    line_count = node.end_lineno - node.lineno if node.lineno and node.end_lineno else 0
                    params = len(node.args.args)

                    self.functions[node.name] = {
                        "file": str(file_path),
                        "lineno": node.lineno,
                        "conditions": conditions,
                        "lines": line_count,
                        "params": params,
                    }

                    if conditions > 10:
                        self.log_finding(
                            f"CAQ-CMP-{len(self.findings)+1}",
                            "ALTO",
                            "Complejidad Ciclomática Alta",
                            str(file_path),
                            node.lineno,
                            node.name,
                            f"Complejidad: {conditions} (máx: 10)",
                            "Función con excesivas ramificaciones",
                            "Refactorizar en funciones más pequeñas",
                            conditions / 10 * 3,
                        )

                    if line_count > 100:
                        self.log_finding(
                            f"CAQ-LEN-{len(self.findings)+1}",
                            "MEDIO",
                            "Función Muy Larga",
                            str(file_path),
                            node.lineno,
                            node.name,
                            f"Longitud: {line_count} líneas (máx: 50)",
                            "Difícil de mantener y testear",
                            "Dividir en funciones más pequeñas",
                            line_count / 50,
                        )

                    if params > 5:
                        self.log_finding(
                            f"CAQ-PAR-{len(self.findings)+1}",
                            "MEDIO",
                            "Demasiados Parámetros",
                            str(file_path),
                            node.lineno,
                            node.name,
                            f"Parámetros: {params} (máx: 5)",
                            "Función difícil de usar",
                            "Agrupar parámetros en objeto",
                            1,
                        )

        except:
            pass

    def log_finding(
        self, id_, severity, tipo, ubicacion, linea, simbolo, descripcion, impacto, solucion, horas
    ) -> None:
        """Registrar hallazgo"""
        self.findings.append(
            {
                "id": id_,
                "severidad": severity,
                "tipo": tipo,
                "ubicacion": ubicacion,
                "linea": linea,
                "simbolo": simbolo,
                "descripcion": descripcion,
                "impacto": impacto,
                "solucion": solucion,
                "esfuerzo_horas": horas,
            }
        )

    def generate_metrics(self) -> Dict:
        """Calcular métricas finales"""
        return {
            "total_files": len(self.files_scanned),
            "total_functions": len(self.functions),
            "total_findings": len(self.findings),
            "critical": sum(1 for f in self.findings if f["severidad"] == "CRÍTICO"),
            "high": sum(1 for f in self.findings if f["severidad"] == "ALTO"),
            "medium": sum(1 for f in self.findings if f["severidad"] == "MEDIO"),
            "low": sum(1 for f in self.findings if f["severidad"] == "BAJO"),
            "total_remediation_hours": sum(f["esfuerzo_horas"] for f in self.findings),
        }

    def export_markdown(self) -> str:
        """Exportar reporte Markdown"""
        metrics = self.generate_metrics()

        report = f"""# AGENT 9 ENHANCED — Code Quality & Architecture Audit

**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Status:** Análisis completo  

---

## 📊 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Archivos Analizados** | {metrics['total_files']} |
| **Funciones Evaluadas** | {metrics['total_functions']} |
| **Hallazgos Totales** | {metrics['total_findings']} |
| **Críticos** | {metrics['critical']} 🔴 |
| **Altos** | {metrics['high']} 🟠 |
| **Medios** | {metrics['medium']} 🟡 |
| **Bajos** | {metrics['low']} 🟢 |
| **Horas Remediación** | {metrics['total_remediation_hours']:.0f}h |

---

## 🔍 Hallazgos por Categoría

"""

        for category in ["CRÍTICO", "ALTO", "MEDIO", "BAJO"]:
            cat_findings = [f for f in self.findings if f["severidad"] == category]
            if cat_findings:
                report += f"\n### {category} ({len(cat_findings)})\n\n"
                for f in cat_findings:
                    report += f"""**{f['id']} — {f['tipo']}**
- Ubicación: {f['ubicacion']}:{f['linea']}
- Problema: {f['descripcion']}
- Impacto: {f['impacto']}
- Solución: {f['solucion']}
- Esfuerzo: {f['esfuerzo_horas']:.1f}h

"""

        report += """
---

## ✅ Próximos Pasos

1. **Resolver CRÍTICOS:** DD-001, DD-011 primero
2. **Validar arquitectura:** Clean Architecture + DDD
3. **Implementar SOLID:** Inyección de dependencias
4. **Eliminar dead code:** Tests inactivos, archivos temporales
5. **Refactorizar:** Funciones complejas, clases grandes

---

**Generado por:** AGENT 9 ENHANCED — Code Quality & Architecture Audit
"""

        return report

    def run_full_audit(self):
        """Ejecutar auditoría completa"""
        logger.info("=" * 70)
        logger.info("AGENT 9 ENHANCED — Code Quality & Architecture Audit")
        logger.info("=" * 70)

        # Scan files
        files = self.scan_python_files()
        self.files_scanned = files
        logger.info(f"\n✅ {len(files)} archivos Python encontrados")

        # Extract symbols
        self.extract_all_symbols(files)

        # Dead code detection
        self.detect_dead_code(files)

        # Architecture validation
        self.validate_clean_architecture(files)

        # DDD validation
        self.validate_ddd(files)

        # SOLID validation
        self.validate_solid(files)

        # Function analysis
        for file_path in files:
            self.analyze_function_complexity(file_path)

        # Generate reports
        metrics = self.generate_metrics()
        logger.info(f"\n✅ Auditoría completada")
        logger.info(f"   Hallazgos: {metrics['total_findings']}")
        logger.info(f"   Horas remediación: {metrics['total_remediation_hours']:.0f}h")

        # Export artifacts
        artifacts_dir = self.root_path / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)

        # Markdown report
        report_path = artifacts_dir / f"AGENT9_ENHANCED_AUDIT_{self.timestamp}.md"
        report_path.write_text(self.export_markdown(), encoding="utf-8")
        logger.info(f"   ✅ Reporte: {report_path.name}")

        # Metrics JSON
        metrics_path = artifacts_dir / f"AGENT9_METRICS_{self.timestamp}.json"
        metrics_path.write_text(
            json.dumps(
                {
                    "metrics": metrics,
                    "findings": self.findings,
                    "architecture_violations": self.architecture_violations,
                    "solid_violations": self.solid_violations,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        logger.info(f"   ✅ Métricas: {metrics_path.name}")

        # Cleanup suggestions
        cleanup_path = artifacts_dir / f"CLEANUP_PLAN_{self.timestamp}.md"
        cleanup_content = self._generate_cleanup_plan()
        cleanup_path.write_text(cleanup_content, encoding="utf-8")
        logger.info(f"   ✅ Plan limpieza: {cleanup_path.name}")

        return {"metrics": metrics, "findings": self.findings}

    def _generate_cleanup_plan(self) -> str:
        """Generar plan de limpieza"""
        dead_findings = [f for f in self.findings if "Dead" in f["tipo"] or "Temporal" in f["tipo"]]

        plan = "# Cleanup Plan — Dead Code Elimination\n\n"

        if dead_findings:
            plan += "## Files to Eliminate\n\n"
            for f in dead_findings:
                plan += f"- [ ] {f['ubicacion']} — {f['descripcion']}\n"

        return plan


if __name__ == "__main__":
    agent = CodeQualityEnhanced()
    results = agent.run_full_audit()
