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

const VIEWBOX_WIDTH = 100;
const VIEWBOX_HEIGHT = 40;
const TOP_Y = 11;
const BOTTOM_Y = 29;

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

  return (
    <div className="relative mx-auto w-full max-w-4xl md:h-40 lg:h-48">
      <svg
        viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
        preserveAspectRatio="none"
        className="absolute inset-0 hidden h-full w-full md:block"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.35" />
            <stop offset="50%" stopColor="#60a5fa" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.35" />
          </linearGradient>
        </defs>
        <path
          d={path}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={0.6}
          strokeLinecap="round"
          opacity={0.5}
        />
        <path
          d={path}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={0.9}
          strokeLinecap="round"
          strokeDasharray="4 6"
          className="motion-safe:animate-dash-flow"
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
