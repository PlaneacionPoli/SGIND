"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { canAccessPath } from "@/config/navigation";
import { useAuthReady, useAuthStore } from "@/stores/auth-store";

/**
 * Wrapper de protección de rutas. Redirige a /login si no hay sesión activa y
 * a /menu si el rol no puede ver la pantalla (p. ej. "procesos" en /gestion-om).
 * Renderiza null (pantalla en blanco) mientras Zustand rehidrata desde localStorage.
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { ready, isAuthenticated } = useAuthReady();
  const router = useRouter();
  const pathname = usePathname();
  const role = useAuthStore((s) => s.role);
  const allowed = canAccessPath(role, pathname);

  useEffect(() => {
    if (ready && !isAuthenticated) {
      router.replace("/login");
    } else if (ready && isAuthenticated && !allowed) {
      router.replace("/menu");
    }
  }, [ready, isAuthenticated, allowed, router]);

  // Mientras rehidrata, mostrar spinner mínimo
  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-poli-blue border-t-transparent" />
      </div>
    );
  }

  // Si no autenticado, no renderizar nada (la redirección ya fue disparada)
  if (!isAuthenticated || !allowed) {
    return null;
  }

  return <>{children}</>;
}
