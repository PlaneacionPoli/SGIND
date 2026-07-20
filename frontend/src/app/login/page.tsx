"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthReady } from "@/stores/auth-store";
import { isDevLoginEnabled, useDevLogin } from "@/hooks/use-dev-login";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const ERROR_MESSAGES: Record<string, string> = {
  missing_token: "No se recibió el token de autenticación.",
  access_denied: "Acceso denegado. Verifica que tu cuenta esté autorizada.",
  invalid_request: "Error en la solicitud de autenticación.",
};

export default function LoginPage() {
  const { ready, isAuthenticated } = useAuthReady();
  const { login, loading, error: devLoginError } = useDevLogin();
  const router = useRouter();
  const searchParams = useSearchParams();
  const showDevLogin = isDevLoginEnabled();

  const errorParam = searchParams.get("error");
  const authError = errorParam
    ? (ERROR_MESSAGES[errorParam] ?? "Error de autenticación. Inténtalo de nuevo.")
    : null;

  // Si ya está autenticado, redirigir al dashboard
  useEffect(() => {
    if (ready && isAuthenticated) {
      router.replace("/resumen-general");
    }
  }, [ready, isAuthenticated, router]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-poli-blue border-t-transparent" />
      </div>
    );
  }

  async function handleDevLogin() {
    const ok = await login();
    if (ok) router.replace("/resumen-general");
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-slate-50 to-slate-100 px-4">
      <div className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        {/* Logo / título */}
        <div className="mb-8 text-center">
          <div className="mb-3 inline-flex h-14 w-14 items-center justify-center rounded-xl bg-poli-blue text-2xl font-bold text-white">
            P
          </div>
          <h1 className="text-xl font-semibold text-slate-800">SGIND v2</h1>
          <p className="mt-1 text-sm text-slate-500">
            Sistema de Indicadores Estratégicos
          </p>
        </div>

        {/* Botón principal: Microsoft / Azure AD */}
        <a
          href={`${API_URL}/api/v1/auth/login`}
          className="flex w-full items-center justify-center gap-3 rounded-lg bg-[#2563eb] px-4 py-3 text-sm font-medium text-white transition hover:bg-[#1d4ed8] focus:outline-none focus:ring-2 focus:ring-[#2563eb] focus:ring-offset-2"
        >
          <svg className="h-5 w-5" viewBox="0 0 21 21" fill="none" aria-hidden="true">
            <rect x="1" y="1" width="9" height="9" fill="#f25022" />
            <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
            <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
            <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
          </svg>
          Iniciar sesión con Microsoft
        </a>

        <p className="mt-3 text-center text-xs text-slate-400">
          Usa tu cuenta institucional @poligran.edu.co
        </p>

        {/* Error de autenticación */}
        {authError && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-center text-xs text-red-700">
            {authError}
          </div>
        )}

        {/* Dev login — solo en desarrollo */}
        {showDevLogin && (
          <>
            <div className="my-5 flex items-center gap-3">
              <hr className="flex-1 border-slate-200" />
              <span className="text-xs text-slate-400">o</span>
              <hr className="flex-1 border-slate-200" />
            </div>

            <button
              type="button"
              onClick={handleDevLogin}
              disabled={loading}
              className="w-full rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm font-medium text-emerald-800 transition hover:bg-emerald-100 disabled:opacity-50"
            >
              {loading ? "Conectando…" : "Acceso de desarrollo"}
            </button>

            {devLoginError && (
              <p className="mt-2 text-center text-xs text-red-600">{devLoginError}</p>
            )}

            <p className="mt-2 text-center text-xs text-slate-400">
              Solo disponible en entorno de desarrollo
            </p>
          </>
        )}
      </div>

      <p className="mt-6 text-center text-xs text-slate-400">
        Politécnico Grancolombiano · {new Date().getFullYear()}
      </p>
    </div>
  );
}
