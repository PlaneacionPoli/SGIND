"use client";

import { useMemo, useState } from "react";
import type { CMIProcesoBar, CMIProcesoComparativa, CMIProcesoDetalle, CMIProcesoTipoCard, CMIUnidadDetalle } from "@/lib/types";
import { CmiCumplimientoHorizBarPlotly } from "@/components/cmi/CmiCumplimientoHorizBarPlotly";
import { CmiProcesosBarPlotly } from "@/components/cmi/CmiProcesosBarPlotly";
import { fmtPct } from "@/components/cmi/nivelUtils";

const PAGE_SIZE = 10;

interface CmiProcesosUnidadesTabProps {
  unidades: CMIUnidadDetalle[];
  procesoBars: CMIProcesoBar[];
  tipoCards: CMIProcesoTipoCard[];
  procesos: CMIProcesoDetalle[];
  comparativa: CMIProcesoComparativa[];
  baseAnio: number;
}

export function CmiProcesosUnidadesTab({
  unidades,
  procesoBars,
  tipoCards,
  procesos,
  comparativa,
  baseAnio,
}: CmiProcesosUnidadesTabProps) {
  const [tipoFiltro, setTipoFiltro] = useState("Todos");
  const [page, setPage] = useState(0);
  const [expanded, setExpanded] = useState<string | null>(null);

  const tipos = useMemo(() => {
    const set = new Set(comparativa.map((c) => c.tipo_proceso).filter(Boolean));
    return ["Todos", ...Array.from(set).sort()];
  }, [comparativa]);

  const comparativaFiltrada = useMemo(() => {
    if (tipoFiltro === "Todos") return comparativa;
    return comparativa.filter((c) => c.tipo_proceso === tipoFiltro);
  }, [comparativa, tipoFiltro]);

  const barsFiltrados = useMemo(() => {
    const tipoByProceso = new Map(comparativa.map((c) => [c.proceso, c.tipo_proceso]));
    const source = procesoBars.length ? procesoBars : comparativa.map((c) => ({
      proceso: c.proceso,
      cumplimiento: c.cumplimiento,
      cumplimiento_anterior: c.cumplimiento_anterior,
      color: c.color,
      n_indicadores: c.n_indicadores,
    }));
    if (tipoFiltro === "Todos") return source;
    return source.filter((b) => tipoByProceso.get(b.proceso) === tipoFiltro);
  }, [procesoBars, comparativa, tipoFiltro]);

  const tipoCardsFiltradas = useMemo(() => {
    if (tipoFiltro === "Todos") return tipoCards;
    return tipoCards.filter((c) => c.tipo === tipoFiltro);
  }, [tipoCards, tipoFiltro]);

  const totalPages = Math.max(1, Math.ceil(comparativaFiltrada.length / PAGE_SIZE));
  const pageRows = comparativaFiltrada.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="space-y-6">
      {tipoCards.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {(tipoFiltro === "Todos" ? tipoCards : tipoCardsFiltradas).map((card) => (
            <div
              key={card.tipo}
              className="rounded-2xl border border-slate-200 p-4 shadow-[0_2px_12px_rgba(26,58,92,0.06)]"
              style={{ backgroundColor: card.color_light, borderTopWidth: 4, borderTopColor: card.color }}
            >
              <div className="flex items-center gap-2">
                <span className="text-xl">{card.icon}</span>
                <span className="text-sm font-bold" style={{ color: card.color }}>
                  {card.tipo}
                </span>
              </div>
                <p className="mt-3 text-2xl font-bold text-slate-900">
                  {fmtPct(card.cumplimiento)}
                </p>
              <p className="text-xs text-slate-600">
                {card.n_indicadores} indicadores · {card.n_riesgo} en riesgo
              </p>
            </div>
          ))}
        </div>
      )}

      <div>
        <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-500">
          Tipo de proceso (gráfica)
        </p>
        <div className="inline-flex flex-wrap gap-1 rounded-xl bg-slate-100 p-1">
          {tipos.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => {
                setTipoFiltro(t);
                setPage(0);
              }}
              className={`rounded-lg px-3 py-2 text-xs font-semibold sm:text-sm ${
                tipoFiltro === t ? "bg-poli-navy text-white shadow-md" : "text-slate-600 hover:bg-white"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_2px_12px_rgba(26,58,92,0.06)]">
          <h4 className="mb-4 text-sm font-bold text-slate-800">Análisis por unidad</h4>
          <CmiCumplimientoHorizBarPlotly
            data={unidades.map((u) => ({
              label: u.unidad,
              value: u.cumplimiento_promedio,
              color: u.color ?? "#9E9E9E",
            }))}
            emptyMessage="No hay unidades para el corte global"
          />
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_2px_12px_rgba(26,58,92,0.06)]">
          <h4 className="mb-4 text-sm font-bold text-slate-800">
            Procesos con mayor cumplimiento {baseAnio ? `(vs ${baseAnio})` : ""}
          </h4>
          <CmiProcesosBarPlotly data={barsFiltrados} baseAnio={baseAnio} maxHeight={360} />
        </div>
      </div>

      <section>
        <h3 className="mb-4 text-lg font-semibold text-slate-800">Ranking de unidades</h3>
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Unidad</th>
                <th className="px-4 py-3 text-right">Indicadores</th>
                <th className="px-4 py-3 text-right">Cumpl. %</th>
                <th className="px-4 py-3 text-right">Críticos</th>
                <th className="px-4 py-3 text-center">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {unidades.map((u) => (
                <tr key={u.unidad} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-800">{u.unidad}</td>
                  <td className="px-4 py-3 text-right">{u.n_indicadores}</td>
                  <td className="px-4 py-3 text-right font-semibold" style={{ color: u.estado_color }}>
                    {fmtPct(u.cumplimiento_promedio)}
                  </td>
                  <td className="px-4 py-3 text-right text-red-700">{u.n_criticos ?? 0}</td>
                  <td className="px-4 py-3 text-center">
                    <span title={u.estado}>
                      {u.estado_icon} <span className="text-xs text-slate-600">{u.estado}</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h3 className="mb-4 text-lg font-semibold text-slate-800">Tabla comparativa de procesos</h3>
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Proceso</th>
                <th className="px-4 py-3 text-right">Cumpl. actual</th>
                <th className="px-4 py-3 text-right">Cumpl. {baseAnio}</th>
                <th className="px-4 py-3 text-right">Variación</th>
                <th className="px-4 py-3 text-right">Indicadores</th>
                <th className="px-4 py-3 text-right">Críticos</th>
                <th className="px-4 py-3 text-center">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {pageRows.map((row) => (
                <tr key={row.proceso} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <span
                      className="rounded-full px-2 py-0.5 text-xs font-bold text-white"
                      style={{ backgroundColor: row.tipo_color }}
                    >
                      {row.tipo_proceso}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-800">{row.proceso}</td>
                  <td className="px-4 py-3 text-right font-semibold" style={{ color: row.color }}>
                    {fmtPct(row.cumplimiento)}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-600">
                    {fmtPct(row.cumplimiento_anterior)}
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-bold ${
                      (row.variacion ?? 0) >= 0 ? "text-emerald-700" : "text-red-700"
                    }`}
                  >
                    {row.variacion != null ? `${row.variacion > 0 ? "+" : ""}${row.variacion} pp` : "—"}
                  </td>
                  <td className="px-4 py-3 text-right">{row.n_indicadores}</td>
                  <td className="px-4 py-3 text-right text-red-700">{row.n_criticos}</td>
                  <td className="px-4 py-3 text-center">
                    {row.estado_icon} <span className="text-xs" style={{ color: row.estado_color }}>{row.estado}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 flex items-center justify-between text-sm text-slate-600">
          <span>
            {comparativaFiltrada.length} procesos · página {page + 1} de {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              className="rounded border border-slate-200 px-3 py-1 disabled:opacity-40"
            >
              Anterior
            </button>
            <button
              type="button"
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              className="rounded border border-slate-200 px-3 py-1 disabled:opacity-40"
            >
              Siguiente
            </button>
          </div>
        </div>
      </section>

      <section>
        <details className="rounded-xl border border-slate-200 bg-white">
          <summary className="cursor-pointer px-4 py-3 text-sm font-semibold text-slate-800">
            Detalle por subproceso ({procesos.length} procesos)
          </summary>
          <div className="space-y-2 border-t border-slate-100 p-3">
          {procesos.map((p) => (
            <div key={p.proceso} className="overflow-hidden rounded-xl border border-slate-200 bg-white">
              <button
                type="button"
                onClick={() => setExpanded(expanded === p.proceso ? null : p.proceso)}
                className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left hover:bg-slate-50"
              >
                <div>
                  <p className="font-semibold text-slate-900">{p.proceso}</p>
                  <p className="text-xs text-slate-500">
                    {p.unidad || "Sin unidad"} · {p.tipo_proceso || "Sin tipo"} · {p.total_indicadores}{" "}
                    indicadores
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-poli-navy">{fmtPct(p.cumplimiento_promedio)}</p>
                  <p className="text-xs text-amber-700">{p.en_riesgo} en riesgo</p>
                </div>
              </button>
              {expanded === p.proceso && p.subprocesos.length > 0 && (
                <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-3">
                  <table className="min-w-full text-left text-sm">
                    <thead className="text-xs uppercase text-slate-500">
                      <tr>
                        <th className="py-2 pr-4">Subproceso</th>
                        <th className="py-2 pr-4 text-right">Indicadores</th>
                        <th className="py-2 pr-4 text-right">Cumpl.</th>
                        <th className="py-2 text-right">Riesgo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {p.subprocesos.map((s) => (
                        <tr key={s.subproceso}>
                          <td className="py-2 pr-4 text-slate-800">{s.subproceso}</td>
                          <td className="py-2 pr-4 text-right">{s.n_indicadores}</td>
                          <td className="py-2 pr-4 text-right">{fmtPct(s.cumplimiento)}</td>
                          <td className="py-2 text-right text-amber-700">{s.en_riesgo}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
          </div>
        </details>
      </section>
    </div>
  );
}
