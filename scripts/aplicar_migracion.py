"""Aplica un archivo SQL de database/migrations/ a una base Postgres (p. ej. la de Render).

Uso (PowerShell, desde la raíz del repo):
    $env:DATABASE_URL = "<Internal/External Database URL de Render>"
    backend\\.venv312\\Scripts\\python.exe scripts\\aplicar_migracion.py database\\migrations\\006_login_otp.sql

Las migraciones son idempotentes (CREATE ... IF NOT EXISTS). La URL de Render puede venir como
postgres:// o postgresql://; también se acepta el prefijo +asyncpg del .env del backend.
"""

import asyncio
import os
import re
import sys
from pathlib import Path

import asyncpg


def _dsn(url: str) -> str:
    url = re.sub(r"^postgres(ql)?(\+asyncpg)?://", "postgresql://", url)
    # Render externo exige TLS; localhost no.
    host = re.search(r"@([^:/]+)", url)
    if host and host.group(1) not in ("localhost", "127.0.0.1") and "sslmode" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


async def main(path: Path) -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("Define DATABASE_URL en el entorno (no se acepta por argumento para no dejarla en el historial).")
    sql = path.read_text(encoding="utf-8")
    conn = await asyncpg.connect(_dsn(url))
    try:
        async with conn.transaction():
            await conn.execute(sql)
        print(f"OK: {path.name} aplicado en {conn.get_server_version()}")
    finally:
        await conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    asyncio.run(main(Path(sys.argv[1])))
