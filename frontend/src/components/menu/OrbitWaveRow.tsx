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

export function OrbitWaveRow({ items, rowIndex, currentRole }: OrbitWaveRowProps) {
  const points = buildPoints(items.length, rowIndex % 2 === 0);
  const path = buildWavePath(points);
  const gradientId = `orbit-wave-gradient-${rowIndex}`;

  const coreId = `orbit-wave-core-${rowIndex}`;

  return (
    <div className="relative mx-auto w-full max-w-4xl md:aspect-[10/3]">
      <svg
        viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
        preserveAspectRatio="none"
        className="absolute inset-0 hidden h-full w-full md:block"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#1e5fd9" />
            <stop offset="55%" stopColor="#38bdf8" />
            <stop offset="100%" stopColor="#00d4ff" />
          </linearGradient>
          <linearGradient id={coreId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#bff0ff" />
            <stop offset="100%" stopColor="#ffffff" />
          </linearGradient>
        </defs>

        {/* Halo exterior difuso — el "brillo" del cable de fibra óptica */}
        <path
          d={path}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={3.2}
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
          style={{
            filter:
              "drop-shadow(0 0 6px #38bdf8) drop-shadow(0 0 14px #1e5fd9)",
          }}
        />
        {/* Núcleo brillante del cable */}
        <path
          d={path}
          fill="none"
          stroke={`url(#${coreId})`}
          strokeWidth={1.1}
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
          opacity={0.9}
        />
        {/* Pulso de luz que recorre la onda en bucle continuo */}
        <path
          d={path}
          fill="none"
          stroke="#ffffff"
          strokeWidth={2}
          strokeLinecap="round"
          strokeDasharray="14 190"
          vectorEffect="non-scaling-stroke"
          className="motion-safe:animate-dash-flow"
          style={{ filter: "drop-shadow(0 0 6px #ffffff)" }}
        />
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
