"use client";

import Image from "next/image";
import Link from "next/link";
import type { NavItemMeta } from "@/config/navigation";
import { cn } from "@/lib/utils";

interface OrbitNodeProps {
  href: string;
  label: string;
  iconSrc: string;
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
  iconSrc,
  meta,
  index,
  highlighted,
  layout,
  left,
  top,
}: OrbitNodeProps) {
  const { pillColor } = meta;

  // El PNG ya es el botón circular completo (con su propio aro y brillo);
  // el resplandor de color y la animación viven en este contenedor.
  const iconCircle = (
    <span
      style={{
        boxShadow: `0 0 26px 6px ${pillColor}80`,
        animationDelay: `${index * 350}ms`,
      }}
      className={cn(
        "relative flex items-center justify-center rounded-full ring-4 ring-white/10",
        "transition-transform duration-300 motion-safe:animate-float",
        "group-hover:scale-110 group-hover:ring-white/30 group-focus-visible:scale-110",
        layout === "orbit" ? "h-16 w-16 md:h-20 md:w-20 lg:h-24 lg:w-24" : "h-16 w-16 sm:h-20 sm:w-20",
        highlighted && "ring-poli-gold/70 motion-safe:animate-glow-pulse"
      )}
    >
      <Image
        src={iconSrc}
        alt=""
        width={192}
        height={192}
        className="h-full w-full rounded-full object-cover"
        aria-hidden="true"
      />
      {highlighted && (
        <span className="absolute -right-1 -top-1 rounded-full bg-poli-gold px-2 py-0.5 text-2xs font-semibold text-white shadow-sm">
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
      className="group absolute flex w-28 -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-2 motion-safe:animate-fade-in lg:w-32"
    >
      {iconCircle}
      <span className="text-center text-sm font-semibold leading-tight text-white drop-shadow-sm transition-colors duration-300 group-hover:text-poli-gold-50 lg:text-base">
        {label}
      </span>
    </Link>
  );
}
