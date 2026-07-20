"use client";

import { QueryClient, QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { isDevLoginEnabled, useDevLogin } from "@/hooks/use-dev-login";
import { setAuthToken } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

function AuthBootstrap() {
  const queryClient = useQueryClient();
  const hasHydrated = useAuthStore((s) => s.hasHydrated);
  const token = useAuthStore((s) => s.token);
  const { login } = useDevLogin();
  const [autoLoginAttempted, setAutoLoginAttempted] = useState(false);

  useEffect(() => {
    const unsub = useAuthStore.persist.onFinishHydration(() => {
      const current = useAuthStore.getState();
      if (current.token) {
        setAuthToken(current.token);
      }
      current.setHasHydrated(true);
    });
    useAuthStore.persist.rehydrate();
    return unsub;
  }, []);

  useEffect(() => {
    if (token) {
      setAuthToken(token);
    }
  }, [token]);

  useEffect(() => {
    if (!hasHydrated || autoLoginAttempted) return;
    setAutoLoginAttempted(true);

    if (!token && isDevLoginEnabled()) {
      login().then((ok) => {
        if (ok) {
          queryClient.invalidateQueries();
        }
      });
    }
  }, [hasHydrated, token, autoLoginAttempted, login, queryClient]);

  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 60_000, retry: 1 },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthBootstrap />
      {children}
    </QueryClientProvider>
  );
}
