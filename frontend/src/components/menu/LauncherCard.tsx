"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { AccentKey, NavItemMeta } from "@/config/navigation";
import { cn } from "@/lib/utils";

interface AccentStyle {
  iconBg: string;
  iconText: string;
  iconHoverBg: string;
  blob: string;
  ring: string;
  chip: string;
}

// Clases Tailwind literales (no se generan dinámicamente) para que el
// compilador JIT las detecte sin necesidad de safelist.
const ACCENTS: Record<AccentKey, AccentStyle> = {
  blue: {
    iconBg: "bg-blue-50", iconText: "text-blue-600", iconHoverBg: "group-hover:bg-blue-600",
    blob: "bg-blue-300", ring: "ring-blue-400", chip: "bg-blue-50 text-blue-700",
  },
  violet: {
    iconBg: "bg-violet-50", iconText: "text-violet-600", iconHoverBg: "group-hover:bg-violet-600",
    blob: "bg-violet-300", ring: "ring-violet-400", chip: "bg-violet-50 text-violet-700",
  },
  teal: {
    iconBg: "bg-teal-50", iconText: "text-teal-600", iconHoverBg: "group-hover:bg-teal-600",
    blob: "bg-teal-300", ring: "ring-teal-400", chip: "bg-teal-50 text-teal-700",
  },
  sky: {
    iconBg: "bg-sky-50", iconText: "text-sky-600", iconHoverBg: "group-hover:bg-sky-600",
    blob: "bg-sky-300", ring: "ring-sky-400", chip: "bg-sky-50 text-sky-700",
  },
  amber: {
    iconBg: "bg-amber-50", iconText: "text-amber-600", iconHoverBg: "group-hover:bg-amber-600",
    blob: "bg-amber-300", ring: "ring-amber-400", chip: "bg-amber-50 text-amber-700",
  },
  rose: {
    iconBg: "bg-rose-50", iconText: "text-rose-600", iconHoverBg: "group-hover:bg-rose-600",
    blob: "bg-rose-300", ring: "ring-rose-400", chip: "bg-rose-50 text-rose-700",
  },
  emerald: {
    iconBg: "bg-emerald-50", iconText: "text-emerald-600", iconHoverBg: "group-hover:bg-emerald-600",
    blob: "bg-emerald-300", ring: "ring-emerald-400", chip: "bg-emerald-50 text-emerald-700",
  },
  indigo: {
    iconBg: "bg-indigo-50", iconText: "text-indigo-600", iconHoverBg: "group-hover:bg-indigo-600",
    blob: "bg-indigo-300", ring: "ring-indigo-400", chip: "bg-indigo-50 text-indigo-700",
  },
  slate: {
    iconBg: "bg-slate-100", iconText: "text-slate-600", iconHoverBg: "group-hover:bg-slate-600",
    blob: "bg-slate-300", ring: "ring-slate-400", chip: "bg-slate-100 text-slate-700",
  },
};

interface LauncherCardProps {
  href: string;
  label: string;
  meta: NavItemMeta;
  index: number;
  highlighted: boolean;
  badgeLabel?: string;
  /** Tarjeta grande destacada (hero) vs. tarjeta estándar de grilla. */
  variant?: "featured" | "default";
  className?: string;
}

export function LauncherCard({
  href,
  label,
  meta,
  index,
  highlighted,
  badgeLabel,
  variant = "default",
  className,
}: LauncherCardProps) {
  const { Icon, description, highlight, accent } = meta;
  const a = ACCENTS[accent];
  const isFeatured = variant === "featured";

  return (
    <Link
      href={href}
      style={{ animationDelay: `${index * 70}ms` }}
      className={cn(
        "card group relative isolate flex flex-col overflow-hidden motion-safe:animate-card-in",
        "border border-white/60 bg-white/70 backdrop-blur-xl",
        "transition-all duration-300 ease-out",
        "hover:-translate-y-1.5 hover:shadow-overlay hover:bg-white/85",
        "focus-visible:-translate-y-1.5 focus-visible:shadow-overlay active:scale-[0.98]",
        isFeatured ? "gap-4 p-6 sm:p-7" : "gap-3 p-5",
        highlighted && `ring-2 ring-offset-2 ring-offset-slate-50 ${a.ring}`,
        className
      )}
    >
      {/* Blob líquido decorativo, difuminado, propio del acento del módulo */}
      <div
        aria-hidden="true"
        className={cn(
          "pointer-events-none absolute -right-8 -top-10 -z-10 rounded-full blur-2xl transition-transform duration-500 motion-safe:animate-liquid-shift",
          a.blob,
          isFeatured ? "h-40 w-40 opacity-40" : "h-24 w-24 opacity-25",
          "group-hover:scale-125 group-hover:opacity-40"
        )}
      />

      <div className="flex items-start justify-between gap-2">
        <div
          className={cn(
            "flex items-center justify-center rounded-2xl shadow-card transition-colors duration-300",
            a.iconBg, a.iconText, a.iconHoverBg, "group-hover:text-white group-hover:shadow-elevated",
            isFeatured ? "h-14 w-14 motion-safe:animate-float" : "h-11 w-11"
          )}
        >
          <Icon className={isFeatured ? "h-7 w-7" : "h-5 w-5"} aria-hidden="true" />
        </div>

        <div className="flex flex-col items-end gap-1">
          {highlighted && (
            <span className={cn("rounded-full px-2 py-0.5 text-2xs font-semibold", a.chip)}>
              {badgeLabel ?? "Para tu rol"}
            </span>
          )}
          {isFeatured && highlight && (
            <span className="rounded-full bg-slate-900/5 px-2 py-0.5 text-2xs font-medium text-muted-fg">
              {highlight}
            </span>
          )}
        </div>
      </div>

      <div className="flex-1">
        <h3 className={cn("font-semibold text-poli-navy", isFeatured ? "text-xl" : "text-base")}>
          {label}
        </h3>
        <p className={cn("mt-1 text-muted-fg", isFeatured ? "text-sm" : "text-sm")}>{description}</p>
      </div>

      <div
        className={cn(
          "flex items-center gap-1 text-sm font-medium text-poli-navy/70 transition-all duration-300",
          "group-hover:gap-2 group-hover:text-poli-navy"
        )}
      >
        Entrar
        <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
      </div>
    </Link>
  );
}
