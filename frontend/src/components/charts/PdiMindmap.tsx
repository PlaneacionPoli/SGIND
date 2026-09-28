"use client";

import { useMemo, useRef, useState, type MouseEvent as ReactMouseEvent } from "react";
import { STRATEGIC_ICON_MAP } from "@/lib/strategic-icons";
import type { ResumenMindmap, ResumenMindmapLinea, ResumenMindmapSublinea } from "@/lib/types";

interface PdiMindmapProps {
  data: ResumenMindmap;
  /** Slug de la línea resaltada/seleccionada (controlado por el padre, ver
   * resumen-general/page.tsx, para poder mostrar la ficha general de la
   * línea al lado del mindmap y dejar que otros elementos —p.ej. la alerta
   * de "Foco y Retos Priorizados"— también la seleccionen). */
  selectedSlug?: string | null;
  onSelectLinea?: (slug: string | null) => void;
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
const LINE_ORBIT = 200;
const SUB_W = 280;
// El alto de cada caja se calcula midiendo el texto real (ver
// estimateSubHeight/countWrappedLines) para que ningún dato quede cortado por
// el recorte duro que aplica <foreignObject> a su contenido — por eso no hay
// un SUB_H fijo.
const SUB_MIN_H = 76;
const SUB_LABEL_FONT = "600 13px Inter, ui-sans-serif, system-ui, sans-serif";
// Cada objetivo cuelga directamente de su línea (no en cadena) y todos los
// objetivos de un mismo eje se ubican al MISMO radio (un abanico parejo, no
// una espiral) para que se vean alineados entre sí — el radio de cada eje se
// calcula para que sus propios ítems no choquen entre sí dado el ángulo
// disponible, con un mínimo común (SUB_LOCAL_R_BASE) para los ejes de un solo
// objetivo. Validado numéricamente contra los 11 objetivos oficiales del PDI
// con >=30px de margen en cualquier par (eje-eje, eje-centro, eje-línea).
const SUB_LOCAL_R_BASE = 240;
const SUB_LOCAL_R_MARGIN = 20;
const SUB_LOCAL_R_SAFETY = 1.05;
const SUB_ANGLE_GAP = 32;
const PADDING = 60;

let measureCanvasCtx: CanvasRenderingContext2D | null | undefined;

function getTextWidth(text: string, font: string): number {
  if (measureCanvasCtx === undefined) {
    measureCanvasCtx = typeof document === "undefined" ? null : document.createElement("canvas").getContext("2d");
  }
  if (!measureCanvasCtx) return text.length * 7.2; // fallback aproximado (SSR o canvas no disponible)
  measureCanvasCtx.font = font;
  return measureCanvasCtx.measureText(text).width;
}

function countWrappedLines(text: string, maxWidth: number, font: string): number {
  const words = text.split(" ");
  let lines = 1;
  let current = "";
  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word;
    if (current && getTextWidth(candidate, font) > maxWidth) {
      lines += 1;
      current = word;
    } else {
      current = candidate;
    }
  }
  return lines;
}

function estimateSubHeight(label: string): number {
  const usableWidth = SUB_W - 56; // padding interno + columna del badge de código
  const lines = countWrappedLines(label, usableWidth, SUB_LABEL_FONT);
  return Math.max(SUB_MIN_H, lines * 18 + 30 + 18);
}

function halfDiagonal(width: number, height: number): number {
  return Math.sqrt((width / 2) ** 2 + (height / 2) ** 2);
}

// Radio común para todos los objetivos de un mismo eje: el mínimo que evita
// que dos objetivos consecutivos (al ángulo disponible) se solapen.
function computeAxisRadius(heights: number[]): number {
  let needed = SUB_LOCAL_R_BASE;
  if (heights.length > 1) {
    const gapRad = toRad(SUB_ANGLE_GAP);
    for (let j = 0; j < heights.length - 1; j++) {
      const pairNeed =
        (halfDiagonal(SUB_W, heights[j]) + halfDiagonal(SUB_W, heights[j + 1]) + SUB_LOCAL_R_MARGIN) /
        (2 * Math.sin(gapRad / 2));
      needed = Math.max(needed, pairNeed);
    }
  }
  return needed * SUB_LOCAL_R_SAFETY;
}

// Curva Bézier cuadrática que arquea el conector hacia afuera del centro
// (en vez de una línea recta), como pétalos — más orgánico y evita que
// conectores largos crucen el lienzo en diagonal.
function curvePath(x1: number, y1: number, x2: number, y2: number): string {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy) || 1;
  let nx = -dy / len;
  let ny = dx / len;
  // Asegura que la curva se arquee alejándose del origen, no hacia él.
  if (nx * mx + ny * my < 0) {
    nx = -nx;
    ny = -ny;
  }
  const bow = len * 0.14;
  const cx = mx + nx * bow;
  const cy = my + ny * bow;
  return `M${x1},${y1} Q${cx},${cy} ${x2},${y2}`;
}

// Umbral de alerta pedido para este mindmap: por debajo de 98% de
// cumplimiento se marca "En Alerta" (independiente del semáforo institucional
// que usa el resto del tablero).
export const ALERTA_UMBRAL = 98;

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

export function PdiMindmap({ data, selectedSlug = null, onSelectLinea }: PdiMindmapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const focused = selectedSlug;
  const setFocused = (next: string | null) => onSelectLinea?.(next);
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
      const radius = computeAxisRadius(heights);
      const subs: SubNode[] = items.map((sub, j) => {
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

    // El radio máximo se mide en valor absoluto y el viewBox se arma simétrico
    // alrededor del origen (0,0): así el nodo central PDI queda siempre
    // centrado en el lienzo, sin importar que un eje tenga más/mayores
    // objetivos que el resto y "jale" el bounding box hacia un lado.
    let maxReachX = CENTER_R;
    let maxReachY = CENTER_R;
    for (const node of nodes) {
      maxReachX = Math.max(maxReachX, Math.abs(node.x) + LINE_R);
      maxReachY = Math.max(maxReachY, Math.abs(node.y) + LINE_R);
      for (const s of node.subs) {
        maxReachX = Math.max(maxReachX, Math.abs(s.x) + SUB_W / 2);
        maxReachY = Math.max(maxReachY, Math.abs(s.y) + s.height / 2);
      }
    }
    const halfWidth = maxReachX + PADDING;
    const halfHeight = maxReachY + PADDING;

    return { nodes, minX: -halfWidth, minY: -halfHeight, width: halfWidth * 2, height: halfHeight * 2 };
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
      <div ref={containerRef} className="relative">
        <svg
          viewBox={`${layout.minX} ${layout.minY} ${layout.width} ${layout.height}`}
          style={{ display: "block", margin: "0 auto", width: "100%", height: "auto" }}
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
                <path d={curvePath(0, 0, node.x, node.y)} fill="none" stroke={node.linea.color} strokeWidth={2} opacity={0.55} />
                <circle r={4.5} fill={node.linea.color} opacity={0.9}>
                  <animateMotion dur="2.6s" repeatCount="indefinite" path={curvePath(0, 0, node.x, node.y)} />
                </circle>
                {node.subs.map((s, subIdx) => {
                  const path = curvePath(node.x, node.y, s.x, s.y);
                  return (
                    <g key={`link-${node.linea.slug}-${s.codigo}`}>
                      <path d={path} fill="none" stroke={node.linea.color} strokeWidth={2} opacity={0.45} />
                      <circle r={3.5} fill={node.linea.color} opacity={0.85}>
                        <animateMotion dur="2.2s" begin={`${subIdx * 0.35}s`} repeatCount="indefinite" path={path} />
                      </circle>
                    </g>
                  );
                })}

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
                  onClick={() => setFocused(focused === node.linea.slug ? null : node.linea.slug)}
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
