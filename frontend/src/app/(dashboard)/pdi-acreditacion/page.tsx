"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { KPICard } from "@/components/ui/KPICard";
import { fetchPDIDashboard } from "@/lib/api";
import { fmtValorSigno } from "@/lib/formatValor";
import { useAuthReady } from "@/stores/auth-store";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

const NIVEL_COLOR: Record<string, string> = {
  Sobrecumplimiento: "#3b82f6",
  Cumplimiento: "#22c55e",
  Alerta: "#f59e0b",
  Peligro: "#ef4444",
  "Sin dato": "#94a3b8",
};

const PLOT_BASE = {
  margin: { l: 50, r: 20, t: 20, b: 80 },
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  xaxis: { tickangle: -35 },
  legend: { orientation: "h" as const, y: -0.3 },
};

export default function PDIAcreditacionPage() {
  const { isAuthenticated } = useAuthReady();
  const [estado, setEstado] = useState("Todos");
  const [macro, setMacro] = useState("Todos");
  const [horizonte, setHorizonte] = useState("");

  const query = useQuery({
    queryKey: ["pdi-dashboard", estado, macro, horizonte],
    queryFn: () =>
      fetchPDIDashboard({
        ...(estado !== "Todos" ? { estado } : {}),
        ...(macro !== "Todos" ? { macro } : {}),
        ...(horizonte ? { horizonte } : {}),
      }),
    enabled: isAuthenticated,
  });

  const data = query.data;

  const benchmarkTraces = [
    {
      type: "bar" as const,
      name: "Cumplimiento",
      x: (data?.benchmark ?? []).map((b) => b.proceso),
      y: (data?.benchmark ?? []).map((b) => b.cumplimiento),
      marker: { color: NIVEL_COLOR.Cumplimiento },
    },
    {
      type: "bar" as const,
      name: "Benchmark (ref)",
      x: (data?.benchmark ?? []).map((b) => b.proceso),
      y: (data?.benchmark ?? []).map((b) => b.benchmark),
      marker: { color: NIVEL_COLOR.Alerta },
    },
  ];

  const procesosUnicos = Array.from(new Set((data?.evolucion_brechas ?? []).map((e) => e.proceso)));
  const evolucionTraces = procesosUnicos.map((proc) => {
    const pts = (data?.evolucion_brechas ?? []).filter((e) => e.proceso === proc);
    return {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: proc,
      x: pts.map((p) => p.periodo),
      y: pts.map((p) => p.brecha),
    };
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">PDI / Acreditación</h2>
        <p className="mt-1 text-slate-600">
          Panel de cumplimiento, brechas y matriz de acreditación — Gestión y Acreditación (Nivel 2).
        </p>
      </div>

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver el módulo de acreditación.</p>
      ) : query.isLoading ? (
        <div className="h-40 animate-pulse rounded-lg bg-slate-200" />
      ) : data?.error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          {data.error}
        </div>
      ) : (
        <>
          {/* Filtros */}
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">Filtros</p>
            <div className="grid gap-3 sm:grid-cols-3">
              <FilterSelect
                label="Estado"
                value={estado}
                options={data?.filtros.estados ?? []}
                allLabel="Todos los estados"
                onChange={setEstado}
              />
              <FilterSelect
                label="Macrolínea"
                value={macro}
                options={data?.filtros.macros ?? []}
                allLabel="Todas las macrolíneas"
                onChange={setMacro}
              />
              <div>
                <p className="mb-1 text-xs font-medium text-slate-500">Horizonte</p>
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={horizonte}
                  onChange={(e) => setHorizonte(e.target.value)}
                >
                  <option value="">Todos los horizontes</option>
                  {(data?.filtros.horizontes ?? []).map((h) => (
                    <option key={h} value={h}>
                      {h}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {(estado !== "Todos" || macro !== "Todos" || horizonte) && (
              <p className="mt-2 text-xs text-slate-500">
                Filtros activos:{" "}
                {[
                  estado !== "Todos" && `Estado: ${estado}`,
                  macro !== "Todos" && `Macrolínea: ${macro}`,
                  horizonte && `Horizonte: ${horizonte}`,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            )}
          </div>

          {/* KPIs */}
          <div className="grid gap-4 sm:grid-cols-3">
            <KPICard label="Indicadores" value={data?.kpis.total ?? 0} />
            <KPICard
              label="Cumplimiento promedio"
              value={data?.kpis.cumplimiento_promedio != null ? `${data.kpis.cumplimiento_promedio}%` : "—"}
            />
            <KPICard
              label="Brecha promedio (pp)"
              value={data?.kpis.brecha_promedio != null ? String(data.kpis.brecha_promedio) : "—"}
            />
          </div>

          {/* Treemap: Árbol de Objetivos */}
          {(data?.treemap?.length ?? 0) > 3 ? (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="mb-3 text-sm font-bold text-slate-800">
                Árbol de Objetivos (Macrolínea → Objetivo → Indicador)
              </h3>
              <TreemapChart data={data!.treemap} />
            </div>
          ) : (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500">
              Sin datos suficientes para el árbol de objetivos con el filtro actual.
            </div>
          )}

          {/* Benchmark */}
          {(data?.benchmark?.length ?? 0) > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="mb-3 text-sm font-bold text-slate-800">
                Comparativa vs Benchmark por proceso
              </h3>
              <Plot
                data={benchmarkTraces}
                layout={{ ...PLOT_BASE, barmode: "group" }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: "100%", height: 340 }}
                useResizeHandler
              />
            </div>
          )}

          {/* Evolución de brechas */}
          {evolucionTraces.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="mb-3 text-sm font-bold text-slate-800">
                Evolución de brechas promedio por periodo
              </h3>
              <Plot
                data={evolucionTraces}
                layout={PLOT_BASE}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: "100%", height: 340 }}
                useResizeHandler
              />
            </div>
          )}

          {/* Matriz de acreditación */}
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <h3 className="border-b border-slate-100 px-4 py-3 text-sm font-bold text-slate-800">
              Matriz de acreditación
            </h3>
            {(data?.tabla?.length ?? 0) === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-slate-500">
                No hay datos para el filtro seleccionado.
              </p>
            ) : (
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    {["Id", "Indicador", "Macrolínea", "Objetivo", "% Cumpl.", "Meta", "Ejecución", "Estado", "Brecha"].map(
                      (h) => (
                        <th key={h} className="px-3 py-2">
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(data?.tabla ?? []).map((row, i) => {
                    const estadoVal = String(row.Estado ?? "");
                    const bg = (row.estado_color as string) ?? NIVEL_COLOR[estadoVal] ?? "#94a3b8";
                    return (
                      <tr key={i} className="hover:bg-slate-50">
                        <td className="px-3 py-2 font-mono text-xs">{String(row.Id ?? "")}</td>
                        <td className="max-w-xs truncate px-3 py-2">{String(row.Indicador ?? "")}</td>
                        <td className="px-3 py-2">{String(row.Linea ?? "")}</td>
                        <td className="max-w-[180px] truncate px-3 py-2">{String(row.Objetivo ?? "")}</td>
                        <td className="px-3 py-2">
                          {row.cumplimiento_pct != null ? `${row.cumplimiento_pct}%` : "—"}
                        </td>
                        <td className="px-3 py-2">{fmtValorSigno(row.Meta as number | null, String(row.Meta_Signo ?? row.EjecS ?? "%"), row.Decimales_Meta as number | null)}</td>
                        <td className="px-3 py-2">{fmtValorSigno(row.Ejecucion as number | null, String(row.Ejecucion_s ?? row.EjecS ?? "%"), row.Decimales_Ejecucion as number | null)}</td>
                        <td className="px-3 py-2">
                          <span
                            className="rounded-full px-2 py-0.5 text-xs font-medium text-white"
                            style={{ backgroundColor: bg }}
                          >
                            {estadoVal}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          {row.brecha != null ? Number(row.brecha).toFixed(1) : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
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
  allLabel,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  allLabel: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <p className="mb-1 text-xs font-medium text-slate-500">{label}</p>
      <select
        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="Todos">{allLabel}</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  );
}

function TreemapChart({
  data,
}: {
  data: Array<{
    id: string;
    label: string;
    parent: string;
    value: number;
    color?: string;
    color_value?: number | null;
  }>;
}) {
  return (
    <Plot
      data={[
        {
          type: "treemap",
          ids: data.map((d) => d.id),
          labels: data.map((d) => d.label),
          parents: data.map((d) => d.parent),
          values: data.map((d) => d.value),
          marker: {
            colors: data.map((d) => d.color_value ?? 50),
            colorscale: [
              [0, "#ef4444"],
              [0.58, "#f59e0b"],
              [0.77, "#22c55e"],
              [1, "#3b82f6"],
            ],
            cmin: 0,
            cmax: 130,
            showscale: true,
          },
          textinfo: "label",
          hovertemplate: "<b>%{label}</b><extra></extra>",
        },
      ]}
      layout={{
        margin: { l: 10, r: 10, t: 10, b: 10 },
        paper_bgcolor: "rgba(0,0,0,0)",
        height: 420,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
      useResizeHandler
    />
  );
}
