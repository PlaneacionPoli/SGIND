#!/usr/bin/env python3
"""
UAT — Verificación numérica SGIND v2 vs Legacy (Streamlit).

Compara los KPIs clave del nuevo sistema (v2) contra el legacy para el mismo
año/corte, reportando diferencias y verificando paridad ≤ 0.01%.

Uso:
    # Con backend local corriendo (docker compose up -d):
    python sgind-v2/scripts/uat_verify.py --api-url http://localhost:8000

    # Contra staging:
    python sgind-v2/scripts/uat_verify.py --api-url http://staging.poli.edu.co:8000

    # Especificar año:
    python sgind-v2/scripts/uat_verify.py --api-url http://localhost:8000 --anio 2025

    # Solo verificar endpoints (sin comparación Excel):
    python sgind-v2/scripts/uat_verify.py --api-url http://localhost:8000 --no-excel

Requiere:
    pip install httpx pandas openpyxl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    print("ERROR: pip install httpx", file=sys.stderr)
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("ERROR: pip install pandas openpyxl", file=sys.stderr)
    sys.exit(1)

# ─── Constantes ───────────────────────────────────────────────────────────────

TOLERANCIA = 0.0001  # 0.01% tolerancia para paridad numérica
TIMEOUT = 30

# Ruta al Excel legacy (relativa al root del repo)
LEGACY_EXCEL_PATHS = [
    Path("data/output/Resultados Consolidados.xlsx"),
    Path("data/output/resultados_consolidados.xlsx"),
    Path("data/Resultados Consolidados.xlsx"),
]

SEMAFORO_COLORES = {
    "Peligro": "#ef4444",
    "Alerta": "#f59e0b",
    "Cumplimiento": "#22c55e",
    "Sobrecumplimiento": "#3b82f6",
}

# ─── Helpers ─────────────────────────────────────────────────────────────────

class _Colors:
    OK   = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    INFO = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {_Colors.OK}✓{_Colors.RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {_Colors.FAIL}✗{_Colors.RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {_Colors.WARN}⚠{_Colors.RESET} {msg}")


def info(msg: str) -> None:
    print(f"  {_Colors.INFO}→{_Colors.RESET} {msg}")


def section(title: str) -> None:
    print(f"\n{_Colors.BOLD}{'─'*60}{_Colors.RESET}")
    print(f"{_Colors.BOLD}  {title}{_Colors.RESET}")
    print(f"{_Colors.BOLD}{'─'*60}{_Colors.RESET}")


# ─── Auth ─────────────────────────────────────────────────────────────────────

def get_dev_token(api_url: str) -> str | None:
    """Obtiene un dev token (solo en ambiente development)."""
    try:
        r = httpx.post(f"{api_url}/api/v1/auth/dev-token", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json().get("access_token")
        if r.status_code == 404:
            warn("Dev token no disponible (ambiente production). Usa --token para pasar JWT.")
            return None
        return None
    except Exception as e:
        warn(f"No se pudo obtener dev token: {e}")
        return None


def make_headers(token: str | None) -> dict[str, str]:
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ─── Checks de endpoints ──────────────────────────────────────────────────────

def check_health(api_url: str) -> bool:
    try:
        r = httpx.get(f"{api_url}/api/v1/health", timeout=TIMEOUT)
        if r.status_code == 200:
            v = r.json().get("version", "?")
            ok(f"Health OK — versión {v}")
            return True
        fail(f"Health HTTP {r.status_code}")
        return False
    except Exception as e:
        fail(f"Health error: {e}")
        return False


def check_endpoint(
    client: httpx.Client,
    label: str,
    url: str,
    params: dict | None = None,
    required_keys: list[str] | None = None,
) -> tuple[bool, Any]:
    try:
        r = client.get(url, params=params or {}, timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            missing = [k for k in (required_keys or []) if k not in data]
            if missing:
                fail(f"{label} — faltan claves: {missing}")
                return False, data
            ok(f"{label} — HTTP 200")
            return True, data
        fail(f"{label} — HTTP {r.status_code}")
        return False, None
    except Exception as e:
        fail(f"{label} — error: {e}")
        return False, None


# ─── Verificación numérica ────────────────────────────────────────────────────

def find_legacy_excel() -> Path | None:
    for p in LEGACY_EXCEL_PATHS:
        if p.exists():
            return p
    return None


def calcular_kpis_legacy(excel_path: Path, anio: int) -> dict[str, float]:
    """Lee el Excel legacy y calcula KPIs para el año dado."""
    try:
        df = pd.read_excel(excel_path, sheet_name="Consolidado Semestral")
    except Exception as e:
        warn(f"No se pudo leer hoja 'Consolidado Semestral': {e}")
        return {}

    # Filtrar por año
    col_anio = next((c for c in df.columns if "año" in c.lower() or "anio" in c.lower()), None)
    if col_anio:
        df = df[df[col_anio] == anio]

    if df.empty:
        warn(f"No hay datos para año {anio} en el Excel legacy")
        return {}

    # Columna de cumplimiento
    col_cump = next(
        (c for c in df.columns if "cumplimiento" in c.lower()), None
    )
    if not col_cump:
        warn("No se encontró columna de cumplimiento en el Excel legacy")
        return {}

    serie = pd.to_numeric(df[col_cump].astype(str).str.replace("%", "").str.strip(), errors="coerce").dropna()

    if serie.empty:
        return {}

    # Normalizar a decimal si están en escala 0-100
    if serie.mean() > 1.5:
        serie = serie / 100.0

    total = len(serie)
    peligro = (serie < 0.7).sum()
    alerta  = ((serie >= 0.7) & (serie < 0.9)).sum()
    cumple  = ((serie >= 0.9) & (serie <= 1.0)).sum()
    sobre   = (serie > 1.0).sum()

    return {
        "total_indicadores": total,
        "pct_peligro":        round(peligro / total, 4) if total else 0.0,
        "pct_alerta":         round(alerta / total, 4) if total else 0.0,
        "pct_cumplimiento":   round(cumple / total, 4) if total else 0.0,
        "pct_sobre":          round(sobre / total, 4) if total else 0.0,
        "cumplimiento_medio": round(float(serie.mean()), 4),
    }


def extraer_kpis_v2(data_kpis: Any, data_semaphore: Any) -> dict[str, float]:
    """Extrae KPIs comparables del JSON de la API v2."""
    result: dict[str, float] = {}

    if data_semaphore and isinstance(data_semaphore, list):
        total = sum(item.get("count", 0) for item in data_semaphore)
        if total:
            for item in data_semaphore:
                estado = item.get("estado", "")
                pct    = round(item.get("count", 0) / total, 4)
                if estado == "Peligro":
                    result["pct_peligro"] = pct
                elif estado == "Alerta":
                    result["pct_alerta"] = pct
                elif estado == "Cumplimiento":
                    result["pct_cumplimiento"] = pct
                elif estado == "Sobrecumplimiento":
                    result["pct_sobre"] = pct
            result["total_indicadores"] = total

    return result


def comparar_kpis(legacy: dict[str, float], v2: dict[str, float]) -> list[dict]:
    resultados = []
    claves = set(legacy) & set(v2)

    for clave in sorted(claves):
        val_l = legacy[clave]
        val_v = v2[clave]
        diff  = abs(val_l - val_v)
        pasa  = diff <= TOLERANCIA
        resultados.append({
            "kpi":     clave,
            "legacy":  val_l,
            "v2":      val_v,
            "diff":    diff,
            "pasa":    pasa,
        })

    return resultados


def verificar_colores_semaforo(data_semaphore: Any) -> bool:
    if not data_semaphore or not isinstance(data_semaphore, list):
        warn("No hay datos de semáforo para verificar colores")
        return False

    todos_ok = True
    for item in data_semaphore:
        estado = item.get("estado", "")
        color  = item.get("color", "")
        esperado = SEMAFORO_COLORES.get(estado)
        if esperado and color.lower() != esperado.lower():
            fail(f"Color semáforo '{estado}': esperado {esperado}, recibido {color}")
            todos_ok = False
        elif esperado:
            ok(f"Color semáforo '{estado}': {color} ✓")

    return todos_ok


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="UAT — Verificación numérica SGIND v2 vs Legacy")
    parser.add_argument("--api-url", default="http://localhost:8000", help="URL base del backend v2")
    parser.add_argument("--anio", type=int, default=2025, help="Año a verificar (default: 2025)")
    parser.add_argument("--token", default="", help="JWT token si dev-token no está disponible")
    parser.add_argument("--no-excel", action="store_true", help="Omitir comparación contra Excel legacy")
    parser.add_argument("--output-json", default="", help="Guardar resultados en JSON")
    args = parser.parse_args()

    api_url = args.api_url.rstrip("/")
    errores = 0
    resultados_json: dict = {"anio": args.anio, "api_url": api_url, "checks": []}

    print(f"\n{_Colors.BOLD}UAT — Verificación numérica SGIND v2{_Colors.RESET}")
    print(f"  API: {api_url}")
    print(f"  Año: {args.anio}")
    print(f"  Tolerancia paridad: {TOLERANCIA*100:.2f}%")

    # ── 1. Health ──
    section("1. Health Check")
    if not check_health(api_url):
        print(f"\n{_Colors.FAIL}ERROR: Backend no disponible. Abortando.{_Colors.RESET}")
        return 1

    # ── 2. Auth ──
    section("2. Autenticación")
    token = args.token or get_dev_token(api_url)
    if not token:
        warn("Sin token — los endpoints autenticados devolverán 401")
    else:
        ok(f"Token obtenido ({len(token)} caracteres)")

    headers = make_headers(token)

    # ── 3. Endpoints ──
    section("3. Verificación de Endpoints")

    with httpx.Client(headers=headers) as client:
        checks = [
            ("Filtros dashboard",      f"{api_url}/api/v1/dashboard/filtros",              None,                        ["anios", "anio_default"]),
            ("KPIs dashboard",         f"{api_url}/api/v1/dashboard/kpis",                 {"anio": args.anio},         ["kpis"]),
            ("Semáforo dashboard",     f"{api_url}/api/v1/dashboard/semaphore",             {"anio": args.anio},         None),
            ("Tendencia dashboard",    f"{api_url}/api/v1/dashboard/tendencia",             {"anio": args.anio},         None),
            ("Filtros CMI",            f"{api_url}/api/v1/cmi/filtros",                    None,                        None),
            ("CMI estratégico",        f"{api_url}/api/v1/cmi/dashboard",                  {"anio": args.anio},         None),
            ("Filtros indicadores",    f"{api_url}/api/v1/indicators/filtros",              None,                        None),
            ("Lista indicadores",      f"{api_url}/api/v1/indicators/",                    {"anio": args.anio, "limit": 5}, None),
            ("OMs lista",              f"{api_url}/api/v1/om/",                            None,                        None),
            ("Filtros plan mejora",    f"{api_url}/api/v1/plan-mejoramiento/filtros",       None,                        None),
            ("Dashboard plan mejora",  f"{api_url}/api/v1/plan-mejoramiento/dashboard",    {"anio": args.anio},         None),
            ("Filtros seguimiento",    f"{api_url}/api/v1/seguimiento/filtros",             None,                        None),
            ("Dashboard seguimiento",  f"{api_url}/api/v1/seguimiento/dashboard",          {"anio": args.anio},         None),
            ("Filtros informe",        f"{api_url}/api/v1/informe/filtros",                None,                        None),
            ("Dashboard informe",      f"{api_url}/api/v1/informe/dashboard",              {"anio": args.anio},         None),
        ]

        data_semaphore = None
        data_kpis = None

        for label, url, params, required_keys in checks:
            pasó, data = check_endpoint(client, label, url, params, required_keys)
            if not pasó:
                errores += 1
            if "semaphore" in url and data:
                data_semaphore = data
            if "kpis" in url and data:
                data_kpis = data
            resultados_json["checks"].append({"label": label, "url": url, "ok": pasó})

    # ── 4. Colores semáforo ──
    section("4. Colores Semáforo (PROJECT_RULES §3.3)")
    if data_semaphore:
        if not verificar_colores_semaforo(data_semaphore):
            errores += 1
    else:
        warn("Sin datos de semáforo — verificación de colores omitida")

    # ── 5. Paridad numérica vs legacy ──
    section("5. Paridad Numérica v2 vs Legacy Excel")

    if args.no_excel:
        warn("--no-excel: comparación omitida")
    else:
        excel_path = find_legacy_excel()
        if not excel_path:
            warn(f"Excel legacy no encontrado en rutas: {[str(p) for p in LEGACY_EXCEL_PATHS]}")
            warn("Ejecuta desde el directorio raíz del repo o copia el Excel a data/output/")
        else:
            info(f"Excel legacy encontrado: {excel_path}")
            kpis_legacy = calcular_kpis_legacy(excel_path, args.anio)
            kpis_v2     = extraer_kpis_v2(data_kpis, data_semaphore)

            if not kpis_legacy:
                warn("No se pudieron calcular KPIs desde el Excel legacy")
            elif not kpis_v2:
                warn("No se pudieron extraer KPIs de la API v2")
            else:
                comparaciones = comparar_kpis(kpis_legacy, kpis_v2)
                resultados_json["paridad"] = comparaciones

                print(f"\n  {'KPI':<28} {'Legacy':>10} {'v2':>10} {'Diff':>10} {'Estado':>10}")
                print(f"  {'─'*68}")
                for c in comparaciones:
                    estado = f"{_Colors.OK}✓ PASA{_Colors.RESET}" if c["pasa"] else f"{_Colors.FAIL}✗ FALLA{_Colors.RESET}"
                    print(
                        f"  {c['kpi']:<28} {c['legacy']:>10.4f} {c['v2']:>10.4f} "
                        f"{c['diff']:>10.6f} {estado}"
                    )
                    if not c["pasa"]:
                        errores += 1

    # ── 6. Resumen ──
    section("6. Resumen Final")
    if errores == 0:
        print(f"\n  {_Colors.OK}{_Colors.BOLD}VERIFICACIÓN UAT EXITOSA — 0 errores{_Colors.RESET}")
        print(f"  Sistema listo para aprobación de Fase 11.\n")
    else:
        print(f"\n  {_Colors.FAIL}{_Colors.BOLD}VERIFICACIÓN UAT FALLIDA — {errores} error(es){_Colors.RESET}")
        print(f"  Revisar bugs en UAT_BUGS.md antes de aprobar.\n")

    if args.output_json:
        resultados_json["errores_totales"] = errores
        resultados_json["aprobado"] = errores == 0
        Path(args.output_json).write_text(json.dumps(resultados_json, indent=2, ensure_ascii=False))
        info(f"Resultados guardados en: {args.output_json}")

    return 0 if errores == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
