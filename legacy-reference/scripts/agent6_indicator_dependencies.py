"""
scripts/agent6_indicator_dependencies.py
AGENT 6 — Indicator Dependencies Analysis
Construye un grafo integral de dependencias entre indicadores
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class IndicatorDependencyGraph:
    """Análisis de dependencias entre indicadores SGIND"""

    def __init__(self, root_path: Path | None = None):
        self.root = Path(root_path) if root_path else Path(__file__).parent.parent
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Tuple[str, str, str]] = []  # (source, target, relation_type)
        self.cycles: List[List[str]] = []
        self.hallazgos: List[Dict[str, Any]] = []

    def build_graph(self) -> Dict[str, Any]:
        """Construir grafo de dependencias"""
        logger.info("=" * 70)
        logger.info("AGENT 6 — Indicator Dependencies Analysis")
        logger.info("=" * 70)

        self._discover_indicators()
        self._build_dependencies()
        self._analyze_graph()
        self._detect_cycles()

        return {
            "timestamp": datetime.now().isoformat(),
            "framework": "SGIND v1.0",
            "nodes": self.nodes,
            "edges": self.edges,
            "cycles": self.cycles,
            "hallazgos": self.hallazgos,
            "metrics": self._calculate_metrics(),
        }

    def _discover_indicators(self):
        """Descubrir indicadores en el codebase"""
        logger.info("\n📋 Descubriendo indicadores...")

        # Indicadores descubiertos (simulado - en producción buscar en código)
        default_indicators = {
            "cumplimiento_academico": {
                "nombre": "Cumplimiento Académico",
                "tipo": "base",
                "fuente": "Kawak",
                "perspectiva": "Procesos",
                "proceso": "Académica",
            },
            "cumplimiento_administrativo": {
                "nombre": "Cumplimiento Administrativo",
                "tipo": "base",
                "fuente": "Kawak",
                "perspectiva": "Procesos",
                "proceso": "Administrativa",
            },
            "cumplimiento_bienestar": {
                "nombre": "Cumplimiento Bienestar",
                "tipo": "base",
                "fuente": "Kawak",
                "perspectiva": "Cliente",
                "proceso": "Bienestar",
            },
            "cmi_estrategico": {
                "nombre": "CMI Estratégico",
                "tipo": "compuesto",
                "perspectiva": "Todas",
                "componentes": ["cumplimiento_academico", "cumplimiento_administrativo", "cumplimiento_bienestar"],
            },
            "ejecucion_presupuestal": {
                "nombre": "Ejecución Presupuestal",
                "tipo": "base",
                "fuente": "Excel",
                "perspectiva": "Financiera",
            },
            "desempeño_general": {
                "nombre": "Desempeño General",
                "tipo": "compuesto",
                "componentes": ["cmi_estrategico", "ejecucion_presupuestal"],
            },
            "tendencia_academica": {
                "nombre": "Tendencia Académica",
                "tipo": "derivado",
                "base": "cumplimiento_academico",
                "transformacion": "tendencia_temporal",
            },
        }

        for ind_id, ind_data in default_indicators.items():
            self.nodes[ind_id] = {
                "id": ind_id,
                **ind_data,
                "in_degree": 0,
                "out_degree": 0,
            }

        logger.info(f"   Indicadores descubiertos: {len(self.nodes)}")

    def _build_dependencies(self):
        """Construir relaciones de dependencia"""
        logger.info("\n📋 Construyendo dependencias...")

        # Relaciones basadas en indicadores descubiertos
        dependencies = [
            # depende_de (indicador → campo/dato)
            ("cumplimiento_academico", "campo_total_cumplido", "depende_de"),
            ("cumplimiento_administrativo", "campo_total_cumplido", "depende_de"),
            ("cumplimiento_bienestar", "campo_total_cumplido", "depende_de"),
            ("ejecucion_presupuestal", "campo_gastos_reales", "depende_de"),

            # compuesto_de (indicador → indicadores componentes)
            ("cmi_estrategico", "cumplimiento_academico", "compuesto_de"),
            ("cmi_estrategico", "cumplimiento_administrativo", "compuesto_de"),
            ("cmi_estrategico", "cumplimiento_bienestar", "compuesto_de"),
            ("desempeño_general", "cmi_estrategico", "compuesto_de"),
            ("desempeño_general", "ejecucion_presupuestal", "compuesto_de"),

            # transforma (derivado → base)
            ("tendencia_academica", "cumplimiento_academico", "transforma"),
        ]

        for source, target, relation_type in dependencies:
            self.edges.append((source, target, relation_type))

            # Actualizar IN/OUT degree para nodos existentes
            if source in self.nodes:
                self.nodes[source]["out_degree"] += 1
            if target in self.nodes:
                self.nodes[target]["in_degree"] += 1

        logger.info(f"   Relaciones mapeadas: {len(self.edges)}")

    def _analyze_graph(self):
        """Analizar el grafo de dependencias"""
        logger.info("\n📋 Analizando grafo...")

        # Indicadores críticos (alta IN-DEGREE)
        critical = sorted(
            self.nodes.items(),
            key=lambda x: x[1]["in_degree"],
            reverse=True
        )[:3]

        for ind_id, ind_data in critical:
            logger.info(f"   Crítico: {ind_data['nombre']} (dependientes: {ind_data['in_degree']})")

    def _detect_cycles(self):
        """Detectar ciclos en el grafo (CRÍTICO)"""
        logger.info("\n📋 Detectando ciclos...")

        # Búsqueda simple de ciclos (DFS)
        def find_cycles_from(start: str, visited: Set[str], path: List[str]) -> None:
            visited.add(start)
            path.append(start)

            for source, target, _ in self.edges:
                if source == start and target not in visited:
                    find_cycles_from(target, visited, path[:])
                elif source == start and target in path:
                    cycle = path[path.index(target):] + [target]
                    if cycle not in self.cycles:
                        self.cycles.append(cycle)
                        self.hallazgos.append({
                            "tipo": "Ciclo Detectado",
                            "severidad": "CRÍTICA",
                            "ciclo": cycle,
                            "recomendación": "Revisar fórmulas - lógica circular detectada",
                        })

        for node_id in self.nodes:
            find_cycles_from(node_id, set(), [])

        if self.cycles:
            logger.warning(f"   ⚠️ Ciclos detectados: {len(self.cycles)}")
        else:
            logger.info("   ✅ No hay ciclos")

    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calcular métricas del grafo"""
        base_indicators = [n for n in self.nodes.values() if n["tipo"] == "base"]
        composite_indicators = [n for n in self.nodes.values() if n["tipo"] == "compuesto"]
        isolated = [n for n in self.nodes.values() if n["in_degree"] == 0 and n["out_degree"] == 0]

        max_depth = self._calculate_max_depth()

        return {
            "total_indicadores": len(self.nodes),
            "total_relaciones": len(self.edges),
            "indicadores_base": len(base_indicators),
            "indicadores_compuestos": len(composite_indicators),
            "indicadores_aislados": len(isolated),
            "ciclos": len(self.cycles),
            "profundidad_maxima": max_depth,
            "criticidad_maxima": max((n["in_degree"] for n in self.nodes.values()), default=0),
        }

    def _calculate_max_depth(self) -> int:
        """Calcular profundidad máxima del grafo"""
        max_depth = 0

        def depth_from(node_id: str, visited: Set[str]) -> int:
            if node_id in visited:
                return 0
            visited.add(node_id)

            dependencies = [
                t for s, t, _ in self.edges if s == node_id
            ]

            if not dependencies:
                return 1

            return 1 + max((depth_from(dep, visited.copy()) for dep in dependencies), default=0)

        for node_id in self.nodes:
            d = depth_from(node_id, set())
            max_depth = max(max_depth, d)

        return max_depth

    def export_json_ld(self) -> str:
        """Exportar grafo en JSON-LD"""
        graph = {
            "@context": {
                "@vocab": "https://indicadores.sgind/",
                "indicadores": "https://indicadores.sgind/indicador/",
                "depende_de": {"@type": "@id"},
                "compuesto_de": {"@type": "@id"},
                "transforma": {"@type": "@id"},
            },
            "@graph": [
                {
                    "@id": f"indicadores:{node_id}",
                    "@type": "Indicador",
                    **node_data,
                }
                for node_id, node_data in self.nodes.items()
            ],
        }

        return json.dumps(graph, indent=2, ensure_ascii=False)

    def export_cypher(self) -> str:
        """Exportar grafo en Cypher (Neo4j)"""
        lines = [
            "// Neo4j Cypher Script — Indicador Dependencies",
            "// Ejecución: neo4j-shell < script.cypher",
            "",
        ]

        # Crear nodos
        for node_id, node_data in self.nodes.items():
            properties = {
                "id": node_id,
                "nombre": node_data.get("nombre", ""),
                "tipo": node_data.get("tipo", ""),
                "in_degree": node_data.get("in_degree", 0),
                "out_degree": node_data.get("out_degree", 0),
            }

            props_str = ", ".join(
                f'{k}: "{v}"' if isinstance(v, str) else f"{k}: {v}"
                for k, v in properties.items()
            )

            lines.append(f'CREATE (:{node_data.get("tipo", "Indicador")} {{{props_str}}})')

        # Crear relaciones
        lines.append("")
        for source, target, relation_type in self.edges:
            lines.append(f'MATCH (a {{ id: "{source}" }}), (b {{ id: "{target}" }})')
            lines.append(f'CREATE (a)-[:{relation_type}]->(b)')

        return "\n".join(lines)

    def export_graphml(self) -> str:
        """Exportar grafo en GraphML (Gephi/Cytoscape)"""
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlformat/graphml">',
            '  <graph edgedefault="directed">',
        ]

        # Nodos
        for node_id, node_data in self.nodes.items():
            size = 30 + (node_data["in_degree"] * 5)  # Tamaño por centralidad
            lines.append(
                f'    <node id="{node_id}" label="{node_data.get("nombre", node_id)}" '
                f'size="{size}"/>'
            )

        # Aristas
        for source, target, relation_type in self.edges:
            lines.append(f'    <edge source="{source}" target="{target}" label="{relation_type}"/>')

        lines.extend([
            "  </graph>",
            "</graphml>",
        ])

        return "\n".join(lines)

    def export_csv(self) -> str:
        """Exportar matriz de dependencias en CSV"""
        lines = ["Indicador,Tipo,Perspectiva,Proceso,Dependientes,Dependencias,Criticidad"]

        for node_id, node_data in self.nodes.items():
            dependents = node_data["in_degree"]
            dependencies = node_data["out_degree"]
            criticality = "ALTA" if dependents > 2 else "MEDIA" if dependents > 0 else "BAJA"

            line = (
                f'{node_data.get("nombre", node_id)},'
                f'{node_data.get("tipo", "")},'
                f'{node_data.get("perspectiva", "")},'
                f'{node_data.get("proceso", "")},'
                f'{dependents},'
                f'{dependencies},'
                f'{criticality}'
            )
            lines.append(line)

        return "\n".join(lines)

    def generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generar reporte Markdown"""
        metrics = results["metrics"]

        report = [
            "# AGENT 6 — Indicator Dependencies Report",
            "",
            f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Framework:** SGIND v1.0  ",
            "",
            "## Resumen Ejecutivo",
            "",
            f"- **Total indicadores mapeados:** {metrics['total_indicadores']}",
            f"- **Indicadores base:** {metrics['indicadores_base']}",
            f"- **Indicadores compuestos:** {metrics['indicadores_compuestos']}",
            f"- **Indicadores aislados:** {metrics['indicadores_aislados']}",
            f"- **Ciclos detectados:** {metrics['ciclos']} {'⚠️ CRÍTICO' if metrics['ciclos'] > 0 else '✅'}",
            f"- **Profundidad máxima:** {metrics['profundidad_maxima']} niveles",
            f"- **Criticidad máxima:** {metrics['criticidad_maxima']} dependientes",
            "",
            "## Indicadores Críticos (Mayor Dependencia)",
            "",
        ]

        # Top 5 indicadores críticos
        critical_top = sorted(
            self.nodes.items(),
            key=lambda x: x[1]["in_degree"],
            reverse=True
        )[:5]

        for idx, (ind_id, ind_data) in enumerate(critical_top, 1):
            report.append(f"{idx}. **{ind_data['nombre']}** ({ind_data['tipo']})")
            report.append(f"   - Dependientes: {ind_data['in_degree']}")
            report.append(f"   - Dependencias: {ind_data['out_degree']}")
            report.append("")

        if self.hallazgos:
            report.append("## Hallazgos Críticos")
            report.append("")
            for hallazgo in self.hallazgos:
                report.append(f"### {hallazgo['tipo']}")
                report.append(f"**Severidad:** {hallazgo['severidad']}")
                report.append(f"**Detalles:** {hallazgo.get('ciclo', [])} → " + hallazgo['recomendación'])
                report.append("")

        return "\n".join(report)


def main():
    """Ejecutar análisis de dependencias"""
    analyzer = IndicatorDependencyGraph()
    results = analyzer.build_graph()

    # Generar artefactos
    output_dir = Path(__file__).parent.parent / "artifacts"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON-LD
    json_file = output_dir / f"AGENT6_INDICATOR_DEPENDENCIES_{timestamp}.json"
    json_file.write_text(analyzer.export_json_ld(), encoding="utf-8")
    logger.info(f"   ✅ JSON-LD: {json_file}")

    # Cypher
    cypher_file = output_dir / f"AGENT6_INDICATOR_DEPENDENCIES_{timestamp}.cypher"
    cypher_file.write_text(analyzer.export_cypher(), encoding="utf-8")
    logger.info(f"   ✅ Cypher: {cypher_file}")

    # GraphML
    graphml_file = output_dir / f"AGENT6_INDICATOR_DEPENDENCIES_{timestamp}.graphml"
    graphml_file.write_text(analyzer.export_graphml(), encoding="utf-8")
    logger.info(f"   ✅ GraphML: {graphml_file}")

    # CSV
    csv_file = output_dir / f"AGENT6_INDICATOR_DEPENDENCIES_{timestamp}.csv"
    csv_file.write_text(analyzer.export_csv(), encoding="utf-8")
    logger.info(f"   ✅ CSV: {csv_file}")

    # Markdown
    md_file = output_dir / f"AGENT6_INDICATOR_DEPENDENCIES_{timestamp}.md"
    md_file.write_text(analyzer.generate_markdown_report(results), encoding="utf-8")
    logger.info(f"   ✅ Markdown: {md_file}")

    logger.info(f"\n✅ Análisis completado")
    logger.info(f"\n📊 Métricas:")
    for key, value in results["metrics"].items():
        logger.info(f"   {key}: {value}")

    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    main()
