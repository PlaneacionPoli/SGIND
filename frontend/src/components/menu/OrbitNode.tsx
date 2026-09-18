"use client";

import Link from "next/link";
import type { NavItemMeta } from "@/config/navigation";
import { cn } from "@/lib/utils";

interface OrbitNodeProps {
  href: string;
  label: string;
  meta: NavItemMeta;
  index: number;
  highlighted: boolean;
  /**
   * "orbit": posicionado en absolute sobre la onda SVG (left/top en %, requeridos).
   * "static": fila normal (ícono + label en línea), usado en el fallback mobile.
   */
  layout: "orbit" | "static";
  left?: number;
  top?: number;
}

export function OrbitNode({
  href,
  label,
  meta,
  index,
  highlighted,
  layout,
  left,
  top,
}: OrbitNodeProps) {
  const { Icon, pillColor } = meta;

  const iconCircle = (
    <span
      style={{
        background: pillColor,
        animationDelay: `${index * 350}ms`,
      }}
      className={cn(
        "relative flex h-14 w-14 items-center justify-center rounded-full shadow-elevated ring-4 ring-white/10 sm:h-16 sm:w-16",
        "transition-transform duration-300 motion-safe:animate-float",
        "group-hover:scale-110 group-hover:ring-white/30 group-focus-visible:scale-110",
        highlighted && "ring-poli-gold/70 motion-safe:animate-glow-pulse"
      )}
    >
      <Icon size={24} className="text-white" aria-hidden="true" />
      {highlighted && (
        <span className="absolute -right-1 -top-1 rounded-full bg-poli-gold px-1.5 py-0.5 text-[0.55rem] font-semibold text-white shadow-sm">
          Tu rol
        </span>
      )}
    </span>
  );

  if (layout === "static") {
    return (
      <Link
        href={href}
        aria-label={label}
        className="group flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-3 transition-colors duration-300 hover:bg-white/10"
      >
        {iconCircle}
        <span className="text-sm font-semibold text-white transition-colors duration-300 group-hover:text-poli-gold-50">
          {label}
        </span>
      </Link>
    );
  }

  return (
    <Link
      href={href}
      aria-label={label}
      style={{ left: `${left}%`, top: `${top}%` }}
      className="group absolute flex w-24 -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-2 motion-safe:animate-fade-in"
    >
      {iconCircle}
      <span className="text-center text-xs font-semibold leading-tight text-white drop-shadow-sm transition-colors duration-300 group-hover:text-poli-gold-50 sm:text-sm">
        {label}
      </span>
    </Link>
  );
}
