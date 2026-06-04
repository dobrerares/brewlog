import type { ReactNode } from "react";

import { AuthLoading } from "@/components/AuthLoading";
import { useAuth } from "@/hooks/useAuth";

export function RequirePerm({
  perm,
  children,
}: {
  perm: string;
  children: ReactNode;
}) {
  const { state, hasPermission } = useAuth();
  if (state.status === "loading") return <AuthLoading />;
  if (state.status === "anon" || !hasPermission(perm)) {
    return (
      <div className="mx-auto mt-16 max-w-md text-center text-stone-700">
        <h1 className="text-3xl font-semibold">403</h1>
        <p className="mt-2">You don't have permission to view this page.</p>
      </div>
    );
  }
  return <>{children}</>;
}
