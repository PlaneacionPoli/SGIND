"use client";

import { useMemo } from "react";
import { STRATEGIC_ICON_MAP } from "@/lib/strategic-icons";
import type { ResumenMindmap, ResumenMindmapLinea, ResumenMindmapSublinea } from "@/lib/types";

interface PdiMindmapProps {
  data: ResumenMindmap;
}

const CENTER_R = 92;
const LINE_R = 52;
const LINE_ORBIT = 230;
const SUB_ORBIT_START = LINE_ORBIT + 110;
const SUB_ORBIT_GAP = 84;
const SUB_W = 176;
const SUB_H = 58;
const PADDING = 40;

const ALERTA_STYLES: Record<ResumenMindmapSublinea["alerta"], { bg: string; text: string; label: string | null }> = {
  ok: { bg: "", text: "#0f172a", label: null },
  alerta: { bg: "#f59e0b", text: "#fff", label: "En Alerta" },
  critica: { bg: "#dc2626", text: "#fff", label: "ALERTA CRÍTICA" },
};

function toRad(deg: number) {
  return (deg * Math.PI) / 180;
}

interface LineNode {
  linea: ResumenMindmapLinea;
  x: number;
  y: number;
  dir: { x: number; y: number };
  subs: Array<{ sub: ResumenMindmapSublinea; x: number; y: number }>;
}

export function PdiMindmap({ data }: PdiMindmapProps) {
  const lineas = data?.lineas ?? [];

  const layout = useMemo(() => {
    const n = Math.max(lineas.length, 1);
    const nodes: LineNode[] = lineas.map((linea, i) => {
      const angleDeg = -90 + (360 / n) * i;
      const rad = toRad(angleDeg);
      const dir = { x: Math.cos(rad), y: Math.sin(rad) };
      const perp = { x: -dir.y, y: dir.x };
      const x = dir.x * LINE_ORBIT;
      const y = dir.y * LINE_ORBIT;

      const subs = (linea.sublineas ?? []).map((sub, j, arr) => {
        const offset = (j - (arr.length - 1) / 2) * SUB_ORBIT_GAP;
        const radius = SUB_ORBIT_START;
        return {
          sub,
          x: dir.x * radius + perp.x * offset,
          y: dir.y * radius + perp.y * offset,
        };
      });

      return { linea, x, y, dir, subs };
    });

    let minX = -CENTER_R;
    let maxX = CENTER_R;
    let minY = -CENTER_R;
    let maxY = CENTER_R;
    for (const node of nodes) {
      minX = Math.min(minX, node.x - LINE_R);
      maxX = Math.max(maxX, node.x + LINE_R);
      minY = Math.min(minY, node.y - LINE_R);
      maxY = Math.max(maxY, node.y + LINE_R);
      for (const s of node.subs) {
        minX = Math.min(minX, s.x - SUB_W / 2);
        maxX = Math.max(maxX, s.x + SUB_W / 2);
        minY = Math.min(minY, s.y - SUB_H / 2);
        maxY = Math.max(maxY, s.y + SUB_H / 2);
      }
    }
    minX -= PADDING;
    minY -= PADDING;
    maxX += PADDING;
    maxY += PADDING;

    return { nodes, viewBox: `${minX} ${minY} ${maxX - minX} ${maxY - minY}` };
  }, [lineas]);

  if (!lineas.length) {
    return (
      <div className="flex h-80 items-center justify-center text-sm text-slate-500">
        Sin datos para el gráfico
      </div>
    );
  }

  return (
    <div className="w-full">
      <svg viewBox={layout.viewBox} className="mx-auto w-full" style={{ maxHeight: 780 }}>
        <circle cx={0} cy={0} r={LINE_ORBIT - 25} fill="none" stroke="#CBD5E1" strokeDasharray="4 6" strokeWidth={1} />
        <circle cx={0} cy={0} r={SUB_ORBIT_START - 25} fill="none" stroke="#E2E8F0" strokeDasharray="4 6" strokeWidth={1} />

        {layout.nodes.map((node) => (
          <g key={`links-${node.linea.slug}`}>
            <line x1={0} y1={0} x2={node.x} y2={node.y} stroke={node.linea.color} strokeDasharray="3 5" strokeWidth={1.5} opacity={0.6} />
            {node.subs.map((s) => (
              <line
                key={`link-${node.linea.slug}-${s.sub.codigo}`}
                x1={node.x}
                y1={node.y}
                x2={s.x}
                y2={s.y}
                stroke={node.linea.color}
                strokeDasharray="2 4"
                strokeWidth={1}
                opacity={0.5}
              />
            ))}
          </g>
        ))}

        <circle cx={0} cy={0} r={CENTER_R} fill="#0B2A5B" stroke="#fff" strokeWidth={3} />
        <foreignObject x={-CENTER_R} y={-CENTER_R} width={CENTER_R * 2} height={CENTER_R * 2}>
          <div className="flex h-full w-full flex-col items-center justify-center text-center text-white">
            <span className="text-[10px] font-semibold uppercase tracking-wide opacity-80">PDI 2022–2026</span>
            <span className="text-2xl font-black leading-tight">{data.alcance_global.toFixed(1)}%</span>
            <span className="text-[9px] font-semibold uppercase tracking-widest opacity-80">Alcance Global</span>
          </div>
        </foreignObject>

        {layout.nodes.map((node) => {
          const IconComponent = STRATEGIC_ICON_MAP[node.linea.icon];
          return (
            <g key={`node-${node.linea.slug}`}>
              <circle cx={node.x} cy={node.y} r={LINE_R} fill={node.linea.color} stroke="#fff" strokeWidth={2.5} />
              <foreignObject x={node.x - LINE_R} y={node.y - LINE_R} width={LINE_R * 2} height={LINE_R * 2}>
                <div className="flex h-full w-full flex-col items-center justify-center text-center text-white">
                  {IconComponent && <IconComponent size={16} strokeWidth={2} />}
                  <span className="text-sm font-black leading-none">{node.linea.cumplimiento.toFixed(0)}%</span>
                </div>
              </foreignObject>
              <foreignObject x={node.x - 70} y={node.y + LINE_R + 2} width={140} height={30}>
                <div
                  className="mx-auto w-fit max-w-[140px] rounded-full border bg-white px-2 py-0.5 text-center text-[10px] font-bold leading-tight shadow-sm"
                  style={{ borderColor: node.linea.color, color: node.linea.color }}
                >
                  {node.linea.label}
                </div>
              </foreignObject>

              {node.subs.map((s) => {
                const alertStyle = ALERTA_STYLES[s.sub.alerta];
                return (
                  <foreignObject
                    key={`sub-${node.linea.slug}-${s.sub.codigo}`}
                    x={s.x - SUB_W / 2}
                    y={s.y - SUB_H / 2}
                    width={SUB_W}
                    height={SUB_H}
                  >
                    <div
                      className="flex h-full w-full flex-col justify-center rounded-lg border bg-white px-2 py-1 shadow-sm"
                      style={{ borderColor: node.linea.color, borderLeftWidth: 4 }}
                    >
                      <div className="flex items-center gap-1">
                        <span
                          className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[9px] font-bold text-white"
                          style={{ backgroundColor: node.linea.color }}
                        >
                          {s.sub.codigo}
                        </span>
                        <span className="truncate text-[10px] font-semibold text-slate-700">{s.sub.label}</span>
                      </div>
                      <div className="mt-0.5 flex items-center gap-1.5">
                        <span className="text-xs font-black" style={{ color: node.linea.color }}>
                          {s.sub.cumplimiento.toFixed(0)}%
                        </span>
                        {s.sub.n_items > 0 && (
                          <span className="text-[9px] text-slate-500">
                            {s.sub.n_items} {s.sub.n_items === 1 ? "elemento" : "elementos"}
                          </span>
                        )}
                        {alertStyle.label && (
                          <span
                            className="rounded px-1 text-[8px] font-bold uppercase tracking-wide"
                            style={{ backgroundColor: alertStyle.bg, color: alertStyle.text }}
                          >
                            {alertStyle.label}
                          </span>
                        )}
                      </div>
                    </div>
                  </foreignObject>
                );
              })}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
