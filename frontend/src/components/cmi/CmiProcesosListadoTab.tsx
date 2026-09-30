"use client";

import { useMemo, useState } from "react";
import { BarChart3, Activity, Search, ExternalLink } from "lucide-react";
import type { Indicator } from "@/lib/types";
import { fmtPct, NivelBadge } from "@/components/cmi/nivelUtils";
import { fmtMeta, fmtEjecucion } from "@/lib/formatValor";

interface CmiProcesosListadoTabProps {
  indicadores: Indicator[];
  summary: Record<string, number>;
  ejecucionVariacion?: {
    positiva: Array<{ indicador: string; ejecucion: number | null; delta: number; periodo: string }>;
    negativa: Array<{ indicador: string; ejecucion: number | null; delta: number; periodo: string }>;
  };
  onOpenFicha?: (id: string) => void;
  onExportCsv?: () => void;
  onExportExcel?: () => void;
  exporting?: boolean;
}

const PAGE_SIZES = [25, 50, 100];

export function CmiProcesosListadoTab({
  indicadores,
  summary,
  ejecucionVariacion,
  onOpenFicha,
  onExportCsv,
  onExportExcel,
  exporting,
}: CmiProcesosListadoTabProps) {
  const [proceso, setProceso] = useState("Todos");
  const [estado, setEstado] = useState("Todos");
  const [busqueda, setBusqueda] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);

  const procesos = useMemo(() => {
    const set = new Set(
      indicadores
        .map((i) => (i as Record<string, unknown>).Proceso_padre as string | undefined)
        .filter(Boolean) as string[]
    );
    return ["Todos", ...Array.from(set).sort()];
  }, [indicadores]);

  const filtered = useMemo(() => {
    return indicadores.filter((ind) => {
      const proc = (ind as Record<string, unknown>).Proceso_padre as string | undefined;
      const nivel = ind["Nivel de cumplimiento"] as string | undefined;
      if (proceso !== "Todos" && proc !== proceso) return false;
      if (estado !== "Todos" && nivel !== estado) return false;
      if (busqueda.trim() && !String(ind.Indicador ?? "").toLowerCase().includes(busqueda.trim().toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [indicadores, proceso, estado, busqueda]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageItems = filtered.slice(page * pageSize, (page + 1) * pageSize);

  const total = summary.total ?? 0;
  const pct = (n: number) => (total > 0 ? `${((n / total) * 100).toFixed(1)}% del total` : "—");

  return (
    <div className="space-y-5">
      <p className="flex items-start gap-1.5 text-xs text-slate-500">
        <span className="mt-0.5 shrink-0 text-slate-400">ℹ️</span>
        Listado filtrado — respeta todos los filtros del panel (año, mes, unidad, proceso, clasificación,
        frecuencia). Columnas de proceso/subproceso, sin líneas estratégicas PDI.
      </p>

      <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-3 lg:grid-cols-6">
        <SummaryCard
          label="Total"
          value={summary.total ?? 0}
          icon={<BarChart3 className="h-[18px] w-[18px] text-slate-400" />}
          hint="Catálogo activo"
        />
        <SummaryCard
          label="Métricas"
          value={summary.metricas ?? 0}
          icon={<Activity className="h-[18px] w-[18px] text-slate-400" />}
          hint="calculadas"
          valueColor="text-poli-navy"
        />
        <SummaryCard
          label="Sobrecumpl."
          value={summary.sobrecumplimiento ?? 0}
          hint={pct(summary.sobrecumplimiento ?? 0)}
          bg="bg-blue-50"
          border="border-blue-200"
          labelColor="text-blue-800"
          valueColor="text-blue-800"
          hintColor="text-blue-700"
          dot="#2563EB"
        />
        <SummaryCard
          label="Cumplimiento"
          value={summary.cumplimiento ?? 0}
          hint={(summary.cumplimiento ?? 0) > 0 ? "Meta alcanzada (100%)" : "Sin registros"}
          bg="bg-emerald-50"
          border="border-emerald-200"
          labelColor="text-emerald-800"
          valueColor="text-emerald-700"
          hintColor="text-emerald-700"
          dot="#16A34A"
        />
        <SummaryCard
          label="Alerta"
          value={summary.alerta ?? 0}
          hint={(summary.alerta ?? 0) > 0 ? pct(summary.alerta ?? 0) : "Sin desvíos leves"}
          bg="bg-amber-50"
          border="border-amber-200"
          labelColor="text-amber-800"
          valueColor="text-amber-700"
          hintColor="text-amber-700"
          dot="#D97706"
        />
        <SummaryCard
          label="Peligro"
          value={summary.peligro ?? 0}
          hint={(summary.peligro ?? 0) > 0 ? `${pct(summary.peligro ?? 0)} (<70%)` : "Sin críticos"}
          bg="bg-red-50"
          border="border-red-200"
          labelColor="text-red-800"
          valueColor="text-red-700"
          hintColor="text-red-700"
          dot="#DC2626"
          accent
          pulse={(summary.peligro ?? 0) > 0}
        />
      </div>

      {ejecucionVariacion &&
        (ejecucionVariacion.positiva.length > 0 || ejecucionVariacion.negativa.length > 0) && (
          <div className="grid gap-4 lg:grid-cols-2">
            <EjecVarTable title="Mayor variación positiva de ejecución" rows={ejecucionVariacion.positiva} positive />
            <EjecVarTable title="Mayor variación negativa de ejecución" rows={ejecucionVariacion.negativa} positive={false} />
          </div>
        )}

      <div className="flex flex-col items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm md:flex-row">
        <div className="flex w-full flex-wrap items-center gap-3 md:w-auto">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-semibold uppercase text-slate-500">Proceso:</span>
            <select
              value={proceso}
              onChange={(e) => {
                setProceso(e.target.value);
                setPage(0);
              }}
              className="h-8 rounded-md border border-slate-200 bg-slate-50 px-2.5 text-xs text-slate-800 focus:border-poli-navy focus:outline-none focus:ring-1 focus:ring-poli-navy"
            >
              {procesos.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-semibold uppercase text-slate-500">Estado:</span>
            <select
              value={estado}
              onChange={(e) => {
                setEstado(e.target.value);
                setPage(0);
              }}
              className="h-8 rounded-md border border-slate-200 bg-slate-50 px-2.5 text-xs text-slate-800 focus:border-poli-navy focus:outline-none focus:ring-1 focus:ring-poli-navy"
            >
              {["Todos", "Sobrecumplimiento", "Cumplimiento", "Alerta", "Peligro", "Pendiente de reporte"].map(
                (e) => (
                  <option key={e} value={e}>
                    {e}
                  </option>
                )
              )}
            </select>
          </div>
          {(onExportCsv || onExportExcel) && (
            <div className="flex gap-2">
              {onExportCsv && (
                <button
                  type="button"
                  onClick={onExportCsv}
                  disabled={exporting}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                  Exportar CSV
                </button>
              )}
              {onExportExcel && (
                <button
                  type="button"
                  onClick={onExportExcel}
                  disabled={exporting}
                  className="rounded-lg bg-poli-navy px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
                >
                  Exportar Excel
                </button>
              )}
            </div>
          )}
        </div>
        <div className="relative w-full md:w-80">
          <input
            type="search"
            value={busqueda}
            onChange={(e) => {
              setBusqueda(e.target.value);
              setPage(0);
            }}
            placeholder="Nombre del indicador..."
            className="h-8 w-full rounded-md border border-slate-200 bg-slate-50 pl-8 pr-3 text-xs text-slate-800 focus:border-poli-navy focus:outline-none focus:ring-1 focus:ring-poli-navy"
          />
          <Search className="pointer-events-none absolute left-2.5 top-2 h-4 w-4 text-slate-400" />
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <th className="px-4 py-3">Indicador</th>
                <th className="px-3 py-3">Proceso</th>
                <th className="px-3 py-3">Subproceso</th>
                <th className="px-2 py-3 text-right">Meta</th>
                <th className="px-2 py-3 text-right">Ejecución</th>
                <th className="px-2 py-3 text-right">Cumpl.</th>
                <th className="px-4 py-3 text-center">Nivel</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {pageItems.map((ind) => {
                const rec = ind as Record<string, unknown>;
                const id = String(ind.Id ?? "");
                const esCritico = ind["Nivel de cumplimiento"] === "Peligro";
                return (
                  <tr
                    key={id || String(ind.Indicador)}
                    className={`group transition-colors hover:bg-slate-50 ${esCritico ? "bg-red-50/30" : ""}`}
                  >
                    <td className="px-4 py-3.5 font-semibold text-poli-navy">
                      {onOpenFicha && id ? (
                        <button
                          type="button"
                          onClick={() => onOpenFicha(id)}
                          className="flex items-center gap-1.5 text-left hover:underline"
                        >
                          <span>{ind.Indicador}</span>
                          <ExternalLink className="h-3.5 w-3.5 text-slate-400 opacity-0 transition-opacity group-hover:opacity-100" />
                        </button>
                      ) : (
                        <span>{ind.Indicador}</span>
                      )}
                    </td>
                    <td className="px-3 py-3.5 text-xs font-medium text-slate-600">
                      {String(rec.Proceso_padre ?? ind.Proceso ?? "—")}
                    </td>
                    <td className="px-3 py-3.5 text-xs text-slate-500">
                      {String(rec.Subproceso_final ?? ind.Subproceso ?? "—")}
                    </td>
                    <td className="px-2 py-3.5 text-right font-medium">{fmtMeta(ind as Record<string, unknown>)}</td>
                    <td className={`px-2 py-3.5 text-right font-semibold ${esCritico ? "text-red-600" : "text-slate-800"}`}>
                      {fmtEjecucion(ind as Record<string, unknown>)}
                    </td>
                    <td className={`px-2 py-3.5 text-right font-bold ${esCritico ? "text-red-600" : "text-poli-navy"}`}>
                      {fmtPct(ind.cumplimiento_pct as number)}
                    </td>
                    <td className="px-4 py-3.5 text-center">
                      <NivelBadge nivel={ind["Nivel de cumplimiento"] as string} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="flex flex-col items-center justify-between gap-3 border-t border-slate-200 bg-slate-50/50 px-4 py-3 text-xs text-slate-500 sm:flex-row">
          <span>
            {filtered.length} indicadores · página {page + 1} de {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(0);
              }}
              className="h-7 rounded border border-slate-200 bg-white px-2 text-xs text-slate-700"
            >
              {PAGE_SIZES.map((s) => (
                <option key={s} value={s}>
                  {s}/pág
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              className="rounded border border-slate-200 bg-white px-2.5 py-1 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Anterior
            </button>
            <button
              type="button"
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              className="rounded border border-slate-200 bg-white px-2.5 py-1 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Siguiente
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  hint,
  icon,
  dot,
  bg = "bg-white",
  border = "border-slate-200",
  labelColor = "text-slate-500",
  valueColor = "text-slate-900",
  hintColor = "text-slate-500",
  accent = false,
  pulse = false,
}: {
  label: string;
  value: number;
  hint?: string;
  icon?: React.ReactNode;
  dot?: string;
  bg?: string;
  border?: string;
  labelColor?: string;
  valueColor?: string;
  hintColor?: string;
  accent?: boolean;
  pulse?: boolean;
}) {
  return (
    <div
      className={`flex flex-col justify-between rounded-xl border p-4 shadow-sm transition-all hover:shadow-md ${bg} ${border} ${
        accent ? "border-l-4 border-l-red-600" : ""
      }`}
    >
      <div className="flex items-center justify-between">
        <span className={`text-[11px] font-bold uppercase tracking-wider ${labelColor}`}>{label}</span>
        {icon}
        {dot && <span className={`h-2.5 w-2.5 rounded-full ${pulse ? "animate-pulse" : ""}`} style={{ backgroundColor: dot }} />}
      </div>
      <p className={`mt-2 text-2xl font-bold ${valueColor}`}>{value}</p>
      {hint && <p className={`mt-1 text-[11px] font-medium ${hintColor}`}>{hint}</p>}
    </div>
  );
}

function EjecVarTable({
  title,
  rows,
  positive,
}: {
  title: string;
  rows: Array<{ indicador: string; ejecucion: number | null; delta: number; periodo: string }>;
  positive: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h4 className="mb-3 text-sm font-bold text-slate-800">{title}</h4>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-500">Sin variación registrada.</p>
      ) : (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-xs uppercase text-slate-500">
              <th className="py-2 text-left">Indicador</th>
              <th className="py-2 text-right">Delta</th>
              <th className="py-2 text-right">Periodo</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={`${r.indicador}-${r.periodo}`} className="border-t border-slate-100">
                <td className="py-2 text-slate-800">{r.indicador}</td>
                <td className={`py-2 text-right font-bold ${positive ? "text-emerald-700" : "text-red-700"}`}>
                  {r.delta > 0 ? "+" : ""}
                  {r.delta}
                </td>
                <td className="py-2 text-right text-slate-500">{r.periodo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
