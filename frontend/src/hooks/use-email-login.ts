"use client";

import { useState } from "react";
import { fetchEmailLogin } from "@/lib/api";
import { decodeJwtPayload } from "@/lib/jwt";
import { useAuthStore } from "@/stores/auth-store";

export function useEmailLogin() {
  const setSession = useAuthStore((s) => s.setSession);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function login(email: string) {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEmailLogin(email);
      const payload = decodeJwtPayload(data.access_token);
      const role = typeof payload.role === "string" ? payload.role : undefined;
      setSession(data.access_token, email, role);
      return true;
    } catch (err) {
      const message =
        typeof err === "object" && err !== null && "response" in err
          ? ((err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
            "No se pudo iniciar sesión.")
          : "No se pudo conectar con el backend.";
      setError(message);
      return false;
    } finally {
      setLoading(false);
    }
  }

  return { login, loading, error };
}

export function isEmailLoginMode(): boolean {
  return process.env.NEXT_PUBLIC_AUTH_MODE === "email";
}
