"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { NAV_ITEMS } from "@/config/navigation";
import { destinoValido, fetchMarcos, moduloHref, type Marco } from "@/lib/pdi";
import { useAuthReady } from "@/stores/auth-store";

export default function SeleccionPdiPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Cargando…</p>}>
      <SeleccionPdiContent />
    </Suspense>
  );
}

function SeleccionPdiContent() {
  const { isAuthenticated } = useAuthReady();
  const destino = destinoValido(useSearchParams().get("destino")) ?? "/resumen-general";
  const modulo = NAV_ITEMS.find((i) => i.href === destino)?.label ?? "Resumen General";

  const marcosQuery = useQuery({
    queryKey: ["marcos", "PDI"],
    queryFn: () => fetchMarcos("PDI"),
    enabled: isAuthenticated,
  });

  // Más reciente primero: el ciclo activo encabeza la selección.
  const marcos = [...(marcosQuery.data ?? [])].sort((a, b) => b.orden - a.orden);

  return (
    <div className="mx-auto max-w-5xl space-y-6 py-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">{modulo}</p>
        <h2 className="mt-1 text-2xl font-bold text-slate-900">Selecciona el Plan de Desarrollo Institucional</h2>
        <p className="mt-1 text-sm text-slate-600">
          Cada PDI tiene su propio catálogo de indicadores, líneas, objetivos y metas estratégicas.
        </p>
      </div>

      {marcosQuery.isLoading && <p className="text-sm text-slate-500">Cargando ciclos…</p>}
      {marcosQuery.isError && (
        <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700">
          No se pudieron cargar los ciclos PDI. Intenta de nuevo más tarde.
        </p>
      )}

      <div className="grid gap-5 sm:grid-cols-2">
        {marcos.map((m) => (
          <PdiCard key={m.version_id} marco={m} href={moduloHref(destino, m.version_id)} />
        ))}
      </div>
    </div>
  );
}

function PdiCard({ marco, href }: { marco: Marco; href: string }) {
  const activo = marco.estado === "activo";
  const datos = marco.anio_datos_hasta
    ? `Datos ${marco.anio_datos_desde}–${marco.anio_datos_hasta}`
    : `Datos desde ${marco.anio_datos_desde}`;

  return (
    <Link
      href={href}
      className="group overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
    >
      <div className="relative bg-white">
        {marco.imagen ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={marco.imagen} alt={marco.nombre} className="h-56 w-full object-contain p-3" />
        ) : (
          <div
            className={`flex h-56 items-center justify-center text-3xl font-bold text-white ${
              activo ? "bg-gradient-to-br from-[#1F6FB5] to-[#0a1a33]" : "bg-gradient-to-br from-slate-500 to-slate-800"
            }`}
          >
            {marco.nombre}
          </div>
        )}
        <span
          className={`absolute right-3 top-3 rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-wider ${
            activo ? "bg-emerald-500 text-white" : "bg-slate-600 text-white"
          }`}
        >
          {activo ? "Vigente" : "Cerrado"}
        </span>
      </div>
      <div className="flex items-center justify-between gap-4 p-5">
        <div>
          <p className="text-base font-semibold text-slate-900">{marco.nombre}</p>
          <p className="text-sm text-slate-700">{marco.descripcion}</p>
          <p className="mt-1 text-xs text-slate-500">{datos}</p>
        </div>
        <span className="text-sm font-semibold text-blue-700 transition group-hover:translate-x-0.5">Entrar →</span>
      </div>
    </Link>
  );
}
