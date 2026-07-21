"use client";

import Image from "next/image";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthReady } from "@/stores/auth-store";
import { isDevLoginEnabled, useDevLogin } from "@/hooks/use-dev-login";
import { isEmailLoginMode, useEmailLogin } from "@/hooks/use-email-login";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const ERROR_MESSAGES: Record<string, string> = {
  missing_token: "No se recibió el token de autenticación.",
  access_denied: "Acceso denegado. Verifica que tu cuenta esté autorizada.",
  invalid_request: "Error en la solicitud de autenticación.",
};

function AnimatedBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute -left-32 -top-32 h-[28rem] w-[28rem] animate-blob rounded-full bg-poli-blue/30 blur-3xl" />
      <div className="absolute -right-24 top-1/3 h-[24rem] w-[24rem] animate-blob-slow rounded-full bg-cyan-500/20 blur-3xl [animation-delay:-6s]" />
      <div className="absolute bottom-[-10rem] left-1/4 h-[26rem] w-[26rem] animate-blob rounded-full bg-poli-navy/40 blur-3xl [animation-delay:-11s]" />
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-950">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-poli-blue border-t-transparent" />
        </div>
      }
    >
      <LoginPageContent />
    </Suspense>
  );
}

function LoginPageContent() {
  const { ready, isAuthenticated } = useAuthReady();
  const { login, loading, error: devLoginError } = useDevLogin();
  const emailLogin = useEmailLogin();
  const [email, setEmail] = useState("");
  const router = useRouter();
  const searchParams = useSearchParams();
  const showDevLogin = isDevLoginEnabled();
  const emailMode = isEmailLoginMode();

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
      <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950">
        <AnimatedBackground />
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-poli-blue border-t-transparent" />
      </div>
    );
  }

  async function handleDevLogin() {
    const ok = await login();
    if (ok) router.replace("/resumen-general");
  }

  async function handleEmailLogin(e: React.FormEvent) {
    e.preventDefault();
    const ok = await emailLogin.login(email);
    if (ok) router.replace("/resumen-general");
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-slate-950 px-4">
      <AnimatedBackground />

      <div className="relative z-10 w-full max-w-sm animate-fade-in rounded-2xl border border-white/10 bg-white/[0.06] p-8 shadow-overlay backdrop-blur-xl">
        {/* Logo / título */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-40 items-center justify-center">
            <Image
              src="/poli-logo.png"
              alt="Politécnico Grancolombiano"
              width={320}
              height={180}
              priority
              className="h-full w-auto object-contain drop-shadow-[0_0_18px_rgba(37,99,235,0.35)]"
            />
          </div>
          <h1 className="text-xl font-semibold text-white">SGIND v2</h1>
          <p className="mt-1 text-sm text-slate-400">
            Sistema de Indicadores Estratégicos
          </p>
        </div>

        {emailMode ? (
          <form onSubmit={handleEmailLogin}>
            <label htmlFor="email" className="mb-1 block text-xs font-medium text-slate-300">
              Correo institucional
            </label>
            <input
              id="email"
              type="email"
              required
              placeholder="nombre@poligran.edu.co"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-white/15 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-poli-blue focus:outline-none focus:ring-2 focus:ring-poli-blue/40"
            />
            <button
              type="submit"
              disabled={emailLogin.loading}
              className="mt-3 flex w-full items-center justify-center gap-3 rounded-lg bg-poli-blue px-4 py-3 text-sm font-medium text-white shadow-lg shadow-poli-blue/25 transition hover:bg-poli-blue-dark focus:outline-none focus:ring-2 focus:ring-poli-blue focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-50"
            >
              {emailLogin.loading ? "Ingresando…" : "Ingresar"}
            </button>
            {emailLogin.error && (
              <p className="mt-2 text-center text-xs text-red-400">{emailLogin.error}</p>
            )}
          </form>
        ) : (
          <a
            href={`${API_URL}/api/v1/auth/login`}
            className="flex w-full items-center justify-center gap-3 rounded-lg bg-poli-blue px-4 py-3 text-sm font-medium text-white shadow-lg shadow-poli-blue/25 transition hover:bg-poli-blue-dark focus:outline-none focus:ring-2 focus:ring-poli-blue focus:ring-offset-2 focus:ring-offset-slate-950"
          >
            <svg className="h-5 w-5" viewBox="0 0 21 21" fill="none" aria-hidden="true">
              <rect x="1" y="1" width="9" height="9" fill="#f25022" />
              <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
              <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
              <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
            </svg>
            Iniciar sesión con Microsoft
          </a>
        )}

        <p className="mt-3 text-center text-xs text-slate-500">
          Usa tu cuenta institucional @poligran.edu.co
        </p>

        {/* Error de autenticación */}
        {authError && (
          <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-center text-xs text-red-300">
            {authError}
          </div>
        )}

        {/* Dev login — solo en desarrollo */}
        {showDevLogin && (
          <>
            <div className="my-5 flex items-center gap-3">
              <hr className="flex-1 border-white/10" />
              <span className="text-xs text-slate-500">o</span>
              <hr className="flex-1 border-white/10" />
            </div>

            <button
              type="button"
              onClick={handleDevLogin}
              disabled={loading}
              className="w-full rounded-lg border border-emerald-400/30 bg-emerald-400/10 px-4 py-2.5 text-sm font-medium text-emerald-300 transition hover:bg-emerald-400/20 disabled:opacity-50"
            >
              {loading ? "Conectando…" : "Acceso de desarrollo"}
            </button>

            {devLoginError && (
              <p className="mt-2 text-center text-xs text-red-400">{devLoginError}</p>
            )}

            <p className="mt-2 text-center text-xs text-slate-500">
              Solo disponible en entorno de desarrollo
            </p>
          </>
        )}
      </div>

      <p className="relative z-10 mt-6 text-center text-xs text-slate-500">
        Politécnico Grancolombiano · {new Date().getFullYear()}
      </p>
    </div>
  );
}
