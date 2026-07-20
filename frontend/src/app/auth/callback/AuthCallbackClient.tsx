"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { decodeJwtPayload } from "@/lib/jwt";

export default function AuthCallbackClient() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);

  useEffect(() => {
    const token = searchParams.get("token");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      router.replace(`/login?error=${encodeURIComponent(errorParam)}`);
      return;
    }

    if (token) {
      const payload = decodeJwtPayload(token);
      const email = typeof payload.sub === "string" ? payload.sub : undefined;
      const role = typeof payload.role === "string" ? payload.role : undefined;
      setSession(token, email, role);
      router.replace("/resumen-general");
    } else {
      router.replace("/login?error=missing_token");
    }
  }, [searchParams, setSession, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="text-center">
        <div className="mx-auto mb-4 h-6 w-6 animate-spin rounded-full border-2 border-poli-blue border-t-transparent" />
        <p className="text-slate-600">Procesando autenticación…</p>
      </div>
    </div>
  );
}
