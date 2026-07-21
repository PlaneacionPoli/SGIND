"use client";

import Link from "next/link";
import type { NavItemMeta } from "@/config/navigation";
import { cn } from "@/lib/utils";

interface LauncherCardProps {
  href: string;
  label: string;
  meta: NavItemMeta;
  index: number;
  highlighted: boolean;
  badgeLabel?: string;
}

export function LauncherCard({
  href,
  label,
  meta,
  index,
  highlighted,
  badgeLabel,
}: LauncherCardProps) {
  const { Icon, description } = meta;

  return (
    <Link
      href={href}
      style={{ animationDelay: `${index * 60}ms` }}
      className={cn(
        "card group relative flex flex-col gap-3 p-5 motion-safe:animate-card-in",
        "transition-all duration-250 hover:-translate-y-1 hover:shadow-elevated",
        "focus-visible:-translate-y-1 focus-visible:shadow-elevated active:scale-[0.98]",
        highlighted && "ring-2 ring-poli-gold ring-offset-2"
      )}
    >
      {highlighted && (
        <span className="absolute right-3 top-3 rounded-full bg-poli-gold-50 px-2 py-0.5 text-2xs font-medium text-poli-gold">
          {badgeLabel ?? "Para tu rol"}
        </span>
      )}

      <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-poli-blue-50 text-poli-blue transition-colors duration-250 group-hover:bg-poli-blue group-hover:text-white">
        <Icon className="h-5 w-5" aria-hidden="true" />
      </div>

      <h3 className="font-medium text-poli-navy">{label}</h3>
      <p className="text-sm text-muted-fg">{description}</p>
    </Link>
  );
}
