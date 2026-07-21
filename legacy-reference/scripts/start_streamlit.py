#!/usr/bin/env python3
"""
scripts/start_streamlit.py

Lanza la app de Streamlit con una configuración base y un modo opcional
"Power Apps embed" activado por variables de entorno.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP_PATH = ROOT / "app.py"


def _env_flag(name: str, default: str = "false") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def main() -> int:
    port = os.getenv("PORT", os.getenv("STREAMLIT_PORT", "8501"))
    address = os.getenv("STREAMLIT_ADDRESS", "0.0.0.0")
    browser_server_address = os.getenv("STREAMLIT_BROWSER_SERVER_ADDRESS", "")
    base_url_path = os.getenv("STREAMLIT_BASE_URL_PATH", "").strip("/")

    embed_mode = _env_flag("POWER_APPS_EMBEDDED") or _env_flag("STREAMLIT_EMBED_MODE")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_PATH),
        "--server.port",
        port,
        "--server.address",
        address,
        "--server.headless",
        "true",
    ]

    if browser_server_address:
        command.extend(["--browser.serverAddress", browser_server_address])

    if base_url_path:
        command.extend(["--server.baseUrlPath", base_url_path])

    if embed_mode:
        command.extend(
            [
                "--server.enableCORS",
                "false",
                "--server.enableXsrfProtection",
                "false",
                "--browser.gatherUsageStats",
                "false",
                "--client.toolbarMode",
                "minimal",
            ]
        )

    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    return subprocess.call(command, cwd=str(ROOT), env=env)


if __name__ == "__main__":
    raise SystemExit(main())