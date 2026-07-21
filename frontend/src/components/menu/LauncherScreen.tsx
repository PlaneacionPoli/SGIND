"use client";

import Image from "next/image";
import {
  BETA_ITEM_META,
  BETA_ITEMS,
  NAV_ITEM_META,
  NAV_ITEMS,
  type Role,
} from "@/config/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { LauncherCard } from "@/components/menu/LauncherCard";
import { useGreeting } from "@/components/menu/useGreeting";

function isHighlighted(roles: Role[] | undefined, currentRole: string | null) {
  if (!roles || !currentRole) return false;
  return roles.includes(currentRole as Role);
}

export function LauncherScreen() {
  const { email, role } = useAuthStore();
  const greeting = useGreeting();
  const firstName = email?.split("@")[0];

  const sortedNavItems = [...NAV_ITEMS].sort((a, b) => {
    const aHighlighted = isHighlighted(NAV_ITEM_META[a.href]?.roles, role);
    const bHighlighted = isHighlighted(NAV_ITEM_META[b.href]?.roles, role);
    return aHighlighted === bHighlighted ? 0 : aHighlighted ? -1 : 1;
  });

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-50">
      {/* Fondo animado — modo claro */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-24 -top-24 h-96 w-96 animate-blob rounded-full bg-poli-blue-50 blur-3xl" />
        <div className="absolute bottom-0 right-0 h-96 w-96 animate-blob-slow rounded-full bg-poli-gold-50 blur-3xl [animation-delay:-6s]" />
      </div>

      <div className="relative z-10 mx-auto max-w-6xl px-6 pb-16 pt-10">
        <header className="mb-8 flex flex-wrap items-center gap-4 animate-fade-in">
          <Image
            src="/poli-logo.png"
            alt="Politécnico Grancolombiano"
            width={160}
            height={90}
            priority
            className="h-10 w-auto object-contain"
          />
          <div>
            <p className="text-sm text-muted-fg">
              {greeting}
              {firstName ? `, ${firstName}` : ""}
            </p>
            <h1 className="text-2xl font-semibold text-poli-navy">
              Panel de indicadores
            </h1>
          </div>
          {role && (
            <span className="ml-auto rounded-full bg-poli-navy-50 px-3 py-1 text-xs font-medium capitalize text-poli-navy">
              {role}
            </span>
          )}
        </header>

        <section>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {sortedNavItems.map((item, index) => {
              const meta = NAV_ITEM_META[item.href];
              if (!meta) return null;
              return (
                <LauncherCard
                  key={item.href}
                  href={item.href}
                  label={item.label}
                  meta={meta}
                  index={index}
                  highlighted={isHighlighted(meta.roles, role)}
                />
              );
            })}
          </div>
        </section>

        <section className="mt-10">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-fg">
            Beta
          </p>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {BETA_ITEMS.map((item, index) => {
              const meta = BETA_ITEM_META[item.href];
              if (!meta) return null;
              return (
                <LauncherCard
                  key={item.href}
                  href={item.href}
                  label={item.label}
                  meta={meta}
                  index={sortedNavItems.length + index}
                  highlighted={false}
                />
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
