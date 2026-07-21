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
import { LauncherVerticalCard } from "@/components/menu/LauncherVerticalCard";
import { useGreeting } from "@/components/menu/useGreeting";

function isHighlighted(roles: Role[] | undefined, currentRole: string | null) {
  if (!roles || !currentRole) return false;
  return roles.includes(currentRole as Role);
}

export function LauncherScreen() {
  const { email, role } = useAuthStore();
  const greeting = useGreeting();
  const firstName = email?.split("@")[0];

  // Orden fijo: siempre Resumen General, CMI Estratégico, CMI por Procesos,
  // Informe por Procesos, en ese orden — el rol solo resalta (ring/badge),
  // nunca reordena ni saca tarjetas a una sección aparte.
  const items = NAV_ITEMS.map((item) => ({
    ...item,
    meta: NAV_ITEM_META[item.href],
    highlighted: isHighlighted(NAV_ITEM_META[item.href]?.roles, role),
  })).filter((item) => Boolean(item.meta));

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-50">
      {/* Fondo animado — modo claro, efecto "liquid glass" */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-24 -top-24 h-96 w-96 animate-blob rounded-full bg-poli-blue-50 blur-3xl" />
        <div className="absolute bottom-0 right-0 h-96 w-96 animate-blob-slow rounded-full bg-poli-gold-50 blur-3xl [animation-delay:-6s]" />
        <div className="absolute left-1/3 top-1/2 h-72 w-72 animate-blob rounded-full bg-violet-100 blur-3xl [animation-delay:-3s]" />
      </div>

      <div className="relative z-10 mx-auto max-w-6xl px-6 pb-16 pt-10">
        <header className="mb-8 flex flex-wrap items-center gap-4 rounded-2xl border border-white/60 bg-white/60 p-4 shadow-card backdrop-blur-xl animate-fade-in">
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

        <section className="grid grid-cols-1 gap-5 py-2 sm:grid-cols-2 lg:grid-cols-4">
          {items.map((item, index) => (
            <LauncherVerticalCard
              key={item.href}
              href={item.href}
              label={item.label}
              meta={item.meta}
              index={index}
              highlighted={item.highlighted}
            />
          ))}
        </section>

        {BETA_ITEMS.length > 0 && (
          <section className="mt-10">
            <p className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-fg">
              <span className="rounded-full bg-slate-200 px-2 py-0.5 text-slate-600">Beta</span>
              Funciones en construcción
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
                    index={items.length + index}
                    highlighted={false}
                    className="border-dashed"
                  />
                );
              })}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
