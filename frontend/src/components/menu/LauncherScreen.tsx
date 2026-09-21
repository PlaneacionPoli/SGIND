"use client";

import Image from "next/image";
import { NAV_ITEM_META, navItemsForRole, splitIntoRows } from "@/config/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { OrbitWaveRow } from "@/components/menu/OrbitWaveRow";
import { useGreeting } from "@/components/menu/useGreeting";

/** Puntos de brillo fijos (sin Math.random en render, para evitar mismatch de hidratación). */
const PARTICLES = [
  { left: 6, top: 12, delay: 0 },
  { left: 14, top: 68, delay: 400 },
  { left: 22, top: 34, delay: 900 },
  { left: 31, top: 82, delay: 1300 },
  { left: 38, top: 18, delay: 200 },
  { left: 47, top: 55, delay: 1600 },
  { left: 55, top: 8, delay: 700 },
  { left: 63, top: 72, delay: 1100 },
  { left: 71, top: 28, delay: 300 },
  { left: 79, top: 60, delay: 1800 },
  { left: 87, top: 15, delay: 500 },
  { left: 93, top: 78, delay: 1000 },
  { left: 10, top: 92, delay: 1500 },
  { left: 50, top: 95, delay: 800 },
  { left: 90, top: 45, delay: 200 },
] as const;

export function LauncherScreen() {
  const { email, role } = useAuthStore();
  const greeting = useGreeting();
  const firstName = email?.split("@")[0];

  // Orden fijo: Resumen General, CMI Estratégico, CMI por Procesos, Informe por
  // Procesos, Plan de Mejoramiento, Seguimiento Operativo, Gestión OM. El rol
  // "procesos" solo ve las cinco primeras (los administradores y calidad/desempeno
  // ven las siete); las filas se reparten parejas (7 → 4+3, 5 → 3+2).
  const items = navItemsForRole(role).filter((item) => Boolean(NAV_ITEM_META[item.href]));
  const rows = splitIntoRows(items);

  return (
    <div className="relative flex h-screen flex-col overflow-hidden bg-[radial-gradient(ellipse_at_top,#16345f_0%,#0a1a33_45%,#050d1a_100%)]">
      {/* Resplandores difusos de profundidad */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-32 -top-32 h-96 w-96 animate-blob-slow rounded-full bg-poli-blue/20 blur-3xl" />
        <div className="absolute -right-24 top-1/3 h-80 w-80 animate-blob rounded-full bg-cyan-400/10 blur-3xl [animation-delay:-4s]" />
      </div>

      {/* Partículas titilantes */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {PARTICLES.map((particle, index) => (
          <span
            key={index}
            style={{
              left: `${particle.left}%`,
              top: `${particle.top}%`,
              animationDelay: `${particle.delay}ms`,
            }}
            className="absolute h-1 w-1 rounded-full bg-cyan-100 motion-safe:animate-twinkle"
          />
        ))}
      </div>

      <div className="relative z-10 mx-auto flex h-full w-full max-w-6xl flex-col overflow-hidden px-6 py-4 sm:py-6">
        <header className="flex flex-shrink-0 flex-wrap items-center gap-3 animate-fade-in">
          <span className="flex items-center rounded-xl bg-white px-2.5 py-1.5 shadow-elevated">
            <Image
              src="/poli-logo.png"
              alt="Politécnico Grancolombiano"
              width={160}
              height={90}
              priority
              className="h-7 w-auto object-contain sm:h-8"
            />
          </span>
          <div>
            <p className="text-xs text-white/70 sm:text-sm">
              {greeting}
              {firstName ? `, ${firstName}` : ""}
            </p>
            <h1 className="text-lg font-semibold text-white sm:text-xl">
              Panel de indicadores
            </h1>
          </div>
          {role && (
            <span className="ml-auto rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium capitalize text-white backdrop-blur-sm">
              {role}
            </span>
          )}
        </header>

        <section className="flex min-h-0 flex-1 flex-col justify-evenly gap-8 overflow-y-auto py-2 sm:overflow-visible">
          {rows.map((rowItems, rowIndex) => (
            <OrbitWaveRow
              key={rowIndex}
              items={rowItems}
              rowIndex={rowIndex}
              currentRole={role}
            />
          ))}
        </section>
      </div>
    </div>
  );
}
