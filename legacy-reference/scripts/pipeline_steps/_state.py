"""
Módulo compartido de estado para el pipeline ETL paso a paso.
Persiste el estado entre scripts en .pipeline_state/
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent  # proyecto root
STATE_DIR = _ROOT / ".pipeline_state"
STATE_FILE = STATE_DIR / "current_run.json"


def _ensure_dir():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "logs").mkdir(exist_ok=True)


def save_state(step_id: str, step_name: str, status: str, resultado: dict | None = None) -> None:
    """Persiste el resultado de un paso en current_run.json."""
    _ensure_dir()
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    state[f"step_{step_id}"] = {
        "nombre": step_name,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "resultado": resultado or {},
    }
    state["_last_updated"] = datetime.now().isoformat()
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_df(name: str, df) -> None:
    """Guarda un DataFrame como CSV en .pipeline_state/."""
    _ensure_dir()
    path = STATE_DIR / f"{name}.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")


def load_df(name: str):
    """Carga un DataFrame desde .pipeline_state/."""
    import pandas as pd
    path = STATE_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Estado '{name}' no encontrado en {path}. "
            f"¿Ejecutaste el paso anterior?"
        )
    return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)


def save_records(name: str, records: list) -> None:
    """Guarda una lista de dicts como JSON en .pipeline_state/."""
    _ensure_dir()
    path = STATE_DIR / f"{name}.json"
    path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def load_records(name: str) -> list:
    """Carga una lista de dicts desde .pipeline_state/."""
    path = STATE_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Registros '{name}' no encontrados en {path}. "
            f"¿Ejecutaste el paso anterior?"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(name: str, data) -> None:
    """Guarda datos JSON genéricos en .pipeline_state/."""
    _ensure_dir()
    path = STATE_DIR / f"{name}.json"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def load_json(name: str) -> dict:
    """Carga datos JSON genéricos desde .pipeline_state/."""
    path = STATE_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Dato '{name}' no encontrado en {path}. "
            f"¿Ejecutaste el paso anterior?"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def reset_state() -> None:
    """Elimina el estado actual del pipeline."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
