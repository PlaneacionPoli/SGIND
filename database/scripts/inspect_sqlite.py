"""Inspección rápida de SQLite legacy para migración Fase 2."""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[3] / "data" / "db" / "registros_om.db"

if not DB.exists():
    print(f"NO_DB:{DB}")
    raise SystemExit(0)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print("tables:", tables)
for table in tables:
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"{table}: rows={count} cols={cols}")
conn.close()
