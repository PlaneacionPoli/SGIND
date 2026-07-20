import { Suspense } from "react";
import AuthCallbackClient from "./AuthCallbackClient";

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-50">
          <p className="text-slate-600">Procesando autenticación…</p>
        </div>
      }
    >
      <AuthCallbackClient />
    </Suspense>
  );
}
