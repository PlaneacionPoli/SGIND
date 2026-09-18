# SGIND v2 Backend

## Entorno Python

Requiere Python 3.11–3.12. **No usar el Python 3.14 global de Windows**:
SQLAlchemy (columnas `Mapped[str | None]` en `app/models/*.py`) falla al
arrancar con Python 3.14 con el error:

```
TypeError: descriptor '__getitem__' requires a 'typing.Union' object but received a 'tuple'
```

Esto ocurre porque Python 3.14 cambió el manejo de anotaciones de tipos y
la versión de SQLAlchemy instalada globalmente (2.0.31) no lo soporta —
además de no coincidir con la versión fijada en `requirements.txt`
(`sqlalchemy[asyncio]==2.0.36`).

**Ya existe un virtualenv correcto en `backend/.venv312`** (Python 3.12.10
+ SQLAlchemy 2.0.36, alineado con `requirements.txt`). Actívalo antes de
correr el backend o los tests:

```powershell
backend\.venv312\Scripts\activate
```

```bash
source backend/.venv312/Scripts/activate  # Git Bash en Windows
```

Si el venv no existe o hay que recrearlo:

```bash
py -3.12 -m venv backend/.venv312
backend/.venv312/Scripts/pip install -r backend/requirements.txt
```

Alternativa: usar Docker para un entorno reproducible sin depender del
Python instalado localmente: `docker compose up backend`.

## Tests

```bash
backend/.venv312/Scripts/python.exe -m pytest
```

Nota: algunos tests fallan por archivos de datos/Excel no presentes en
este repo (`Resultados Consolidados.xlsx`, etc.) y por configuración de
staging/deploy (`test_fase10_staging.py`) — son fallos preexistentes no
relacionados con el entorno Python, confirmado comparando la misma suite
contra el código sin cambios.
