"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { NavItemMeta } from "@/config/navigation";
import { cn } from "@/lib/utils";

interface LauncherVerticalCardProps {
  href: string;
  label: string;
  meta: NavItemMeta;
  index: number;
  highlighted: boolean;
}

export function LauncherVerticalCard({
  href,
  label,
  meta,
  index,
  highlighted,
}: LauncherVerticalCardProps) {
  const { Icon, description, pillColor } = meta;

  return (
    <Link
      href={href}
      style={{ background: pillColor, animationDelay: `${index * 90}ms` }}
      className={cn(
        "group relative flex h-full min-h-[15rem] flex-col overflow-hidden rounded-2xl p-5 shadow-lg motion-safe:animate-card-in",
        "transition-all duration-300 hover:-translate-y-1 hover:shadow-xl",
        "focus-visible:-translate-y-1 focus-visible:shadow-xl active:scale-[0.98]",
        highlighted && "ring-2 ring-poli-gold ring-offset-2 ring-offset-slate-50"
      )}
    >
      {highlighted && (
        <span className="absolute right-4 top-4 rounded-full bg-poli-gold px-2.5 py-1 text-2xs font-semibold text-white shadow-sm">
          Tu rol
        </span>
      )}

      <span className="flex h-14 w-14 items-center justify-center rounded-full bg-white shadow-sm transition-transform duration-300 group-hover:scale-105">
        <Icon size={26} style={{ color: pillColor }} aria-hidden="true" />
      </span>

      <h3 className="mt-5 text-xl font-bold leading-tight text-white">{label}</h3>
      <p className="mt-2 text-sm text-white/85">{description}</p>

      <div className="mt-auto flex items-center gap-1 pt-4 text-sm font-medium text-white/80 transition-all duration-300 group-hover:gap-2 group-hover:text-white">
        Entrar
        <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
      </div>
    </Link>
  );
}
