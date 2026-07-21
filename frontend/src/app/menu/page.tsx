"use client";

import { AuthGuard } from "@/components/layout/AuthGuard";
import { LauncherScreen } from "@/components/menu/LauncherScreen";

export default function MenuPage() {
  return (
    <AuthGuard>
      <LauncherScreen />
    </AuthGuard>
  );
}
