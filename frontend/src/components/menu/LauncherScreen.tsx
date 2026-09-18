"use client";

import Image from "next/image";
import { NAV_ITEM_META, NAV_ITEMS } from "@/config/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { OrbitWaveRow } from "@/components/menu/OrbitWaveRow";
import { useGreeting } from "@/components/menu/useGreeting";

const ROW_SIZE = 4;

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

function chunk<T>(items: T[], size: number): T[][] {
  const rows: T[][] = [];
  for (let i = 0; i < items.length; i += size) {
    rows.push(items.slice(i, i + size));
  }
  return rows;
}

export function LauncherScreen() {
  const { email, role } = useAuthStore();
  const greeting = useGreeting();
  const firstName = email?.split("@")[0];

  // Orden fijo: siempre Resumen General, CMI Estratégico, CMI por Procesos,
  // Informe por Procesos, Plan de Mejoramiento, Seguimiento Operativo, Gestión OM —
  // el rol solo resalta (glow/badge), nunca reordena ni saca íconos del recorrido.
  const items = NAV_ITEMS.filter((item) => Boolean(NAV_ITEM_META[item.href]));
  const rows = chunk(items, ROW_SIZE);

  return (
    <div className="relative min-h-screen bg-[radial-gradient(ellipse_at_top,#16345f_0%,#0a1a33_45%,#050d1a_100%)]">
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

      <div className="relative z-10 mx-auto max-w-6xl px-6 pb-24 pt-10">
        <header className="mb-12 flex flex-wrap items-center gap-4 animate-fade-in">
          <span className="flex items-center rounded-xl bg-white px-3 py-2 shadow-elevated">
            <Image
              src="/poli-logo.png"
              alt="Politécnico Grancolombiano"
              width={160}
              height={90}
              priority
              className="h-9 w-auto object-contain"
            />
          </span>
          <div>
            <p className="text-sm text-white/70">
              {greeting}
              {firstName ? `, ${firstName}` : ""}
            </p>
            <h1 className="text-2xl font-semibold text-white">
              Panel de indicadores
            </h1>
          </div>
          {role && (
            <span className="ml-auto rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium capitalize text-white backdrop-blur-sm">
              {role}
            </span>
          )}
        </header>

        <section className="flex flex-col gap-10 sm:gap-14">
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
