"use client";

import Link from "next/link";
import type { NavItemMeta } from "@/config/navigation";
import { cn } from "@/lib/utils";

interface LauncherTimelineItemProps {
  href: string;
  label: string;
  meta: NavItemMeta;
  index: number;
  highlighted: boolean;
}

export function LauncherTimelineItem({
  href,
  label,
  meta,
  index,
  highlighted,
}: LauncherTimelineItemProps) {
  const { Icon, pillColor } = meta;

  return (
    <Link
      href={href}
      style={{ background: pillColor, animationDelay: `${index * 90}ms` }}
      className={cn(
        "group relative flex h-16 w-full items-center gap-4 rounded-full px-3 shadow-lg motion-safe:animate-card-in",
        "transition-transform duration-300 hover:-translate-y-0.5 hover:shadow-xl",
        "focus-visible:-translate-y-0.5 focus-visible:shadow-xl active:scale-[0.99]",
        highlighted && "ring-2 ring-poli-gold ring-offset-2 ring-offset-slate-50"
      )}
    >
      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white shadow-sm transition-transform duration-300 group-hover:scale-105">
        <Icon size={22} style={{ color: pillColor }} aria-hidden="true" />
      </span>

      <span className="flex-1 text-base font-bold text-white sm:text-lg">{label}</span>

      {highlighted && (
        <span className="mr-2 shrink-0 rounded-full bg-poli-gold px-2.5 py-1 text-2xs font-semibold text-white shadow-sm">
          Tu rol
        </span>
      )}
    </Link>
  );
}
