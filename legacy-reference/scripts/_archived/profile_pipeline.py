"""
scripts/profile_pipeline.py
===========================

Pipeline profiling tool — identifica cuellos de botella en ETL.

Ejecuta cada componente del pipeline y mide:
  - Tiempo total de ejecución
  - Memoria usada
  - Funciones más lentas (per-component)
  - Estadísticas de I/O

Uso:
    python scripts/profile_pipeline.py              # Profile normal
    python scripts/profile_pipeline.py --full       # Full cProfile dump
    python scripts/profile_pipeline.py --component consolidar_api  # Single component

Salida:
    artifacts/profile_<timestamp>.json
    artifacts/profile_<timestamp>.html
    artifacts/profile_<timestamp>.log
"""

from __future__ import annotations

import argparse
import cProfile
import json
import logging
import os
import pstats
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional
import psutil
import gc


# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)

PIPELINE_COMPONENTS = [
    {
        "name": "consolidar_api",
        "script": SCRIPT_DIR / "consolidar_api.py",
        "description": "Consolidate API and Kawak data sources",
        "output_files": [
            "data/raw/Fuentes Consolidadas/Indicadores Kawak.xlsx",
            "data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx",
        ],
    },
    {
        "name": "actualizar_consolidado",
        "script": SCRIPT_DIR / "actualizar_consolidado.py",
        "description": "Update historical consolidation with latest data",
        "output_files": [
            "data/output/Resultados Consolidados.xlsx",
        ],
    },
    {
        "name": "generar_reporte",
        "script": SCRIPT_DIR / "generar_reporte.py",
        "description": "Generate final report",
        "output_files": [
            "data/output/Reporte Final.xlsx",
        ],
    },
]


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class MemoryMetrics:
    """Memory usage statistics."""
    initial_mb: float = 0.0
    peak_mb: float = 0.0
    final_mb: float = 0.0
    delta_mb: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class IOMetrics:
    """I/O operation metrics."""
    read_count: int = 0
    write_count: int = 0
    read_bytes: int = 0
    write_bytes: int = 0

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class ComponentProfile:
    """Profile data for a single pipeline component."""
    name: str
    description: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration_sec: float = 0.0
    success: bool = False
    error_message: Optional[str] = None
    memory: MemoryMetrics = field(default_factory=MemoryMetrics)
    io_ops: IOMetrics = field(default_factory=IOMetrics)
    output_files_created: List[str] = field(default_factory=list)
    cprofile_stats: Optional[str] = None
    top_functions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["memory"] = self.memory.to_dict()
        d["io_ops"] = self.io_ops.to_dict()
        return d


@dataclass
class PipelineProfile:
    """Overall profile for entire pipeline."""
    timestamp: str = ""
    total_duration_sec: float = 0.0
    components: List[ComponentProfile] = field(default_factory=list)
    success_rate: float = 0.0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_duration_sec": self.total_duration_sec,
            "success_rate": self.success_rate,
            "components": [c.to_dict() for c in self.components],
            "notes": self.notes,
        }


# ============================================================================
# PROFILING FUNCTIONS
# ============================================================================


def _get_memory_info() -> MemoryMetrics:
    """Get current process memory usage."""
    process = psutil.Process(os.getpid())
    info = process.memory_info()
    mb = info.rss / 1024 / 1024
    return MemoryMetrics(initial_mb=mb)


def _get_io_counters() -> IOMetrics:
    """Get I/O counters for current process."""
    try:
        process = psutil.Process(os.getpid())
        io = process.io_counters()
        return IOMetrics(
            read_count=io.read_count,
            write_count=io.write_count,
            read_bytes=io.read_bytes,
            write_bytes=io.write_bytes,
        )
    except (AttributeError, OSError):
        return IOMetrics()


def _run_component_with_profile(
    component: Dict[str, Any],
    profiler: Optional[cProfile.Profile] = None,
) -> ComponentProfile:
    """
    Run a single pipeline component with profiling.
    
    Returns:
        ComponentProfile with timing, memory, and performance data.
    """
    profile = ComponentProfile(
        name=component["name"],
        description=component["description"],
    )

    # Record initial state
    gc.collect()
    profile.memory.initial_mb = _get_memory_info().initial_mb
    profile.io_ops = _get_io_counters()
    profile.start_time = time.time()

    try:
        # Run component script
        if profiler:
            profiler.enable()

        result = subprocess.run(
            [sys.executable, str(component["script"])],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        if profiler:
            profiler.disable()

        # Record end state
        profile.end_time = time.time()
        profile.duration_sec = profile.end_time - profile.start_time

        if result.returncode == 0:
            profile.success = True
        else:
            profile.success = False
            profile.error_message = f"Exit code {result.returncode}: {result.stderr}"

        # Check output files
        for output_file in component["output_files"]:
            full_path = REPO_ROOT / output_file
            if full_path.exists():
                profile.output_files_created.append(output_file)

        # Record final memory
        gc.collect()
        profile.memory.final_mb = _get_memory_info().initial_mb
        profile.memory.delta_mb = profile.memory.final_mb - profile.memory.initial_mb

    except subprocess.TimeoutExpired as e:
        profile.success = False
        profile.error_message = f"Timeout after 600 seconds: {e}"
        profile.end_time = time.time()
        profile.duration_sec = profile.end_time - profile.start_time

    except Exception as e:
        profile.success = False
        profile.error_message = f"Error: {type(e).__name__}: {e}"
        profile.end_time = time.time()
        profile.duration_sec = profile.end_time - profile.start_time

    return profile


def _extract_top_functions(
    profiler: cProfile.Profile,
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """
    Extract top functions from cProfile stats.
    
    Args:
        profiler: Completed cProfile.Profile object
        top_n: Number of top functions to extract
    
    Returns:
        List of dicts with function name, calls, total time, per-call time
    """
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats("cumulative")

    top_functions = []
    for func, (cc, nc, tt, ct, callers) in ps.timings.items():
        if nc == 0:
            continue
        top_functions.append({
            "function": f"{func[0]}:{func[1]}",
            "calls": nc,
            "total_time_sec": tt,
            "per_call_sec": ct,
            "file": func[0],
            "line": func[1],
        })

    return sorted(top_functions, key=lambda x: x["total_time_sec"], reverse=True)[:top_n]


# ============================================================================
# REPORTING
# ============================================================================


def _generate_html_report(profile: PipelineProfile) -> str:
    """Generate HTML report of pipeline profile."""
    timestamp = profile.timestamp
    components_html = ""

    for comp in profile.components:
        status_badge = "✅" if comp.success else "❌"
        error_section = (
            f"<tr><td colspan='2'><strong>Error:</strong> {comp.error_message}</td></tr>"
            if comp.error_message
            else ""
        )

        components_html += f"""
        <section class="component">
            <h3>{status_badge} {comp.name.replace('_', ' ').title()}</h3>
            <p><em>{comp.description}</em></p>
            
            <table>
                <tr><td><strong>Duration</strong></td><td>{comp.duration_sec:.2f}s</td></tr>
                <tr><td><strong>Memory Delta</strong></td><td>{comp.memory.delta_mb:.2f} MB</td></tr>
                <tr><td><strong>Output Files</strong></td><td>{len(comp.output_files_created)}</td></tr>
                {error_section}
            </table>

            <h4>Top Functions (by cumulative time)</h4>
            <ol>
        """

        if comp.top_functions:
            for func in comp.top_functions[:5]:
                components_html += f"""
                <li>
                    <code>{func['function']}</code><br/>
                    Calls: {func['calls']}, 
                    Total: {func['total_time_sec']:.3f}s, 
                    Per-call: {func['per_call_sec']:.6f}s
                </li>
                """
        else:
            components_html += "<li>No profiling data available</li>"

        components_html += "</ol></section>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Pipeline Profile Report</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .component {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; background: #f9f9f9; }}
            .component h3 {{ margin-top: 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
            td:first-child {{ font-weight: bold; width: 30%; }}
            code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }}
            ol {{ margin: 10px 0; }}
            li {{ margin: 8px 0; }}
        </style>
    </head>
    <body>
        <h1>🔍 Pipeline Profiling Report</h1>
        <div class="summary">
            <p><strong>Timestamp:</strong> {timestamp}</p>
            <p><strong>Total Duration:</strong> {profile.total_duration_sec:.2f}s</p>
            <p><strong>Success Rate:</strong> {profile.success_rate:.1%}</p>
            <p><strong>Notes:</strong> {profile.notes}</p>
        </div>
        
        {components_html}
        
        <hr>
        <p style="color: #999; font-size: 12px;">Generated by scripts/profile_pipeline.py</p>
    </body>
    </html>
    """
    return html


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Main profiling orchestrator."""
    parser = argparse.ArgumentParser(
        description="Profile SGIND pipeline to identify bottlenecks"
    )
    parser.add_argument(
        "--component",
        type=str,
        help="Profile only a specific component (e.g., 'consolidar_api')",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Enable full cProfile instrumentation (slower, more detailed)",
    )
    args = parser.parse_args()

    # Setup logging
    log_file = ARTIFACTS_DIR / f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("PIPELINE PROFILING STARTED")
    logger.info("=" * 80)

    # Determine which components to profile
    components_to_profile = PIPELINE_COMPONENTS
    if args.component:
        components_to_profile = [
            c for c in PIPELINE_COMPONENTS if c["name"] == args.component
        ]
        if not components_to_profile:
            logger.error(f"Component '{args.component}' not found")
            sys.exit(1)

    # Run profiling
    overall_start = time.time()
    profiler = cProfile.Profile() if args.full else None
    profile = PipelineProfile(timestamp=datetime.now().isoformat())

    for component in components_to_profile:
        logger.info(f"Profiling: {component['name']}...")
        comp_profile = _run_component_with_profile(component, profiler)
        profile.components.append(comp_profile)

        status = "✅" if comp_profile.success else "⚠️"
        logger.info(
            f"{status} {component['name']} completed "
            f"({comp_profile.duration_sec:.2f}s, "
            f"Δ {comp_profile.memory.delta_mb:+.2f}MB)"
        )

    overall_end = time.time()
    profile.total_duration_sec = overall_end - overall_start

    # Calculate success rate
    successful = sum(1 for c in profile.components if c.success)
    profile.success_rate = successful / len(profile.components) if profile.components else 0

    # Generate reports
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON report
    json_file = ARTIFACTS_DIR / f"profile_{timestamp_str}.json"
    json_file.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")
    logger.info(f"📊 JSON report: {json_file.relative_to(REPO_ROOT)}")

    # HTML report
    html_file = ARTIFACTS_DIR / f"profile_{timestamp_str}.html"
    html_content = _generate_html_report(profile)
    html_file.write_text(html_content, encoding="utf-8")
    logger.info(f"📊 HTML report: {html_file.relative_to(REPO_ROOT)}")

    # Summary
    logger.info("=" * 80)
    logger.info("PROFILING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total Duration: {profile.total_duration_sec:.2f}s")
    logger.info(f"Success Rate: {profile.success_rate:.1%}")
    logger.info(f"Components Profiled: {len(profile.components)}")

    for comp in profile.components:
        logger.info(
            f"  - {comp.name}: {comp.duration_sec:.2f}s "
            f"({'✅ OK' if comp.success else '❌ FAILED'})"
        )

    logger.info("=" * 80)


if __name__ == "__main__":
    main()
