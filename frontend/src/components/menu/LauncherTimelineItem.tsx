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
  const flipped = index % 2 === 1;

  return (
    <div
      className={cn("flex motion-safe:animate-card-in", flipped ? "justify-start" : "justify-end")}
      style={{ animationDelay: `${index * 90}ms` }}
    >
      <Link
        href={href}
        className={cn(
          "group relative flex h-16 w-[88%] items-center rounded-full shadow-lg transition-transform duration-300 sm:w-[78%]",
          "hover:-translate-y-0.5 hover:shadow-xl focus-visible:-translate-y-0.5 focus-visible:shadow-xl active:scale-[0.99]",
          flipped ? "justify-start pl-6 pr-[4.5rem]" : "justify-end pl-[4.5rem] pr-6",
          highlighted && "ring-2 ring-poli-gold ring-offset-2 ring-offset-slate-50"
        )}
        style={{ background: pillColor }}
      >
        <span
          className={cn(
            "absolute top-1/2 flex h-16 w-16 -translate-y-1/2 items-center justify-center rounded-full bg-white shadow-md ring-4 ring-slate-50 transition-transform duration-300 group-hover:scale-105",
            flipped ? "-right-2" : "-left-2"
          )}
        >
          <Icon size={26} style={{ color: pillColor }} aria-hidden="true" />
        </span>

        <span className="text-base font-bold text-white sm:text-lg">{label}</span>

        {highlighted && (
          <span className="absolute -top-2 left-1/2 -translate-x-1/2 rounded-full bg-poli-gold px-2 py-0.5 text-2xs font-semibold text-white shadow-sm">
            Tu rol
          </span>
        )}
      </Link>
    </div>
  );
}
