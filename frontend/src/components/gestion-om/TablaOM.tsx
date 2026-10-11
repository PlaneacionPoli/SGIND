"use client";

import { Fragment, useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown, Ellipsis, Layers, Pencil, Plus, Trash2, CircleCheck, FileText } from "lucide-react";
import { Paginador } from "@/components/seguimiento/Paginador";
import { Vacio } from "@/components/seguimiento/Panel";
import { tonoCumplimiento } from "@/components/seguimiento/constants";
import type { OMFila } from "@/lib/types";
import {
  CATEGORIA_STYLE,
  ESTADO_OM_STYLE,
  contarPorEstado,
  estadoOM,
  filtrarFilas,
  formatNumero,
  ordenarFilas,
  type ColumnaOM,
  type Orden,
  type Pestana,
} from "./utils";

interface Props {
  filas: OMFila[];
  busqueda: string;
  pestana: Pestana;
  onPestana: (p: Pestana) => void;
  canEdit: boolean;
  canDelete: boolean;
  onRegistrar: (fila: OMFila) => void;
  onVerPlan: (numeroOm: string) => void;
  onCerrar: (fila: OMFila) => void;
  onEliminar: (fila: OMFila) => void;
}

const PESTANAS: Array<{ id: Pestana; etiqueta: string }> = [
  { id: "pendientes", etiqueta: "Pendientes de OM" },
  { id: "en_gestion", etiqueta: "En gestión" },
  { id: "cerradas", etiqueta: "Cerradas" },
  { id: "todos", etiqueta: "Todos" },
];

function Encabezado({ col, etiqueta, orden, onOrden, className = "" }: { col: ColumnaOM; etiqueta: string; orden: Orden; onOrden: (c: ColumnaOM) => void; className?: string }) {
  const activo = orden.por === col;
  const Icono = !activo ? ArrowUpDown : orden.dir === "asc" ? ArrowUp : ArrowDown;
  return (
    <th scope="col" aria-sort={activo ? (orden.dir === "asc" ? "ascending" : "descending") : "none"} className={`px-4 py-3 ${className}`}>
      <button type="button" onClick={() => onOrden(col)} className="inline-flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-slate-500 hover:text-slate-800">
        {etiqueta}
        <Icono className={`h-3 w-3 ${activo ? "text-poli-navy" : "text-slate-300"}`} aria-hidden />
      </button>
    </th>
  );
}

function Resultado({ f }: { f: OMFila }) {
  const tono = tonoCumplimiento(f.cumplimiento_pct);
  return (
    <div className="min-w-[150px]">
      <p className="text-sm font-semibold text-slate-900" style={{ fontVariantNumeric: "tabular-nums" }}>
        {formatNumero(f.ejecucion)}
        <span className="font-normal text-slate-400"> / meta {formatNumero(f.meta)}</span>
      </p>
      {f.cumplimiento_pct != null ? (
        <div className="mt-1.5 flex items-center gap-2">
          <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-100" role="presentation">
            <div className={`h-full rounded-full ${tono.bar}`} style={{ width: `${Math.max(0, Math.min(100, f.cumplimiento_pct))}%` }} />
          </div>
          <span className={`text-xs font-semibold ${tono.text}`} style={{ fontVariantNumeric: "tabular-nums" }}>
            {f.cumplimiento_pct}%
          </span>
        </div>
      ) : (
        <p className="mt-1 text-xs text-slate-400">Sin cumplimiento calculado</p>
      )}
    </div>
  );
}

function Gestion({ f, canEdit, onRegistrar, onVerPlan }: { f: OMFila; canEdit: boolean; onRegistrar: (f: OMFila) => void; onVerPlan: (n: string) => void }) {
  const estado = estadoOM(f);
  if (estado === "sin_om") {
    return canEdit ? (
      <button
        type="button"
        onClick={() => onRegistrar(f)}
        className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-poli-navy px-3 text-xs font-semibold text-white shadow-sm hover:bg-poli-navy/90"
      >
        <Plus className="h-3.5 w-3.5" aria-hidden />
        Registrar OM
      </button>
    ) : (
      <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${ESTADO_OM_STYLE.sin_om.chip}`}>Sin OM</span>
    );
  }
  const st = ESTADO_OM_STYLE[estado];
  return (
    <div className="min-w-[170px] space-y-1.5">
      <div className="flex flex-wrap items-center gap-1.5">
        <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${st.chip}`}>{st.etiqueta}</span>
        <span className="inline-flex items-center gap-1 text-xs text-slate-600">
          <span className="h-2 w-2 rounded-full" style={{ background: f.tipo_accion_color }} aria-hidden />
          {f.tipo_accion}
        </span>
      </div>
      <p className="text-xs text-slate-500">{f.numero_om ? `OM ${f.numero_om}` : "Sin identificador"}</p>
      {f.avance_om != null && (
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-emerald-500" style={{ width: `${Math.min(100, f.avance_om)}%` }} />
          </div>
          <span className="text-xs font-semibold text-slate-700">{f.avance_om}%</span>
        </div>
      )}
      {f.numero_om && (
        <button type="button" onClick={() => onVerPlan(f.numero_om)} className="inline-flex items-center gap-1 text-xs font-semibold text-poli-blue hover:underline">
          <FileText className="h-3 w-3" aria-hidden />
          Ver plan de acción
        </button>
      )}
    </div>
  );
}

export function TablaOM({ filas, busqueda, pestana, onPestana, canEdit, canDelete, onRegistrar, onVerPlan, onCerrar, onEliminar }: Props) {
  const [orden, setOrden] = useState<Orden>({ por: "prioridad", dir: "asc" });
  const [agrupar, setAgrupar] = useState(false);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [menu, setMenu] = useState<{ id: string; top: number; right: number } | null>(null);

  const conteo = useMemo(() => contarPorEstado(filas), [filas]);
  const visibles = useMemo(
    () => ordenarFilas(filtrarFilas(filas, pestana, busqueda), orden, agrupar),
    [filas, pestana, busqueda, orden, agrupar],
  );
  const totalPaginas = Math.max(1, Math.ceil(visibles.length / pageSize));
  const paginaActual = Math.min(page, totalPaginas - 1);
  const pagina = visibles.slice(paginaActual * pageSize, (paginaActual + 1) * pageSize);

  useEffect(() => setPage(0), [pestana, busqueda, filas, pageSize]);

  // Cierra el menú «⋯» con Escape, scroll o clic fuera.
  useEffect(() => {
    if (!menu) return;
    const cerrar = () => setMenu(null);
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && cerrar();
    window.addEventListener("keydown", tecla);
    window.addEventListener("scroll", cerrar, true);
    window.addEventListener("resize", cerrar);
    return () => {
      window.removeEventListener("keydown", tecla);
      window.removeEventListener("scroll", cerrar, true);
      window.removeEventListener("resize", cerrar);
    };
  }, [menu]);

  const cambiarOrden = (col: ColumnaOM) =>
    setOrden((o) => (o.por === col ? { por: col, dir: o.dir === "asc" ? "desc" : "asc" } : { por: col, dir: "asc" }));

  const cantidad: Record<Pestana, number> = {
    pendientes: conteo.sin_om,
    en_gestion: conteo.en_gestion,
    cerradas: conteo.cerrada,
    todos: filas.length,
  };
  const filaMenu = menu ? filas.find((f) => f.id === menu.id) : undefined;
  const mostrarAcciones = canEdit;

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-card" aria-label="Indicadores en riesgo">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-4 pt-3">
        <div role="tablist" aria-label="Estado de la OM" className="flex flex-wrap gap-1">
          {PESTANAS.map((p) => (
            <button
              key={p.id}
              type="button"
              role="tab"
              aria-selected={pestana === p.id}
              onClick={() => onPestana(p.id)}
              className={`-mb-px inline-flex items-center gap-2 border-b-2 px-3 pb-3 pt-1 text-sm font-semibold transition ${
                pestana === p.id ? "border-poli-navy text-poli-navy" : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              {p.etiqueta}
              <span className={`rounded-full px-2 py-0.5 text-xs ${pestana === p.id ? "bg-poli-navy text-white" : "bg-slate-100 text-slate-600"}`}>{cantidad[p.id]}</span>
            </button>
          ))}
        </div>
        <button
          type="button"
          aria-pressed={agrupar}
          onClick={() => setAgrupar((v) => !v)}
          className={`mb-2 inline-flex h-8 items-center gap-1.5 rounded-lg px-3 text-xs font-semibold transition ${agrupar ? "bg-poli-navy text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}
        >
          <Layers className="h-3.5 w-3.5" aria-hidden />
          Agrupar por proceso
        </button>
      </div>

      {visibles.length === 0 ? (
        <div className="p-5">
          <Vacio
            texto={
              filas.length === 0
                ? "No hay indicadores en Peligro con los filtros seleccionados."
                : pestana === "pendientes"
                  ? "No quedan indicadores pendientes de OM con estos filtros."
                  : "Ningún indicador coincide con la pestaña y la búsqueda actuales."
            }
          />
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left">
            <thead className="sticky top-0 bg-slate-50/95 backdrop-blur">
              <tr className="border-b border-slate-200">
                <Encabezado col="id" etiqueta="Id" orden={orden} onOrden={cambiarOrden} />
                <Encabezado col="indicador" etiqueta="Indicador" orden={orden} onOrden={cambiarOrden} />
                <Encabezado col="cumplimiento" etiqueta="Resultado" orden={orden} onOrden={cambiarOrden} />
                <Encabezado col="prioridad" etiqueta="Gestión OM" orden={orden} onOrden={cambiarOrden} />
                {mostrarAcciones && <th scope="col" className="w-12 px-4 py-3"><span className="sr-only">Más acciones</span></th>}
              </tr>
            </thead>
            <tbody>
              {pagina.map((f, i) => {
                const nuevoGrupo = agrupar && (i === 0 || pagina[i - 1].proceso !== f.proceso);
                const cat = CATEGORIA_STYLE[f.categoria] ?? { chip: "bg-slate-100 text-slate-700 ring-slate-200", dot: "bg-slate-400" };
                return (
                  <Fragment key={f.id}>
                    {nuevoGrupo && (
                      <tr className="bg-slate-50">
                        <th colSpan={mostrarAcciones ? 5 : 4} scope="colgroup" className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wider text-slate-500">
                          {f.proceso || "Sin proceso"}
                        </th>
                      </tr>
                    )}
                    <tr className="border-b border-slate-100 align-top transition hover:bg-slate-50/70">
                      <td className="whitespace-nowrap px-4 py-3">
                        <span className="inline-flex items-center gap-2">
                          <span className={`h-2.5 w-2.5 rounded-full ${cat.dot}`} title={f.categoria} aria-hidden />
                          <span className="font-mono text-xs text-slate-600">{f.id}</span>
                          <span className="sr-only">{f.categoria}</span>
                        </span>
                      </td>
                      <td className="min-w-[280px] max-w-[460px] px-4 py-3">
                        <p className="text-sm font-semibold leading-snug text-slate-900">{f.indicador}</p>
                        <p className="mt-0.5 text-xs text-slate-500">
                          {[f.proceso, f.subproceso && f.subproceso !== f.proceso ? f.subproceso : null].filter(Boolean).join(" · ")}
                          {f.periodicidad ? ` · ${f.periodicidad}` : ""}
                        </p>
                        <span className={`mt-1.5 inline-flex rounded-md px-1.5 py-0.5 text-[11px] font-semibold ring-1 ${cat.chip}`}>{f.categoria}</span>
                      </td>
                      <td className="px-4 py-3">
                        <Resultado f={f} />
                      </td>
                      <td className="px-4 py-3">
                        <Gestion f={f} canEdit={canEdit} onRegistrar={onRegistrar} onVerPlan={onVerPlan} />
                      </td>
                      {mostrarAcciones && (
                        <td className="px-2 py-3">
                          {estadoOM(f) !== "sin_om" && (
                            <button
                              type="button"
                              aria-label={`Más acciones del indicador ${f.id}`}
                              aria-haspopup="menu"
                              aria-expanded={menu?.id === f.id}
                              onClick={(e) => {
                                const r = e.currentTarget.getBoundingClientRect();
                                setMenu(menu?.id === f.id ? null : { id: f.id, top: r.bottom + 4, right: window.innerWidth - r.right });
                              }}
                              className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100"
                            >
                              <Ellipsis className="h-4 w-4" aria-hidden />
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {visibles.length > 0 && (
        <Paginador page={paginaActual} pageSize={pageSize} total={visibles.length} onPage={setPage} onPageSize={setPageSize} sizes={[10, 25, 50]} etiqueta="indicadores" />
      )}

      {menu && filaMenu && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setMenu(null)} aria-hidden />
          <div role="menu" style={{ top: menu.top, right: menu.right }} className="fixed z-50 w-48 rounded-xl border border-slate-200 bg-white p-1 shadow-lg">
            <button role="menuitem" type="button" onClick={() => { setMenu(null); onRegistrar(filaMenu); }} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-100">
              <Pencil className="h-4 w-4" aria-hidden /> Editar registro
            </button>
            {estadoOM(filaMenu) === "en_gestion" && (
              <button role="menuitem" type="button" onClick={() => { setMenu(null); onCerrar(filaMenu); }} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-100">
                <CircleCheck className="h-4 w-4" aria-hidden /> Cerrar OM
              </button>
            )}
            {canDelete && filaMenu.om_id != null && (
              <button role="menuitem" type="button" onClick={() => { setMenu(null); onEliminar(filaMenu); }} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-rose-700 hover:bg-rose-50">
                <Trash2 className="h-4 w-4" aria-hidden /> Eliminar
              </button>
            )}
          </div>
        </>
      )}
    </section>
  );
}
