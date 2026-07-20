"use client";

import { Treemap, ResponsiveContainer, Tooltip } from "recharts";

export interface SunburstNode {
  id: string;
  label: string;
  parent: string;
  value: number;
  color?: string;
}

interface SunburstChartProps {
  nodes: SunburstNode[];
}

function buildTreemapData(nodes: SunburstNode[]) {
  const children = nodes.filter((n) => n.parent === "root" && n.id !== "root");
  if (!children.length) {
    const leaf = nodes.find((n) => n.id !== "root");
    if (leaf) {
      return [{ name: leaf.label, size: Math.max(leaf.value, 1), fill: leaf.color ?? "#457B9D" }];
    }
    return [{ name: "Sin datos", size: 1, fill: "#94a3b8" }];
  }
  return children.map((node) => {
    const objetivos = nodes.filter((n) => n.parent === node.id);
    if (objetivos.length) {
      return {
        name: node.label,
        children: objetivos.map((o) => ({
          name: o.label.length > 28 ? `${o.label.slice(0, 28)}…` : o.label,
          size: Math.max(o.value, 1),
          fill: o.color ?? node.color ?? "#457B9D",
          fullLabel: o.label,
          promedio: o.value,
        })),
      };
    }
    return {
      name: node.label,
      size: Math.max(node.value, 1),
      fill: node.color ?? "#457B9D",
      promedio: node.value,
    };
  });
}

export function SunburstChart({ nodes }: SunburstChartProps) {
  const data = buildTreemapData(nodes);

  if (!nodes.length) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-500">
        Sin datos para el gráfico jerárquico
      </div>
    );
  }

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={data}
          dataKey="size"
          aspectRatio={4 / 3}
          stroke="#fff"
          fill="#457B9D"
        >
          <Tooltip
            content={({ payload }) => {
              if (!payload?.length) return null;
              const item = payload[0].payload as {
                fullLabel?: string;
                name?: string;
                promedio?: number;
                size?: number;
              };
              const label = item.fullLabel ?? item.name ?? "";
              const pct = item.promedio ?? item.size;
              return (
                <div className="rounded-md border border-slate-200 bg-white px-3 py-2 text-xs shadow-md">
                  <p className="font-semibold text-slate-800">{label}</p>
                  <p className="text-slate-600">Cumplimiento prom.: {Number(pct).toFixed(1)}%</p>
                </div>
              );
            }}
          />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
}
