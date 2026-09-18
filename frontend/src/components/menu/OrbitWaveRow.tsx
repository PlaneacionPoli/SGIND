"use client";

import type { Role } from "@/config/navigation";
import { NAV_ITEM_META } from "@/config/navigation";
import { OrbitNode } from "@/components/menu/OrbitNode";

interface OrbitWaveRowItem {
  href: string;
  label: string;
}

interface OrbitWaveRowProps {
  items: OrbitWaveRowItem[];
  rowIndex: number;
  currentRole: string | null;
}

// El viewBox debe conservar la misma proporción que el contenedor (aspect-[10/3]
// abajo); si no coinciden, preserveAspectRatio="none" estira x e y en proporciones
// distintas y cualquier trazo con stroke-dasharray sale distorsionado en diagonal.
const VIEWBOX_WIDTH = 100;
const VIEWBOX_HEIGHT = 30;
const TOP_Y = 6;
const BOTTOM_Y = 24;

function isHighlighted(roles: Role[] | undefined, currentRole: string | null) {
  if (!roles || !currentRole) return false;
  return roles.includes(currentRole as Role);
}

/** Puntos donde se apoyan los nodos: x equiespaciado, y alternando arriba/abajo. */
function buildPoints(count: number, startHigh: boolean) {
  return Array.from({ length: count }, (_, i) => {
    const x = count === 1 ? VIEWBOX_WIDTH / 2 : (i / (count - 1)) * VIEWBOX_WIDTH;
    const high = startHigh ? i % 2 === 0 : i % 2 === 1;
    const y = high ? TOP_Y : BOTTOM_Y;
    return { x, y };
  });
}

/** Curva suave tipo "S" que pasa por cada punto (tangente horizontal en cada nodo). */
function buildWavePath(points: { x: number; y: number }[]) {
  if (points.length < 2) return "";
  let d = `M ${points[0].x},${points[0].y}`;
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    const dx = (curr.x - prev.x) / 2;
    d += ` C ${prev.x + dx},${prev.y} ${curr.x - dx},${curr.y} ${curr.x},${curr.y}`;
  }
  return d;
}

/** Misma curva desplazada verticalmente — usada para los bordes de neón superior/inferior de la cinta. */
function buildEdgePath(points: { x: number; y: number }[], offset: number) {
  return buildWavePath(points.map((p) => ({ x: p.x, y: p.y + offset })));
}

export function OrbitWaveRow({ items, rowIndex, currentRole }: OrbitWaveRowProps) {
  const points = buildPoints(items.length, rowIndex % 2 === 0);
  const path = buildWavePath(points);
  const upperEdgePath = buildEdgePath(points, -2.2);
  const lowerEdgePath = buildEdgePath(points, 2.2);

  const ribbonId = `orbit-wave-ribbon-${rowIndex}`;
  const coreId = `orbit-wave-core-${rowIndex}`;
  const filamentId = `orbit-wave-filament-${rowIndex}`;
  const glowId = `orbit-wave-ambient-glow-${rowIndex}`;

  return (
    <div className="relative mx-auto w-full max-w-4xl self-center md:aspect-[10/3] md:h-[26vh] md:max-h-[250px] lg:h-[30vh] lg:max-h-[290px]">
      <svg
        viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
        preserveAspectRatio="none"
        className="absolute inset-0 hidden h-full w-full overflow-visible motion-safe:animate-wave-pulse md:block"
        aria-hidden="true"
      >
        <defs>
          {/* Cuerpo de la cinta: azul profundo → cian → violeta, translúcido */}
          <linearGradient id={ribbonId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#1e40af" stopOpacity="0.55" />
            <stop offset="35%" stopColor="#0ea5e9" stopOpacity="0.6" />
            <stop offset="70%" stopColor="#38bdf8" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#a855f7" stopOpacity="0.5" />
          </linearGradient>
          {/* Núcleo brillante interior */}
          <linearGradient id={coreId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#7dd3fc" />
            <stop offset="50%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#e9d5ff" />
          </linearGradient>
          {/* Filamentos de luz que recorren la cinta */}
          <linearGradient id={filamentId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="50%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#38bdf8" />
          </linearGradient>
          <filter id={glowId} x="-20%" y="-200%" width="140%" height="500%">
            <feGaussianBlur stdDeviation="1.6" />
          </filter>
        </defs>

        {/* Capa 1 — resplandor ambiental ancho y difuso */}
        <path
          d={path}
          fill="none"
          stroke={`url(#${ribbonId})`}
          strokeWidth={5.5}
          strokeLinecap="round"
          filter={`url(#${glowId})`}
        />
        {/* Capa 2 — cuerpo translúcido de la cinta */}
        <path d={path} fill="none" stroke={`url(#${ribbonId})`} strokeWidth={3.4} strokeLinecap="round" />
        {/* Capa 3 — núcleo luminoso interior */}
        <path
          d={path}
          fill="none"
          stroke={`url(#${coreId})`}
          strokeWidth={1.7}
          strokeLinecap="round"
          opacity={0.9}
        />
        {/* Capa 4 — bordes de neón superior/inferior, dan efecto de tubo */}
        <path d={upperEdgePath} fill="none" stroke={`url(#${coreId})`} strokeWidth={0.35} strokeLinecap="round" opacity={0.55} />
        <path d={lowerEdgePath} fill="none" stroke={`url(#${coreId})`} strokeWidth={0.35} strokeLinecap="round" opacity={0.45} />

        {/* Capa 5 — filamentos de luz viajando en bucle continuo, distintas velocidades */}
        <path
          d={path}
          fill="none"
          stroke={`url(#${filamentId})`}
          strokeWidth={1.6}
          strokeLinecap="round"
          strokeDasharray="20 44"
          className="motion-safe:animate-dash-flow"
        />
        <path
          d={upperEdgePath}
          fill="none"
          stroke="#e0f7ff"
          strokeWidth={0.7}
          strokeLinecap="round"
          strokeDasharray="6 30"
          opacity={0.8}
          style={{ animationDuration: "6s" }}
          className="motion-safe:animate-dash-flow"
        />
        <path
          d={lowerEdgePath}
          fill="none"
          stroke="#22d3ee"
          strokeWidth={0.6}
          strokeLinecap="round"
          strokeDasharray="5 26"
          opacity={0.7}
          className="motion-safe:animate-dash-flow-reverse"
        />

        {/* Beacons pulsantes en cada nodo */}
        {points.map((point, index) => (
          <circle
            key={index}
            cx={point.x}
            cy={point.y}
            r={0.9}
            fill="#e0f7ff"
            className="motion-safe:animate-twinkle"
            style={{ animationDelay: `${index * 300}ms` }}
          />
        ))}
      </svg>

      {/* Fallback vertical para mobile: columna simple sin la onda SVG */}
      <div className="flex h-auto flex-col gap-3 md:hidden">
        {items.map((item, index) => {
          const meta = NAV_ITEM_META[item.href];
          if (!meta) return null;
          return (
            <OrbitNode
              key={item.href}
              href={item.href}
              label={item.label}
              meta={meta}
              index={index}
              highlighted={isHighlighted(meta.roles, currentRole)}
              layout="static"
            />
          );
        })}
      </div>

      <div className="relative hidden h-full md:block">
        {items.map((item, index) => {
          const meta = NAV_ITEM_META[item.href];
          if (!meta) return null;
          const point = points[index];
          return (
            <OrbitNode
              key={item.href}
              href={item.href}
              label={item.label}
              meta={meta}
              index={index}
              highlighted={isHighlighted(meta.roles, currentRole)}
              layout="orbit"
              left={point.x}
              top={(point.y / VIEWBOX_HEIGHT) * 100}
            />
          );
        })}
      </div>
    </div>
  );
}
