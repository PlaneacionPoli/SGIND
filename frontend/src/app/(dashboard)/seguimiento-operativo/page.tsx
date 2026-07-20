"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { KPICard } from "@/components/ui/KPICard";
import { YearSegmentedControl } from "@/components/ui/YearSegmentedControl";
import { downloadSeguimientoExport, fetchSeguimientoDashboard } from "@/lib/api";
import { useAuthReady } from "@/stores/auth-store";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

export default function SeguimientoOperativoPage() {
  const { isAuthenticated } = useAuthReady();
  const [anio, setAnio] = useState<number | null>(null);
  const [mes, setMes] = useState<number | null>(null);
  const [proceso, setProceso] = useState("Todos");
  const [estado, setEstado] = useState("Todos");
  const [exporting, setExporting] = useState(false);

  const query = useQuery({
    queryKey: ["seguimiento", anio, mes, proceso, estado],
    queryFn: () =>
      fetchSeguimientoDashboard({
        ...(anio != null ? { anio } : {}),
        ...(mes != null ? { mes } : {}),
        ...(proceso !== "Todos" ? { proceso } : {}),
        ...(estado !== "Todos" ? { estado } : {}),
      }),
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (query.data?.filtros && anio == null) {
      setAnio(query.data.filtros.anio_default ?? new Date().getFullYear());
      setMes(query.data.filtros.mes_default ?? 12);
    }
  }, [query.data, anio]);

  const anioEff = anio ?? query.data?.filtros.anio_default ?? new Date().getFullYear();
  const mesEff = mes ?? query.data?.filtros.mes_default ?? 12;
  const data = query.data;

  const chartData = data?.estado_por_proceso ?? [];
  const estadosUnicos = Array.from(new Set(chartData.flatMap((p) => p.estados.map((e) => e.estado))));
  const traces = estadosUnicos.map((est) => ({
    type: "bar" as const,
    name: est,
    x: chartData.map((p) => p.proceso),
    y: chartData.map((p) => p.estados.find((e) => e.estado === est)?.cantidad ?? 0),
    marker: { color: data?.estado_colores?.[est] ?? "#94a3b8" },
  }));

  const handleExport = async () => {
    setExporting(true);
    try {
      await downloadSeguimientoExport({
        anio: anioEff,
        mes: mesEff,
        ...(proceso !== "Todos" ? { proceso } : {}),
        ...(estado !== "Todos" ? { estado } : {}),
      });
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Seguimiento Operativo</h2>
        <p className="mt-1 text-slate-600">
          Vista operativa de reportes mensuales por estado, proceso y periodicidad.
        </p>
      </div>

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver el seguimiento.</p>
      ) : query.isLoading ? (
        <div className="h-40 animate-pulse rounded-lg bg-slate-200" />
      ) : data?.error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{data.error}</div>
      ) : (
        <>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">Filtros de reporte</p>
            <div className="flex flex-wrap items-center gap-4">
              {data?.filtros.anios?.length ? (
                <div>
                  <p className="mb-1 text-xs text-slate-500">Año</p>
                  <YearSegmentedControl years={data.filtros.anios} anio={anioEff} onChange={setAnio} />
                </div>
              ) : null}
              <div>
                <p className="mb-1 text-xs text-slate-500">Mes</p>
                <select
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={mesEff}
                  onChange={(e) => setMes(Number(e.target.value))}
                >
                  <option value={0}>Todos</option>
                  {(data?.filtros.meses ?? []).map((m) => (
                    <option key={m} value={m}>
                      {MESES[m - 1]}
                    </option>
                  ))}
                </select>
              </div>
              <FilterSelect label="Proceso" value={proceso} options={data?.filtros.procesos ?? []} onChange={setProceso} />
              <FilterSelect label="Estado" value={estado} options={data?.filtros.estados ?? []} onChange={setEstado} />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KPICard label="Registros" value={data?.kpis.registros ?? 0} />
            <KPICard label="Reportados" value={data?.kpis.reportados ?? 0} />
            <KPICard label="Pendientes" value={data?.kpis.pendientes ?? 0} />
            <KPICard label="No aplica" value={data?.kpis.no_aplica ?? 0} />
          </div>

          {(data?.alertas.vencidos_total ?? 0) > 0 || (data?.alertas.por_vencer_total ?? 0) > 0 ? (
            <section className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-800">⚠️ Alertas de frecuencia de reporte</h3>
              <div className="grid gap-4 lg:grid-cols-2">
                <AlertTable
                  title={`${data?.alertas.vencidos_total ?? 0} indicadores vencidos`}
                  rows={data?.alertas.vencidos ?? []}
                  variant="danger"
                />
                <AlertTable
                  title={`${data?.alertas.por_vencer_total ?? 0} por vencer`}
                  rows={data?.alertas.por_vencer ?? []}
                  variant="warning"
                />
              </div>
            </section>
          ) : null}

          {chartData.length > 0 ? (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="mb-3 text-sm font-bold text-slate-800">Estado de reportes por proceso</h3>
              <Plot
                data={traces}
                layout={{
                  barmode: "stack",
                  margin: { l: 40, r: 20, t: 20, b: 80 },
                  paper_bgcolor: "rgba(0,0,0,0)",
                  plot_bgcolor: "rgba(0,0,0,0)",
                  xaxis: { tickangle: -35 },
                  legend: { orientation: "h", y: -0.25 },
                }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: "100%", height: 360 }}
                useResizeHandler
              />
            </div>
          ) : null}

          <div className="flex items-center justify-between gap-4">
            <h3 className="text-lg font-semibold text-slate-800">Detalle</h3>
            <button
              type="button"
              onClick={handleExport}
              disabled={exporting}
              className="rounded-lg bg-poli-navy px-4 py-2 text-sm font-semibold text-white hover:bg-poli-navy/90 disabled:opacity-50"
            >
              {exporting ? "Exportando…" : "Descargar Excel"}
            </button>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  {["Id", "Indicador", "Proceso", "Año", "Mes", "Estado", "Periodicidad"].map((h) => (
                    <th key={h} className="px-3 py-2">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(data?.detalle ?? []).slice(0, 200).map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-mono text-xs">{String(row.Id ?? "")}</td>
                    <td className="px-3 py-2">{String(row.Indicador ?? "")}</td>
                    <td className="px-3 py-2">{String(row.Proceso ?? "")}</td>
                    <td className="px-3 py-2">{String(row["Año"] ?? "")}</td>
                    <td className="px-3 py-2">{String(row.Mes ?? "")}</td>
                    <td className="px-3 py-2">
                      <EstadoBadge estado={String(row.Estado ?? "")} colores={data?.estado_colores} />
                    </td>
                    <td className="px-3 py-2">{String(row.Periodicidad ?? "")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <p className="mb-1 text-xs text-slate-500">{label}</p>
      <select
        className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="Todos">Todos</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  );
}

function EstadoBadge({ estado, colores }: { estado: string; colores?: Record<string, string> }) {
  const bg = colores?.[estado] ?? "#94a3b8";
  return (
    <span className="rounded-full px-2 py-0.5 text-xs font-medium text-white" style={{ backgroundColor: bg }}>
      {estado}
    </span>
  );
}

function AlertTable({
  title,
  rows,
  variant,
}: {
  title: string;
  rows: Array<Record<string, string | number | null>>;
  variant: "danger" | "warning";
}) {
  const border = variant === "danger" ? "border-red-200 bg-red-50" : "border-amber-200 bg-amber-50";
  return (
    <div className={`rounded-xl border p-4 ${border}`}>
      <p className="mb-2 text-sm font-bold">{title}</p>
      {rows.length === 0 ? (
        <p className="text-xs text-slate-500">Sin registros</p>
      ) : (
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="py-1">Id</th>
              <th>Indicador</th>
              <th>Meses</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 20).map((r, i) => (
              <tr key={i} className="border-t border-white/50">
                <td className="py-1 font-mono">{String(r.Id ?? "")}</td>
                <td className="max-w-[180px] truncate">{String(r.Indicador ?? "")}</td>
                <td>{String(r.diff_meses ?? "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
