"use client";

import { useMemo, useRef, useState, type MouseEvent as ReactMouseEvent } from "react";
import { STRATEGIC_ICON_MAP } from "@/lib/strategic-icons";
import type { ResumenMindmap, ResumenMindmapLinea, ResumenMindmapSublinea } from "@/lib/types";

interface PdiMindmapProps {
  data: ResumenMindmap;
}

// Todas las medidas están en "unidades de diseño" == px reales del SVG
// (el <svg> se renderiza con width/height explícitos, sin escalar el
// viewBox), para que el texto declarado en px nunca se achique por un
// mismatch entre el tamaño lógico y el tamaño físico renderizado.
const CENTER_R = 120;
const LINE_R = 78;
const LINE_ORBIT = 300;
const SUB_W = 270;
const SUB_H = 100;
// Radio mínimo para que un pétalo (línea) no choque con su primer badge, y
// paso mínimo entre badges consecutivos del mismo pétalo — calculado con la
// semidiagonal del badge para que sea seguro sin importar el ángulo del rayo.
const SUB_HALF_DIAG = Math.sqrt((SUB_W / 2) ** 2 + (SUB_H / 2) ** 2);
const SUB_START_R = LINE_ORBIT + LINE_R + SUB_HALF_DIAG + 35;
const SUB_STEP_R = SUB_HALF_DIAG * 2 + 35;
const PADDING = 60;

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

      return { linea, x: dir.x * LINE_ORBIT, y: dir.y * LINE_ORBIT, subs };
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
    return { x: e.clientX - rect.left + (containerRef.current?.scrollLeft ?? 0), y: e.clientY - rect.top };
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
    <div>
      <p className="mb-2 text-center text-xs text-slate-400">
        Pasa el cursor sobre un nodo para ver el detalle · Haz clic en una línea para resaltarla
      </p>
      <div ref={containerRef} className="relative overflow-x-auto">
        <svg
          viewBox={`${layout.minX} ${layout.minY} ${layout.width} ${layout.height}`}
          width={layout.width}
          height={layout.height}
          style={{ display: "block", margin: "0 auto" }}
          onMouseLeave={() => setTooltip(null)}
        >
          <circle cx={0} cy={0} r={LINE_ORBIT - 40} fill="none" stroke="#CBD5E1" strokeDasharray="5 8" strokeWidth={1.5} />
          <circle cx={0} cy={0} r={SUB_START_R - 40} fill="none" stroke="#E2E8F0" strokeDasharray="5 8" strokeWidth={1.5} />

          {orderedNodes.map((node) => {
            const isFocused = focused === node.linea.slug;
            const isDimmed = focused !== null && !isFocused;
            const isHovered = hovered === node.linea.slug;
            const IconComponent = STRATEGIC_ICON_MAP[node.linea.icon];

            return (
              <g key={node.linea.slug} opacity={isDimmed ? 0.2 : 1} style={{ transition: "opacity 200ms ease" }}>
                <line
                  x1={0}
                  y1={0}
                  x2={node.x}
                  y2={node.y}
                  stroke={node.linea.color}
                  strokeDasharray="4 6"
                  strokeWidth={2}
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
                    strokeDasharray="3 5"
                    strokeWidth={1.5}
                    opacity={0.5}
                  />
                ))}

                <g
                  transform={`translate(${node.x} ${node.y}) scale(${isHovered || isFocused ? 1.08 : 1})`}
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
                  <circle cx={0} cy={0} r={LINE_R} fill={node.linea.color} stroke="#fff" strokeWidth={isFocused ? 5 : 3} />
                  <foreignObject x={-LINE_R + 8} y={-LINE_R + 8} width={(LINE_R - 8) * 2} height={(LINE_R - 8) * 2}>
                    <div className="flex h-full w-full flex-col items-center justify-center gap-0.5 text-center text-white">
                      {IconComponent && <IconComponent size={26} strokeWidth={2} />}
                      <span className="text-2xl font-black leading-none">{node.linea.cumplimiento.toFixed(0)}%</span>
                      <span className="line-clamp-2 px-1 text-[11px] font-semibold leading-tight opacity-95">
                        {node.linea.label}
                      </span>
                    </div>
                  </foreignObject>
                </g>

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
                        className="flex h-full w-full cursor-pointer flex-col justify-center gap-1.5 rounded-xl border-2 bg-white px-3 py-2 shadow-md"
                        style={{
                          borderColor: node.linea.color,
                          borderLeftWidth: 7,
                          transform: isSubHovered ? "scale(1.05)" : "scale(1)",
                          transition: "transform 150ms ease, box-shadow 150ms ease",
                          boxShadow: isSubHovered ? "0 10px 24px rgba(15,23,42,0.22)" : undefined,
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
                        <div className="flex items-start gap-2">
                          <span
                            className="mt-0.5 flex h-6 w-9 shrink-0 items-center justify-center rounded-full text-[12px] font-bold text-white"
                            style={{ backgroundColor: node.linea.color }}
                          >
                            {s.sub.codigo}
                          </span>
                          <span className="line-clamp-2 text-[14px] font-semibold leading-tight text-slate-700">
                            {s.sub.label}
                          </span>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-xl font-black" style={{ color: node.linea.color }}>
                            {s.sub.cumplimiento.toFixed(0)}%
                          </span>
                          {s.sub.n_items > 0 && (
                            <span className="text-[12px] text-slate-500">
                              {s.sub.n_items} {s.sub.n_items === 1 ? "elemento" : "elementos"}
                            </span>
                          )}
                          {alertStyle.label && (
                            <span
                              className="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide"
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

          <g style={{ cursor: focused ? "pointer" : "default" }} onClick={() => setFocused(null)}>
            <circle cx={0} cy={0} r={CENTER_R} fill="#0B2A5B" stroke="#fff" strokeWidth={4} />
            <foreignObject x={-CENTER_R} y={-CENTER_R} width={CENTER_R * 2} height={CENTER_R * 2}>
              <div className="flex h-full w-full flex-col items-center justify-center text-center text-white">
                <span className="text-[13px] font-semibold uppercase tracking-wide opacity-80">PDI 2022–2026</span>
                <span className="text-4xl font-black leading-tight">{data.alcance_global.toFixed(1)}%</span>
                <span className="text-[12px] font-semibold uppercase tracking-widest opacity-80">Alcance Global</span>
              </div>
            </foreignObject>
          </g>
        </svg>

        {tooltip && (
          <div
            className="pointer-events-none absolute z-10 max-w-[260px] rounded-lg border-2 bg-white px-3 py-2 text-sm shadow-lg"
            style={{ left: tooltip.x + 16, top: tooltip.y + 16, borderColor: tooltip.color }}
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
    </div>
  );
}
