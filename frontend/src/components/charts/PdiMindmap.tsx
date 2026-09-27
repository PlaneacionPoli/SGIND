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
const LINE_ORBIT = 220;
const SUB_W = 300;
// El alto de cada caja se calcula según el largo de su texto (ver
// estimateSubHeight) para que la etiqueta nunca se corte con "..." — por eso
// no hay un SUB_H fijo.
const SUB_MIN_H = 78;
// Cada objetivo cuelga directamente de su línea (no en cadena): se distribuyen
// en abanico alrededor del nodo de la línea. El radio de cada ítem se acumula
// a partir del alto real del anterior (no un paso fijo), para que las cajas
// más altas no choquen con la siguiente — validado numéricamente contra los
// 11 objetivos oficiales del PDI con >=40px de margen en cualquier par.
const SUB_LOCAL_R_BASE = 280;
const SUB_LOCAL_R_STEP_MARGIN = 20;
const SUB_ANGLE_GAP = 22;
const PADDING = 60;

function estimateSubHeight(label: string): number {
  const usableWidth = SUB_W - 60;
  const avgCharWidth = 7;
  const charsPerLine = Math.max(10, Math.floor(usableWidth / avgCharWidth));
  const lines = Math.max(1, Math.ceil(label.length / charsPerLine));
  return Math.max(SUB_MIN_H, lines * 17 + 30 + 20);
}

function halfDiagonal(width: number, height: number): number {
  return Math.sqrt((width / 2) ** 2 + (height / 2) ** 2);
}

// Umbral de alerta pedido para este mindmap: por debajo de 98% de
// cumplimiento se marca "En Alerta" (independiente del semáforo institucional
// que usa el resto del tablero).
const ALERTA_UMBRAL = 98;

function getAlertaDisplay(cumplimiento: number): { bg: string; text: string; label: string | null } {
  if (cumplimiento < ALERTA_UMBRAL) {
    return { bg: "#f59e0b", text: "#fff", label: "En Alerta" };
  }
  return { bg: "", text: "#0f172a", label: null };
}

function toRad(deg: number) {
  return (deg * Math.PI) / 180;
}

interface SubNode {
  sub: ResumenMindmapSublinea;
  codigo: string;
  x: number;
  y: number;
  height: number;
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
      const heights = items.map((sub) => estimateSubHeight(sub.label));
      let radius = SUB_LOCAL_R_BASE;
      const subs: SubNode[] = items.map((sub, j) => {
        if (j > 0) {
          radius += halfDiagonal(SUB_W, heights[j - 1]) + halfDiagonal(SUB_W, heights[j]) + SUB_LOCAL_R_STEP_MARGIN;
        }
        const offsetDeg = (j - (items.length - 1) / 2) * SUB_ANGLE_GAP;
        const a = toRad(angleDeg + offsetDeg);
        return {
          sub,
          codigo: `${i + 1}.${j + 1}`,
          x: x + radius * Math.cos(a),
          y: y + radius * Math.sin(a),
          height: heights[j],
        };
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
        minY = Math.min(minY, s.y - s.height / 2);
        maxY = Math.max(maxY, s.y + s.height / 2);
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
    const alertStyle = getAlertaDisplay(s.sub.cumplimiento);
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
          <circle cx={0} cy={0} r={LINE_ORBIT - 30} fill="none" stroke="#E2E8F0" strokeWidth={1.5} />

          {orderedNodes.map((node) => {
            const isFocused = focused === node.linea.slug;
            const isDimmed = focused !== null && !isFocused;
            const isHovered = hovered === node.linea.slug;
            const IconComponent = STRATEGIC_ICON_MAP[node.linea.icon];

            return (
              <g key={node.linea.slug} opacity={isDimmed ? 0.2 : 1} style={{ transition: "opacity 200ms ease" }}>
                <line x1={0} y1={0} x2={node.x} y2={node.y} stroke={node.linea.color} strokeWidth={2.5} opacity={0.55} />
                <circle r={4.5} fill={node.linea.color} opacity={0.9}>
                  <animateMotion dur="2.6s" repeatCount="indefinite" path={`M0,0 L${node.x},${node.y}`} />
                </circle>
                {node.subs.map((s, subIdx) => (
                  <g key={`link-${node.linea.slug}-${s.codigo}`}>
                    <line x1={node.x} y1={node.y} x2={s.x} y2={s.y} stroke={node.linea.color} strokeWidth={2} opacity={0.45} />
                    <circle r={3.5} fill={node.linea.color} opacity={0.85}>
                      <animateMotion
                        dur="2.2s"
                        begin={`${subIdx * 0.35}s`}
                        repeatCount="indefinite"
                        path={`M${node.x},${node.y} L${s.x},${s.y}`}
                      />
                    </circle>
                  </g>
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
                  const alertStyle = getAlertaDisplay(s.sub.cumplimiento);
                  const subKey = `${node.linea.slug}::${s.codigo}`;
                  const isSubHovered = hovered === subKey;
                  return (
                    <foreignObject
                      key={subKey}
                      x={s.x - SUB_W / 2}
                      y={s.y - s.height / 2}
                      width={SUB_W}
                      height={s.height}
                    >
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
                          <span className="text-[13px] font-semibold leading-tight text-slate-700">
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
