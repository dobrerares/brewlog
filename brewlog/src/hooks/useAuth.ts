import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

export type CurrentUser = {
  id: string;
  email: string;
  roles: string[];
  permissions: string[];
};

type State =
  | { status: "loading" }
  | { status: "anon" }
  | { status: "auth"; user: CurrentUser };

export function useAuth() {
  const [state, setState] = useState<State>({ status: "loading" });

  const refresh = useCallback(async () => {
    try {
      const user = await api<CurrentUser>("/api/v1/auth/me");
      setState({ status: "auth", user });
    } catch {
      setState({ status: "anon" });
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(
    async (email: string, password: string) => {
      await api("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      await refresh();
    },
    [refresh],
  );

  const register = useCallback(
    async (email: string, password: string) => {
      await api("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(async () => {
    await api("/api/v1/auth/logout", { method: "POST" });
    setState({ status: "anon" });
  }, []);

  const hasPermission = useCallback(
    (code: string) =>
      state.status === "auth" && state.user.permissions.includes(code),
    [state],
  );

  return {
    state,
    user: state.status === "auth" ? state.user : null,
    permissions: state.status === "auth" ? state.user.permissions : [],
    hasPermission,
    login,
    register,
    logout,
    refresh,
  };
}
