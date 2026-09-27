"use client";

import { useMemo, useRef, useState, type MouseEvent as ReactMouseEvent } from "react";
import { STRATEGIC_ICON_MAP } from "@/lib/strategic-icons";
import type { ResumenMindmap, ResumenMindmapLinea, ResumenMindmapSublinea } from "@/lib/types";

interface PdiMindmapProps {
  data: ResumenMindmap;
}

const CENTER_R = 92;
const LINE_R = 52;
const LINE_ORBIT = 240;
const PILL_R = LINE_ORBIT + LINE_R + 40;
const SUB_START_R = PILL_R + 70;
const SUB_STEP_R = 104;
const SUB_W = 208;
const SUB_H = 70;
const PADDING = 50;

const ALERTA_STYLES: Record<ResumenMindmapSublinea["alerta"], { bg: string; text: string; label: string | null }> = {
  ok: { bg: "", text: "#0f172a", label: null },
  alerta: { bg: "#f59e0b", text: "#fff", label: "En Alerta" },
  critica: { bg: "#dc2626", text: "#fff", label: "ALERTA CRÍTICA" },
};

function toRad(deg: number) {
  return (deg * Math.PI) / 180;
}

interface SubNode {
  sub: ResumenMindmapSublinea;
  x: number;
  y: number;
}

interface LineNode {
  linea: ResumenMindmapLinea;
  x: number;
  y: number;
  pillX: number;
  pillY: number;
  subs: SubNode[];
}

interface TooltipState {
  x: number;
  y: number;
  title: string;
  lines: string[];
  color: string;
}

export function PdiMindmap({ data }: PdiMindmapProps) {
  const lineas = data?.lineas ?? [];
  const containerRef = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [focused, setFocused] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const layout = useMemo(() => {
    const n = Math.max(lineas.length, 1);
    const nodes: LineNode[] = lineas.map((linea, i) => {
      const angleDeg = -90 + (360 / n) * i;
      const rad = toRad(angleDeg);
      const dir = { x: Math.cos(rad), y: Math.sin(rad) };

      const subs: SubNode[] = (linea.sublineas ?? []).map((sub, j) => {
        const radius = SUB_START_R + j * SUB_STEP_R;
        return { sub, x: dir.x * radius, y: dir.y * radius };
      });

      return {
        linea,
        x: dir.x * LINE_ORBIT,
        y: dir.y * LINE_ORBIT,
        pillX: dir.x * PILL_R,
        pillY: dir.y * PILL_R,
        subs,
      };
    });

    let minX = -CENTER_R;
    let maxX = CENTER_R;
    let minY = -CENTER_R;
    let maxY = CENTER_R;
    for (const node of nodes) {
      minX = Math.min(minX, node.x - LINE_R, node.pillX - 80);
      maxX = Math.max(maxX, node.x + LINE_R, node.pillX + 80);
      minY = Math.min(minY, node.y - LINE_R, node.pillY - 20);
      maxY = Math.max(maxY, node.y + LINE_R, node.pillY + 20);
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

    return { nodes, minX, minY, width: maxX - minX, height: maxY - minY };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.lineas]);

  if (!lineas.length) {
    return (
      <div className="flex h-80 items-center justify-center text-sm text-slate-500">
        Sin datos para el gráfico
      </div>
    );
  }

  function svgPointFromEvent(e: ReactMouseEvent) {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  function showLineTooltip(e: ReactMouseEvent, linea: ResumenMindmapLinea) {
    const { x, y } = svgPointFromEvent(e);
    setTooltip({
      x,
      y,
      title: linea.label,
      lines: [`Cumplimiento: ${linea.cumplimiento.toFixed(1)}%`],
      color: linea.color,
    });
  }

  function showSubTooltip(e: ReactMouseEvent, linea: ResumenMindmapLinea, sub: ResumenMindmapSublinea) {
    const { x, y } = svgPointFromEvent(e);
    const alertStyle = ALERTA_STYLES[sub.alerta];
    const detail = [
      `Cumplimiento: ${sub.cumplimiento.toFixed(1)}%`,
      `${sub.n_items} ${sub.n_items === 1 ? "elemento" : "elementos"}`,
    ];
    if (alertStyle.label) detail.push(alertStyle.label);
    setTooltip({ x, y, title: `${sub.codigo} · ${sub.label}`, lines: detail, color: linea.color });
  }

  const orderedNodes = focused
    ? [...layout.nodes].sort((a, b) => (a.linea.slug === focused ? 1 : b.linea.slug === focused ? -1 : 0))
    : layout.nodes;

  return (
    <div ref={containerRef} className="relative w-full">
      <p className="mb-2 text-center text-[11px] text-slate-400">
        Pasa el cursor para ver el detalle · Haz clic en una línea para resaltarla
      </p>
      <svg
        viewBox={`${layout.minX} ${layout.minY} ${layout.width} ${layout.height}`}
        className="mx-auto w-full"
        style={{ maxHeight: 820 }}
        onMouseLeave={() => setTooltip(null)}
      >
        <circle cx={0} cy={0} r={LINE_ORBIT - 30} fill="none" stroke="#CBD5E1" strokeDasharray="4 6" strokeWidth={1} />
        <circle cx={0} cy={0} r={SUB_START_R - 30} fill="none" stroke="#E2E8F0" strokeDasharray="4 6" strokeWidth={1} />

        {orderedNodes.map((node) => {
          const isFocused = focused === node.linea.slug;
          const isDimmed = focused !== null && !isFocused;
          const isHovered = hovered === node.linea.slug;
          const IconComponent = STRATEGIC_ICON_MAP[node.linea.icon];

          return (
            <g
              key={node.linea.slug}
              opacity={isDimmed ? 0.25 : 1}
              style={{ transition: "opacity 200ms ease" }}
            >
              <line
                x1={0}
                y1={0}
                x2={node.x}
                y2={node.y}
                stroke={node.linea.color}
                strokeDasharray="3 5"
                strokeWidth={1.5}
                opacity={0.6}
              />
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

              <g
                transform={`translate(${node.x} ${node.y}) scale(${isHovered || isFocused ? 1.1 : 1})`}
                style={{ transition: "transform 150ms ease", cursor: "pointer" }}
                onMouseEnter={(e) => {
                  setHovered(node.linea.slug);
                  showLineTooltip(e, node.linea);
                }}
                onMouseMove={(e) => showLineTooltip(e, node.linea)}
                onMouseLeave={() => {
                  setHovered(null);
                  setTooltip(null);
                }}
                onClick={() => setFocused((prev) => (prev === node.linea.slug ? null : node.linea.slug))}
              >
                <circle
                  cx={0}
                  cy={0}
                  r={LINE_R}
                  fill={node.linea.color}
                  stroke="#fff"
                  strokeWidth={isFocused ? 4 : 2.5}
                />
                <foreignObject x={-LINE_R} y={-LINE_R} width={LINE_R * 2} height={LINE_R * 2}>
                  <div className="flex h-full w-full flex-col items-center justify-center text-center text-white">
                    {IconComponent && <IconComponent size={16} strokeWidth={2} />}
                    <span className="text-sm font-black leading-none">{node.linea.cumplimiento.toFixed(0)}%</span>
                  </div>
                </foreignObject>
              </g>

              <foreignObject x={node.pillX - 90} y={node.pillY - 13} width={180} height={26}>
                <div
                  className="mx-auto w-fit max-w-[180px] truncate rounded-full border bg-white px-2 py-0.5 text-center text-[10px] font-bold leading-tight shadow-sm"
                  style={{ borderColor: node.linea.color, color: node.linea.color }}
                  title={node.linea.label}
                >
                  {node.linea.label}
                </div>
              </foreignObject>

              {node.subs.map((s) => {
                const alertStyle = ALERTA_STYLES[s.sub.alerta];
                const subKey = `${node.linea.slug}::${s.sub.codigo}`;
                const isSubHovered = hovered === subKey;
                return (
                  <foreignObject
                    key={subKey}
                    x={s.x - SUB_W / 2}
                    y={s.y - SUB_H / 2}
                    width={SUB_W}
                    height={SUB_H}
                  >
                    <div
                      className="flex h-full w-full cursor-pointer flex-col justify-center rounded-lg border bg-white px-2 py-1 shadow-sm"
                      style={{
                        borderColor: node.linea.color,
                        borderLeftWidth: 4,
                        transform: isSubHovered ? "scale(1.06)" : "scale(1)",
                        transition: "transform 150ms ease, box-shadow 150ms ease",
                        boxShadow: isSubHovered ? "0 6px 16px rgba(15,23,42,0.18)" : undefined,
                      }}
                      onMouseEnter={(e) => {
                        setHovered(subKey);
                        showSubTooltip(e, node.linea, s.sub);
                      }}
                      onMouseMove={(e) => showSubTooltip(e, node.linea, s.sub)}
                      onMouseLeave={() => {
                        setHovered(null);
                        setTooltip(null);
                      }}
                    >
                      <div className="flex items-start gap-1">
                        <span
                          className="mt-0.5 flex h-4 w-6 shrink-0 items-center justify-center rounded-full text-[9px] font-bold text-white"
                          style={{ backgroundColor: node.linea.color }}
                        >
                          {s.sub.codigo}
                        </span>
                        <span className="line-clamp-2 text-[10px] font-semibold leading-tight text-slate-700">
                          {s.sub.label}
                        </span>
                      </div>
                      <div className="mt-1 flex flex-wrap items-center gap-1">
                        <span className="text-xs font-black" style={{ color: node.linea.color }}>
                          {s.sub.cumplimiento.toFixed(0)}%
                        </span>
                        {s.sub.n_items > 0 && (
                          <span className="text-[9px] text-slate-500">
                            {s.sub.n_items} {s.sub.n_items === 1 ? "elem." : "elems."}
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

        <g
          style={{ cursor: focused ? "pointer" : "default" }}
          onClick={() => setFocused(null)}
        >
          <circle cx={0} cy={0} r={CENTER_R} fill="#0B2A5B" stroke="#fff" strokeWidth={3} />
          <foreignObject x={-CENTER_R} y={-CENTER_R} width={CENTER_R * 2} height={CENTER_R * 2}>
            <div className="flex h-full w-full flex-col items-center justify-center text-center text-white">
              <span className="text-[10px] font-semibold uppercase tracking-wide opacity-80">PDI 2022–2026</span>
              <span className="text-2xl font-black leading-tight">{data.alcance_global.toFixed(1)}%</span>
              <span className="text-[9px] font-semibold uppercase tracking-widest opacity-80">Alcance Global</span>
            </div>
          </foreignObject>
        </g>
      </svg>

      {tooltip && (
        <div
          className="pointer-events-none absolute z-10 max-w-[220px] rounded-lg border bg-white px-3 py-2 text-xs shadow-lg"
          style={{
            left: Math.min(tooltip.x + 14, (containerRef.current?.clientWidth ?? 0) - 232),
            top: tooltip.y + 14,
            borderColor: tooltip.color,
          }}
        >
          <p className="font-bold text-slate-800">{tooltip.title}</p>
          {tooltip.lines.map((line) => (
            <p key={line} className="text-slate-500">
              {line}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
