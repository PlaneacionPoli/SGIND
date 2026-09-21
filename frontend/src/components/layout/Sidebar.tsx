"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  ArrowLeft,
  ClipboardCheck,
  FileText,
  LayoutDashboard,
  Target,
  Workflow,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import { navItemsForRole } from "@/config/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";

const NAV_ICONS: Record<string, LucideIcon> = {
  "/resumen-general": LayoutDashboard,
  "/cmi-estrategico": Target,
  "/cmi-procesos": Workflow,
  "/informe-procesos": FileText,
  "/plan-mejoramiento": ClipboardCheck,
  "/seguimiento-operativo": Activity,
  "/gestion-om": Wrench,
};

/** Texto que solo se ve con el sidebar expandido. */
const REVEAL = "whitespace-nowrap opacity-0 transition-opacity duration-200 group-hover:opacity-100 group-focus-within:opacity-100";

/**
 * Sidebar compacto: por defecto solo íconos (w-16); al pasar el cursor o al enfocar/tocar
 * un ítem se expande a w-64 por encima del contenido, sin desplazarlo. El contenedor
 * exterior reserva el ancho compacto para que el layout no salte.
 */
export function Sidebar() {
  const pathname = usePathname();
  const role = useAuthStore((s) => s.role);

  return (
    <div className="relative h-full w-16 shrink-0">
      <aside className="group absolute inset-y-0 left-0 z-40 flex w-16 flex-col overflow-hidden border-r border-slate-200 bg-poli-navy text-white transition-[width] duration-200 hover:w-64 focus-within:w-64 hover:shadow-elevated focus-within:shadow-elevated">
        <div className="max-h-0 overflow-hidden border-b border-white/10 px-5 opacity-0 transition-all duration-200 group-hover:max-h-40 group-hover:py-6 group-hover:opacity-100 group-focus-within:max-h-40 group-focus-within:py-6 group-focus-within:opacity-100">
          {/* El logo tiene texto azul oscuro: necesita fondo blanco sobre el sidebar navy */}
          <span className="inline-flex items-center rounded-xl bg-white px-3 py-2 shadow-elevated">
            <Image
              src="/poli-logo.png"
              alt="Politécnico Grancolombiano"
              width={1280}
              height={728}
              priority
              className="h-9 w-auto object-contain"
            />
          </span>
          <h1 className="mt-3 whitespace-nowrap text-lg font-bold leading-tight text-white">Sistema de Indicadores</h1>
        </div>

        <nav className="flex-1 overflow-y-auto overflow-x-hidden px-2.5 py-4">
          <Link
            href="/menu"
            aria-label="Menú principal"
            className="mb-4 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-slate-300 transition-colors hover:bg-white/10 hover:text-white"
          >
            <ArrowLeft className="h-5 w-5 shrink-0" aria-hidden="true" />
            <span className={REVEAL}>Menú principal</span>
          </Link>

          <ul className="space-y-1">
            {navItemsForRole(role).map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              const Icon = NAV_ICONS[item.href] ?? LayoutDashboard;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-label={item.label}
                    title={item.label}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                      active
                        ? "bg-poli-blue font-medium text-white"
                        : "text-slate-300 hover:bg-white/10 hover:text-white"
                    )}
                  >
                    <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                    <span className={REVEAL}>{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <footer
          className={cn(
            "max-h-0 overflow-hidden border-white/10 px-5 text-xs leading-relaxed text-slate-400 opacity-0 transition-all duration-200",
            "group-hover:max-h-40 group-hover:border-t group-hover:py-4 group-hover:opacity-100",
            "group-focus-within:max-h-40 group-focus-within:border-t group-focus-within:py-4 group-focus-within:opacity-100"
          )}
        >
          <span className="whitespace-nowrap">
            Politécnico Grancolombiano
            <br />
            Gerencia de Planeación
            <br />
            Medición y Mejora
          </span>
        </footer>
      </aside>
    </div>
  );
}
