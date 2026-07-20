import { create } from "zustand";
import { persist } from "zustand/middleware";
import { setAuthToken } from "@/lib/api";

interface AuthState {
  token: string | null;
  email: string | null;
  role: string | null;
  hasHydrated: boolean;
  setSession: (token: string, email?: string, role?: string) => void;
  clearSession: () => void;
  setHasHydrated: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      email: null,
      role: null,
      hasHydrated: false,
      setSession: (token, email, role) => {
        setAuthToken(token);
        set({ token, email: email ?? null, role: role ?? null });
      },
      clearSession: () => {
        setAuthToken(null);
        set({ token: null, email: null, role: null });
      },
      setHasHydrated: (value) => set({ hasHydrated: value }),
    }),
    {
      name: "sgind-auth",
      partialize: (state) => ({
        token: state.token,
        email: state.email,
        role: state.role,
      }),
      onRehydrateStorage: () => (state, error) => {
        if (!error && state?.token) {
          setAuthToken(state.token);
        }
        useAuthStore.getState().setHasHydrated(true);
      },
    }
  )
);

export function useAuthReady() {
  const hasHydrated = useAuthStore((s) => s.hasHydrated);
  const token = useAuthStore((s) => s.token);
  return { ready: hasHydrated, token, isAuthenticated: hasHydrated && !!token };
}
