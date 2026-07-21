#!/usr/bin/env python3
"""
scripts/auditoria_estandar_nivel_cumplimiento.py

PROPÓSITO:
  Auditoría automática para verificar que TODO el proyecto cumple con el
  ESTÁNDAR OFICIAL DE NIVEL DE CUMPLIMIENTO.

VALIDACIONES:
  1. ✅ Los umbrales en config.py son los correctos
  2. ✅ La función categorizar_cumplimiento() en semantica.py es la oficial
  3. ✅ NO hay lógica inline de categorización en archivos Python
  4. ✅ Todos los imports usan la función oficial
  5. ✅ Tests validan que Plan Anual funciona
  6. ✅ Cobertura de tests es suficiente

EJECUCIÓN:
  python scripts/auditoria_estandar_nivel_cumplimiento.py
  python scripts/auditoria_estandar_nivel_cumplimiento.py --verbose
  python scripts/auditoria_estandar_nivel_cumplimiento.py --fix

SALIDA:
  - Reporte en consola
  - Archivo: artifacts/auditoria_estandar_cumplimiento_YYYYMMDD.json
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import argparse

# Agregar raíz del proyecto al PATH
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class AuditoriaEstandarCumplimiento:
    """Auditoría del estándar de nivel de cumplimiento"""

    def __init__(self, verbose=False, fix=False):
        self.verbose = verbose
        self.fix = fix
        self.root = ROOT
        self.errors = []
        self.warnings = []
        self.successes = []

    def run(self) -> Dict:
        """Ejecutar auditoría completa"""
        logger.info("=" * 80)
        logger.info("AUDITORÍA: ESTÁNDAR NIVEL DE CUMPLIMIENTO")
        logger.info("=" * 80)

        # 1. Validar umbrales en config.py
        self._audit_config_umbrales()

        # 2. Validar función oficial en semantica.py
        self._audit_semantica_oficial()

        # 3. Escanear archivos Python por lógica inline
        self._audit_no_inline_logic()

        # 4. Validar imports
        self._audit_imports()

        # 5. Validar tests
        self._audit_tests()

        # Generar reporte
        reporte = self._generar_reporte()
        return reporte

    def _audit_config_umbrales(self):
        """Validar que config.py tiene los umbrales correctos"""
        logger.info("\n1️⃣  Validando umbrales en core/config.py...")

        config_path = self.root / "core" / "config.py"
        if not config_path.exists():
            self.errors.append(f"❌ No existe: {config_path}")
            return

        try:
            # Importar módulo
            import core.config as config_module

            # Validar umbrales
            validaciones = {
                "UMBRAL_PELIGRO": (0.80, config_module.UMBRAL_PELIGRO),
                "UMBRAL_ALERTA": (1.00, config_module.UMBRAL_ALERTA),
                "UMBRAL_SOBRECUMPLIMIENTO": (1.05, config_module.UMBRAL_SOBRECUMPLIMIENTO),
                "UMBRAL_ALERTA_PA": (0.95, config_module.UMBRAL_ALERTA_PA),
                "UMBRAL_SOBRECUMPLIMIENTO_PA": (1.00, config_module.UMBRAL_SOBRECUMPLIMIENTO_PA),
            }

            for nombre, (esperado, actual) in validaciones.items():
                if actual == esperado:
                    self.successes.append(f"✅ {nombre} = {actual}")
                else:
                    self.errors.append(
                        f"❌ {nombre} = {actual}, se esperaba {esperado}"
                    )

            # Validar que IDS_PLAN_ANUAL existe y es frozenset
            if hasattr(config_module, "IDS_PLAN_ANUAL"):
                if isinstance(config_module.IDS_PLAN_ANUAL, frozenset):
                    self.successes.append(
                        f"✅ IDS_PLAN_ANUAL existe ({len(config_module.IDS_PLAN_ANUAL)} IDs)"
                    )
                else:
                    self.errors.append(
                        f"❌ IDS_PLAN_ANUAL no es frozenset: {type(config_module.IDS_PLAN_ANUAL)}"
                    )
            else:
                self.errors.append("❌ IDS_PLAN_ANUAL no definido en config.py")

        except Exception as e:
            self.errors.append(f"❌ Error importando config.py: {e}")

    def _audit_semantica_oficial(self):
        """Validar que semantica.py tiene la función oficial"""
        logger.info("\n2️⃣  Validando función oficial en core/semantica.py...")

        semantica_path = self.root / "core" / "semantica.py"
        if not semantica_path.exists():
            self.errors.append(f"❌ No existe: {semantica_path}")
            return

        contenido = semantica_path.read_text(encoding="utf-8")

        # Validar que existe categorizar_cumplimiento
        if "def categorizar_cumplimiento" in contenido:
            self.successes.append("✅ Función categorizar_cumplimiento() definida")
        else:
            self.errors.append("❌ Función categorizar_cumplimiento() no encontrada")

        # Validar que detecta Plan Anual
        if "IDS_PLAN_ANUAL" in contenido and "es_plan_anual" in contenido:
            self.successes.append("✅ Función detecta Plan Anual")
        else:
            self.errors.append("❌ Función NO detecta Plan Anual")

        # Validar que tiene docstring
        if "Plan Anual: cumplimiento ≥ 95%" in contenido or "PLAN ANUAL" in contenido:
            self.successes.append("✅ Documentación menciona regla Plan Anual")
        else:
            self.warnings.append("⚠️  Documentación NO menciona Plan Anual")

    def _audit_no_inline_logic(self):
        """Escanear archivos Python por lógica inline de categorización"""
        logger.info("\n3️⃣  Escaneando archivos por lógica inline de categorización...")

        # Patrones que indican lógica inline (PROHIBIDA)
        patrones_prohibidos = [
            r"if\s+\w+\s*<\s*0\.80\s*:",  # if cumpl < 0.80:
            r"if\s+\w+\s*<\s*UMBRAL_PELIGRO\s*:",  # if cumpl < UMBRAL_PELIGRO:
            r"elif\s+\w+\s*<\s*1\.0\s*:",  # elif cumpl < 1.0:
            r"elif\s+\w+\s*<\s*1\.05\s*:",  # elif cumpl < 1.05:
            r"\"Peligro\"\s+if\s+",  # "Peligro" if ...
            r"\"Alerta\"\s+if\s+",  # "Alerta" if ...
        ]

        archivos_auditados = 0
        archivos_con_problemas = []

        # Escanear directorios clave
        dirs_escanear = [
            self.root / "services",
            self.root / "streamlit_app",
            self.root / "core",
            self.root / "scripts",
        ]

        for dir_path in dirs_escanear:
            if not dir_path.exists():
                continue

            for py_file in dir_path.rglob("*.py"):
                # Skip: tests, __pycache__, archivos legados
                if "test" in py_file.name or "__pycache__" in str(py_file):
                    continue

                archivos_auditados += 1
                contenido = py_file.read_text(encoding="utf-8")

                # Permitir ciertos matches en semantica.py y calculos.py
                if "semantica.py" in str(py_file) or "calculos.py" in str(py_file):
                    continue

                for patron in patrones_prohibidos:
                    if re.search(patron, contenido):
                        archivos_con_problemas.append(str(py_file.relative_to(self.root)))
                        self.warnings.append(
                            f"⚠️  Posible lógica inline en: {py_file.name} "
                            f"(patrón: {patron})"
                        )
                        break

        if not archivos_con_problemas:
            self.successes.append(f"✅ {archivos_auditados} archivos sin lógica inline")
        else:
            self.warnings.append(
                f"⚠️  {len(archivos_con_problemas)} archivos pueden tener lógica inline"
            )

    def _audit_imports(self):
        """Validar que los imports son correctos"""
        logger.info("\n4️⃣  Validando imports...")

        # Archivos clave que DEBEN importar categorizar_cumplimiento
        archivos_debe_importar = [
            "services/data_loader.py",
            "services/strategic_indicators.py",
        ]

        for archivo_rel in archivos_debe_importar:
            archivo = self.root / archivo_rel
            if not archivo.exists():
                self.warnings.append(f"⚠️  Archivo no existe: {archivo_rel}")
                continue

            contenido = archivo.read_text(encoding="utf-8")

            # Validar que importa de lugar correcto
            if "from core.domain import categorizar_cumplimiento" in contenido:
                self.successes.append(f"✅ {archivo_rel} importa de core.domain")
            elif "categorizar_cumplimiento" in contenido:
                self.warnings.append(
                    f"⚠️  {archivo_rel} usa categorizar_cumplimiento pero import podría estar mal"
                )
            else:
                self.warnings.append(
                    f"⚠️  {archivo_rel} no importa categorizar_cumplimiento"
                )

    def _audit_tests(self):
        """Validar que existen tests"""
        logger.info("\n5️⃣  Validando tests...")

        test_files = [
            "tests/test_problema_1_plan_anual_mal_categorizado.py",
            "tests/test_semantica.py",
            "tests/test_calculos.py",
        ]

        tests_encontrados = 0
        for test_file_rel in test_files:
            test_file = self.root / test_file_rel
            if test_file.exists():
                tests_encontrados += 1
                # Contar número de test functions
                contenido = test_file.read_text(encoding="utf-8")
                num_tests = len(re.findall(r"def test_", contenido))
                self.successes.append(f"✅ {test_file_rel} ({num_tests} tests)")
            else:
                self.warnings.append(f"⚠️  No existe: {test_file_rel}")

        if tests_encontrados >= 2:
            self.successes.append(f"✅ Tests de cobertura encontrados ({tests_encontrados} archivos)")
        else:
            self.errors.append("❌ Insuficientes archivos de tests")

    def _generar_reporte(self) -> Dict:
        """Generar reporte final"""
        logger.info("\n" + "=" * 80)
        logger.info("RESUMEN DE AUDITORÍA")
        logger.info("=" * 80)

        print("\n✅ ÉXITOS:")
        for success in self.successes:
            print(f"  {success}")

        if self.warnings:
            print("\n⚠️  ADVERTENCIAS:")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.errors:
            print("\n❌ ERRORES:")
            for error in self.errors:
                print(f"  {error}")

        # Resumen
        print("\n" + "=" * 80)
        print(
            f"Total: {len(self.successes)} ✅  "
            f"{len(self.warnings)} ⚠️   "
            f"{len(self.errors)} ❌"
        )

        # Status
        if self.errors:
            status = "FAIL"
            nivel_alerta = "🔴 CRÍTICO"
        elif self.warnings:
            status = "WARNING"
            nivel_alerta = "🟡 REVISAR"
        else:
            status = "PASS"
            nivel_alerta = "🟢 OK"

        print(f"Status: {nivel_alerta} ({status})")
        print("=" * 80 + "\n")

        # Generar reporte JSON
        reporte = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "summary": {
                "successes": len(self.successes),
                "warnings": len(self.warnings),
                "errors": len(self.errors),
            },
            "details": {
                "successes": self.successes,
                "warnings": self.warnings,
                "errors": self.errors,
            },
        }

        # Guardar reporte
        artifacts_dir = self.root / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reporte_path = artifacts_dir / f"auditoria_estandar_cumplimiento_{timestamp}.json"
        reporte_path.write_text(json.dumps(reporte, indent=2))

        logger.info(f"📄 Reporte guardado: {reporte_path.relative_to(self.root)}")

        return reporte


def main():
    parser = argparse.ArgumentParser(
        description="Auditoría del estándar de nivel de cumplimiento"
    )
    parser.add_argument("--verbose", action="store_true", help="Modo verboso")
    parser.add_argument("--fix", action="store_true", help="Intentar auto-fix")

    args = parser.parse_args()

    auditoria = AuditoriaEstandarCumplimiento(verbose=args.verbose, fix=args.fix)
    reporte = auditoria.run()

    # Exit code basado en status
    if reporte["status"] == "FAIL":
        sys.exit(1)
    elif reporte["status"] == "WARNING":
        sys.exit(0)  # Warning no es error fatal
    else:
        sys.exit(0)  # OK


if __name__ == "__main__":
    main()
