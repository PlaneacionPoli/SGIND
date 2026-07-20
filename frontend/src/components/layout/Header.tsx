"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

export function Header() {
  const { email, role, clearSession } = useAuthStore();
  const router = useRouter();

  function handleLogout() {
    clearSession();
    router.replace("/login");
  }

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-6">
      <div className="text-sm text-slate-500">Panel de indicadores institucionales</div>
      <div className="flex items-center gap-3">
        {email ? (
          <>
            <div className="text-right text-sm">
              <div className="font-medium text-slate-800">{email}</div>
              {role && (
                <div className="text-xs capitalize text-slate-500">Rol: {role}</div>
              )}
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
            >
              Cerrar sesión
            </button>
          </>
        ) : (
          <Link
            href="/login"
            className="rounded-md bg-poli-blue px-4 py-2 text-sm font-medium text-white hover:bg-poli-blue-dark"
          >
            Iniciar sesión
          </Link>
        )}
      </div>
    </header>
  );
}
