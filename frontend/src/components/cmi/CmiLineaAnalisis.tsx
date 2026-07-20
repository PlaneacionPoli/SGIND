"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CMILineaAnalisis, CMILineaDetalle } from "@/lib/types";
import { fmtPct, NivelBadge } from "@/components/cmi/nivelUtils";

interface CmiLineaAnalisisProps {
  linea: CMILineaDetalle;
}

const ICONS: Record<string, string> = {
  success: "✅",
  chart: "📊",
  warning: "⚠️",
  alert: "🚨",
  info: "ℹ️",
};

export function CmiLineaAnalisisPanel({ linea }: CmiLineaAnalisisProps) {
  const analisis: CMILineaAnalisis =
    linea.analisis ?? {
      historico: linea.historico ?? [],
      cumplimiento_actual: linea.cumplimiento_promedio,
      cumplimiento_anterior: null,
      variacion_pp: null,
      periodo_comparacion: "",
      mejoraron: [],
      empeoraron: [],
      indicadores_riesgo: [],
      narrativa: {
        titulo: "Insights y Directrices Estratégicas",
        estado: "",
        estado_color: linea.color,
        estado_icon: "info",
        foco_urgente: "",
        directrices: [],
        texto_html: "Análisis no disponible para esta línea.",
        fuente: "heuristica",
      },
    };

  const { historico, narrativa } = analisis;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <KpiMini
          label="Cumplimiento actual"
          value={fmtPct(analisis.cumplimiento_actual)}
          accent={linea.color}
        />
        <KpiMini
          label={
            analisis.periodo_comparacion
              ? `Corte anterior (${analisis.periodo_comparacion})`
              : "Corte anterior"
          }
          value={
            analisis.cumplimiento_anterior != null
              ? fmtPct(analisis.cumplimiento_anterior)
              : "—"
          }
          accent="#64748B"
        />
        <KpiMini
          label="Variación vs corte anterior"
          value={
            analisis.variacion_pp != null
              ? `${analisis.variacion_pp > 0 ? "+" : ""}${analisis.variacion_pp.toFixed(1)} pp`
              : "—"
          }
          accent={
            analisis.variacion_pp == null
              ? "#94A3B8"
              : analisis.variacion_pp >= 0
                ? "#16A34A"
                : "#DC2626"
          }
        />
      </div>

      {historico.length > 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h4 className="mb-3 text-sm font-semibold text-slate-800">
            Tendencia de Cumplimiento Histórico
          </h4>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={historico} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="periodo" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} domain={[0, "auto"]} unit="%" />
              <Tooltip formatter={(v) => [`${Number(v ?? 0).toFixed(1)}%`, "Cumplimiento"]} />
              <ReferenceLine
                y={100}
                stroke="#6B7280"
                strokeDasharray="4 4"
                label={{ value: "Meta 100%", position: "insideTopRight", fontSize: 10, fill: "#6B7280" }}
              />
              <Line
                type="monotone"
                dataKey="cumplimiento"
                stroke={linea.color}
                strokeWidth={2.5}
                dot={{ r: 4, fill: linea.color }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="rounded-lg border border-dashed border-slate-300 p-4 text-sm text-slate-500">
          No hay histórico para esta línea.
        </p>
      )}

      {(analisis.mejoraron.length > 0 || analisis.empeoraron.length > 0) && (
        <div className="grid gap-4 lg:grid-cols-2">
          <TrendList title="Indicadores que mejoraron" items={analisis.mejoraron} positive />
          <TrendList title="Indicadores que empeoraron" items={analisis.empeoraron} positive={false} />
        </div>
      )}

      {analisis.indicadores_riesgo.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h4 className="mb-3 text-sm font-semibold text-slate-800">Indicadores en riesgo (prioridad)</h4>
          <div className="space-y-3">
            {analisis.indicadores_riesgo.map((ind) => (
              <div key={ind.Id ?? ind.Indicador} className="flex flex-wrap items-center gap-3 text-sm">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-slate-800">{ind.Indicador}</p>
                  {ind.Objetivo && <p className="truncate text-xs text-slate-500">{ind.Objetivo}</p>}
                </div>
                <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.min(100, Number(ind.cumplimiento_pct ?? 0))}%`,
                      backgroundColor:
                        String(ind["Nivel de cumplimiento"]).includes("Peligro") ? "#DC2626" : "#F59E0B",
                    }}
                  />
                </div>
                <span className="w-12 text-right font-bold text-slate-900">
                  {fmtPct(ind.cumplimiento_pct as number | undefined)}
                </span>
                <NivelBadge nivel={ind["Nivel de cumplimiento"] as string | undefined} />
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <h4 className="mb-3 text-sm font-semibold text-slate-800">Análisis Estratégico Automático</h4>
        <div
          className="rounded-xl border bg-gradient-to-br from-white to-slate-50 p-5 shadow-sm"
          style={{ borderLeftWidth: 5, borderLeftColor: narrativa.estado_color }}
        >
          <div className="mb-3 flex items-center gap-2">
            <span className="text-xl">{ICONS[narrativa.estado_icon] ?? "📢"}</span>
            <h5 className="font-bold text-poli-navy">{narrativa.titulo}</h5>
            {narrativa.fuente === "heuristica" && (
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500">
                Análisis heurístico
              </span>
            )}
          </div>
          <div
            className="space-y-2 text-sm leading-relaxed text-slate-700"
            dangerouslySetInnerHTML={{ __html: narrativa.texto_html }}
          />
          {narrativa.directrices.length > 0 && (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-slate-600">
              {narrativa.directrices.map((d) => (
                <li key={d}>{d}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

function KpiMini({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-bold text-slate-900">{value}</p>
      <div className="mt-2 h-1 w-10 rounded-full" style={{ backgroundColor: accent }} />
    </div>
  );
}

function TrendList({
  title,
  items,
  positive,
}: {
  title: string;
  items: Array<{ indicador: string; variacion: number }>;
  positive: boolean;
}) {
  if (!items.length) return null;
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h4 className="mb-3 text-sm font-semibold text-slate-800">{title}</h4>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.indicador} className="flex items-center justify-between gap-2 text-sm">
            <span className="min-w-0 flex-1 truncate text-slate-700">{item.indicador}</span>
            <span
              className={`shrink-0 font-bold ${positive ? "text-emerald-600" : "text-red-600"}`}
            >
              {item.variacion > 0 ? "+" : ""}
              {item.variacion.toFixed(1)} pp
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
