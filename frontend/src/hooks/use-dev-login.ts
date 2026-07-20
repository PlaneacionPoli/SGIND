"use client";

import { useState } from "react";
import { fetchDevToken } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

export function useDevLogin() {
  const setSession = useAuthStore((s) => s.setSession);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function login(email = "dev@poligran.edu.co", role = "calidad") {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDevToken(email, role);
      setSession(data.access_token, email, role);
      return true;
    } catch {
      setError("No se pudo conectar con el backend. Verifique que esté activo en el puerto 8000.");
      return false;
    } finally {
      setLoading(false);
    }
  }

  return { login, loading, error };
}

export function isDevLoginEnabled(): boolean {
  return (
    process.env.NEXT_PUBLIC_ENABLE_DEV_LOGIN === "true" ||
    process.env.NODE_ENV === "development"
  );
}
