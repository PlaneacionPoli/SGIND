"use client";

import { Treemap, ResponsiveContainer, Tooltip } from "recharts";

export interface FactorTreemapItem {
  factor: string;
  cantidad: number;
  children: Array<{ caracteristica: string; cantidad: number }>;
  color: string;
}

interface PmFactorCaracteristicaTreemapProps {
  data: FactorTreemapItem[];
}

interface TreemapDatum {
  name: string;
  size?: number;
  fill?: string;
  children?: TreemapDatum[];
  [key: string]: unknown;
}

function buildData(data: FactorTreemapItem[]): TreemapDatum[] {
  return data
    .filter((f) => f.children.length > 0)
    .map((f) => ({
      name: f.factor,
      fill: f.color,
      children: f.children.map((c) => ({
        name: c.caracteristica.length > 28 ? `${c.caracteristica.slice(0, 28)}…` : c.caracteristica,
        size: Math.max(c.cantidad, 1),
        fill: f.color,
      })),
    }));
}

export function PmFactorCaracteristicaTreemap({ data }: PmFactorCaracteristicaTreemapProps) {
  const treeData = buildData(data);

  if (!treeData.length) {
    return (
      <div className="flex h-72 items-center justify-center text-sm text-slate-500">
        Sin datos válidos para el mapa de factor y característica
      </div>
    );
  }

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <Treemap data={treeData} dataKey="size" aspectRatio={4 / 3} stroke="#fff" fill="#457B9D">
          <Tooltip
            content={({ payload }) => {
              if (!payload?.length) return null;
              const item = payload[0].payload as { name?: string; size?: number };
              if (item.size == null) return null;
              return (
                <div className="rounded-md border border-slate-200 bg-white px-3 py-2 text-xs shadow-md">
                  <p className="font-semibold text-slate-800">{item.name}</p>
                  <p className="text-slate-600">Indicadores: {item.size}</p>
                </div>
              );
            }}
          />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
}
