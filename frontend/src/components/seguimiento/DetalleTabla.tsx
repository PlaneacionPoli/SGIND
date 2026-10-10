"use client";

import { ArrowDown, ArrowUp, ChevronsUpDown, Table2 } from "lucide-react";
import type { SeguimientoColumna } from "@/lib/api";
import type { SeguimientoDetalleFila } from "@/lib/types";
import { ESTADO_STYLE } from "./constants";
import { Paginador } from "./Paginador";
import { Panel, Vacio } from "./Panel";

interface Props {
  filas: SeguimientoDetalleFila[];
  total: number;
  page: number;
  pageSize: number;
  orden: { por: SeguimientoColumna | null; dir: "asc" | "desc" };
  cargando: boolean;
  onPage: (p: number) => void;
  onPageSize: (s: number) => void;
  onOrden: (col: SeguimientoColumna) => void;
}

const COLUMNAS: Array<{ clave: SeguimientoColumna; etiqueta: string; ancho?: string }> = [
  { clave: "Id", etiqueta: "ID", ancho: "w-16" },
  { clave: "Indicador", etiqueta: "Indicador" },
  { clave: "Proceso", etiqueta: "Proceso" },
  { clave: "Periodicidad", etiqueta: "Frecuencia", ancho: "w-32" },
  { clave: "Corte", etiqueta: "Corte", ancho: "w-28" },
  { clave: "Estado", etiqueta: "Estado", ancho: "w-36" },
];

function IconoOrden({ activo, dir }: { activo: boolean; dir: "asc" | "desc" }) {
  if (!activo) return <ChevronsUpDown className="h-3.5 w-3.5 text-slate-300" aria-hidden />;
  return dir === "asc" ? <ArrowUp className="h-3.5 w-3.5 text-poli-blue" aria-hidden /> : <ArrowDown className="h-3.5 w-3.5 text-poli-blue" aria-hidden />;
}

export function DetalleTabla({ filas, total, page, pageSize, orden, cargando, onPage, onPageSize, onOrden }: Props) {
  return (
    <Panel
      titulo="Detalle de reportes"
      subtitulo={orden.por ? "Ordenado por la columna elegida." : "Los pendientes aparecen primero. Haga clic en un encabezado para ordenar."}
      icono={Table2}
      sinPadding
    >
      {total === 0 ? (
        <div className="px-5 pb-5">
          <Vacio texto="Sin registros para este filtro." />
        </div>
      ) : (
        <>
          <div className={`max-h-[34rem] overflow-auto border-t border-slate-100 transition-opacity ${cargando ? "opacity-60" : ""}`}>
            <table className="min-w-full text-left text-sm">
              <thead className="sticky top-0 z-10 bg-slate-50/95 backdrop-blur">
                <tr>
                  {COLUMNAS.map((c) => {
                    const activo = orden.por === c.clave;
                    return (
                      <th
                        key={c.clave}
                        scope="col"
                        aria-sort={activo ? (orden.dir === "asc" ? "ascending" : "descending") : "none"}
                        className={`whitespace-nowrap px-4 py-2.5 ${c.ancho ?? ""}`}
                      >
                        <button type="button" onClick={() => onOrden(c.clave)} className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500 hover:text-slate-900">
                          {c.etiqueta}
                          <IconoOrden activo={activo} dir={orden.dir} />
                        </button>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filas.map((row, i) => {
                  const st = ESTADO_STYLE[row.Estado];
                  return (
                    <tr key={`${row.Id}-${row.Corte}-${i}`} className="hover:bg-slate-50/80">
                      <td className="px-4 py-2.5 font-mono text-xs text-slate-400">{row.Id}</td>
                      <td className="max-w-md px-4 py-2.5 font-medium text-slate-800">{row.Indicador}</td>
                      <td className="max-w-xs px-4 py-2.5 text-slate-600">{row.Proceso}</td>
                      <td className="whitespace-nowrap px-4 py-2.5">
                        <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">{row.Periodicidad}</span>
                      </td>
                      <td className="whitespace-nowrap px-4 py-2.5 text-slate-600">{row.Corte}</td>
                      <td className="whitespace-nowrap px-4 py-2.5">
                        <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${st?.chip ?? "bg-slate-100 text-slate-600 ring-slate-200"}`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${st?.dot ?? "bg-slate-400"}`} />
                          {row.Estado}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <Paginador page={page} pageSize={pageSize} total={total} onPage={onPage} onPageSize={onPageSize} sizes={[25, 50, 100]} />
        </>
      )}
    </Panel>
  );
}
