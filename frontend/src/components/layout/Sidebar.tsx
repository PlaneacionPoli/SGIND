"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { NAV_ITEMS } from "@/config/navigation";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-64 flex-col border-r border-slate-200 bg-poli-navy text-white">
      <div className="border-b border-white/10 px-5 py-6">
        <Image
          src="/poli-logo.png"
          alt="Politécnico Grancolombiano"
          width={1280}
          height={728}
          priority
          className="h-10 w-auto object-contain"
        />
        <h1 className="mt-1 text-lg font-bold leading-tight">Sistema de Indicadores</h1>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <Link
          href="/menu"
          className="mb-4 flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm text-slate-300 transition-colors hover:bg-white/10 hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Menú principal
        </Link>

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
      </nav>
    </aside>
  );
}
