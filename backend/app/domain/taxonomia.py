"""Taxonomía estratégica por versión de marco (líneas → objetivos → metas) y
validación de la asociación manual indicador ↔ marco.

Fuente: app/data/taxonomia/<version_id>.json (ver marcos.toml). Módulo puro:
sin Excel ni FastAPI. La asociación la diligencia Planeación en la hoja
`Indicador_Marco` del catálogo, eligiendo los textos oficiales; aquí se
resuelven a ids y se verifica la coherencia línea → objetivo → meta.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd

TAXONOMIA_DIR = Path(__file__).resolve().parent.parent / "data" / "taxonomia"

COLUMNAS_ASOCIACION = ("Id", "version_id", "Linea", "Objetivo", "Meta")


def parse_flag01(valor: object) -> int | None:
    """Marcador numérico 1/0 (también '1.0', True/False). Vacío o inválido → None."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    if isinstance(valor, bool):
        return int(valor)
    try:
        n = float(str(valor).strip().replace(",", "."))
    except ValueError:
        return None
    return int(n) if n in (0.0, 1.0) else None


def regla_meta(marcador: int | None, tiene_meta: bool, version_id: str) -> str | None:
    """Regla de negocio: indicador estratégico del PDI (1) => debe tener meta
    estratégica; de proceso (0) => no puede tenerla. Devuelve el motivo del
    incumplimiento o None."""
    if marcador is None:
        return f"Asociado a {version_id} pero sin marcador 1/0 en esa versión (vacío = no pertenece al PDI)"
    if marcador == 1 and not tiene_meta:
        return "Indicador estratégico del PDI (1) sin meta estratégica"
    if marcador == 0 and tiene_meta:
        return "Indicador de proceso (0, no PDI) con meta estratégica"
    return None


@dataclass(frozen=True)
class Meta:
    id: str
    nombre: str


@dataclass(frozen=True)
class Objetivo:
    id: str
    numero: int
    nombre: str
    metas: tuple[Meta, ...]


@dataclass(frozen=True)
class Linea:
    id: str
    orden: int
    nombre: str
    objetivos: tuple[Objetivo, ...]


@dataclass(frozen=True)
class Taxonomia:
    version_id: str
    tipo: str
    lineas: tuple[Linea, ...]
    fuente: str = ""

    def iter_metas(self):
        for linea in self.lineas:
            for obj in linea.objetivos:
                for meta in obj.metas:
                    yield linea, obj, meta


def norm_texto(valor: object) -> str:
    """Minúsculas, sin tildes ni puntuación y con espacios colapsados: tolera las
    variantes de escritura que ya existen en el catálogo ('Crecer con compromiso
    social ', 'institucional, centrada' vs 'institucional centrada')."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    s = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())


def parse_taxonomia(data: dict) -> Taxonomia:
    lineas = tuple(
        Linea(
            id=ln["id"],
            orden=int(ln.get("orden", 0)),
            nombre=ln["nombre"],
            objetivos=tuple(
                Objetivo(
                    id=o["id"],
                    numero=int(o["numero"]),
                    nombre=o["nombre"],
                    metas=tuple(Meta(id=m["id"], nombre=m["nombre"]) for m in o.get("metas", [])),
                )
                for o in ln.get("objetivos", [])
            ),
        )
        for ln in data["lineas"]
    )
    tax = Taxonomia(
        version_id=data["version_id"], tipo=data.get("tipo", "PDI"), lineas=lineas, fuente=data.get("fuente", "")
    )
    ids = [ln.id for ln in lineas] + [o.id for ln in lineas for o in ln.objetivos]
    ids += [m.id for _, _, m in tax.iter_metas()]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{tax.version_id}: ids duplicados en la taxonomía")
    return tax


@lru_cache
def load_taxonomia(version_id: str, base_dir: Path = TAXONOMIA_DIR) -> Taxonomia:
    path = base_dir / f"{version_id}.json"
    if not path.exists():
        raise KeyError(f"Sin taxonomía para {version_id}")
    with open(path, encoding="utf-8") as f:
        tax = parse_taxonomia(json.load(f))
    if tax.version_id != version_id:
        raise ValueError(f"{path.name}: version_id interno {tax.version_id!r} no coincide")
    return tax


@dataclass
class ResultadoAsociacion:
    """Filas válidas (con ids resueltos), errores por fila, advertencias e incumplimientos."""

    validas: pd.DataFrame
    errores: list[dict] = field(default_factory=list)
    advertencias: list[dict] = field(default_factory=list)
    # Regla de negocio (no descarta la fila): ver `regla_meta`.
    incumplimientos: list[dict] = field(default_factory=list)


def resolver_asociaciones(
    df: pd.DataFrame, version_id: str | None = None, *, meta_tolerante: bool = False
) -> ResultadoAsociacion:
    """Valida la hoja de un PDI y resuelve nombres de línea/objetivo/meta a ids.

    Una fila sin Linea/Objetivo/Meta se omite (indicador aún sin asociar). Errores:
    versión sin taxonomía, línea fuera de la taxonomía, objetivo que no pertenece a la
    línea, meta que no pertenece al objetivo o asociación repetida. La comparación ignora
    mayúsculas, tildes, puntuación y espacios.

    `meta_tolerante=True` (hoja de un PDI ya cerrado, migrada del catálogo con redacciones
    de meta distintas a la oficial): una meta que no coincide no es error; se conserva la
    asociación a nivel de objetivo (meta_id vacío) y se registra una advertencia.

    Columna opcional `PDI` (1/0): aplica `regla_meta` (1 = estratégico, exige meta;
    0 = de proceso, no puede tenerla). Los hallazgos van a `incumplimientos` y la fila se
    conserva igualmente.
    """
    faltan = [c for c in COLUMNAS_ASOCIACION if c not in df.columns]
    if faltan:
        raise ValueError(f"Hoja del PDI: faltan columnas {faltan}")

    validas: list[dict] = []
    errores: list[dict] = []
    advertencias: list[dict] = []
    incumplimientos: list[dict] = []
    vistos: set[tuple[str, str, str]] = set()

    for pos, row in df.iterrows():
        fila = int(pos) + 2  # +1 encabezado, +1 base 1
        ind = str(row["Id"]).strip() if pd.notna(row["Id"]) else ""
        ver = str(row["version_id"]).strip() if pd.notna(row["version_id"]) else ""
        if version_id is not None and ver != version_id:
            continue
        linea_t, obj_t, meta_t = (norm_texto(row[c]) for c in ("Linea", "Objetivo", "Meta"))
        if not (linea_t or obj_t or meta_t):
            continue

        def err(motivo: str, _ctx=(fila, ind, ver)) -> None:
            errores.append({"fila": _ctx[0], "Id": _ctx[1], "version_id": _ctx[2], "motivo": motivo})

        if not ind:
            err("Id vacío")
            continue
        try:
            tax = load_taxonomia(ver)
        except KeyError:
            err(f"version_id sin taxonomía: {ver!r}")
            continue

        linea = next((ln for ln in tax.lineas if norm_texto(ln.nombre) == linea_t), None)
        if linea is None:
            err(f"Linea fuera de la taxonomía {ver}: {row['Linea']!r}")
            continue
        objetivo = None
        if obj_t:
            objetivo = next((o for o in linea.objetivos if norm_texto(o.nombre) == obj_t), None)
            if objetivo is None:
                err(f"Objetivo no pertenece a la línea {linea.nombre!r}: {row['Objetivo']!r}")
                continue
        elif meta_t:
            err("Meta sin Objetivo")
            continue
        meta = None
        if meta_t:
            meta = next((m for m in objetivo.metas if norm_texto(m.nombre) == meta_t), None)
            if meta is None and meta_tolerante:
                advertencias.append(
                    {"fila": fila, "Id": ind, "version_id": ver,
                     "motivo": f"Meta no coincide con la taxonomía: {str(row['Meta'])[:80]!r}"}
                )
            elif meta is None:
                err(f"Meta no pertenece al objetivo {objetivo.id!r}: {row['Meta']!r}")
                continue

        if "PDI" in df.columns:
            motivo = regla_meta(parse_flag01(row["PDI"]) or 0, bool(meta_t), ver)  # PDI vacío = 0 (de proceso)
            if motivo:
                incumplimientos.append({"fila": fila, "Id": ind, "version_id": ver, "motivo": motivo})

        clave = (ind, ver, meta.id if meta else (objetivo.id if objetivo else linea.id))
        if clave in vistos:
            err("asociación repetida")
            continue
        vistos.add(clave)
        validas.append(
            {
                "Id": ind,
                "version_id": ver,
                "linea_id": linea.id,
                "objetivo_id": objetivo.id if objetivo else None,
                "meta_id": meta.id if meta else None,
            }
        )

    cols = ["Id", "version_id", "linea_id", "objetivo_id", "meta_id"]
    return ResultadoAsociacion(
        validas=pd.DataFrame(validas, columns=cols),
        errores=errores,
        advertencias=advertencias,
        incumplimientos=incumplimientos,
    )
