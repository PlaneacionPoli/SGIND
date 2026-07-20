"use client";

import { useEffect, useState } from "react";
import { fetchHealth, api } from "@/lib/api";
import { useAuthReady } from "@/stores/auth-store";

interface CheckResult {
  label: string;
  status: "ok" | "error" | "loading" | "warn";
  detail: string;
}

const STATUS_STYLES: Record<
  CheckResult["status"],
  { dot: string; badge: string; text: string; icon: string }
> = {
  ok: { dot: "bg-green-500", badge: "bg-green-50 border-green-200", text: "text-green-800", icon: "✓" },
  error: { dot: "bg-red-500", badge: "bg-red-50 border-red-200", text: "text-red-800", icon: "✗" },
  warn: { dot: "bg-amber-400", badge: "bg-amber-50 border-amber-200", text: "text-amber-800", icon: "⚠" },
  loading: {
    dot: "bg-slate-300 animate-pulse",
    badge: "bg-slate-50 border-slate-200",
    text: "text-slate-500",
    icon: "…",
  },
};

function useSystemChecks(isAuthenticated: boolean) {
  const [checks, setChecks] = useState<CheckResult[]>([
    { label: "Backend API", status: "loading", detail: "Verificando…" },
    { label: "Autenticación", status: "loading", detail: "Verificando…" },
    { label: "Datos CMI", status: "loading", detail: "Verificando…" },
    { label: "Datos Seguimiento", status: "loading", detail: "Verificando…" },
    { label: "Plan de Mejoramiento", status: "loading", detail: "Verificando…" },
  ]);

  const set = (label: string, patch: Partial<CheckResult>) =>
    setChecks((prev) => prev.map((c) => (c.label === label ? { ...c, ...patch } : c)));

  useEffect(() => {
    fetchHealth()
      .then((h) => set("Backend API", { status: "ok", detail: `v${h.version} · env: ${h.environment}` }))
      .catch((e: unknown) =>
        set("Backend API", { status: "error", detail: String((e as { message?: string })?.message ?? "Sin respuesta") })
      );

    set("Autenticación", {
      status: isAuthenticated ? "ok" : "warn",
      detail: isAuthenticated ? "Sesión activa (dev login)" : "Sin sesión iniciada",
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) return;

    api
      .get("/cmi/filtros")
      .then((r) => {
        const anios: number[] = r.data?.anios ?? [];
        set("Datos CMI", {
          status: anios.length > 0 ? "ok" : "warn",
          detail: anios.length > 0 ? `Años: ${anios.join(", ")}` : "Sin años disponibles",
        });
      })
      .catch(() => set("Datos CMI", { status: "error", detail: "Error al consultar /cmi/filtros" }));

    api
      .get("/seguimiento/filtros")
      .then((r) => {
        const anios: number[] = r.data?.anios ?? [];
        set("Datos Seguimiento", {
          status: anios.length > 0 ? "ok" : "warn",
          detail: anios.length > 0 ? `Años: ${anios.join(", ")}` : "Sin años disponibles",
        });
      })
      .catch(() => set("Datos Seguimiento", { status: "error", detail: "Error al consultar /seguimiento/filtros" }));

    api
      .get("/plan-mejoramiento/filtros")
      .then((r) => {
        const anios: number[] = r.data?.anios ?? [];
        set("Plan de Mejoramiento", {
          status: anios.length > 0 ? "ok" : "warn",
          detail: anios.length > 0 ? `Años: ${anios.join(", ")}` : "Sin años disponibles",
        });
      })
      .catch(() =>
        set("Plan de Mejoramiento", { status: "error", detail: "Error al consultar /plan-mejoramiento/filtros" })
      );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  return checks;
}

const MODULOS = [
  { modulo: "Resumen General", ruta: "/resumen-general" },
  { modulo: "CMI Estratégico", ruta: "/cmi-estrategico" },
  { modulo: "CMI Procesos", ruta: "/cmi-procesos" },
  { modulo: "Gestión OM", ruta: "/gestion-om" },
  { modulo: "Plan de Mejoramiento", ruta: "/plan-mejoramiento" },
  { modulo: "Seguimiento Operativo", ruta: "/seguimiento-operativo" },
  { modulo: "Informe por Procesos", ruta: "/informe-procesos" },
  { modulo: "PDI / Acreditación", ruta: "/pdi-acreditacion" },
  { modulo: "Diagnóstico", ruta: "/diagnostico" },
];

export default function DiagnosticoPage() {
  const { isAuthenticated } = useAuthReady();
  const checks = useSystemChecks(isAuthenticated);

  const okCount = checks.filter((c) => c.status === "ok").length;
  const errCount = checks.filter((c) => c.status === "error").length;
  const loadCount = checks.filter((c) => c.status === "loading").length;

  const globalStatus = loadCount > 0 ? "loading" : errCount > 0 ? "error" : "ok";
  const g = STATUS_STYLES[globalStatus];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Diagnóstico del Sistema</h2>
        <p className="mt-1 text-slate-600">
          Verificación de conectividad, disponibilidad de datos y estado de los módulos.
        </p>
      </div>

      {/* Banner global */}
      <div className={`rounded-xl border p-4 ${g.badge}`}>
        <div className="flex items-center gap-3">
          <span className={`h-3 w-3 rounded-full ${g.dot}`} />
          <p className={`font-semibold ${g.text}`}>
            {loadCount > 0
              ? "Ejecutando diagnóstico…"
              : errCount > 0
              ? `${errCount} componente(s) con error`
              : `Sistema operativo — ${okCount}/${checks.length} checks pasados`}
          </p>
        </div>
      </div>

      {/* Check cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {checks.map((check) => {
          const s = STATUS_STYLES[check.status];
          return (
            <div key={check.label} className={`rounded-xl border p-4 ${s.badge}`}>
              <div className="mb-2 flex items-center gap-2">
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded-full text-xs font-bold text-white ${s.dot}`}
                >
                  {s.icon}
                </span>
                <span className={`text-sm font-semibold ${s.text}`}>{check.label}</span>
              </div>
              <p className={`text-xs ${s.text}`}>{check.detail}</p>
            </div>
          );
        })}
      </div>

      {/* Entorno */}
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-bold text-slate-800">Entorno de ejecución</h3>
        <dl className="grid gap-2 text-sm sm:grid-cols-2">
          {[
            ["Frontend", "Next.js 14 App Router · TypeScript · Tailwind"],
            ["Backend", "FastAPI · SQLAlchemy 2.0 async · asyncpg"],
            ["Base de datos", "PostgreSQL 16"],
            ["Auth", "Dev login activo (Azure AD en Fase 7)"],
            ["API URL", process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"],
            ["Sesión", isAuthenticated ? "Autenticada" : "Sin sesión"],
          ].map(([label, value]) => (
            <div key={label} className="flex gap-2">
              <dt className="min-w-[110px] font-medium text-slate-500">{label}:</dt>
              <dd className="text-slate-800">{value}</dd>
            </div>
          ))}
        </dl>
      </div>

      {/* Tabla módulos */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <h3 className="border-b border-slate-100 px-4 py-3 text-sm font-bold text-slate-800">
          Estado de módulos — Fase 5
        </h3>
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2 text-left">Módulo</th>
              <th className="px-3 py-2 text-left">Ruta</th>
              <th className="px-3 py-2 text-left">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {MODULOS.map((row) => (
              <tr key={row.ruta} className="hover:bg-slate-50">
                <td className="px-3 py-2 font-medium text-slate-800">{row.modulo}</td>
                <td className="px-3 py-2 font-mono text-xs text-slate-500">{row.ruta}</td>
                <td className="px-3 py-2">
                  <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                    Conectado
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
