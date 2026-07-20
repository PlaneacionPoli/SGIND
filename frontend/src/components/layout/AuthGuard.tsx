"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthReady } from "@/stores/auth-store";

/**
 * Wrapper de protección de rutas. Redirige a /login si no hay sesión activa.
 * Renderiza null (pantalla en blanco) mientras Zustand rehidrata desde localStorage.
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { ready, isAuthenticated } = useAuthReady();
  const router = useRouter();

  useEffect(() => {
    if (ready && !isAuthenticated) {
      router.replace("/login");
    }
  }, [ready, isAuthenticated, router]);

  // Mientras rehidrata, mostrar spinner mínimo
  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-poli-blue border-t-transparent" />
      </div>
    );
  }

  // Si no autenticado, no renderizar nada (la redirección ya fue disparada)
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
