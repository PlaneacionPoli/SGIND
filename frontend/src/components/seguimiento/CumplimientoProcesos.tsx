"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronDown, Layers } from "lucide-react";
import type { SeguimientoProcesoCumplimiento } from "@/lib/types";
import { tonoCumplimiento } from "./constants";
import { Paginador } from "./Paginador";
import { Panel, Vacio } from "./Panel";

interface Props {
  procesos: SeguimientoProcesoCumplimiento[];
  /** Proceso seleccionado en el filtro global (resalta la fila). */
  seleccionado: string;
  onSeleccionar: (proceso: string) => void;
}

export function CumplimientoProcesos({ procesos, seleccionado, onSeleccionar }: Props) {
  const [soloPendientes, setSoloPendientes] = useState(true);
  const [abierto, setAbierto] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const visibles = useMemo(() => procesos.filter((p) => !soloPendientes || p.pendientes > 0), [procesos, soloPendientes]);
  useEffect(() => setPage(0), [soloPendientes, procesos]);
  const pagina = visibles.slice(page * pageSize, (page + 1) * pageSize);

  return (
    <Panel
      titulo="Avance por proceso"
      subtitulo="Del menos al más cumplido. Despliegue un proceso para ver qué indicadores le faltan."
      icono={Layers}
      sinPadding
      acciones={
        <label className="flex cursor-pointer items-center gap-2 text-xs font-medium text-slate-600">
          <input type="checkbox" checked={soloPendientes} onChange={(e) => setSoloPendientes(e.target.checked)} className="h-4 w-4 rounded border-slate-300" />
          Solo con pendientes
        </label>
      }
    >
      {visibles.length === 0 ? (
        <div className="px-5 pb-5">
          <Vacio texto={soloPendientes ? "Ningún proceso tiene pendientes en este corte." : "Sin procesos para mostrar."} />
        </div>
      ) : (
        <>
          <ul className="divide-y divide-slate-100 border-t border-slate-100">
            {pagina.map((p) => {
              const exigibles = p.total - p.no_aplica;
              const t = tonoCumplimiento(p.cumplimiento_pct);
              const open = abierto === p.proceso;
              const marcado = seleccionado === p.proceso;
              return (
                <li key={p.proceso} className={marcado ? "bg-poli-blue-50/70" : ""}>
                  <div className="grid grid-cols-[minmax(0,1.3fr)_minmax(0,1.6fr)_auto] items-center gap-x-5 gap-y-1 px-5 py-3 max-md:grid-cols-[1fr_auto]">
                    <button type="button" onClick={() => onSeleccionar(marcado ? "Todos" : p.proceso)} title="Filtrar por este proceso" className="truncate text-left text-sm font-semibold text-slate-800 hover:text-poli-blue">
                      {p.proceso}
                    </button>
                    <div className="max-md:order-3 max-md:col-span-2">
                      <div className="flex h-2 overflow-hidden rounded-full bg-slate-100" role="img" aria-label={`${p.reportados} reportados, ${p.pendientes} pendientes, ${p.no_aplica} no aplica`}>
                        <div className="bg-emerald-500" style={{ width: `${(p.reportados / p.total) * 100}%` }} />
                        <div className="bg-amber-400" style={{ width: `${(p.pendientes / p.total) * 100}%` }} />
                        <div className="bg-slate-300" style={{ width: `${(p.no_aplica / p.total) * 100}%` }} />
                      </div>
                      <p className="mt-1 text-xs text-slate-500">
                        {p.reportados} de {exigibles} reportados
                        {p.pendientes > 0 && <span className="font-semibold text-amber-700"> · {p.pendientes} pendientes</span>}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-16 text-right">
                        <p className={`text-lg font-bold leading-none ${t.text}`} style={{ fontVariantNumeric: "tabular-nums" }}>
                          {p.cumplimiento_pct === null ? "—" : `${Math.round(p.cumplimiento_pct)}%`}
                        </p>
                        <p className={`mt-0.5 text-[11px] ${t.text}`}>{t.label}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setAbierto(open ? null : p.proceso)}
                        disabled={p.pendientes === 0}
                        aria-expanded={open}
                        aria-label={`Ver pendientes de ${p.proceso}`}
                        className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-30"
                      >
                        <ChevronDown className={`h-4 w-4 transition ${open ? "rotate-180" : ""}`} />
                      </button>
                    </div>
                  </div>
                  {open && (
                    <div className="border-t border-amber-100 bg-amber-50/60 px-5 py-3">
                      <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-amber-800">Indicadores pendientes</p>
                      <ul className="space-y-1">
                        {p.indicadores_pendientes.map((i) => (
                          <li key={`${i.Id}-${i.Corte}`} className="flex items-baseline gap-3 text-sm text-slate-800">
                            <span className="w-10 shrink-0 font-mono text-xs text-slate-500">{i.Id}</span>
                            <span className="min-w-0 flex-1">{i.Indicador}</span>
                            <span className="whitespace-nowrap rounded-full bg-white px-2 py-0.5 text-xs text-slate-500 ring-1 ring-inset ring-amber-200">
                              {i.Periodicidad} · {i.Corte}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
          <Paginador page={page} pageSize={pageSize} total={visibles.length} onPage={setPage} onPageSize={(s) => { setPageSize(s); setPage(0); }} sizes={[10, 25, 50]} etiqueta="procesos" />
        </>
      )}
    </Panel>
  );
}
