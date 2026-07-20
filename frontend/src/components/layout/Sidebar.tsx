"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BETA_ITEMS, NAV_ITEMS } from "@/config/navigation";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-64 flex-col border-r border-slate-200 bg-poli-navy text-white">
      <div className="border-b border-white/10 px-5 py-6">
        <div className="text-xs font-semibold uppercase tracking-widest text-poli-gold">
          Politécnico Grancolombiano
        </div>
        <h1 className="mt-1 text-lg font-bold leading-tight">Sistema de Indicadores</h1>
        <p className="mt-1 text-xs text-slate-300">SGIND v2 — Migración</p>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                    active
                      ? "bg-poli-blue font-medium text-white"
                      : "text-slate-300 hover:bg-white/10 hover:text-white"
                  )}
                >
                  <span className="text-base opacity-80">{item.icon}</span>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="mt-6 border-t border-white/10 pt-4">
          <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Beta
          </p>
          <ul className="space-y-1">
            {BETA_ITEMS.map((item) => {
              const active = pathname === item.href;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={cn(
                      "block rounded-lg px-3 py-2 text-sm transition-colors",
                      active
                        ? "bg-poli-blue text-white"
                        : "text-slate-400 hover:bg-white/10 hover:text-white"
                    )}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </nav>
    </aside>
  );
}
