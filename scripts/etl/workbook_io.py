from __future__ import annotations

import shutil
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def _validar_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path, "r") as archive:
        if "[Content_Types].xml" not in archive.namelist():
            raise zipfile.BadZipFile(f"{path.name} no tiene estructura xlsx valida")


def _candidatos_workbook(path_objetivo: Path) -> list[Path]:
    vistos: set[Path] = set()
    candidatos: list[Path] = []
    nombre_valores = f"{path_objetivo.stem} VALORES.xlsx"

    def _agregar(path_candidato: Path) -> None:
        if path_candidato in vistos or not path_candidato.exists():
            return
        if path_candidato.suffix.lower() != ".xlsx":
            return
        if path_candidato.name == nombre_valores:
            return
        vistos.add(path_candidato)
        candidatos.append(path_candidato)

    _agregar(path_objetivo)
    _agregar(path_objetivo.with_suffix(".bak.xlsx"))

    hermanos = sorted(
        path_objetivo.parent.glob(f"{path_objetivo.stem}*.xlsx"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for hermano in hermanos:
        _agregar(hermano)

    return candidatos


@contextmanager
def workbook_local_copy(path_objetivo: Path) -> Iterator[tuple[Path, Path]]:
    errores: list[str] = []
    with tempfile.TemporaryDirectory(prefix="sip_excel_") as temp_dir:
        temp_root = Path(temp_dir)
        for candidato in _candidatos_workbook(path_objetivo):
            try:
                local_path = temp_root / candidato.name
                shutil.copy2(candidato, local_path)
                _validar_xlsx(local_path)
                yield local_path, candidato
                return
            except Exception as exc:
                errores.append(f"{candidato.name}: {exc}")

    detalle = "; ".join(errores) if errores else "sin archivos candidatos"
    raise FileNotFoundError(
        f"No fue posible materializar una copia local valida de {path_objetivo.name}: {detalle}"
    )