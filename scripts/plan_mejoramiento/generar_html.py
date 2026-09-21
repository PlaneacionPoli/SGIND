"""Genera un HTML autocontenido del módulo Plan de Mejoramiento.

Lee los Excel fuente con los mismos constructores del backend
(`backend/app/domain/plan_mejoramiento_builders.py`, así las cifras coinciden
con las de la aplicación), precalcula tablas y fichas de detalle, y las embebe
en `plan_mejoramiento_template.html`. El resultado se abre con doble clic, sin
servidor: los filtros, las pestañas, los modales y las gráficas corren en el
navegador.

Fuentes (rutas relativas a --data-root, las mismas que usa el backend):
  raw/Plan de mejoramiento/Indicadores Plan de Mejoramiento.xlsx   (pestaña Indicadores)
  raw/Plan de mejoramiento/Catalogo_Indicadores_Plan_Mejoramiento.xlsx
  output/Resultados_Consolidados_CNA.xlsx, hoja "Metricas"        (pestaña Métricas)

Uso (desde la raíz del repo):
  python scripts/plan_mejoramiento/generar_html.py
  python scripts/plan_mejoramiento/generar_html.py --out ruta/salida.html
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.domain import plan_mejoramiento_builders as pm  # noqa: E402

TEMPLATE = Path(__file__).with_name("plan_mejoramiento_template.html")
DEFAULT_OUT = REPO / "data" / "output" / "Plan_de_Mejoramiento.html"

FUENTES = [
    ("Indicadores Plan de Mejoramiento", pm._PLAN_INDICADORES_PATH),
    ("Catálogo de indicadores del Plan", pm._CATALOGO_PLAN_PATH),
    ("Resultados Consolidados CNA – Métricas", pm._METRICAS_CNA_PATH),
]
TENDENCIAS = ["Toda tendencia", "Creciente", "Decreciente", "Estable"]
SEP = "\x1f"  # separador de la llave de detalle de métrica (el JS usa el mismo)


class ExcelLocal:
    """Lector mínimo con la interfaz que esperan los constructores (data_root, ttl, read_excel)."""

    ttl = 10**9

    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root

    def read_excel(self, rel: str, *, sheet_name=0, header=0, use_cache=True) -> pd.DataFrame:
        return pd.read_excel(self.data_root / rel, sheet_name=sheet_name, header=header, engine="openpyxl")


def vacios_reales(df: pd.DataFrame) -> pd.DataFrame:
    """Los loaders hacen `astype(str)`: con pandas < 3 eso convierte los vacíos en el texto "nan",
    y la lógica que sigue (que espera vacíos reales: subtotales fantasma, Periodicidad/Sentido
    ausentes…) deja de funcionar. Con pandas 3 `astype(str)` conserva los vacíos, así que esto
    hace que el resultado sea el mismo con cualquier versión."""
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].where(df[col] != "nan", None)
    return df


def parchear_loaders() -> None:
    cargar_plan, cargar_metricas = pm._load_plan_indicadores_uncached, pm.load_metricas_raw
    pm._load_plan_indicadores_uncached = lambda excel: vacios_reales(cargar_plan(excel))
    pm.load_metricas_raw = lambda excel: vacios_reales(cargar_metricas(excel))


def limpio(obj: Any) -> Any:
    """Deja el objeto serializable: NaN/None -> null, numpy -> nativo, floats redondeados."""
    if isinstance(obj, dict):
        return {str(k): limpio(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [limpio(v) for v in obj]
    if obj is None or obj is pd.NA:
        return None
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):  # numpy escalar
        obj = obj.item()
    if isinstance(obj, float):
        return None if math.isnan(obj) or math.isinf(obj) else round(obj, 6)
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# Pestaña Indicadores
# ─────────────────────────────────────────────────────────────────────────────


def hist_es(hist: dict[str, Any]) -> dict[str, Any]:
    """El texto del % de cumplimiento sale del backend con punto decimal ("103.2%") mientras el
    resto de la tabla usa coma ("98,0%"): se unifica a coma."""
    for k, v in hist.items():
        if k.startswith("cump_") and v["valor_fmt"] != "—":
            v["valor_fmt"] = v["valor_fmt"].replace(".", ",")
    return hist


def build_indicadores(excel: ExcelLocal) -> dict[str, Any]:
    # El Excel actual trae "Indicador o Métrica" (con tilde) en la hoja maestra, pero el
    # loader solo renombra la variante sin tilde y deja el Tipo en "nan" para las filas
    # que no cruzan con la hoja "Indicadores Real". Se acepta también la variante con tilde.
    pm._PLAN_RENAME.setdefault("Indicador o Métrica", "Tipo")

    df = pm.load_plan_indicadores(excel)
    if df.empty:
        raise SystemExit("No se pudo leer 'Indicadores Plan de Mejoramiento.xlsx' (o está vacío).")
    df = df[~df["Tipo"].isin(["Metrica", "Métrica"])].reset_index(drop=True)
    df = pm.sort_plan_indicadores(df)

    metas = pm.build_plan_indicadores_tabla_metas(df)
    historico = pm.build_plan_indicadores_tabla_historico(df)
    assert len(metas) == len(historico) == len(df)

    filas = []
    for (_, row), m, h in zip(df.iterrows(), metas, historico, strict=True):
        assert m["indicador"] == h["indicador"] == row["Indicador"]
        tipo = row.get("Tipo")
        tipo = None if pd.isna(tipo) or tipo == "" else tipo
        texto_busqueda = " ".join(
            str(row.get(c) if pd.notna(row.get(c)) else "") for c in ("Indicador", "Caracteristica", "Accion_Mejora")
        ).lower()
        filas.append(
            {
                "factor": m["factor"],
                "factor_num": m["factor_num"],
                "caracteristica": m["caracteristica"],
                "caracteristica_num": m["caracteristica_num"],
                "indicador": m["indicador"],
                "tipo": tipo,
                "metas": m["metas"],
                "hist": hist_es({k: h[k] for k in h if k.startswith(("meta_", "ejecucion_", "cump_"))}),
                "q": texto_busqueda,
                "detalle": pm.build_indicador_detalle(row),
            }
        )

    factores = pm.sort_factores(df["Factor"].dropna().unique().tolist())
    return limpio(
        {
            "kpis": pm.build_plan_indicadores_kpis(df),
            "factores": factores,
            "carac_por_factor": {"Todos": pm.build_caracteristicas_cascade(df, None)}
            | {f: pm.build_caracteristicas_cascade(df, f) for f in factores},
            "tipos": sorted(df["Tipo"].dropna().unique().tolist()),
            "filas": filas,
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pestaña Métricas
# ─────────────────────────────────────────────────────────────────────────────


def detalle_metrica(df: pd.DataFrame, factor: str, indicador: str, sub: str | None, grupo: str | None):
    """Misma resolución que PlanMejoramientoService.get_metrica_detalle (la copiamos porque
    importar el servicio arrastra FastAPI/pydantic, que este script no necesita)."""
    # A diferencia del servicio, la comparación ignora espacios repetidos: el desglose se arma
    # con los nombres normalizados ("Brasil - ENTRANTE") pero el Excel trae "Brasil  - ENTRANTE",
    # y con la comparación exacta esas fichas no se encontraban.
    def norm(s: Any) -> str:
        return " ".join(str(s).split())

    base = (df["Factor"] == factor.strip()) & (df["Indicador"] == indicador.strip())
    sub_norm = df["Subindicador"].map(norm)
    if grupo is not None:
        match = df[base & sub_norm.str.casefold().str.startswith(norm(grupo).casefold() + " - ")]
        return pm.build_metrica_detalle(match, consolidado=True, grupo=grupo.strip()) if not match.empty else None
    match = df[base & (sub_norm == norm(sub))] if sub is not None else df[base]
    if match.empty:
        return None
    return pm.build_metrica_detalle(match, consolidado=sub is None and len(match) > 1)


def build_metricas(excel: ExcelLocal) -> dict[str, Any]:
    df = pm.build_metricas_historico(excel)
    if df.empty:
        raise SystemExit("No se pudo leer la hoja 'Metricas' de Resultados_Consolidados_CNA.xlsx.")

    carac = df.groupby(["Factor", "Indicador"])["Caracteristica"].first().to_dict()
    sub_texto = df.groupby(["Factor", "Indicador"])["Subindicador"].apply(
        lambda s: " ".join(sorted({str(x) for x in s.dropna()}))
    ).to_dict()

    # Los filtros del backend (tendencia, texto) actúan sobre filas Subindicador ANTES de agrupar,
    # así que la tabla depende de la tendencia elegida: se precalcula una por opción. Factor y
    # característica son constantes por indicador (verificado), así que se filtran en el navegador.
    assert (df.groupby(["Factor", "Indicador"])["Caracteristica"].nunique() <= 1).all()
    pool: list[dict] = []
    pool_idx: dict[str, int] = {}
    tablas: dict[str, list[int]] = {}
    for t in TENDENCIAS:
        registros = pm.build_metricas_tabla_agrupada(pm.apply_metricas_filters(df, tendencia=t))
        indices = []
        for r in registros:
            r = limpio(r)
            r["c"] = carac[(r["factor"], r["indicador"])]
            r["q"] = f"{r['indicador']} {sub_texto.get((r['factor'], r['indicador']), '')}".lower()
            clave = json.dumps(r, sort_keys=True, ensure_ascii=False)
            if clave not in pool_idx:
                pool_idx[clave] = len(pool)
                pool.append(r)
            indices.append(pool_idx[clave])
        tablas[t] = indices

    # Fichas de detalle para todo lo que se puede abrir desde la tabla.
    pedidos: set[tuple[str, str, str | None, str | None]] = set()
    for r in pool:
        f, i = r["factor"], r["indicador"]
        pedidos.add((f, i, None, None))
        for g in r.get("grupos") or []:
            pedidos.add((f, i, None, g["nombre"]))
            for h in g["hojas"]:
                pedidos.add((f, i, f"{g['nombre']} - {h['subindicador']}", None))
        for d in r.get("desglose") or []:
            pedidos.add((f, i, d["subindicador"], None))
    for (f, i), g in df.groupby(["Factor", "Indicador"]):
        for sub in g["Subindicador"].dropna():
            pedidos.add((f, i, sub, None))

    detalles: dict[str, Any] = {}
    for f, i, sub, grupo in sorted(pedidos, key=lambda p: tuple("" if x is None else x for x in p)):
        d = detalle_metrica(df, f, i, sub, grupo)
        if d is not None:
            detalles[SEP.join([f, i, sub or "", grupo or ""])] = limpio(d)

    faltan = [p for p in pedidos if SEP.join([p[0], p[1], p[2] or "", p[3] or ""]) not in detalles]
    if faltan:
        print(f"  aviso: {len(faltan)} fichas de métrica sin datos (se mostrarán como 'no encontrada').")

    factores = pm.sort_factores(df["Factor"].dropna().unique().tolist())
    return {
        "factores": factores,
        "carac_por_factor": {"Todos": pm.build_caracteristicas_cascade(df, None)}
        | {f: pm.build_caracteristicas_cascade(df, f) for f in factores},
        "tendencias": TENDENCIAS,
        "pool": pool,
        "tablas": tablas,
        "detalles": detalles,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    data_root = args.data_root.resolve()
    parchear_loaders()
    excel = ExcelLocal(data_root)
    for nombre, rel in FUENTES:
        if not (data_root / rel).exists():
            raise SystemExit(f"Falta el Excel fuente '{nombre}': {data_root / rel}")

    print("Leyendo indicadores del plan…")
    indicadores = build_indicadores(excel)
    print(f"  {len(indicadores['filas'])} indicadores")
    print("Construyendo métricas (tarda ~20 s)…")
    metricas = build_metricas(excel)
    print(f"  {len(metricas['tablas']['Toda tendencia'])} métricas, {len(metricas['detalles'])} fichas")

    modificados = [(data_root / rel).stat().st_mtime for _, rel in FUENTES]
    payload = {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "anio_cierre": pm.MAX_ANIO_FILTROS,  # último año cerrado: 2026 es parcial (ver backend)
        "datos_actualizados": datetime.fromtimestamp(max(modificados)).isoformat(timespec="seconds"),
        "fuentes": [
            {"nombre": n, "archivo": Path(rel).name, "modificado": datetime.fromtimestamp((data_root / rel).stat().st_mtime).isoformat(timespec="seconds")}
            for n, rel in FUENTES
        ],
        "ind": indicadores,
        "met": metricas,
    }
    datos = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", datos)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"Listo: {args.out} ({args.out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
