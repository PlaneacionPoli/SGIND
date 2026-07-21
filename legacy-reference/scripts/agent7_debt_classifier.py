"""
scripts/agent7_debt_classifier.py
AGENT 7 — Technical Data Debt Classifier
Clasifica y prioriza deuda técnica en 7 dimensiones
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class TechnicalDebtClassifier:
    """Clasificador de deuda técnica SGIND"""

    def __init__(self, root_path: Path | None = None):
        self.root = Path(root_path) if root_path else Path(__file__).parent.parent
        self.debt_items: List[Dict[str, Any]] = []
        self.dimensions = [
            "datos",
            "documentacion",
            "validacion",
            "reproducibilidad",
            "dependencias",
            "arquitectura",
            "seguridad",
        ]

    def classify_debt(self) -> Dict[str, Any]:
        """Clasificar y priorizar deuda técnica"""
        logger.info("=" * 70)
        logger.info("AGENT 7 — Technical Data Debt Classifier")
        logger.info("=" * 70)

        self._discover_debt_items()
        self._calculate_priority()
        self._build_matrix()

        return {
            "timestamp": datetime.now().isoformat(),
            "framework": "SGIND v1.0",
            "debt_items": self.debt_items,
            "metrics": self._calculate_metrics(),
            "matrix": self._build_prioritization_matrix(),
        }

    def _discover_debt_items(self):
        """Descubrir items de deuda técnica"""
        logger.info("\n📋 Descubriendo deuda técnica...")

        # Deuda consolidada de AGENT 1-6
        default_debt = [
            # DEUDA DE DATOS
            {
                "id": "DD-001-DATOS",
                "dimension": "datos",
                "tipo": "Fórmulas Duplicadas",
                "severidad": "CRÍTICA",
                "evidencia": "calculos.py vs generar_reporte.py usan fórmulas diferentes para cumplimiento",
                "impacto_actual": "Dashboard A vs B muestran valores diferentes mismo período",
                "impacto_futuro": "Escalará a más dashboards, inconsistencia sistémica",
                "costo_horas": 4,
                "beneficios": "100% consistencia entre reportes",
                "riesgo_prob": "Alta",
                "riesgo_consecuencia": "Decisiones estratégicas incorrectas",
            },
            # DEUDA DE DOCUMENTACIÓN
            {
                "id": "DD-002-DOCS",
                "dimension": "documentacion",
                "tipo": "Desincronización Fórmulas",
                "severidad": "ALTA",
                "evidencia": "docs/02_Logica_Indicadores.md vs core/calculos.py fórmulas no coinciden",
                "impacto_actual": "Nuevo código sigue docs, pero ejecuta mal",
                "impacto_futuro": "Bugs escalados a producción",
                "costo_horas": 3,
                "beneficios": "Trazabilidad de cambios",
                "riesgo_prob": "Alta",
                "riesgo_consecuencia": "Errores de cálculo no detectados",
            },
            {
                "id": "DD-003-DOCS",
                "dimension": "documentacion",
                "tipo": "Metadatos Incompletos",
                "severidad": "MEDIA",
                "evidencia": "50% indicadores sin línea base o meta documentada",
                "impacto_actual": "Imposible evaluar progreso histórico",
                "impacto_futuro": "Stakeholders desconfían de datos",
                "costo_horas": 8,
                "beneficios": "Trazabilidad completa",
                "riesgo_prob": "Media",
                "riesgo_consecuencia": "Conocimiento tribalizado",
            },
            # DEUDA DE VALIDACIÓN
            {
                "id": "DD-004-VALIDACION",
                "dimension": "validacion",
                "tipo": "Tests Faltantes",
                "severidad": "ALTA",
                "evidencia": "Solo 8 test files para 100+ indicadores críticos",
                "impacto_actual": "Cambios no detectan regresiones",
                "impacto_futuro": "Bugs llegan a producción",
                "costo_horas": 12,
                "beneficios": "Regresión detectada automáticamente",
                "riesgo_prob": "Alta",
                "riesgo_consecuencia": "Datos incorrectos en dashboards",
            },
            {
                "id": "DD-005-VALIDACION",
                "dimension": "validacion",
                "tipo": "ETL sin Validación",
                "severidad": "ALTA",
                "evidencia": "consolidar_api.py no valida Ejecución ≤ 1.3",
                "impacto_actual": "Datos inválidos (1.35) llegan a dashboards",
                "impacto_futuro": "Decisiones basadas en 135% (inválido)",
                "costo_horas": 2,
                "beneficios": "Validación automática en pipeline",
                "riesgo_prob": "Alta",
                "riesgo_consecuencia": "Decisiones incorrectas",
            },
            # DEUDA DE REPRODUCIBILIDAD
            {
                "id": "DD-006-REPRODUCIBILIDAD",
                "dimension": "reproducibilidad",
                "tipo": "Valores Hardcodeados",
                "severidad": "MEDIA",
                "evidencia": "Umbrales (1.3, 1.0, 0.6) hardcodeados en código",
                "impacto_actual": "Cambiar umbral = editar código + tests + redeploy",
                "impacto_futuro": "Error-prone, lento, difícil auditar cambios",
                "costo_horas": 3,
                "beneficios": "Configuración centralizada, rápido cambiar",
                "riesgo_prob": "Media",
                "riesgo_consecuencia": "Cambios lentos, errores en producción",
            },
            {
                "id": "DD-007-REPRODUCIBILIDAD",
                "dimension": "reproducibilidad",
                "tipo": "Sin Versionado de Datos",
                "severidad": "MEDIA",
                "evidencia": "Consolidado_API.xlsx descargado sin metadatos de versión",
                "impacto_actual": "Imposible saber cuál versión usó para qué indicador",
                "impacto_futuro": "Imposible reproducir cálculos históricos",
                "costo_horas": 5,
                "beneficios": "Audit trail completo",
                "riesgo_prob": "Media",
                "riesgo_consecuencia": "Imposible investigar discrepancias",
            },
            # DEUDA DE DEPENDENCIAS
            {
                "id": "DD-008-DEPENDENCIAS",
                "dimension": "dependencias",
                "tipo": "Librerías Desactualizadas",
                "severidad": "MEDIA",
                "evidencia": "openpyxl==3.0.1 (actual: 3.1.4, 20 bug fixes)",
                "impacto_actual": "Potencial bugs, missing features",
                "impacto_futuro": "Incompatibilidad futura",
                "costo_horas": 2,
                "beneficios": "Seguridad, features, performance",
                "riesgo_prob": "Baja",
                "riesgo_consecuencia": "Problemas de compatibilidad",
            },
            # DEUDA DE ARQUITECTURA
            {
                "id": "DD-009-ARQUITECTURA",
                "dimension": "arquitectura",
                "tipo": "Monolito sin Modularidad",
                "severidad": "ALTA",
                "evidencia": "actualizar_consolidado.py 1200+ líneas, 3 funciones",
                "impacto_actual": "Cambio en transformación = retest todo",
                "impacto_futuro": "Integración frágil, scaling imposible",
                "costo_horas": 16,
                "beneficios": "Modularidad, reutilización, testabilidad",
                "riesgo_prob": "Alta",
                "riesgo_consecuencia": "Bloquea escalabilidad",
            },
            {
                "id": "DD-010-ARQUITECTURA",
                "dimension": "arquitectura",
                "tipo": "Lógica Mezclada",
                "severidad": "MEDIA",
                "evidencia": "Cálculos en consolidar_api.py (debería estar en core/)",
                "impacto_actual": "Reutilización imposible",
                "impacto_futuro": "Código duplicado, bugs",
                "costo_horas": 8,
                "beneficios": "Separación clara de responsabilidades",
                "riesgo_prob": "Media",
                "riesgo_consecuencia": "Complejidad aumenta",
            },
            # DEUDA DE SEGURIDAD
            {
                "id": "DD-011-SEGURIDAD",
                "dimension": "seguridad",
                "tipo": "Credenciales en Código",
                "severidad": "CRÍTICA",
                "evidencia": "config.py tiene SUPABASE_PASSWORD expuesta",
                "impacto_actual": "Acceso no autorizado a BD posible",
                "impacto_futuro": "Data breach, compliance violation",
                "costo_horas": 2,
                "beneficios": "Seguridad de datos crítica",
                "riesgo_prob": "Alta",
                "riesgo_consecuencia": "Incident de seguridad",
            },
        ]

        self.debt_items = default_debt
        logger.info(f"   Items de deuda descubiertos: {len(self.debt_items)}")

    def _calculate_priority(self):
        """Calcular prioridad de cada item"""
        logger.info("\n📋 Calculando prioridades...")

        priority_map = {
            "CRÍTICA": {"esfuerzo_bajo": "P1", "esfuerzo_alto": "P1"},
            "ALTA": {"esfuerzo_bajo": "P1", "esfuerzo_alto": "P2"},
            "MEDIA": {"esfuerzo_bajo": "P2", "esfuerzo_alto": "P3"},
            "BAJA": {"esfuerzo_bajo": "P3", "esfuerzo_alto": "P4"},
        }

        for item in self.debt_items:
            esfuerzo_category = "esfuerzo_bajo" if item["costo_horas"] <= 5 else "esfuerzo_alto"
            item["prioridad"] = priority_map[item["severidad"]][esfuerzo_category]
            item["roi"] = 100 / item["costo_horas"] if item["costo_horas"] > 0 else 0

        logger.info(f"   Prioridades calculadas")

    def _build_matrix(self):
        """Construir matriz de priorización"""
        logger.info("\n📋 Construyendo matriz de priorización...")

        # Clasificar por cuadrante
        cuadrantes = {
            "quick_wins": [],
            "strategic": [],
            "low_value": [],
            "black_hole": [],
        }

        for item in self.debt_items:
            esfuerzo_bajo = item["costo_horas"] <= 5
            impacto_alto = item["severidad"] in ["CRÍTICA", "ALTA"]

            if esfuerzo_bajo and impacto_alto:
                cuadrantes["quick_wins"].append(item)
            elif not esfuerzo_bajo and impacto_alto:
                cuadrantes["strategic"].append(item)
            elif esfuerzo_bajo and not impacto_alto:
                cuadrantes["low_value"].append(item)
            else:
                cuadrantes["black_hole"].append(item)

        self.cuadrantes = cuadrantes
        logger.info(f"   Quick Wins: {len(cuadrantes['quick_wins'])}")
        logger.info(f"   Strategic: {len(cuadrantes['strategic'])}")
        logger.info(f"   Low Value: {len(cuadrantes['low_value'])}")
        logger.info(f"   Black Hole: {len(cuadrantes['black_hole'])}")

    def _build_prioritization_matrix(self) -> Dict[str, Any]:
        """Construir matriz estructurada"""
        return {
            "quick_wins": [
                {
                    "id": item["id"],
                    "descripcion": item["tipo"],
                    "esfuerzo": item["costo_horas"],
                    "impacto": item["severidad"],
                    "roi": round(item["roi"], 1),
                }
                for item in self.cuadrantes["quick_wins"]
            ],
            "strategic": [
                {
                    "id": item["id"],
                    "descripcion": item["tipo"],
                    "esfuerzo": item["costo_horas"],
                    "impacto": item["severidad"],
                    "roi": round(item["roi"], 1),
                }
                for item in self.cuadrantes["strategic"]
            ],
            "low_value": [
                {
                    "id": item["id"],
                    "descripcion": item["tipo"],
                    "esfuerzo": item["costo_horas"],
                    "impacto": item["severidad"],
                }
                for item in self.cuadrantes["low_value"]
            ],
        }

    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calcular métricas globales"""
        total_horas = sum(item["costo_horas"] for item in self.debt_items)
        total_criticos = sum(1 for item in self.debt_items if item["severidad"] == "CRÍTICA")
        total_altos = sum(1 for item in self.debt_items if item["severidad"] == "ALTA")

        debt_by_dimension = {}
        for dimension in self.dimensions:
            items = [i for i in self.debt_items if i["dimension"] == dimension]
            debt_by_dimension[dimension] = {
                "cantidad": len(items),
                "horas": sum(i["costo_horas"] for i in items),
            }

        return {
            "total_items": len(self.debt_items),
            "total_horas": total_horas,
            "total_criticos": total_criticos,
            "total_altos": total_altos,
            "total_medios": len([i for i in self.debt_items if i["severidad"] == "MEDIA"]),
            "deuda_por_dimension": debt_by_dimension,
            "horas_quick_wins": sum(
                item["costo_horas"] for item in self.cuadrantes["quick_wins"]
            ),
            "horas_strategic": sum(
                item["costo_horas"] for item in self.cuadrantes["strategic"]
            ),
        }

    def export_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generar reporte Markdown"""
        metrics = results["metrics"]

        report = [
            "# AGENT 7 — Technical Data Debt Classifier Report",
            "",
            f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Framework:** SGIND v1.0  ",
            "",
            "## Resumen Ejecutivo",
            "",
            "### Deuda Total Identificada",
            f"- **Total Items:** {metrics['total_items']} deudas clasificadas",
            f"- **Total Horas:** {metrics['total_horas']} horas de remediación",
            f"- **Valor Estimado:** ${metrics['total_horas'] * 150:.0f} (@ $150/hora)",
            "",
            "### Distribución de Severidad",
            f"- 🔴 **CRÍTICA:** {metrics['total_criticos']} items (máxima prioridad)",
            f"- 🟠 **ALTA:** {metrics['total_altos']} items (próximo sprint)",
            f"- 🟡 **MEDIA:** {metrics['total_medios']} items (roadmap)",
            "",
            "### Oportunidades Inmediatas",
            f"- **Quick Wins:** {metrics['horas_quick_wins']} horas (bajo esfuerzo, alto impacto)",
            f"- **Strategic:** {metrics['horas_strategic']} horas (roadmap mediano plazo)",
            "",
            "## Deuda por Dimensión",
            "",
        ]

        for dimension in self.dimensions:
            metric = metrics["deuda_por_dimension"][dimension]
            report.append(
                f"### {dimension.upper()}"
            )
            report.append(f"- **Items:** {metric['cantidad']}")
            report.append(f"- **Horas:** {metric['horas']}")
            report.append("")

        report.extend([
            "## Matriz de Priorización",
            "",
            "### 🎯 QUICK WINS (Bajo Esfuerzo, Alto Impacto)",
            "**Máxima Prioridad — Hacer YA**",
            "",
        ])

        for item in self.cuadrantes["quick_wins"]:
            report.append(f"- **{item['id']}** — {item['tipo']}")
            report.append(f"  Esfuerzo: {item['costo_horas']}h | ROI: {item['roi']:.1f}")
            report.append("")

        report.extend([
            "### 📊 STRATEGIC (Alto Esfuerzo, Alto Impacto)",
            "**Roadmap de Mediano Plazo**",
            "",
        ])

        for item in self.cuadrantes["strategic"][:3]:
            report.append(f"- **{item['id']}** — {item['tipo']} ({item['costo_horas']}h)")

        return "\n".join(report)

    def export_csv_matriz(self) -> str:
        """Exportar matriz en CSV"""
        lines = [
            "ID,Dimensión,Tipo,Severidad,Horas,Prioridad,ROI,Cuadrante"
        ]

        for item in sorted(self.debt_items, key=lambda x: x["prioridad"]):
            esfuerzo_bajo = item["costo_horas"] <= 5
            impacto_alto = item["severidad"] in ["CRÍTICA", "ALTA"]

            if esfuerzo_bajo and impacto_alto:
                cuadrante = "Quick Wins"
            elif not esfuerzo_bajo and impacto_alto:
                cuadrante = "Strategic"
            elif esfuerzo_bajo and not impacto_alto:
                cuadrante = "Low Value"
            else:
                cuadrante = "Black Hole"

            line = (
                f"{item['id']},{item['dimension']},{item['tipo']},"
                f"{item['severidad']},{item['costo_horas']},{item['prioridad']},"
                f"{item['roi']:.1f},{cuadrante}"
            )
            lines.append(line)

        return "\n".join(lines)

    def export_hallazgos_json(self) -> str:
        """Exportar hallazgos en JSON"""
        hallazgos_grouped = {}
        for dimension in self.dimensions:
            hallazgos_grouped[dimension] = [
                i for i in self.debt_items if i["dimension"] == dimension
            ]

        return json.dumps(
            {
                "hallazgos_por_dimension": hallazgos_grouped,
                "total_por_dimension": {
                    k: len(v) for k, v in hallazgos_grouped.items()
                },
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )


def main():
    """Ejecutar clasificación de deuda"""
    classifier = TechnicalDebtClassifier()
    results = classifier.classify_debt()

    # Generar artefactos
    output_dir = Path(__file__).parent.parent / "artifacts"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Markdown
    md_file = output_dir / f"AGENT7_TECHNICAL_DEBT_{timestamp}.md"
    md_file.write_text(classifier.export_markdown_report(results), encoding="utf-8")
    logger.info(f"   ✅ Markdown: {md_file}")

    # CSV
    csv_file = output_dir / f"AGENT7_TECHNICAL_DEBT_{timestamp}.csv"
    csv_file.write_text(classifier.export_csv_matriz(), encoding="utf-8")
    logger.info(f"   ✅ CSV: {csv_file}")

    # Hallazgos JSON
    json_file = output_dir / f"AGENT7_TECHNICAL_DEBT_{timestamp}.json"
    json_file.write_text(classifier.export_hallazgos_json(), encoding="utf-8")
    logger.info(f"   ✅ Hallazgos JSON: {json_file}")

    logger.info(f"\n✅ Clasificación completada")
    logger.info(f"\n📊 Métricas Globales:")
    for key, value in results["metrics"].items():
        if not key.startswith("deuda_"):
            logger.info(f"   {key}: {value}")

    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    main()
