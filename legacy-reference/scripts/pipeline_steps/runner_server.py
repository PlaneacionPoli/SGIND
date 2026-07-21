#!/usr/bin/env python3
"""
Runner HTTP Server — ETL Pipeline Runner
Servidor HTTP mínimo (solo stdlib Python) para controlar el pipeline
desde el frontend runner_ui.html.

EJECUTAR:
  python scripts/pipeline_steps/runner_server.py
  → Abre http://localhost:8765 automáticamente

ENDPOINTS:
  GET  /           → sirve runner_ui.html
  GET  /status     → lee .pipeline_state/current_run.json
  POST /run/{id}   → ejecuta el script del paso (non-blocking)
  GET  /log/{id}   → últimas 150 líneas del log del paso
  GET  /audit/latest → último JSON en artifacts/audit/
  POST /reset      → limpia .pipeline_state/current_run.json
"""

import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

# ── Rutas ──────────────────────────────────────────────────────────
_STEPS_DIR = Path(__file__).parent
_ROOT = _STEPS_DIR.parent.parent
STATE_FILE = _ROOT / ".pipeline_state" / "current_run.json"
LOG_DIR    = _ROOT / ".pipeline_state" / "logs"
AUDIT_DIR  = _ROOT / "artifacts" / "audit"
UI_FILE    = _STEPS_DIR / "runner_ui.html"
PORT       = 8765

# Mapeo step_id → script filename
STEP_SCRIPTS = {
    "01":    "01_cargar_fuente.py",
    "02":    "02_validar_contrato.py",
    "03_04": "03_04_cargar_catalogo_metadatos.py",
    "05":    "05_abrir_workbook.py",
    "06":    "06_construir_registros.py",
    "07":    "07_aplicar_correcciones.py",
    "08":    "08_validacion_intermedia.py",
    "09_10": "09_10_escribir_reparar.py",
    "11":    "11_deduplicar_formulas.py",
    "12":    "12_actualizar_catalogo.py",
    "13":    "13_guardar.py",
    "14_15": "14_15_auditoria_respaldo.py",
    "00":    "00_run_all.py",
}

# Proceso activo actualmente (solo uno a la vez)
_running_proc = None
_running_step = None
_proc_lock = threading.Lock()


def _ensure_dirs():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _read_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _read_log(step_id: str, n_lines: int = 150) -> str:
    log_file = LOG_DIR / f"{step_id}.log"
    if not log_file.exists():
        return f"(sin log para paso {step_id})"
    try:
        lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-n_lines:])
    except Exception as e:
        return f"Error leyendo log: {e}"


def _latest_audit() -> dict:
    try:
        files = sorted(AUDIT_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if files:
            return json.loads(files[0].read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"error": "No se encontraron archivos de auditoría"}


def _run_step(step_id: str, extra_args: list | None = None) -> tuple[bool, str]:
    global _running_proc, _running_step
    script = STEP_SCRIPTS.get(step_id)
    if not script:
        return False, f"step_id desconocido: {step_id}"

    script_path = _STEPS_DIR / script
    if not script_path.exists():
        return False, f"Script no encontrado: {script_path}"

    with _proc_lock:
        if _running_proc is not None and _running_proc.poll() is None:
            return False, "Ya hay un paso en ejecución. Espera a que termine."
        _running_step = step_id

    log_file = LOG_DIR / f"{step_id}.log"
    cmd = [sys.executable, str(script_path)] + (extra_args or [])

    # Actualizar estado a "running" antes de lanzar
    state = _read_state()
    state[f"step_{step_id}"] = {
        "nombre": script.replace(".py", ""),
        "status": "running",
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "resultado": {},
    }
    state["_last_updated"] = __import__("datetime").datetime.now().isoformat()
    state["_current_running"] = step_id
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    with open(log_file, "w", encoding="utf-8") as lf:
        proc = subprocess.Popen(
            cmd,
            cwd=str(_ROOT),
            stdout=lf,
            stderr=lf,
            text=True,
        )

    with _proc_lock:
        _running_proc = proc

    def _monitor():
        global _running_proc, _running_step
        proc.wait()
        with _proc_lock:
            _running_proc = None
            _running_step = None
        # Quitar _current_running del estado
        state = _read_state()
        state.pop("_current_running", None)
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    threading.Thread(target=_monitor, daemon=True).start()
    return True, "started"


class PipelineHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # silenciar logs del servidor HTTP

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text: str, status: int = 200):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: bytes, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in ("", "/"):
            if UI_FILE.exists():
                self._send_html(UI_FILE.read_bytes())
            else:
                self._send_text("runner_ui.html no encontrado", 404)

        elif path == "/status":
            state = _read_state()
            state["_server_running"] = True
            state["_running_step"] = _running_step
            self._send_json(state)

        elif path.startswith("/log/"):
            step_id = path[5:]
            self._send_text(_read_log(step_id))

        elif path == "/audit/latest":
            self._send_json(_latest_audit())

        else:
            self._send_text("Not found", 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/run/"):
            step_id = path[5:]
            content_len = int(self.headers.get("Content-Length", 0))
            body = {}
            if content_len > 0:
                try:
                    body = json.loads(self.rfile.read(content_len))
                except Exception:
                    pass
            extra_args = body.get("args", [])
            ok, msg = _run_step(step_id, extra_args)
            self._send_json({"status": "started" if ok else "error", "message": msg})

        elif path == "/reset":
            if STATE_FILE.exists():
                STATE_FILE.unlink()
            self._send_json({"status": "ok", "message": "Estado reseteado"})

        elif path == "/stop":
            with _proc_lock:
                if _running_proc and _running_proc.poll() is None:
                    _running_proc.terminate()
                    self._send_json({"status": "ok", "message": "Proceso detenido"})
                else:
                    self._send_json({"status": "ok", "message": "No había proceso activo"})
        else:
            self._send_text("Not found", 404)


def main():
    _ensure_dirs()
    server = HTTPServer(("localhost", PORT), PipelineHandler)
    url = f"http://localhost:{PORT}"
    print(f"")
    print(f"  🔷 ETL Pipeline Runner")
    print(f"  ──────────────────────")
    print(f"  Servidor: {url}")
    print(f"  Raíz:     {_ROOT}")
    print(f"  Ctrl+C para detener")
    print(f"")

    # Abrir navegador tras breve pausa
    def _open_browser():
        import time
        time.sleep(0.8)
        webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.")
        server.shutdown()


if __name__ == "__main__":
    main()
