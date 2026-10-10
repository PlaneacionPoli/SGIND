"use client";

import { useEffect, useMemo, useState } from "react";
import { BellRing, Search } from "lucide-react";
import type { SeguimientoAlertaFila } from "@/lib/types";
import { Paginador } from "./Paginador";
import { Panel } from "./Panel";

interface Props {
  referencia: string;
  vencidos: SeguimientoAlertaFila[];
  porVencer: SeguimientoAlertaFila[];
}

function Atraso({ fila, vencido }: { fila: SeguimientoAlertaFila; vencido: boolean }) {
  if (!vencido) {
    return <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-800 ring-1 ring-inset ring-amber-200">Próximo a vencer</span>;
  }
  if (fila.diff_meses === null) {
    return <span className="rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700 ring-1 ring-inset ring-rose-200">Nunca ha reportado</span>;
  }
  const grave = fila.diff_meses >= 6;
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${grave ? "bg-rose-50 text-rose-700 ring-rose-200" : "bg-orange-50 text-orange-700 ring-orange-200"}`}>
      {fila.diff_meses} {fila.diff_meses === 1 ? "mes" : "meses"} sin reportar
    </span>
  );
}

export function AlertasFrecuencia({ referencia, vencidos, porVencer }: Props) {
  const [tab, setTab] = useState<"vencidos" | "por_vencer">("vencidos");
  const [busqueda, setBusqueda] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const filas = tab === "vencidos" ? vencidos : porVencer;
  const filtradas = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return q ? filas.filter((f) => `${f.Indicador} ${f.Proceso} ${f.Id}`.toLowerCase().includes(q)) : filas;
  }, [filas, busqueda]);
  useEffect(() => setPage(0), [tab, busqueda, vencidos, porVencer]);

  if (vencidos.length === 0 && porVencer.length === 0) return null;

  const fecha = new Date(`${referencia}T00:00:00`).toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric" });
  const pagina = filtradas.slice(page * pageSize, (page + 1) * pageSize);

  return (
    <Panel
      titulo="Alertas de periodicidad"
      subtitulo={`Según la frecuencia de cada indicador y su último reporte, al ${fecha}. Respeta el proceso filtrado, no el corte.`}
      icono={BellRing}
      sinPadding
      acciones={
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" aria-hidden />
          <input type="search" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Buscar…" className="h-8 w-48 rounded-lg border border-slate-200 pl-8 pr-3 text-sm" />
        </div>
      }
    >
      <div className="px-5 pb-3">
        <div className="inline-flex rounded-xl bg-slate-100 p-1" role="tablist">
          {(
            [
              ["vencidos", "Vencidos", vencidos.length, "bg-rose-500"],
              ["por_vencer", "Por vencer", porVencer.length, "bg-amber-400"],
            ] as const
          ).map(([key, label, n, punto]) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={tab === key}
              onClick={() => setTab(key)}
              className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-sm font-semibold transition ${tab === key ? "bg-white text-poli-navy shadow-sm" : "text-slate-500 hover:text-slate-800"}`}
            >
              <span className={`h-2 w-2 rounded-full ${punto}`} />
              {label}
              <span className="rounded-full bg-slate-100 px-1.5 text-xs text-slate-600" style={{ fontVariantNumeric: "tabular-nums" }}>{n}</span>
            </button>
          ))}
        </div>
      </div>

      {filtradas.length === 0 ? (
        <p className="border-t border-slate-100 px-5 py-8 text-center text-sm text-slate-500">Sin resultados.</p>
      ) : (
        <ul className="divide-y divide-slate-100 border-t border-slate-100">
          {pagina.map((f) => (
            <li key={f.Id} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-5 py-2.5 hover:bg-slate-50/70">
              <span className="w-10 font-mono text-xs text-slate-400">{f.Id}</span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-slate-800" title={f.Indicador}>{f.Indicador}</p>
                <p className="truncate text-xs text-slate-500">{f.Proceso}</p>
              </div>
              <span className="hidden text-xs text-slate-500 sm:inline">{f.Periodicidad} · último: {f.ultimo_reporte}</span>
              <Atraso fila={f} vencido={tab === "vencidos"} />
            </li>
          ))}
        </ul>
      )}
      <Paginador page={page} pageSize={pageSize} total={filtradas.length} onPage={setPage} onPageSize={(s) => { setPageSize(s); setPage(0); }} sizes={[10, 25, 50]} etiqueta="indicadores" />
    </Panel>
  );
}
