"""Marcos de referencia versionados (PDI y CNA).

Fuente única de los ciclos disponibles: app/data/marcos.toml. Reemplaza el
supuesto implícito de un solo PDI (ANIOS_RANGO, "Cierre PDI 2022-2025", etc.;
ver impact_report.md §2.2). Módulo puro: sin Excel ni FastAPI.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

TipoMarco = Literal["PDI", "CNA"]
TIPOS_MARCO: tuple[str, ...] = ("PDI", "CNA")
ESTADOS_MARCO: tuple[str, ...] = ("activo", "cerrado")

# Dentro del paquete app/ (domain -> app): estable en local y en contenedor,
# igual que pdi_2022_2026.json en narrativa_estrategica_service.
MARCOS_TOML_PATH = Path(__file__).resolve().parent.parent / "data" / "marcos.toml"


@dataclass(frozen=True)
class Marco:
    tipo: str
    version_id: str
    nombre: str
    anio_datos_desde: int
    anio_datos_hasta: int | None
    estado: str
    orden: int = 0
    descripcion: str = ""
    imagen: str | None = None
    hoja_cierre: str | None = None
    taxonomia: str | None = None
    # Módulos del dashboard habilitados para este PDI (vacío = todos si datos_disponibles).
    modulos: tuple[str, ...] = ()
    # De dónde salen los indicadores del PDI: "hoja" (hoja PDI_* del catálogo) o
    # "catalogo" (columnas heredadas del catálogo; solo el PDI 2022-2026, que se conserva igual).
    indicadores_desde: str = "hoja"
    etiqueta_cierre_cfg: str | None = None
    datos_disponibles: bool = False

    @property
    def hoja_asociacion(self) -> str:
        """Hoja del catálogo con los indicadores de este PDI, su marcador 1/0 y los códigos
        de línea/objetivo/meta (p. ej. 'PDI_2026_2030')."""
        return self.version_id.replace("-", "_")

    def sirve(self, modulo: str) -> bool:
        """True si el módulo del dashboard (p. ej. 'resumen-general', 'cmi-estrategico',
        'cmi-procesos') está habilitado para este PDI."""
        return self.datos_disponibles and (not self.modulos or modulo in self.modulos)

    @property
    def etiqueta_cierre(self) -> str:
        """Texto del corte "cierre del PDI" en filtros y reportes."""
        return self.etiqueta_cierre_cfg or f"Cierre {self.nombre}"

    @property
    def anios(self) -> list[int]:
        """Años de datos del marco. Si no tiene fin, no se puede enumerar."""
        if self.anio_datos_hasta is None:
            raise ValueError(f"{self.version_id} no tiene anio_datos_hasta")
        return list(range(self.anio_datos_desde, self.anio_datos_hasta + 1))

    def incluye_anio(self, anio: int) -> bool:
        hasta = self.anio_datos_hasta if self.anio_datos_hasta is not None else 9999
        return self.anio_datos_desde <= anio <= hasta

    def se_traslapa(self, desde: int, hasta: int | None = None) -> bool:
        """True si la vigencia [desde, hasta] cruza los años de datos del marco."""
        fin_marco = self.anio_datos_hasta if self.anio_datos_hasta is not None else 9999
        fin = hasta if hasta is not None else 9999
        return desde <= fin_marco and self.anio_datos_desde <= fin


def parse_marcos(data: dict) -> list[Marco]:
    """Valida y construye los marcos desde el dict del TOML."""
    marcos: list[Marco] = []
    vistos: set[str] = set()
    for raw in data.get("marco", []):
        m = Marco(
            tipo=raw["tipo"],
            version_id=raw["version_id"],
            nombre=raw.get("nombre", raw["version_id"]),
            anio_datos_desde=int(raw["anio_datos_desde"]),
            anio_datos_hasta=(
                int(raw["anio_datos_hasta"]) if raw.get("anio_datos_hasta") is not None else None
            ),
            estado=raw.get("estado", "cerrado"),
            orden=int(raw.get("orden", 0)),
            descripcion=raw.get("descripcion", ""),
            imagen=raw.get("imagen"),
            hoja_cierre=raw.get("hoja_cierre"),
            taxonomia=raw.get("taxonomia"),
            modulos=tuple(raw.get("modulos", ())),
            indicadores_desde=raw.get("indicadores_desde", "hoja"),
            etiqueta_cierre_cfg=raw.get("etiqueta_cierre"),
            datos_disponibles=bool(raw.get("datos_disponibles", False)),
        )
        if m.tipo not in TIPOS_MARCO:
            raise ValueError(f"{m.version_id}: tipo inválido {m.tipo!r}")
        if m.estado not in ESTADOS_MARCO:
            raise ValueError(f"{m.version_id}: estado inválido {m.estado!r}")
        if m.anio_datos_hasta is not None and m.anio_datos_hasta < m.anio_datos_desde:
            raise ValueError(f"{m.version_id}: anio_datos_hasta < anio_datos_desde")
        if m.version_id in vistos:
            raise ValueError(f"version_id duplicado: {m.version_id}")
        vistos.add(m.version_id)
        marcos.append(m)

    for tipo in TIPOS_MARCO:
        activos = [m for m in marcos if m.tipo == tipo and m.estado == "activo"]
        if len(activos) > 1:
            raise ValueError(f"Más de un marco {tipo} activo: {[m.version_id for m in activos]}")
    return sorted(marcos, key=lambda m: (m.tipo, m.orden, m.anio_datos_desde))


@lru_cache
def load_marcos(path: Path = MARCOS_TOML_PATH) -> tuple[Marco, ...]:
    with open(path, "rb") as f:
        return tuple(parse_marcos(tomllib.load(f)))


def get_marcos(tipo: str | None = None) -> list[Marco]:
    return [m for m in load_marcos() if tipo is None or m.tipo == tipo]


def get_marco(version_id: str) -> Marco:
    for m in load_marcos():
        if m.version_id == version_id:
            return m
    raise KeyError(f"Marco desconocido: {version_id}")


def marco_activo(tipo: str = "PDI") -> Marco:
    for m in get_marcos(tipo):
        if m.estado == "activo":
            return m
    raise LookupError(f"No hay marco {tipo} activo")


def marco_por_defecto(tipo: str = "PDI") -> Marco:
    """Marco a usar cuando la API no recibe `pdi`. Se prefiere el que sirve a TODOS los módulos
    (el activo si lo hay; si no, el más reciente): un PDI con solo algunos módulos habilitados
    (p. ej. el 2026-2030 mientras el Resumen General no esté listo) no puede ser el
    predeterminado, o los clientes que aún no envían `pdi` recibirían datos de otro ciclo."""
    con_datos = [m for m in get_marcos(tipo) if m.datos_disponibles]
    if not con_datos:
        raise LookupError(f"No hay marco {tipo} con datos disponibles")
    completos = [m for m in con_datos if not m.modulos] or con_datos
    activos = [m for m in completos if m.estado == "activo"]
    return activos[0] if activos else completos[-1]


def marcos_traslapados(tipo: str, desde: int, hasta: int | None = None) -> list[Marco]:
    """Versiones cuya vigencia cruza [desde, hasta]. Base de la regla de la
    ficha de CMI por Procesos: un indicador que inició en 2023 muestra su
    asociación del PDI 2022-2026 y la del 2026-2030 (impact_report.md D7)."""
    return [m for m in get_marcos(tipo) if m.se_traslapa(desde, hasta)]
