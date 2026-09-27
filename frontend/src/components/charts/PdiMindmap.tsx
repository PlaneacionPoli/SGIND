"use client";

import { useMemo, useRef, useState, type MouseEvent as ReactMouseEvent } from "react";
import { STRATEGIC_ICON_MAP } from "@/lib/strategic-icons";
import type { ResumenMindmap, ResumenMindmapLinea, ResumenMindmapSublinea } from "@/lib/types";

interface PdiMindmapProps {
  data: ResumenMindmap;
}

// Orden oficial del PDI 2022-2026 (docs/PDI/Plan_de_Desarrollo_Institucional_PDI_2022-2026.docx:
// "1. Calidad", "2. Expansión", "3. Educación para Toda la Vida", "4. Experiencia",
// "5. Transformación Organizacional", "6. Sostenibilidad"). El mindmap se dibuja en
// sentido horario empezando arriba (12 en punto) siguiendo esta numeración.
const OFFICIAL_LINE_ORDER = [
  "calidad",
  "expansion",
  "educacion-para-toda-la-vida",
  "experiencia",
  "transformacion-organizacional",
  "sostenibilidad",
];

// Todas las medidas están en "unidades de diseño" == px reales del SVG
// (el <svg> se renderiza con width/height explícitos, sin escalar el
// viewBox), para que el texto declarado en px nunca se achique por un
// mismatch entre el tamaño lógico y el tamaño físico renderizado.
const CENTER_R = 100;
const LINE_R = 72;
const LINE_ORBIT = 190;
const SUB_W = 190;
const SUB_H = 76;
// Cada objetivo cuelga directamente de su línea (no en cadena): se distribuyen
// en abanico alrededor del nodo de la línea, con un pequeño incremento de
// radio por ítem para separarlos sin necesitar ángulos grandes que invadan el
// sector de la línea vecina (validado numéricamente para 1-3 objetivos/línea).
const SUB_LOCAL_R_BASE = 220;
const SUB_LOCAL_R_STEP = 110;
const SUB_ANGLE_GAP = 45;
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
  codigo: string;
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

function orderLineas(lineas: ResumenMindmapLinea[]): ResumenMindmapLinea[] {
  const bySlug = new Map(lineas.map((l) => [l.slug, l]));
  const ordered = OFFICIAL_LINE_ORDER.map((slug) => bySlug.get(slug)).filter(
    (l): l is ResumenMindmapLinea => Boolean(l)
  );
  const seen = new Set(ordered.map((l) => l.slug));
  const rest = lineas.filter((l) => !seen.has(l.slug));
  return [...ordered, ...rest];
}

export function PdiMindmap({ data }: PdiMindmapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [focused, setFocused] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const layout = useMemo(() => {
    const lineas = orderLineas(data?.lineas ?? []);
    const n = Math.max(lineas.length, 1);
    const nodes: LineNode[] = lineas.map((linea, i) => {
      const angleDeg = -90 + (360 / n) * i;
      const rad = toRad(angleDeg);
      const dir = { x: Math.cos(rad), y: Math.sin(rad) };
      const x = dir.x * LINE_ORBIT;
      const y = dir.y * LINE_ORBIT;

      const items = linea.sublineas ?? [];
      const subs: SubNode[] = items.map((sub, j) => {
        const offsetDeg = (j - (items.length - 1) / 2) * SUB_ANGLE_GAP;
        const a = toRad(angleDeg + offsetDeg);
        const r = SUB_LOCAL_R_BASE + j * SUB_LOCAL_R_STEP;
        return { sub, codigo: `${i + 1}.${j + 1}`, x: x + r * Math.cos(a), y: y + r * Math.sin(a) };
      });

      return { linea, x, y, subs };
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
  }, [data?.lineas]);

  if (!layout.nodes.length) {
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

  function showSubTooltip(e: ReactMouseEvent, linea: ResumenMindmapLinea, s: SubNode) {
    const { x, y } = svgPointFromEvent(e);
    const alertStyle = ALERTA_STYLES[s.sub.alerta];
    const detail = [
      `Cumplimiento: ${s.sub.cumplimiento.toFixed(1)}%`,
      `${s.sub.n_items} ${s.sub.n_items === 1 ? "elemento" : "elementos"}`,
    ];
    if (alertStyle.label) detail.push(alertStyle.label);
    setTooltip({ x, y, title: `${s.codigo} · ${s.sub.label}`, lines: detail, color: linea.color });
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
          style={{ display: "block", margin: "0 auto", maxWidth: "100%", height: "auto" }}
          onMouseLeave={() => setTooltip(null)}
        >
          <circle cx={0} cy={0} r={LINE_ORBIT - 30} fill="none" stroke="#CBD5E1" strokeDasharray="5 8" strokeWidth={1.5} />

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
                    key={`link-${node.linea.slug}-${s.codigo}`}
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
                  <foreignObject x={-LINE_R + 6} y={-LINE_R + 6} width={(LINE_R - 6) * 2} height={(LINE_R - 6) * 2}>
                    <div className="flex h-full w-full flex-col items-center justify-center gap-0.5 text-center text-white">
                      {IconComponent && <IconComponent size={22} strokeWidth={2} />}
                      <span className="text-xl font-black leading-none">{node.linea.cumplimiento.toFixed(0)}%</span>
                      <span className="line-clamp-2 px-1 text-[10px] font-semibold leading-tight opacity-95">
                        {node.linea.label}
                      </span>
                    </div>
                  </foreignObject>
                </g>

                {node.subs.map((s) => {
                  const alertStyle = ALERTA_STYLES[s.sub.alerta];
                  const subKey = `${node.linea.slug}::${s.codigo}`;
                  const isSubHovered = hovered === subKey;
                  return (
                    <foreignObject key={subKey} x={s.x - SUB_W / 2} y={s.y - SUB_H / 2} width={SUB_W} height={SUB_H}>
                      <div
                        className="flex h-full w-full cursor-pointer flex-col justify-center gap-1 rounded-xl border-2 bg-white px-3 py-2 shadow-md"
                        style={{
                          borderColor: node.linea.color,
                          borderLeftWidth: 7,
                          transform: isSubHovered ? "scale(1.05)" : "scale(1)",
                          transition: "transform 150ms ease, box-shadow 150ms ease",
                          boxShadow: isSubHovered ? "0 10px 24px rgba(15,23,42,0.22)" : undefined,
                        }}
                        onMouseEnter={(e) => {
                          setHovered(subKey);
                          showSubTooltip(e, node.linea, s);
                        }}
                        onMouseMove={(e) => showSubTooltip(e, node.linea, s)}
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
                            {s.codigo}
                          </span>
                          <span className="line-clamp-2 text-[13px] font-semibold leading-tight text-slate-700">
                            {s.sub.label}
                          </span>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-lg font-black" style={{ color: node.linea.color }}>
                            {s.sub.cumplimiento.toFixed(0)}%
                          </span>
                          {s.sub.n_items > 0 && (
                            <span className="text-[11px] text-slate-500">
                              {s.sub.n_items} {s.sub.n_items === 1 ? "elemento" : "elementos"}
                            </span>
                          )}
                          {alertStyle.label && (
                            <span
                              className="rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide"
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
                <span className="text-[12px] font-semibold uppercase tracking-wide opacity-80">PDI 2022–2026</span>
                <span className="text-3xl font-black leading-tight">{data.alcance_global.toFixed(1)}%</span>
                <span className="text-[11px] font-semibold uppercase tracking-widest opacity-80">Alcance Global</span>
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
