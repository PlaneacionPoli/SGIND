"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthReady } from "@/stores/auth-store";

export default function Home() {
  const { ready, isAuthenticated } = useAuthReady();
  const router = useRouter();

  useEffect(() => {
    if (!ready) return;
    if (isAuthenticated) {
      router.replace("/resumen-general");
    } else {
      router.replace("/login");
    }
  }, [ready, isAuthenticated, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
    </div>
  );
}
