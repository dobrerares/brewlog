import type { ReactNode } from "react";
import { Navigate } from "react-router";

import { AuthLoading } from "@/components/AuthLoading";
import { useAuth } from "@/hooks/useAuth";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { state } = useAuth();
  if (state.status === "loading") return <AuthLoading />;
  if (state.status === "anon") return <Navigate to="/login" replace />;
  return <>{children}</>;
}
