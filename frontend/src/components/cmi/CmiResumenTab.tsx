"use client";

import type { CMIDashboardResponse } from "@/lib/types";
import { CmiBarLineasPlotly } from "@/components/cmi/CmiBarLineasPlotly";
import { CmiDonutNivelPlotly } from "@/components/cmi/CmiDonutNivelPlotly";
import { CmiMetricCard } from "@/components/cmi/CmiMetricCard";
import { CmiVistaRapidaCards } from "@/components/cmi/CmiVistaRapidaCards";

const NIVEL_COLORS: Record<string, string> = {
  Sobrecumplimiento: "#6699FF",
  Cumplimiento: "#43A047",
  Alerta: "#FBAF17",
  Peligro: "#D32F2F",
  "Pendiente de reporte": "#9E9E9E",
};

interface CmiResumenTabProps {
  data: CMIDashboardResponse;
  onVerLinea?: (lineaKey: string) => void;
}

export function CmiResumenTab({ data, onVerLinea }: CmiResumenTabProps) {
  const { kpis, cumplimiento_por_linea, distribucion_nivel, vista_rapida_lineas, insights } = data;
  const topCount = kpis.conteo_estados[kpis.top_nivel] ?? 0;
  const nivelColor = NIVEL_COLORS[kpis.top_nivel] ?? "#1A3A5C";

  return (
    <div className="space-y-8">
      <h3 className="text-xl font-bold text-slate-900">Resumen Desglosado</h3>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <CmiMetricCard
          title="Indicadores PDI"
          value={String(kpis.total)}
          subtitle={`Con cumplimiento: ${kpis.con_dato}`}
          icon="📊"
          color="#1A3A5C"
        />
        <CmiMetricCard
          title="Promedio de Cumplimiento"
          value={`${kpis.promedio}%`}
          subtitle="Sobre la meta institucional"
          icon="📈"
          color="#43A047"
        />
        <CmiMetricCard
          title="Nivel Predominante"
          value={kpis.top_nivel}
          subtitle={`${topCount} de ${kpis.total} indicadores`}
          icon="🏆"
          color={nivelColor}
        />
        <CmiMetricCard
          title="Indicadores en Riesgo"
          value={String(kpis.en_riesgo)}
          subtitle="Requieren atención"
          icon="⚠️"
          color={kpis.en_riesgo > 0 ? "#D32F2F" : "#43A047"}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_2px_12px_rgba(26,58,92,0.06)] lg:col-span-3">
          <h4 className="mb-4 text-sm font-bold text-slate-800">
            Cumplimiento promedio por línea estratégica
          </h4>
          <CmiBarLineasPlotly data={cumplimiento_por_linea} />
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_2px_12px_rgba(26,58,92,0.06)] lg:col-span-2">
          <h4 className="mb-4 text-sm font-bold text-slate-800">Distribución por nivel</h4>
          <CmiDonutNivelPlotly data={distribucion_nivel} total={kpis.total} />
        </div>
      </div>

      <div>
        <h4 className="mb-4 text-sm font-bold text-slate-800">Vista rápida por línea</h4>
        <CmiVistaRapidaCards lineas={vista_rapida_lineas} onVerLinea={onVerLinea} />
      </div>

      <div>
        <h4 className="mb-4 text-sm font-bold text-slate-800">Insights Automáticos</h4>
        <div className="flex flex-col gap-3">
          {insights.map((insight) => (
            <InsightBlock
              key={`${insight.tipo}-${insight.titulo}`}
              tipo={insight.tipo}
              titulo={insight.titulo}
              mensaje={insight.mensaje}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

const INSIGHT_STYLES: Record<
  string,
  { emoji: string; border: string; gradient: string; titleColor: string; countColor: string }
> = {
  peligro: {
    emoji: "🚨",
    border: "#D32F2F",
    gradient: "from-red-100 to-amber-50",
    titleColor: "#B71C1C",
    countColor: "#D32F2F",
  },
  alerta: {
    emoji: "⚠️",
    border: "#FBAF17",
    gradient: "from-amber-50 to-yellow-50",
    titleColor: "#F57F17",
    countColor: "#F57F17",
  },
  positivo: {
    emoji: "✅",
    border: "#43A047",
    gradient: "from-emerald-50 to-blue-50",
    titleColor: "#2E7D32",
    countColor: "#2E7D32",
  },
  excelente: {
    emoji: "🎉",
    border: "#43A047",
    gradient: "from-emerald-50 to-blue-50",
    titleColor: "#2E7D32",
    countColor: "#2E7D32",
  },
  info: {
    emoji: "ℹ️",
    border: "#94A3B8",
    gradient: "from-slate-50 to-slate-100",
    titleColor: "#475569",
    countColor: "#475569",
  },
};

function InsightBlock({
  tipo,
  titulo,
  mensaje,
}: {
  tipo: string;
  titulo: string;
  mensaje: string;
}) {
  const s = INSIGHT_STYLES[tipo] ?? INSIGHT_STYLES.info;
  return (
    <div
      className={`rounded-xl border-l-[5px] bg-gradient-to-r p-4 shadow-[0_2px_6px_rgba(0,0,0,0.06)] ${s.gradient}`}
      style={{ borderLeftColor: s.border }}
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl">{s.emoji}</span>
        <div>
          <p className="text-sm font-bold" style={{ color: s.titleColor }}>
            {titulo}
          </p>
          <p className="mt-1 text-sm text-slate-700">{mensaje}</p>
        </div>
      </div>
    </div>
  );
}
