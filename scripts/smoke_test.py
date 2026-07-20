#!/usr/bin/env python3
"""
Smoke tests post-deploy para SGIND v2 staging.

Verifica que el backend y frontend responden correctamente después de un deploy.
Diseñado para correr en CI (GitHub Actions) y localmente.

Uso:
    # Con URLs configuradas:
    python sgind-v2/scripts/smoke_test.py \
        --api-url http://staging.poli.edu.co:8000 \
        --frontend-url http://staging.poli.edu.co:3000

    # Solo backend local:
    python sgind-v2/scripts/smoke_test.py --api-url http://localhost:8000

    # En CI (no falla si no hay URL configurada):
    python sgind-v2/scripts/smoke_test.py \
        --api-url "" --frontend-url "" --skip-if-unconfigured
"""

from __future__ import annotations

import argparse
import sys
import time

try:
    import httpx
except ImportError:
    print("ERROR: pip install httpx", file=sys.stderr)
    sys.exit(1)


# ─── Checks individuales ──────────────────────────────────────────────────────

def check_backend_health(api_url: str, timeout: int = 10) -> tuple[bool, str]:
    """GET /api/v1/health debe responder 200."""
    try:
        r = httpx.get(f"{api_url}/api/v1/health", timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            version = data.get("version", "?")
            return True, f"OK — version {version}"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)


def check_backend_auth_login_url(api_url: str, timeout: int = 10) -> tuple[bool, str]:
    """GET /api/v1/auth/login-url debe responder 200 o 503 (si Azure no configurado)."""
    try:
        r = httpx.get(f"{api_url}/api/v1/auth/login-url", timeout=timeout)
        if r.status_code in (200, 503):
            return True, f"HTTP {r.status_code} (503 = Azure no configurado, esperado en staging sin credenciales)"
        return False, f"HTTP {r.status_code} inesperado"
    except Exception as e:
        return False, str(e)


def check_backend_unauthenticated_api(api_url: str, timeout: int = 10) -> tuple[bool, str]:
    """GET /api/v1/dashboard/kpis sin token debe responder 401/403 (no 500)."""
    try:
        r = httpx.get(f"{api_url}/api/v1/dashboard/kpis?anio=2025", timeout=timeout)
        if r.status_code in (401, 403, 422):
            return True, f"HTTP {r.status_code} — auth funciona correctamente"
        return False, f"HTTP {r.status_code} (esperado 401/403)"
    except Exception as e:
        return False, str(e)


def check_backend_pdf_endpoint_unauthenticated(api_url: str, timeout: int = 10) -> tuple[bool, str]:
    """GET /api/v1/reports/resumen-general sin token debe responder 401/403."""
    try:
        r = httpx.get(f"{api_url}/api/v1/reports/resumen-general?anio=2025", timeout=timeout)
        if r.status_code in (401, 403, 422):
            return True, f"HTTP {r.status_code} — PDF endpoint protegido"
        return False, f"HTTP {r.status_code} (esperado 401/403)"
    except Exception as e:
        return False, str(e)


def check_backend_docs(api_url: str, timeout: int = 10) -> tuple[bool, str]:
    """GET /docs (Swagger UI) debe responder 200."""
    try:
        r = httpx.get(f"{api_url}/docs", timeout=timeout)
        if r.status_code == 200:
            return True, "Swagger UI disponible"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)


def check_frontend(frontend_url: str, timeout: int = 15) -> tuple[bool, str]:
    """GET frontend raíz debe responder 200."""
    try:
        r = httpx.get(frontend_url, timeout=timeout, follow_redirects=True)
        if r.status_code == 200:
            content_type = r.headers.get("content-type", "")
            if "html" in content_type:
                return True, "Frontend HTML disponible"
            return True, f"HTTP 200 (content-type: {content_type})"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)


# ─── Retry helper ─────────────────────────────────────────────────────────────

def with_retry(check_fn, *args, retries: int = 3, wait: int = 5, **kwargs) -> tuple[bool, str]:
    """Reintenta un check hasta N veces con espera entre intentos."""
    last_ok, last_msg = False, "No intentado"
    for attempt in range(1, retries + 1):
        ok, msg = check_fn(*args, **kwargs)
        if ok:
            return True, msg
        last_ok, last_msg = ok, msg
        if attempt < retries:
            print(f"  Intento {attempt}/{retries} fallido: {msg} — reintentando en {wait}s...")
            time.sleep(wait)
    return last_ok, last_msg


# ─── Suite principal ──────────────────────────────────────────────────────────

def run_smoke_tests(api_url: str, frontend_url: str, retries: int = 3) -> bool:
    results: list[tuple[str, bool, str]] = []

    print(f"\nSMOKE TESTS - SGIND v2 Staging")
    print(f"API URL:      {api_url or '(no configurada)'}")
    print(f"Frontend URL: {frontend_url or '(no configurada)'}")
    print("=" * 60)

    if api_url:
        checks_backend = [
            ("Backend health",        check_backend_health),
            ("Auth /login-url",       check_backend_auth_login_url),
            ("API auth (401 sin JWT)", check_backend_unauthenticated_api),
            ("PDF endpoint protegido", check_backend_pdf_endpoint_unauthenticated),
            ("Swagger /docs",         check_backend_docs),
        ]
        for name, fn in checks_backend:
            ok, msg = with_retry(fn, api_url, retries=retries)
            results.append((name, ok, msg))
            icon = "[OK]" if ok else "[FAIL]"
            print(f"  {icon}  {name}: {msg}")

    if frontend_url:
        ok, msg = with_retry(check_frontend, frontend_url, retries=retries)
        results.append(("Frontend home", ok, msg))
        icon = "[OK]" if ok else "[FAIL]"
        print(f"  {icon}  Frontend home: {msg}")

    print("=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    failed = [(name, msg) for name, ok, msg in results if not ok]

    print(f"Resultado: {passed}/{total} checks pasaron")
    if failed:
        print("\nFallos:")
        for name, msg in failed:
            print(f"  - {name}: {msg}")
        return False

    print("Todos los smoke tests pasaron.")
    return True


# ─── Punto de entrada ─────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke tests SGIND v2 staging")
    parser.add_argument("--api-url", default="", help="URL base del backend FastAPI")
    parser.add_argument("--frontend-url", default="", help="URL base del frontend Next.js")
    parser.add_argument(
        "--skip-if-unconfigured",
        action="store_true",
        help="Salir con codigo 0 si no hay URLs configuradas (para CI)",
    )
    parser.add_argument(
        "--retries", type=int, default=3,
        help="Numero de reintentos por check (default: 3)",
    )
    args = parser.parse_args()

    api_url = args.api_url.rstrip("/")
    frontend_url = args.frontend_url.rstrip("/")

    if not api_url and not frontend_url:
        if args.skip_if_unconfigured:
            print("Smoke tests omitidos: STAGING_URL y STAGING_API_URL no configurados.")
            print("Para activar: configurar variables en Settings > Environments > staging del repo GitHub.")
            return 0
        print("ERROR: use --api-url y/o --frontend-url", file=sys.stderr)
        return 1

    ok = run_smoke_tests(api_url=api_url, frontend_url=frontend_url, retries=args.retries)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
