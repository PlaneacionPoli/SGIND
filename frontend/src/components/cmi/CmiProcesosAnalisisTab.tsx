"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Layout } from "plotly.js";
import {
  Brain,
  AlertTriangle,
  ListChecks,
  TrendingUp,
  TrendingDown,
  LineChart as LineChartIcon,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { CMIProcesosDashboardResponse, NarrativaIaProceso } from "@/lib/types";
import { fetchNarrativaIaBorrador, publicarNarrativaIaProceso } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { paletteColor } from "@/components/cmi/cmiChartColors";
import { fmtPct } from "@/components/cmi/nivelUtils";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface CmiProcesosAnalisisTabProps {
  data: CMIProcesosDashboardResponse;
  narrativaIaProceso?: NarrativaIaProceso | null;
  narrativaIaPendiente?: boolean;
}

const ESTADO_LABEL: Record<string, string> = {
  "#16A34A": "Favorable",
  "#2563EB": "Estable",
  "#DC2626": "Crítico",
};

type NarrativaDisplay = {
  titulo: string;
  estado_color: string;
  foco_urgente: string;
  directrices: string[];
  texto_html: string;
  fuenteLabel: string;
  esIA: boolean;
};

export function CmiProcesosAnalisisTab({
  data,
  narrativaIaProceso,
  narrativaIaPendiente,
}: CmiProcesosAnalisisTabProps) {
  const { analisis_avanzado, anio, mes, mes_nombre, filtros_aplicados } = data;
  const av = analisis_avanzado ?? {};
  const narrativaHeuristica = av.narrativa_proceso;
  const historico = useMemo(() => av.historico_indicadores ?? [], [av.historico_indicadores]);
  const variacion = av.variacion_indicadores ?? { mejoraron: [], empeoraron: [] };
  const proceso = filtros_aplicados?.proceso || "Todos";

  const [histId, setHistId] = useState(historico[0]?.id ?? "");

  const histChart = useMemo(() => {
    const item = historico.find((h) => h.id === histId);
    return item?.puntos ?? [];
  }, [historico, histId]);

  const narrativa: NarrativaDisplay | null = narrativaIaProceso
    ? {
        titulo: narrativaIaProceso.titulo,
        estado_color: narrativaIaProceso.estado_color,
        foco_urgente: narrativaIaProceso.foco_urgente,
        directrices: narrativaIaProceso.directrices,
        texto_html: narrativaIaProceso.texto_html,
        fuenteLabel: narrativaIaProceso.revisado_por
          ? `Generado por IA (${narrativaIaProceso.modelo}) · Publicado por ${narrativaIaProceso.revisado_por}`
          : `Generado por IA (${narrativaIaProceso.modelo})`,
        esIA: true,
      }
    : narrativaHeuristica
      ? {
          titulo: narrativaHeuristica.titulo,
          estado_color: narrativaHeuristica.estado_color,
          foco_urgente: narrativaHeuristica.foco_urgente,
          directrices: narrativaHeuristica.directrices,
          texto_html: narrativaHeuristica.texto_html,
          fuenteLabel: "Motor de reglas heurístico SIGP — narrativa IA pendiente de auditoría/publicación",
          esIA: false,
        }
      : null;

  const estadoLabel = narrativa ? (ESTADO_LABEL[narrativa.estado_color] ?? "Diagnóstico") : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2.5 rounded-xl border border-blue-100 bg-blue-50/40 px-4 py-3">
        <Brain className="h-5 w-5 shrink-0 text-poli-navy" />
        <p className="text-sm text-slate-700">
          Diagnóstico generado a partir del catálogo filtrado — corte{" "}
          <span className="font-semibold text-poli-navy">
            {mes_nombre} {anio}
          </span>
          .
        </p>
      </div>

      {narrativa && (
        <section
          className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
          style={{ borderLeftWidth: 6, borderLeftColor: narrativa.estado_color }}
        >
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-5 py-4">
            <div className="flex items-center gap-2.5">
              {narrativa.esIA ? (
                <Sparkles className="h-5 w-5" style={{ color: narrativa.estado_color }} />
              ) : (
                <Brain className="h-5 w-5" style={{ color: narrativa.estado_color }} />
              )}
              <h3 className="text-base font-bold text-slate-900">{narrativa.titulo}</h3>
            </div>
            {estadoLabel && (
              <span
                className="rounded-full px-3 py-1 text-xs font-bold text-white"
                style={{ backgroundColor: narrativa.estado_color }}
              >
                {estadoLabel}
              </span>
            )}
          </div>

          <div className="space-y-4 p-5">
            {narrativa.foco_urgente && (
              <div className="flex items-start gap-2.5 rounded-lg border border-amber-200 bg-amber-50 p-3.5">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-wider text-amber-800">Foco urgente</p>
                  <p className="text-sm text-amber-900">{narrativa.foco_urgente}</p>
                </div>
              </div>
            )}

            <p
              className="text-sm leading-relaxed text-slate-700"
              dangerouslySetInnerHTML={{ __html: narrativa.texto_html }}
            />

            {narrativa.directrices.length > 0 && (
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <ListChecks className="h-3.5 w-3.5" />
                  Directrices recomendadas
                </p>
                <ul className="space-y-1.5">
                  {narrativa.directrices.map((d, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                      <span
                        className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white"
                        style={{ backgroundColor: narrativa.estado_color }}
                      >
                        {i + 1}
                      </span>
                      {d}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <p className="pt-1 text-[11px] text-slate-400">Fuente: {narrativa.fuenteLabel}</p>
          </div>
        </section>
      )}

      <NarrativaIaAuditPanel
        proceso={proceso}
        anio={anio}
        mes={mes}
        pendiente={!!narrativaIaPendiente}
      />

      {(variacion.mejoraron.length > 0 || variacion.empeoraron.length > 0) && (
        <section className="grid gap-4 lg:grid-cols-2">
          <VariationList
            title="Indicadores con mayor mejora"
            icon={<TrendingUp className="h-4 w-4 text-emerald-600" />}
            rows={variacion.mejoraron.slice(0, 3)}
            positive
          />
          <VariationList
            title="Indicadores con mayor riesgo"
            icon={<TrendingDown className="h-4 w-4 text-red-600" />}
            rows={variacion.empeoraron.slice(0, 3)}
            positive={false}
          />
        </section>
      )}

      {historico.length > 0 && (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-3 flex items-center gap-2">
            <LineChartIcon className="h-4 w-4 text-slate-500" />
            <h3 className="text-sm font-bold text-slate-800">Evolución histórica del indicador</h3>
          </div>
          <label className="mb-3 flex flex-col gap-1 text-sm">
            <span className="font-medium text-slate-600">Indicador</span>
            <select
              value={histId}
              onChange={(e) => setHistId(e.target.value)}
              className="max-w-xl rounded-lg border border-slate-200 px-3 py-2"
            >
              {historico.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.indicador}
                </option>
              ))}
            </select>
          </label>
          {histChart.length > 0 && (
            <Plot
              data={[
                {
                  type: "scatter",
                  mode: "lines+markers",
                  x: histChart.map((p) => p.periodo),
                  y: histChart.map((p) => p.cumplimiento),
                  line: { color: "#1A3A5C", width: 2 },
                  marker: {
                    size: 8,
                    color: histChart.map((_, i) => paletteColor(i)),
                  },
                  hovertemplate: "<b>%{x}</b><br>Cumplimiento: %{y:.1f}%<extra></extra>",
                },
              ]}
              layout={
                {
                  margin: { l: 48, r: 24, t: 16, b: 48 },
                  height: 280,
                  paper_bgcolor: "rgba(0,0,0,0)",
                  plot_bgcolor: "rgba(0,0,0,0)",
                  yaxis: { range: [0, 120], ticksuffix: "%", gridcolor: "#E2E8F0" },
                  xaxis: { gridcolor: "#E2E8F0" },
                  shapes: [
                    { type: "line", x0: 0, x1: 1, xref: "paper", y0: 100, y1: 100, line: { color: "#2E7D32", dash: "dot" } },
                    { type: "line", x0: 0, x1: 1, xref: "paper", y0: 80, y1: 80, line: { color: "#F9A825", dash: "dot" } },
                  ],
                  font: { family: "inherit", size: 11 },
                } as Partial<Layout>
              }
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: "100%" }}
              useResizeHandler
            />
          )}
        </section>
      )}
    </div>
  );
}

const AUDITOR_ROLES = new Set(["auditor_ia", "administrador"]);

function NarrativaIaAuditPanel({
  proceso,
  anio,
  mes,
  pendiente,
}: {
  proceso: string;
  anio: number;
  mes: number;
  pendiente: boolean;
}) {
  const role = useAuthStore((s) => s.role);
  const queryClient = useQueryClient();
  const [revisando, setRevisando] = useState(false);

  const puedeAuditar = !!role && AUDITOR_ROLES.has(role);

  const borradorQuery = useQuery({
    queryKey: ["narrativa-ia-borrador", proceso, anio, mes],
    queryFn: () => fetchNarrativaIaBorrador({ proceso, anio, mes }),
    enabled: puedeAuditar && revisando,
  });

  const publicarMutation = useMutation({
    mutationFn: () => publicarNarrativaIaProceso({ proceso, anio, mes }),
    onSuccess: () => {
      setRevisando(false);
      queryClient.invalidateQueries({ queryKey: ["informe-dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["narrativa-ia-borrador", proceso, anio, mes] });
    },
  });

  if (!puedeAuditar || !pendiente) return null;

  const borrador = borradorQuery.data?.borrador;

  return (
    <section className="rounded-xl border-2 border-dashed border-poli-navy/30 bg-blue-50/30 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="h-5 w-5 text-poli-navy" />
          <div>
            <p className="text-sm font-bold text-poli-navy">Auditoría de narrativa IA</p>
            <p className="text-xs text-slate-600">
              Hay un borrador generado por IA pendiente de revisión para este proceso y corte.
            </p>
          </div>
        </div>
        {!revisando && (
          <button
            type="button"
            onClick={() => setRevisando(true)}
            className="rounded-lg border border-poli-navy px-3 py-1.5 text-xs font-semibold text-poli-navy hover:bg-white"
          >
            Revisar borrador
          </button>
        )}
      </div>

      {revisando && (
        <div className="mt-4 space-y-3 border-t border-poli-navy/20 pt-4">
          {borradorQuery.isLoading && <p className="text-sm text-slate-500">Cargando borrador…</p>}
          {borradorQuery.isError && (
            <p className="text-sm text-red-600">No se pudo cargar el borrador.</p>
          )}
          {borrador && (
            <>
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <p className="mb-1 text-sm font-bold text-slate-900">{borrador.titulo}</p>
                <p
                  className="text-sm leading-relaxed text-slate-700"
                  dangerouslySetInnerHTML={{ __html: borrador.texto_html }}
                />
                {borrador.foco_urgente && (
                  <p className="mt-2 text-xs font-semibold text-amber-700">
                    Foco urgente: {borrador.foco_urgente}
                  </p>
                )}
                {borrador.directrices.length > 0 && (
                  <ul className="mt-2 list-inside list-disc text-xs text-slate-600">
                    {borrador.directrices.map((d, i) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                )}
                <p className="mt-2 text-[11px] text-slate-400">Modelo: {borrador.modelo}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => publicarMutation.mutate()}
                  disabled={publicarMutation.isPending}
                  className="rounded-lg bg-poli-navy px-4 py-2 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
                >
                  {publicarMutation.isPending ? "Publicando…" : "Publicar narrativa"}
                </button>
                {publicarMutation.isError && (
                  <span className="text-xs text-red-600">No se pudo publicar.</span>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}

function VariationList({
  title,
  icon,
  rows,
  positive,
}: {
  title: string;
  icon: React.ReactNode;
  rows: Array<{ indicador: string; linea: string; linea_color: string; variacion: number }>;
  positive: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h4 className="mb-3 flex items-center gap-2 text-sm font-bold text-slate-800">
        {icon}
        {title}
      </h4>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-500">Sin datos comparativos.</p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {rows.map((r) => (
            <li key={r.indicador} className="flex items-center justify-between gap-3 py-2.5">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-800">{r.indicador}</p>
                <span
                  className="inline-block rounded px-1.5 py-0.5 text-[10px] font-semibold"
                  style={{ backgroundColor: `${r.linea_color}22`, color: r.linea_color }}
                >
                  {r.linea}
                </span>
              </div>
              <span className={`shrink-0 text-sm font-bold ${positive ? "text-emerald-700" : "text-red-700"}`}>
                {r.variacion > 0 ? "+" : ""}
                {fmtPct(r.variacion)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
