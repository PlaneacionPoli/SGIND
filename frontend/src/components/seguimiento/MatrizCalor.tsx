"use client";

import { useState } from "react";
import { Grid3x3 } from "lucide-react";
import type { SeguimientoMatrizCalor } from "@/lib/types";
import { TRAMOS_CALOR, tramoCalor } from "./constants";
import { Panel, Vacio } from "./Panel";

interface Props {
  matriz: SeguimientoMatrizCalor;
  corte: { anio: number; mes: number } | null;
  proceso: string;
  onSeleccionar: (proceso: string, anio: number, mes: number) => void;
}

const INICIAL = 15;

export function MatrizCalor({ matriz, corte, proceso, onSeleccionar }: Props) {
  const [todos, setTodos] = useState(false);
  const filas = todos ? matriz.filas : matriz.filas.slice(0, INICIAL);
  const n = matriz.cortes.length;

  return (
    <Panel
      titulo="Mapa de calor: proceso × corte"
      subtitulo={`Cumplimiento de los últimos ${n} cortes. Ordenado del proceso más atrasado al más al día · clic en una celda para ir a ese corte y proceso`}
      icono={Grid3x3}
      acciones={
        <ul className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500" aria-label="Leyenda">
          {TRAMOS_CALOR.map((t) => (
            <li key={t.label} className="inline-flex items-center gap-1.5">
              <span className="h-3 w-3 rounded" style={{ background: t.bg }} />
              {t.label}
            </li>
          ))}
          <li className="inline-flex items-center gap-1.5">
            <span className="h-3 w-3 rounded border border-slate-200 bg-slate-50" />
            No reporta
          </li>
        </ul>
      }
    >
      {matriz.filas.length === 0 ? (
        <Vacio texto="Sin histórico para mostrar." />
      ) : (
        <>
          <div className="overflow-x-auto">
            <div
              className="grid min-w-[44rem] items-center gap-x-1 gap-y-1"
              style={{ gridTemplateColumns: `minmax(11rem,1.7fr) repeat(${n}, minmax(2.5rem,1fr)) 3.5rem` }}
              role="table"
              aria-label="Cumplimiento por proceso y corte"
            >
              <div role="row" className="contents">
                <div role="columnheader" className="sticky left-0 z-10 bg-white pb-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                  Proceso
                </div>
                {matriz.cortes.map((c) => {
                  const activo = corte?.anio === c.anio && corte?.mes === c.mes;
                  return (
                    <div key={c.corte} role="columnheader" className={`pb-1 text-center text-[11px] font-semibold ${activo ? "text-poli-navy" : "text-slate-400"}`}>
                      <span className={activo ? "rounded bg-poli-navy px-1 py-0.5 text-white" : ""}>{c.corte.slice(0, 3)}</span>
                      <span className="block text-[10px] font-normal">{String(c.anio).slice(2)}</span>
                    </div>
                  );
                })}
                <div role="columnheader" className="pb-1 text-center text-[11px] font-bold uppercase tracking-wider text-slate-400">
                  Prom.
                </div>
              </div>

              {filas.map((f) => {
                const sel = f.proceso === proceso;
                return (
                  <div key={f.proceso} role="row" className="contents">
                    <div role="rowheader" className={`sticky left-0 z-10 truncate bg-white py-1 pr-2 text-xs ${sel ? "font-bold text-poli-navy" : "text-slate-700"}`} title={f.proceso}>
                      {f.proceso}
                    </div>
                    {f.celdas.map((c, i) => {
                      const k = matriz.cortes[i];
                      const activo = corte?.anio === k.anio && corte?.mes === k.mes;
                      if (!c) {
                        return (
                          <div key={k.corte} role="cell" className="h-7 rounded-md border border-dashed border-slate-100 bg-slate-50/60" title={`${f.proceso} · ${k.corte}: no reporta`} />
                        );
                      }
                      const t = tramoCalor(c.pct);
                      return (
                        <button
                          key={k.corte}
                          type="button"
                          role="cell"
                          onClick={() => onSeleccionar(f.proceso, k.anio, k.mes)}
                          title={`${f.proceso} · ${k.corte}: ${c.pct}% (${c.pendientes} pendientes)`}
                          className={`h-7 rounded-md text-[11px] font-semibold transition hover:scale-105 hover:shadow-md ${activo ? "ring-2 ring-poli-navy ring-offset-1" : ""}`}
                          style={{ background: t.bg, color: t.fg, fontVariantNumeric: "tabular-nums" }}
                        >
                          {Math.round(c.pct)}
                        </button>
                      );
                    })}
                    <div role="cell" className="text-center text-xs font-bold text-slate-700" style={{ fontVariantNumeric: "tabular-nums" }}>
                      {f.promedio_pct === null ? "—" : `${Math.round(f.promedio_pct)}%`}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          {matriz.filas.length > INICIAL && (
            <div className="mt-4 text-center">
              <button type="button" onClick={() => setTodos((v) => !v)} className="rounded-lg border border-slate-200 px-4 py-1.5 text-sm font-semibold text-slate-600 hover:bg-slate-50">
                {todos ? `Ver solo los ${INICIAL} más atrasados` : `Ver los ${matriz.filas.length} procesos`}
              </button>
            </div>
          )}
        </>
      )}
    </Panel>
  );
}
