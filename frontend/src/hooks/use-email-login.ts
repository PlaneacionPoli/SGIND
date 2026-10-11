"use client";

import { useState } from "react";
import { requestEmailOtp, verifyEmailOtp } from "@/lib/api";
import { decodeJwtPayload } from "@/lib/jwt";
import { useAuthStore } from "@/stores/auth-store";

function errorMessage(err: unknown, fallback: string): string {
  if (typeof err === "object" && err !== null && "response" in err) {
    const detail = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail;
    return typeof detail === "string" ? detail : fallback;
  }
  return "No se pudo conectar con el backend.";
}

/** Login por correo en dos pasos: 1) solicitar código, 2) verificarlo. */
export function useEmailLogin() {
  const setSession = useAuthStore((s) => s.setSession);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function requestCode(email: string) {
    setLoading(true);
    setError(null);
    try {
      await requestEmailOtp(email);
      return true;
    } catch (err) {
      setError(errorMessage(err, "No se pudo enviar el código."));
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function verifyCode(email: string, code: string) {
    setLoading(true);
    setError(null);
    try {
      const data = await verifyEmailOtp(email, code);
      const payload = decodeJwtPayload(data.access_token);
      const role = typeof payload.role === "string" ? payload.role : undefined;
      setSession(data.access_token, email, role);
      return true;
    } catch (err) {
      setError(errorMessage(err, "No se pudo iniciar sesión."));
      return false;
    } finally {
      setLoading(false);
    }
  }

  return { requestCode, verifyCode, loading, error };
}

export function isEmailLoginMode(): boolean {
  return process.env.NEXT_PUBLIC_AUTH_MODE === "email";
}
