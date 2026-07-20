"use client";

import dynamic from "next/dynamic";
import type { Layout } from "plotly.js";
import { paletteColor } from "@/components/cmi/cmiChartColors";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface CatalogItem {
  label: string;
  count: number;
}

interface CmiCatalogChartsPlotlyProps {
  periodicidad: CatalogItem[];
  tipoIndicador: CatalogItem[];
}

export function CmiCatalogChartsPlotly({ periodicidad, tipoIndicador }: CmiCatalogChartsPlotlyProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <ChartCard title="Indicadores por periodicidad">
        {periodicidad.length > 0 ? (
          <Plot
            data={[
              {
                type: "pie",
                labels: periodicidad.map((d) => d.label),
                values: periodicidad.map((d) => d.count),
                hole: 0.35,
                textinfo: "label+percent",
                textposition: "inside",
                textfont: { size: 11, color: "#FFFFFF" },
                marker: {
                  colors: periodicidad.map((_, i) => paletteColor(i)),
                  line: { color: "#FFFFFF", width: 2 },
                },
                hovertemplate: "<b>%{label}</b><br>%{value} indicadores<extra></extra>",
              },
            ]}
            layout={pieLayout}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: "100%", height: 260 }}
            useResizeHandler
          />
        ) : (
          <EmptyChart />
        )}
      </ChartCard>

      <ChartCard title="Indicadores por tipo">
        {tipoIndicador.length > 0 ? (
          <Plot
            data={[
              {
                type: "bar",
                orientation: "h",
                y: tipoIndicador.map((d) => d.label),
                x: tipoIndicador.map((d) => d.count),
                marker: {
                  color: tipoIndicador.map((_, i) => paletteColor(i)),
                },
                text: tipoIndicador.map((d) => String(d.count)),
                textposition: "outside",
                hovertemplate: "<b>%{y}</b><br>%{x} indicadores<extra></extra>",
              },
            ]}
            layout={{
              ...pieLayout,
              margin: { l: 120, r: 40, t: 10, b: 20 },
              xaxis: { gridcolor: "#E2E8F0" },
              yaxis: { automargin: true },
              showlegend: false,
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: "100%", height: Math.max(260, tipoIndicador.length * 36) }}
            useResizeHandler
          />
        ) : (
          <EmptyChart />
        )}
      </ChartCard>
    </div>
  );
}

const pieLayout: Partial<Layout> = {
  margin: { l: 10, r: 10, t: 10, b: 10 },
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "inherit", size: 11 },
};

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_2px_12px_rgba(26,58,92,0.06)]">
      <h4 className="mb-4 text-sm font-bold text-slate-800">{title}</h4>
      {children}
    </div>
  );
}

function EmptyChart() {
  return (
    <div className="flex h-48 items-center justify-center text-sm text-slate-500">Sin datos de catálogo</div>
  );
}
